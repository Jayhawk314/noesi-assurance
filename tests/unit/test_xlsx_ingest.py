# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Excel workbooks (.xlsx) ingest like CSV — read, reviewed, reperformed.

The fixture was produced by Microsoft Excel 16 from Harborline's
payments.csv, laid out the way clients send registers: a title and subtitle
above the headings (row 4), real Excel dates and currency formats, a blank
line, a totals row computed by =SUM, and a second 'Notes' sheet.
"""

import io
import zipfile
from pathlib import Path

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts import xlsx
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

ROOT = Path(__file__).resolve().parents[2]
WORKBOOK = ROOT / "tests" / "fixtures" / "excel" / "harborline_payments_register.xlsx"
PAYMENTS_CSV = ROOT / "case-studies" / "harborline-marine" / "data" / "payments.csv"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PREPARER, REVIEWER, PARTNER = "p-prep", "p-rev", "p-partner"


def test_reader_finds_the_header_and_stops_before_the_totals():
    content = WORKBOOK.read_bytes()
    assert xlsx.list_sheets(content) == ["Check register", "Notes"]
    extraction, headers, rows = xlsx.extract(content, sheet="Check register")
    assert extraction["header_row"] == 4                 # title rows skipped
    assert extraction["data_rows"] == 123
    assert extraction["stopped_at_blank_row"] == 128
    assert extraction["nonblank_rows_below_ignored"] == 1   # the =SUM total
    assert headers[:4] == ["Payment Number", "Voucher Number",
                           "Vendor Number", "Payment Amount"]
    first = rows[0]
    assert first["Payment Date"] == "2026-03-16" or first["Payment Date"].count("-") == 2
    assert all(r["Payment Amount"].replace(".", "", 1).isdigit() for r in rows)


def test_a_workbook_with_several_sheets_needs_a_choice():
    with pytest.raises(xlsx.WorkbookError, match="choose one"):
        xlsx.extract(WORKBOOK.read_bytes())


def test_formula_without_saved_value_is_refused_not_guessed():
    sheet = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Amount</t></is></c></row>'
             '<row r="2"><c r="A2"><f>SUM(B1:B9)</f></c></row></sheetData></worksheet>')
    assert "recalculate" in _refusal(_minimal_workbook(sheet))


def test_legacy_xls_is_refused_with_instructions():
    with pytest.raises(xlsx.WorkbookError, match=r"save it as \.xlsx"):
        xlsx.extract(b"\xd0\xcf\x11\xe0" + b"\x00" * 100)


def test_oversized_parts_are_refused_before_reading():
    original, xlsx.MAX_MEMBER_BYTES = xlsx.MAX_MEMBER_BYTES, 10
    try:
        with pytest.raises(xlsx.WorkbookError, match="refusing to read"):
            xlsx.list_sheets(WORKBOOK.read_bytes())
    finally:
        xlsx.MAX_MEMBER_BYTES = original


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                           ensure_tenant(conn, "xlsx"))
    yield svc
    conn.close()


def _load(service, eid, content, name, media, extraction=None, mode=None):
    artifact = service.store_source(PREPARER, eid, content=content,
                                    media_type=media, original_name=name)
    proposal = service.confirm_source_mapping(
        PREPARER, eid, role="Payments", artifact_id=artifact["artifact_id"],
        extraction=extraction)
    normalized = service.normalize_source(PREPARER, eid, proposal["spec_id"],
                                          mode=mode)
    return artifact, proposal, normalized


def test_workbook_and_csv_normalize_to_the_same_dataset(service):
    eid = service.create_engagement(PARTNER, "Harborline", "2026-12-31")["engagement_id"]

    _, csv_prop, csv_norm = _load(service, eid, PAYMENTS_CSV.read_bytes(),
                                  "payments.csv", "text/csv")
    artifact, xl_prop, xl_norm = _load(
        service, eid, WORKBOOK.read_bytes(), "payments.xlsx", XLSX_TYPE,
        extraction={"sheet": "Check register"}, mode="replace")

    # The reviewer sees which rows were read, and where reading stopped.
    assert xl_prop["extraction"]["header_row"] == 4
    assert xl_prop["extraction"]["nonblank_rows_below_ignored"] == 1
    assert xl_prop["column_map"] == csv_prop["column_map"]
    assert xl_norm["reconciliation"]["rows_loaded"] == 123
    assert xl_norm["reconciliation"]["rows_rejected"] == 0
    # Same population, whichever format the client sent: every business
    # field agrees and the control totals tie. Provenance differs, as it
    # must: source_row points at the file as received (CSV line 2, sheet
    # row 5 under the title rows) and source_hash fingerprints the raw row
    # (Excel stores 1577 where the CSV says 1577.0).
    datasets = service.sources(eid)["datasets"]
    assert datasets[0]["control_total"] == datasets[1]["control_total"]
    csv_records = service._rebuild_table(csv_prop["spec_id"]).records
    xl_records = service._rebuild_table(xl_prop["spec_id"]).records
    provenance = {"source_row", "source_hash"}
    assert [{k: v for k, v in r.items() if k not in provenance} for r in csv_records] == \
           [{k: v for k, v in r.items() if k not in provenance} for r in xl_records]
    assert csv_records[0]["source_row"] == 2
    assert xl_records[0]["source_row"] == 5
    assert xl_records[-1]["source_row"] == 127

    # The sheet choice is part of the reviewed spec and its digest.
    spec = next(s for s in service.sources(eid)["mapping_specs"]
                if s["spec_id"] == xl_prop["spec_id"])
    assert spec["status"] == "approved"
    stored = service._conn.execute(
        "SELECT spec, spec_digest FROM mapping_spec WHERE spec_id = ?",
        (xl_prop["spec_id"],)).fetchone()
    assert '"sheet": "Check register"' in stored["spec"]
    csv_digest = service._conn.execute(
        "SELECT spec_digest FROM mapping_spec WHERE spec_id = ?",
        (csv_prop["spec_id"],)).fetchone()["spec_digest"]
    assert stored["spec_digest"] != csv_digest

    # Reperform-on-read works from the vaulted workbook.
    tables = service._tables(eid)
    assert len(tables["Payments"].records) == 123

    preview = service.workbook_preview(eid, artifact["artifact_id"])
    assert [s["sheet"] for s in preview["sheets"]] == ["Check register", "Notes"]
    assert preview["sheets"][0]["suggested_header_row"] == 4


def _minimal_workbook(sheet_xml: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("xl/workbook.xml",
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


def _refusal(content: bytes) -> str:
    with pytest.raises(xlsx.WorkbookError) as info:
        xlsx.extract(content)
    return str(info.value)


# ------------------------------------------------ K2: multi-section reports
def _sectioned_report() -> bytes:
    """A reconciliation-style report: summary lines, then sections that each
    repeat the same heading row."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in (["Company"], ["Checking, Period Ending 06/30/2026"],
                ["RECONCILIATION REPORT"], [],
                ["Statement ending balance", None, None, 1000.0], [],
                ["Checks and payments cleared (2)"],
                ["DATE", "TYPE", "REF NO.", "AMOUNT"],
                ["06/02/2026", "Check", "101", -50.0],
                ["06/03/2026", "Check", "102", -25.0], [],
                ["Uncleared checks and payments (1)"],
                ["DATE", "TYPE", "REF NO.", "AMOUNT"],
                ["06/29/2026", "Check", "109", -80.0]):
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_k2_a_report_of_several_sections_is_not_read_as_one_table():
    with pytest.raises(xlsx.WorkbookError) as refused:
        xlsx.extract(_sectioned_report())
    message = str(refused.value)
    assert "repeats its heading row (DATE, TYPE, REF NO., AMOUNT) at row 13" in message
    assert "only the first section" in message


