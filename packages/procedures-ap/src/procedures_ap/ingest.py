# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Client-export ingestion: proposed mappings, reviewed approval, normalization.

Port of the prototype's synonym-based header detection, upgraded to the
reviewed-transformation model the assessment requires: a detected mapping is
a *proposal*; a different principal approves it; only an approved spec can
normalize rows. Normalization quarantines rejected rows, reports duplicate-
key and null diagnostics, and reconciles row counts and control totals —
in Decimal.

Honesty rules kept from the prototype: unmapped columns and absent canonical
fields are recorded as refusals, never guessed; every row keeps its source
line number and content hash.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from assurance_domain.lifecycle import require_separation
from assurance_domain.money import fnum

from procedures_ap.structural import content_hash

# Canonical table -> (field -> header synonyms). Field order is the detection
# priority; keys are listed before names so an ambiguous "vendor" header binds
# the id first. Canonical field names match exactly what the engines read.
ROLE_SCHEMAS: dict[str, dict[str, list[str]]] = {
    "Vendors": {
        "vendor_number": ["vendor number", "vendor no", "vendor id", "vendor code",
                          "supplier number", "supplier no", "supplier id", "vendor"],
        "vendor_name": ["vendor name", "supplier name", "payee name", "name"],
    },
    "Employees": {
        "employee_number": ["employee number", "employee no", "employee id",
                            "emp id", "emp no", "staff id", "employee"],
        "employee_name": ["employee name", "name"],
    },
    "Purchase_orders": {
        "po_number": ["po number", "po no", "po id", "purchase order number",
                      "purchase order no", "purchase order", "po"],
        "vendor_number": ["vendor number", "vendor no", "vendor id", "supplier number",
                          "supplier id", "vendor"],
        "po_amount": ["po amount", "purchase order amount", "po total", "amount", "total"],
        "po_date": ["po date", "purchase order date", "order date", "date"],
        "created_by": ["created by", "entered by", "requested by", "buyer"],
        "approved_by": ["approved by", "authorized by", "approver"],
        "created_on": ["created on", "created date", "entry date"],
        "approved_on": ["approved on", "approved date", "approval date"],
    },
    "Vouchers": {
        "voucher_number": ["voucher number", "voucher no", "voucher id",
                           "invoice number", "invoice no", "invoice id", "voucher", "invoice"],
        # The supplier's own invoice number, which only a supplier reuses.
        # A voucher system's voucher number is the client's sequence, unique
        # by design, so duplicate-bill testing needs this field, not that one.
        "invoice_number": ["vendor invoice number", "supplier invoice number",
                           "vendor invoice no", "supplier invoice no", "vendor invoice",
                           "supplier invoice", "bill number", "bill no",
                           "invoice number", "invoice no"],
        "po_number": ["po number", "po no", "purchase order number", "purchase order", "po"],
        "vendor_number": ["vendor number", "vendor no", "vendor id", "supplier number",
                          "supplier id", "vendor"],
        "voucher_amount": ["voucher amount", "invoice amount", "invoice total",
                           "amount", "total"],
        "voucher_date": ["voucher date", "invoice date", "date"],
        "created_by": ["created by", "entered by"],
        "approved_by": ["approved by", "authorized by", "approver"],
    },
    "Payments": {
        "payment_number": ["payment number", "payment no", "payment id",
                           "disbursement number", "check number", "check no",
                           "cheque number", "payment"],
        "voucher_number": ["voucher number", "voucher no", "invoice number",
                           "invoice no", "voucher", "invoice"],
        "vendor_number": ["vendor number", "vendor no", "vendor id", "supplier number",
                          "supplier id", "vendor"],
        "payment_amount": ["payment amount", "paid amount", "check amount",
                           "disbursement amount", "amount", "total"],
        "payment_date": ["payment date", "check date", "paid date", "date"],
        "created_by": ["created by", "entered by"],
        "approved_by": ["approved by", "authorized by", "approver"],
        "check_number": ["check number", "check no", "cheque number"],
    },
    "Value_flows": {
        "flow_id": ["flow id", "flow", "transfer id", "transaction id", "id"],
        "source_entity": ["source entity", "source", "from", "from entity", "payer"],
        "target_entity": ["target entity", "target", "to", "to entity", "payee"],
        "amount": ["amount", "value", "total"],
        "flow_date": ["flow date", "date", "value date"],
        "relation": ["relation", "type"],
        "flow_type": ["flow type", "type", "category"],
    },
    "Bank": {
        "bank_txn_id": ["bank txn id", "bank transaction id", "transaction id",
                        "txn id", "bank id", "id"],
        "payment_number": ["payment number", "payment no", "check number", "check no",
                           "cheque number", "reference", "payment"],
        "amount": ["amount", "debit", "disbursement amount", "check amount", "value"],
        "bank_date": ["bank date", "cleared date", "value date", "posting date", "date"],
    },
    "GL": {
        "gl_entry_id": ["gl entry id", "gl id", "entry id", "journal id",
                        "je id", "line id", "id"],
        "account": ["account", "gl account", "account number", "account no", "acct"],
        "reference": ["reference", "ref", "document", "document number", "source document",
                      "payment number", "voucher number", "invoice number"],
        "amount": ["amount", "debit", "credit", "value"],
        "gl_date": ["gl date", "posting date", "post date", "effective date", "date"],
    },
    "Goods_receipts": {
        "receipt_number": ["receipt number", "receipt no", "goods receipt number",
                           "goods receipt no", "grn", "receipt id", "id"],
        "po_number": ["po number", "po no", "purchase order number",
                      "purchase order", "po"],
        "received_amount": ["received amount", "receipt amount", "goods received value",
                            "amount", "value", "total"],
        "receipt_date": ["receipt date", "goods received date", "received date", "date"],
    },
    "AP_control_balance": {
        "period_end": ["period end", "period end date", "balance date", "date"],
        "subledger_balance": ["subledger balance", "ap subledger balance",
                              "payables subledger", "subledger"],
        "gl_balance": ["gl balance", "control account balance", "ap control balance",
                       "general ledger balance"],
    },
}

