# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Read Excel workbooks (.xlsx) as plain rows — standard library only.

Clients send Excel, not CSV. This reader turns one sheet of an .xlsx into
the same header-keyed rows the CSV path produces, so the rest of ingestion
(mapping proposal, review, normalization, digest verification) is unchanged.

Deliberate choices:

- **Deterministic.** Same bytes + same extraction parameters -> same rows,
  so normalization can be reperformed from the vaulted original forever.
- **Values, not formatting.** Numbers come back in their shortest exact
  decimal form (``16607.94``, never ``16607.939999999999``); cells formatted
  as dates come back as ISO dates. Formulas yield the value Excel saved with
  the file; a formula saved without a value is refused, not guessed.
- **Bounded.** An .xlsx is a zip of XML. Member sizes are capped before
  anything is read, so a zip bomb fails fast. Python's expat rejects
  external entities and bounds entity expansion.
- **Legacy .xls (binary) is refused** with instructions; it is a different
  format this reader does not parse.
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from xml.etree import ElementTree as ET

MAX_MEMBER_BYTES = 200 * 1024 * 1024
MAX_ROWS = 1_000_000
HEADER_SCAN_ROWS = 25
CONVERTER = "noesi-xlsx-v1"

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
       "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
_BUILTIN_DATE_FORMATS = set(range(14, 23)) | {45, 46, 47}
_CELL_REF = re.compile(r"([A-Z]+)(\d+)")


class WorkbookError(ValueError):
    """The workbook cannot be read honestly; the message says why and what to do."""


def is_xlsx(content: bytes) -> bool:
    return content[:4] == b"PK\x03\x04"


def is_legacy_xls(content: bytes) -> bool:
    return content[:4] == b"\xd0\xcf\x11\xe0"


@dataclass(frozen=True)
class Sheet:
    name: str
    rows: list[list[str]]


def _col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _col_letters(index: int) -> str:
    out = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


def _is_date_format(code: str) -> bool:
    # Strip quoted literals, escaped chars and [colour]/[$-locale] blocks;
    # a remaining y/d, or an m next to them, marks a date. Pure time and
    # elapsed-duration formats are treated as numbers.
    stripped = re.sub(r'"[^"]*"|\\.|\[[^\]]*\]', "", code.lower())
    return bool(re.search(r"[yd]", stripped))


class _Workbook:
    def __init__(self, content: bytes):
        if is_legacy_xls(content):
            raise WorkbookError(
                "this is a legacy Excel 97-2003 (.xls) workbook; open it in "
                "Excel and save it as .xlsx (or export the sheet as CSV)")
        if not is_xlsx(content):
            raise WorkbookError("not an .xlsx workbook")
        try:
            self._zip = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile as exc:
            raise WorkbookError(f"the workbook is damaged: {exc}") from exc
        for info in self._zip.infolist():
            if info.file_size > MAX_MEMBER_BYTES:
                raise WorkbookError(
                    f"workbook part {info.filename} expands to "
                    f"{info.file_size} bytes; refusing to read it")
        workbook = self._xml("xl/workbook.xml")
        pr = workbook.find("m:workbookPr", _NS)
        self._epoch = (datetime(1904, 1, 1) if pr is not None
                       and pr.get("date1904") in ("1", "true")
                       else datetime(1899, 12, 30))
        rels = {r.get("Id"): r.get("Target")
                for r in self._xml("xl/_rels/workbook.xml.rels").findall("rel:Relationship", _NS)}
        self.sheets: list[tuple[str, str]] = []
        for sheet in workbook.findall("m:sheets/m:sheet", _NS):
            target = rels.get(sheet.get(f"{{{_NS['r']}}}id"), "")
            target = target.lstrip("/")
            path = target if target.startswith("xl/") else f"xl/{target}"
            self.sheets.append((sheet.get("name", ""), path))
        self._shared = self._shared_strings()
        self._date_styles = self._date_style_indexes()

    def _xml(self, name: str) -> ET.Element:
        try:
            with self._zip.open(name) as handle:
                return ET.parse(handle).getroot()
        except KeyError as exc:
            raise WorkbookError(f"the workbook is missing its {name} part") from exc
        except ET.ParseError as exc:
            raise WorkbookError(f"the workbook part {name} is not valid XML: {exc}") from exc

    def _has(self, name: str) -> bool:
        return name in self._zip.namelist()

    def _shared_strings(self) -> list[str]:
        if not self._has("xl/sharedStrings.xml"):
            return []
        root = self._xml("xl/sharedStrings.xml")
        return ["".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t"))
                for si in root.findall("m:si", _NS)]

    def _date_style_indexes(self) -> set[int]:
        if not self._has("xl/styles.xml"):
            return set()
        root = self._xml("xl/styles.xml")
        custom = {int(f.get("numFmtId")): f.get("formatCode", "")
                  for f in root.findall("m:numFmts/m:numFmt", _NS)}
        dates = set()
        for index, xf in enumerate(root.findall("m:cellXfs/m:xf", _NS)):
            fmt = int(xf.get("numFmtId", "0"))
            if fmt in _BUILTIN_DATE_FORMATS or (fmt in custom and _is_date_format(custom[fmt])):
                dates.add(index)
        return dates

    def _number(self, raw: str, style: int, ref: str) -> str:
        try:
            value = float(raw)
        except ValueError as exc:
            raise WorkbookError(f"cell {ref} holds an unreadable number {raw!r}") from exc
        if style in self._date_styles:
            moment = self._epoch + timedelta(days=value)
            if moment.hour == moment.minute == moment.second == 0 and moment.microsecond == 0:
                return moment.date().isoformat()
            return moment.replace(microsecond=0).isoformat()
        text = repr(value)
        return text[:-2] if text.endswith(".0") else text

    def read(self, name: str) -> Sheet:
        match = [path for sheet_name, path in self.sheets if sheet_name == name]
        if not match:
            raise WorkbookError(
                f"no sheet named {name!r}; sheets: {[s for s, _ in self.sheets]}")
        root = self._xml(match[0])
        rows: dict[int, dict[int, str]] = {}
        for row in root.iter(f"{{{_NS['m']}}}row"):
            for cell in row.findall("m:c", _NS):
                ref = cell.get("r", "")
                parsed = _CELL_REF.fullmatch(ref)
                if not parsed:
                    raise WorkbookError(f"a cell has no usable reference ({ref!r})")
                col, row_no = _col_index(parsed.group(1)), int(parsed.group(2))
                if row_no > MAX_ROWS:
                    raise WorkbookError(f"sheet {name!r} exceeds {MAX_ROWS} rows")
                kind = cell.get("t", "n")
                v = cell.find("m:v", _NS)
                formula = cell.find("m:f", _NS) is not None
                if kind == "inlineStr":
                    text = "".join(t.text or "" for t in cell.iter(f"{{{_NS['m']}}}t"))
                elif v is None or v.text is None:
                    if formula:
                        raise WorkbookError(
                            f"cell {ref} on sheet {name!r} is a formula saved "
                            "without a calculated value; open the file in Excel, "
                            "recalculate, save, and upload it again")
                    continue
                elif kind == "s":
                    text = self._shared[int(v.text)]
                elif kind in ("str", "e"):
                    text = v.text
                elif kind == "b":
                    text = "TRUE" if v.text == "1" else "FALSE"
                else:
                    text = self._number(v.text, int(cell.get("s", "0")), ref)
                if text != "":
                    rows.setdefault(row_no, {})[col] = text
        if not rows:
            return Sheet(name, [])
        width = max(max(cols) for cols in rows.values()) + 1
        last = max(rows)
        return Sheet(name, [[rows.get(r, {}).get(c, "") for c in range(width)]
                            for r in range(1, last + 1)])