def test_k2_a_chosen_heading_row_reads_that_section_and_says_it_repeats():
    extraction, _, rows = xlsx.extract(_sectioned_report(), header_row=13)
    assert [r["REF NO."] for r in rows] == ["109"]      # the uncleared section
    assert "repeated_heading_rows" not in extraction    # nothing repeats below 13
    extraction, _, rows = xlsx.extract(_sectioned_report(), header_row=8)
    assert [r["REF NO."] for r in rows] == ["101", "102"]
    assert extraction["repeated_heading_rows"] == [13]


def test_k2_a_plain_table_is_unaffected():
    extraction, _, _ = xlsx.extract(WORKBOOK.read_bytes(), sheet="Check register")
    assert "repeated_heading_rows" not in extraction


KESTREL_REC = (ROOT / "case-studies" / "kestrel-valley-cycle" / "data" / "quickbooks"
               / "Checking_Reconciliation.xlsx")


@pytest.mark.skipif(not KESTREL_REC.is_file(), reason="case data not in tree")
def test_k2_quickbooks_reconciliation_report_is_refused_not_misread(service):
    eid = service.create_engagement(PARTNER, "Kestrel", "2026-06-30")["engagement_id"]
    art = service.store_source(PREPARER, eid, content=KESTREL_REC.read_bytes(),
                               media_type=XLSX_TYPE,
                               original_name="Checking_Reconciliation.xlsx")
    with pytest.raises(ValueError, match="report of several sections"):
        service.confirm_source_mapping(PREPARER, eid, role="Bank_reconciliation",
                                       artifact_id=art["artifact_id"])