_AMOUNT_FIELDS = {"po_amount", "voucher_amount", "payment_amount", "amount",
                  "received_amount", "subledger_balance", "gl_balance"}
_DATE_FIELDS = {"po_date", "voucher_date", "payment_date", "flow_date",
                "created_on", "approved_on", "bank_date", "gl_date",
                "receipt_date", "period_end"}
_REQUIRED: dict[str, tuple[str, ...]] = {
    "Vendors": ("vendor_number",),
    "Employees": ("employee_number",),
    "Purchase_orders": ("po_number", "vendor_number"),
    "Vouchers": ("voucher_number",),
    "Payments": ("payment_number",),
    "Value_flows": ("source_entity", "target_entity"),
    "Bank": ("bank_txn_id", "payment_number"),
    "GL": ("gl_entry_id", "reference"),
    "Goods_receipts": ("receipt_number", "po_number"),
    "AP_control_balance": ("period_end", "subledger_balance", "gl_balance"),
}

_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%d-%b-%Y",
                 "%m-%d-%Y", "%Y%m%d", "%d/%m/%Y")

# Filename hints per canonical role, for bulk loading. Inference is only a
# *suggestion* that pre-fills the role on a proposal; the proposal still
# crosses the reviewer's approval gate, so a wrong hint costs a click, not
# an integrity property. Ambiguity or no hit yields None — never a guess.
ROLE_FILENAME_HINTS: dict[str, list[str]] = {
    "Vendors": ["vendors", "vendor", "vendor master", "suppliers",
                "supplier master"],
    "Employees": ["employees", "employee", "employee master", "staff",
                  "personnel"],
    "Purchase_orders": ["purchase orders", "purchase order", "po register",
                        "pos", "po"],
    "Goods_receipts": ["goods receipts", "goods receipt", "goods received",
                       "receipts", "receiving", "grn"],
    "Vouchers": ["vouchers", "voucher", "invoices", "invoice", "ap invoices",
                 "bills"],
    "Payments": ["payments", "payment", "disbursements", "disbursement",
                 "checks", "cheques", "check register"],
    "Bank": ["bank", "bank statement", "bank transactions", "bank stmt"],
    "GL": ["general ledger", "gl detail", "journal entries", "ledger", "gl",
           "je"],
    "AP_control_balance": ["ap control balance", "ap control",
                           "control balance", "ap balance",
                           "ap reconciliation"],
    "Value_flows": ["value flows", "flows", "transfers", "related party",
                    "intercompany"],
}