def list_sheets(content: bytes) -> list[str]:
    return [name for name, _ in _Workbook(content).sheets]


def suggest_header_row(rows: list[list[str]]) -> int:
    """1-based row most likely to hold column headings: the first row, among
    the first few, with the most filled cells that are all text. A proposal
    for a reviewer, like every other mapping choice."""
    best, best_score = 1, -1
    for index, row in enumerate(rows[:HEADER_SCAN_ROWS], start=1):
        filled = [c for c in row if c.strip()]
        if not filled:
            continue
        numeric = sum(1 for c in filled if re.fullmatch(r"-?[\d.,]+", c.strip()))
        score = len(filled) - 2 * numeric
        if score > best_score:
            best, best_score = index, score
    return best


def preview(content: bytes, *, max_rows: int = 12) -> list[dict]:
    """Every sheet's first rows and suggested header row, for choosing."""
    book = _Workbook(content)
    out = []
    for name, _ in book.sheets:
        sheet = book.read(name)
        out.append({"sheet": name, "rows": sheet.rows[:max_rows],
                    "row_count": len(sheet.rows),
                    "suggested_header_row": suggest_header_row(sheet.rows)})
    return out


def extract(content: bytes, *, sheet: str | None = None,
            header_row: int | None = None) -> tuple[dict, list[str], list[dict]]:
    """Header-keyed rows from one sheet, plus the resolved extraction.

    ``sheet`` defaults to the only sheet (refused when there are several —
    the choice is the reviewer's). ``header_row`` (1-based) defaults to the
    suggestion. Data runs from the row after the header to the first
    entirely blank row, so a totals block under a blank line is excluded;
    the extraction reports how many rows it read and where it stopped.
    """
    book = _Workbook(content)
    names = [name for name, _ in book.sheets]
    if sheet is None:
        if len(names) != 1:
            raise WorkbookError(
                f"the workbook has {len(names)} sheets {names}; choose one")
        sheet = names[0]
    data = book.read(sheet)
    if not data.rows:
        raise WorkbookError(f"sheet {sheet!r} is empty")
    header_row = header_row or suggest_header_row(data.rows)
    if not 1 <= header_row <= len(data.rows):
        raise WorkbookError(
            f"header row {header_row} is outside sheet {sheet!r} "
            f"(rows 1-{len(data.rows)})")
    raw_headers = data.rows[header_row - 1]
    headers: list[str] = []
    for index, value in enumerate(raw_headers):
        name = value.strip() or f"Column {_col_letters(index)}"
        base, n = name, 2
        while name in headers:
            name, n = f"{base} ({n})", n + 1
        headers.append(name)
    records: list[dict] = []
    stopped_at = None
    for offset, row in enumerate(data.rows[header_row:], start=header_row + 1):
        if not any(cell.strip() for cell in row):
            stopped_at = offset
            break
        records.append(dict(zip(headers, row)))
    ignored_below = (sum(1 for row in data.rows[stopped_at:] if any(c.strip() for c in row))
                     if stopped_at else 0)
    extraction = {"converter": CONVERTER, "sheet": sheet, "header_row": header_row,
                  "data_rows": len(records),
                  "stopped_at_blank_row": stopped_at,
                  "nonblank_rows_below_ignored": ignored_below}
    return extraction, headers, records