def infer_role_from_headers(headers: list[str]) -> str | None:
    """Suggest the role a file's column headings best fit, for files whose
    name says nothing (``export (3).csv``). A role qualifies only when every
    one of its required fields maps and at least two fields map in all; the
    role mapping the most fields wins, and a tie returns None rather than
    picking one. A suggestion for the reviewer, never an approval."""
    best: list[tuple[int, str]] = []
    for role, schema in ROLE_SCHEMAS.items():
        mapped = detect_columns(headers, schema)
        required = _REQUIRED.get(role, ())
        if len(mapped) < 2 or any(f not in mapped for f in required):
            continue
        best.append((len(mapped), role))
    if not best:
        return None
    best.sort(reverse=True)
    if len(best) > 1 and best[0][0] == best[1][0]:
        return None
    return best[0][1]


def infer_role(filename: str) -> str | None:
    """Suggest the canonical role a filename most likely carries.

    The stem is tokenized on non-alphanumerics and every contiguous token
    run is matched against the normalized hints; the longest hint wins.
    A tie between different roles returns None rather than picking one.
    """
    stem = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    stem = stem.rsplit(".", 1)[0] if "." in stem else stem
    tokens = "".join(ch if ch.isalnum() else " " for ch in stem.lower()).split()
    grams = {"".join(tokens[i:j]) for i in range(len(tokens))
             for j in range(i + 1, len(tokens) + 1)}
    best_role: str | None = None
    best_len = 0
    tied = False
    for role, hints in ROLE_FILENAME_HINTS.items():
        for hint in hints:
            normalized = _norm(hint)
            if normalized not in grams:
                continue
            if len(normalized) > best_len:
                best_role, best_len, tied = role, len(normalized), False
            elif len(normalized) == best_len and role != best_role:
                tied = True
    return None if tied else best_role


def _norm(header: str) -> str:
    return "".join(ch for ch in (header or "").lower() if ch.isalnum())


def detect_columns(headers: list[str],
                   schema: dict[str, list[str]]) -> dict[str, str]:
    """Map canonical fields to actual headers (normalized, no header reuse)."""
    norm_syn = {f: {_norm(s) for s in syns} for f, syns in schema.items()}
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for field_name in schema:  # detection priority = declaration order
        for header in headers:
            if header in used:
                continue
            if _norm(header) in norm_syn[field_name]:
                mapping[field_name] = header
                used.add(header)
                break
    return mapping


def parse_decimal(raw: str | None) -> Decimal | None:
    """Parse one accounting text amount exactly; None when unparseable.

    Accepts parenthesized negatives, $ signs, and thousands separators —
    the prototype's boundary, on Decimal instead of float (D3).
    """
    s = (raw or "").strip()
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("$", "").replace(",", "").strip()
    if s in ("", "-", "."):
        return None
    try:
        value = Decimal(s)
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    return -value if neg else value


def parse_date_text(raw: str | None) -> date | None:
    s = (raw or "").strip()
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


@dataclass(frozen=True)
class MappingSpec:
    """A durable, reviewable transformation object — never just a dict."""

    role: str
    headers: tuple[str, ...]
    column_map: dict[str, str]
    unmapped_headers: tuple[str, ...]
    refused_fields: tuple[str, ...]
    source_sha256: str = ""
    status: str = "proposed"     # proposed | approved | superseded
    proposed_by: str = ""
    approved_by: str = ""
    version: int = 1

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "headers": list(self.headers),
            "column_map": dict(self.column_map),
            "unmapped_headers": list(self.unmapped_headers),
            "refused_fields": list(self.refused_fields),
            "source_sha256": self.source_sha256,
            "status": self.status,
            "proposed_by": self.proposed_by,
            "approved_by": self.approved_by,
            "version": self.version,
        }

    @property
    def digest(self) -> str:
        payload = json.dumps(
            {"role": self.role, "headers": list(self.headers),
             "column_map": self.column_map, "version": self.version},
            sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def propose_mapping(role: str, headers: list[str], *,
                    source_sha256: str = "",
                    proposed_by: str = "",
                    column_map: dict[str, str] | None = None) -> MappingSpec:
    """Detect a candidate mapping. A proposal, not an authority.

    ``column_map`` replaces synonym detection when a recipe already knows
    the layout (a recognized QuickBooks report); it is checked against the
    role's fields and the actual headings, and is still only a proposal.
    """
    if role not in ROLE_SCHEMAS:
        raise ValueError(
            f"unknown role {role!r}; expected one of {list(ROLE_SCHEMAS)}")
    schema = ROLE_SCHEMAS[role]
    if column_map is None:
        column_map = detect_columns(headers, schema)
    else:
        bad = [f for f in column_map if f not in schema]
        missing = [h for h in column_map.values() if h not in headers]
        if bad or missing:
            raise ValueError(f"column map does not fit {role}: unknown fields "
                             f"{bad}, headings not in the file {missing}")
        column_map = {f: column_map[f] for f in schema if f in column_map}
    mapped = set(column_map.values())
    return MappingSpec(
        role=role,
        headers=tuple(headers),
        column_map=column_map,
        unmapped_headers=tuple(h for h in headers if h not in mapped),
        refused_fields=tuple(f for f in schema if f not in column_map),
        source_sha256=source_sha256,
        proposed_by=proposed_by,
    )


def approve_mapping(spec: MappingSpec, *, approved_by: str) -> MappingSpec:
    """A different principal approves the proposal; separation is enforced."""
    if spec.status != "proposed":
        raise ValueError(f"mapping spec is {spec.status}, not proposed")
    require_separation(prepared_by=spec.proposed_by, approved_by=approved_by)
    return replace(spec, status="approved", approved_by=approved_by)


@dataclass
class NormalizedTable:
    """Normalized canonical rows plus the receipts that make them reviewable.

    Attribute-compatible with the engine table protocol (records,
    refused_fields, column_map, control_total, source_file).
    """

    role: str
    records: list[dict] = field(default_factory=list)
    rejects: list[dict] = field(default_factory=list)
    refused_fields: tuple[str, ...] = ()
    column_map: dict[str, str] = field(default_factory=dict)
    unmapped_headers: tuple[str, ...] = ()
    control_total: Decimal | None = None
    source_file: str = ""
    source_sha256: str = ""
    diagnostics: dict = field(default_factory=dict)

    @property
    def output_digest(self) -> str:
        return content_hash({"role": self.role,
                             "records": _jsonable_rows(self.records)})

    def reconciliation(self) -> dict:
        return {
            "role": self.role,
            "source_file": self.source_file,
            "source_sha256": self.source_sha256,
            "rows_in": len(self.records) + len(self.rejects),
            "rows_loaded": len(self.records),
            "rows_rejected": len(self.rejects),
            "control_total": str(self.control_total)
            if self.control_total is not None else None,
            "column_map": dict(self.column_map),
            "unmapped_headers": list(self.unmapped_headers),
            "refused_fields": list(self.refused_fields),
            "diagnostics": dict(self.diagnostics),
            "output_digest": self.output_digest,
        }

    def engine_view(self) -> "NormalizedTable":
        """Float projection for the float-parity screening layer (D7)."""
        projected = [
            {k: (fnum(v) if isinstance(v, Decimal) else v)
             for k, v in record.items()}
            for record in self.records
        ]
        return replace(self, records=projected)


def _jsonable_rows(records: list[dict]) -> list[dict]:
    out = []
    for record in records:
        row = {}
        for key, value in record.items():
            if isinstance(value, Decimal):
                row[key] = str(value)
            elif isinstance(value, date):
                row[key] = value.isoformat()
            else:
                row[key] = value
        out.append(row)
    return out


_TOTAL_LABEL = re.compile(r"^\s*(grand\s+)?totals?(\s|:|$)", re.IGNORECASE)


def _looks_like_total(raw: dict, key_header: str | None) -> bool:
    """A report's total or subtotal line: its label reads "TOTAL", "Total
    for ...", "Grand total". The label is the row's key column (payment
    number, customer, ...) when the mapping has one, else the first
    non-blank cell; so a payee named "Total Cycling" is never a total,
    whatever order the columns come in (review 2026-09-28 F3, re-review
    RR3). Whether it *is* one is then decided by whether its amount ties."""
    if key_header is not None:
        label = raw.get(key_header) or ""
    else:
        label = next((v for v in raw.values() if isinstance(v, str) and v.strip()), "")
    return isinstance(label, str) and bool(_TOTAL_LABEL.match(label))


# Fields a report's total line may carry: amounts and quantities.
_QUANTITY_FIELDS = {"quantity", "hours"}
# Per-unit rates: never summed, so never a file's control total.
_RATE_FIELDS = {"unit_cost", "pay_rate", "interest_rate"}


def _measure_fields() -> set[str]:
    return _AMOUNT_FIELDS | _QUANTITY_FIELDS


def _measure(record: dict, raw: dict, spec, field_name: str) -> Decimal | None:
    """A measure column's value as a number (quantities are kept as text)."""
    value = record.get(field_name)
    if isinstance(value, Decimal):
        return value
    return parse_decimal(raw.get(spec.column_map[field_name]))


def _only_label_and_amounts(raw: dict, column_map: dict, label_header) -> bool:
    """A report's total line carries its label and numbers, nothing else: no
    date, no counterparty, no second identifier. A real record always does,
    so a payee or entity named "Total ..." is never taken for a total
    (re-review RRR3)."""
    for field_name, header in column_map.items():
        if header == label_header:
            continue
        value = raw.get(header)
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        # By the field's type, not the text's look: an identifier "12345" or
        # a date "20250102" is not a total measure (re-review RRRR1).
        if field_name in _measure_fields():
            continue
        return False
    return True


def normalize_table(rows: list[dict], spec: MappingSpec, *,
                    source_file: str = "", first_row: int = 2,
                    source_rows: list[int] | None = None) -> NormalizedTable:
    """Normalize raw rows through an *approved* mapping spec.

    Rows whose required key fields are blank are quarantined with reasons,
    not silently loaded; duplicate keys and null amounts are reported as
    diagnostics; the control total accumulates in Decimal. A row labelled
    as a total whose amount equals the sum of the rows above it is set
    aside as a total, not loaded as a record (a report's TOTAL line would
    otherwise double the population); a total-labelled row that does not
    tie is kept and named in the diagnostics for the reviewer.
    """
    if spec.status != "approved":
        raise ValueError(
            "normalization requires an approved mapping spec; "
            f"this one is {spec.status!r}")
    schema = ROLE_SCHEMAS[spec.role]
    required = [f for f in _REQUIRED.get(spec.role, ())
                if f in spec.column_map]
    amount_field = next((f for f in schema
                         if f in _AMOUNT_FIELDS and f not in _RATE_FIELDS), None)
    have_amount = amount_field in spec.column_map if amount_field else False

    table = NormalizedTable(
        role=spec.role,
        refused_fields=spec.refused_fields,
        column_map=dict(spec.column_map),
        unmapped_headers=spec.unmapped_headers,
        source_file=source_file,
        source_sha256=spec.source_sha256,
    )
    control = Decimal("0")
    key_counts: dict[str, int] = {}
    null_amounts = 0
    # Running sums of every mapped measure column since the last total row,
    # and over all loaded rows (a grand total): a report total may tie on
    # any of them, e.g. extended cost rather than unit cost (re-review RRRRR2).
    measures = [f for f in schema if f in spec.column_map
                and f in _measure_fields() and f not in _RATE_FIELDS]
    since_total = {f: Decimal("0") for f in measures}
    all_loaded = {f: Decimal("0") for f in measures}
    totals_set_aside = 0
    totals_not_tying: list[dict] = []
    total_labels_kept: list[int] = []
    # source_row points at the row in the file as the client sent it: CSV
    # line numbers by default (header on line 1); a workbook passes the
    # sheet row of its first data row. A recipe that drops rows (subtotals,
    # filtered transaction types) passes each kept row's own row number.
    if source_rows is not None and len(source_rows) != len(rows):
        raise ValueError("source_rows must give one row number per row")
    numbers = source_rows if source_rows is not None else range(first_row, first_row + len(rows))
    for source_row, raw in zip(numbers, rows):
        record: dict = {}
        for field_name, header in spec.column_map.items():
            value = raw.get(header)
            if field_name in _AMOUNT_FIELDS:
                record[field_name] = parse_decimal(value)
            elif field_name in _DATE_FIELDS:
                record[field_name] = parse_date_text(value)
            else:
                record[field_name] = (value or "").strip()
        record["source_row"] = source_row
        record["source_hash"] = content_hash(raw)

        label_header = spec.column_map.get(required[0]) if required else None
        if _looks_like_total(raw, label_header) and _only_label_and_amounts(
                raw, spec.column_map, label_header):
            # A row labelled like a total, carrying only its label and
            # measures. It is a total when every populated measure ties on one
            # basis (since the last total, or over all rows). Otherwise it is
            # ambiguous: a report total that disagrees with its detail, or a
            # real record named "Total ..." — so it is held for review, never
            # loaded and never described as a total (re-reviews 5 and 6).
            shown, unreadable = {}, []
            for f in measures:
                cell = raw.get(spec.column_map[f])
                if cell is None or (isinstance(cell, str) and not cell.strip()):
                    continue
                value = _measure(record, raw, spec, f)
                if value is None:
                    unreadable.append(f"{f} shows {cell!r}, not a number")
                else:
                    shown[f] = value
            ties = [basis for basis in (since_total, all_loaded)
                    if shown and not unreadable
                    and all(v == basis[f] for f, v in shown.items())]
            if ties:
                reason = (f"a total row: its {', '.join(shown)} equal the sums of the "
                          "rows above it, so it is not a record")
            else:
                def gaps_against(basis):
                    return [f"{f} shows {v}, rows above sum to {basis[f]}"
                            for f, v in shown.items() if v != basis[f]]
                since_gaps, all_gaps = gaps_against(since_total), gaps_against(all_loaded)
                basis, gaps = (("since the last subtotal", since_gaps)
                               if len(since_gaps) <= len(all_gaps)
                               else ("over all rows", all_gaps))
                gaps = unreadable + gaps
                reason = ("held for review: labelled like a total but it does not tie ("
                          + ("; ".join(gaps) if gaps else "it carries no amounts")
                          + f"; compared {basis}). Either the report's total disagrees "
                            "with its detail, or this is a real record named like a "
                            "total — not loaded until resolved")
                totals_not_tying.append({"source_row": source_row, "basis": basis,
                                         "gaps": gaps})
            table.rejects.append({"source_row": source_row, "reason": reason,
                                  "raw": dict(raw)})
            totals_set_aside += 1
            since_total = {f: Decimal("0") for f in measures}
            continue
        if _looks_like_total(raw, label_header):
            total_labels_kept.append(source_row)     # a record named "Total ..."

        blank = [f for f in required
                 if record.get(f) in (None, "")]
        if blank:
            table.rejects.append({
                "source_row": source_row,
                "reason": f"required field(s) blank: {blank}",
                "raw": dict(raw),
            })
            continue

        if required:
            key = str(record[required[0]])
            key_counts[key] = key_counts.get(key, 0) + 1
        if have_amount:
            amount = record.get(amount_field)
            if amount is None:
                null_amounts += 1
            else:
                control += amount
        for f in measures:
            value = _measure(record, raw, spec, f)
            if value is not None:
                since_total[f] += value
                all_loaded[f] += value
        table.records.append(record)

    duplicate_keys = sorted(k for k, n in key_counts.items() if n > 1)
    table.diagnostics = {
        "duplicate_keys": duplicate_keys,
        "duplicate_key_rows": sum(n for n in key_counts.values() if n > 1),
        "null_amount_rows": null_amounts,
        "required_fields_checked": required,
        "total_rows_set_aside": totals_set_aside,
        "total_labelled_rows_kept": total_labels_kept,
        "total_rows_not_tying": totals_not_tying,
    }
    table.control_total = (control.quantize(Decimal("0.01"))
                           if have_amount else None)
    return table
