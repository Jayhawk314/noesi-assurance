# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""QuickBooks Online report exports: recognize them, flatten them, check them.

QuickBooks does not export flat tables. A transaction report exported to
Excel carries a title block (company, report name, period), a blank line,
the column headings with an empty first column, then *groups*: a heading
row that holds only the group name (a vendor, a bank account), its detail
rows, and a "Total for <group>" row, ending in a grand "TOTAL" and a
timestamp footer. List reports (the vendor contact list) are flat.

A recipe turns one such report into ordinary rows for one canonical role:

- the group name moves onto each detail row as a named column;
- subtotal rows are dropped, but every subtotal and the grand total are
  recomputed from the detail rows in Decimal, for every amount column, and
  compared, so the dropped rows still do work — a difference is reported,
  never absorbed;
- a transaction-type filter keeps only the rows the role is about (bills
  for Vouchers, bill payments for Payments), and the counts of every type
  kept or left out are reported;
- payments get a positive "Paid Amount": QuickBooks signs an amount by the
  paying account (a check is negative in the bank register, a card payment
  positive on the card), so the sign says which account paid, not whether
  money was paid. The as-exported Amount stays in the row, and the report
  counts the signs seen per account;
- every row keeps its real sheet row number.

Recognition is exact: the report name in the title block and the heading
row must match the standard layout the recipe was built from (verified
against real QuickBooks Online exports, tests/fixtures/quickbooks/). A
report with customized columns is not recognized and falls back to the
ordinary header mapping, which the reviewer checks as usual. A recipe is
a proposal like any other mapping; the reviewer approves it, and its id is
part of the reviewed spec's digest.

What QuickBooks does not export is refused, not invented: bills usually
carry no number (Num is blank unless someone typed the vendor's invoice
number), vendors are identified by name, and no standard vendor report
states which bill a payment settled (Bills and Applied Payments lists them
side by side, in no consistent order). Rows missing a required key are
quarantined by normalization with the reason.

Not yet covered: the General Ledger export nests sub-accounts inside
accounts and opens each with a Beginning Balance row; it needs its own
structure, not this one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from procedures_ap.ingest import _REQUIRED, parse_decimal

RECIPE_VERSION = "qbo-v1"
GROUP_HEADER = "Column A"     # the reader's name for the blank first heading
PAID_AMOUNT = "Paid Amount"
_CENT = Decimal("0.01")


class RecipeError(ValueError):
    """The file does not have the structure the recipe was built for."""


@dataclass(frozen=True)
class Recipe:
    recipe_id: str
    report: str                     # report name, row 2 of the title block
    role: str
    headers: tuple[str, ...]        # grouped: the headings after the blank first column
    column_map: dict[str, str]      # canonical field -> heading
    group_column: str = ""          # name given to the group heading; "" = flat list
    amount_columns: tuple[str, ...] = ("Amount",)
    type_column: str | None = None
    types: tuple[str, ...] = ()
    paid_amount: bool = False
    sign_account_column: str | None = None   # None: the group is the account
    note: str = ""

    @property
    def grouped(self) -> bool:
        return bool(self.group_column)

    @property
    def label(self) -> str:
        return f"QuickBooks {self.report} → {self.role}"


_TX_BY_VENDOR = ("Date", "Track 1099", "Transaction type", "Num", "Posting (Y/N)",
                 "Memo", "Account full name", "Item split account", "Amount")
_BILL_PAYMENTS = ("Bill Payment (Check)", "Bill Payment (Credit Card)")
_NO_BILL_NUMBER = ("Bills are identified by Num, which QuickBooks leaves blank "
                   "unless the vendor's invoice number was typed in; bills "
                   "without one are quarantined, not numbered for you.")

RECIPES: dict[str, Recipe] = {r.recipe_id: r for r in (
    Recipe(
        recipe_id="qbo.bill_payment_list.payments", report="Bill Payment List",
        role="Payments", headers=("Date", "Num", "Vendor", "Amount"),
        group_column="Paid From Account",
        column_map={"payment_number": "Num", "vendor_number": "Vendor",
                    "payment_amount": PAID_AMOUNT, "payment_date": "Date"},
        paid_amount=True,
        note="Num is the check or card reference and can repeat (card "
             "payments are often all '1'); the list does not name the bill "
             "each payment settled."),
    Recipe(
        recipe_id="qbo.transaction_list_by_vendor.vouchers",
        report="Transaction List by Vendor", role="Vouchers",
        headers=_TX_BY_VENDOR, group_column="Vendor",
        column_map={"voucher_number": "Num", "vendor_number": "Vendor",
                    "voucher_amount": "Amount", "voucher_date": "Date"},
        type_column="Transaction type", types=("Bill",), note=_NO_BILL_NUMBER),
    Recipe(
        recipe_id="qbo.transaction_list_by_vendor.payments",
        report="Transaction List by Vendor", role="Payments",
        headers=_TX_BY_VENDOR, group_column="Vendor",
        column_map={"payment_number": "Num", "vendor_number": "Vendor",
                    "payment_amount": PAID_AMOUNT, "payment_date": "Date"},
        type_column="Transaction type", types=_BILL_PAYMENTS,
        paid_amount=True, sign_account_column="Account full name",
        note="Only bill payments are kept; checks and expenses paid without "
             "a bill are left out and counted."),
    Recipe(
        recipe_id="qbo.transaction_list_by_vendor.purchase_orders",
        report="Transaction List by Vendor", role="Purchase_orders",
        headers=_TX_BY_VENDOR, group_column="Vendor",
        column_map={"po_number": "Num", "vendor_number": "Vendor",
                    "po_amount": "Amount", "po_date": "Date"},
        type_column="Transaction type", types=("Purchase Order",),
        note="Purchase orders are non-posting in QuickBooks; they appear "
             "here but not in the ledger."),
    Recipe(
        recipe_id="qbo.unpaid_bills.vouchers", report="Unpaid Bills Report",
        role="Vouchers",
        headers=("Date", "Transaction type", "Num", "Due date", "Past due",
                 "Amount", "Open balance"),
        group_column="Vendor", amount_columns=("Amount", "Open balance"),
        column_map={"voucher_number": "Num", "vendor_number": "Vendor",
                    "voucher_amount": "Amount", "voucher_date": "Date"},
        note="Open bills only. The grand TOTAL of Open balance is the AP "
             "subledger balance, to compare with the ledger's Accounts "
             "Payable. " + _NO_BILL_NUMBER),
    Recipe(
        recipe_id="qbo.vendor_contact_list.vendors", report="Vendor Contact List",
        role="Vendors",
        headers=("Vendor", "Phone numbers", "Email", "Full name",
                 "Billing address", "Account #"),
        column_map={"vendor_number": "Vendor", "vendor_name": "Vendor"},
        amount_columns=(),
        note="QuickBooks identifies vendors by display name, so the name "
             "is also the vendor key. 'Account #' is your account number "
             "with the vendor, not a vendor id."),
)}


def _heading_row(rows: list[list[str]], recipe: Recipe) -> int | None:
    for index, row in enumerate(rows, start=1):
        cells = [c.strip() for c in row]
        while cells and not cells[-1]:
            cells.pop()
        if recipe.grouped:
            if cells and not cells[0] and tuple(cells[1:]) == recipe.headers:
                return index
        elif tuple(cells) == recipe.headers:
            return index
    return None


def recognize(rows: list[list[str]]) -> list[dict]:
    """Recipes whose report name and heading row match a sheet's first rows."""
    title = [(row[0].strip() if row else "") for row in rows[:4]]
    found = []
    for recipe in RECIPES.values():
        if recipe.report not in title:
            continue
        header_row = _heading_row(rows[:12], recipe)
        if header_row is None:
            continue
        found.append({"recipe": recipe.recipe_id, "label": recipe.label,
                      "report": recipe.report, "role": recipe.role,
                      "header_row": header_row, "note": recipe.note})
    return found


def get(recipe_id: str) -> Recipe:
    try:
        return RECIPES[recipe_id]
    except KeyError:
        raise RecipeError(f"unknown QuickBooks recipe {recipe_id!r}; "
                          f"known: {sorted(RECIPES)}") from None


def apply(recipe_id: str, headers: list[str], records: list[dict],
          first_row: int) -> tuple[list[str], list[dict], list[int], dict]:
    """Flatten one extracted report into rows for the recipe's role.

    Returns the new headings, the kept rows, each kept row's sheet row
    number, and a report of what was checked, kept and left out. A file
    whose structure departs from the recipe is refused with the row that
    departs, so a wrong recipe cannot quietly produce plausible rows.
    """
    recipe = get(recipe_id)
    expected = [GROUP_HEADER, *recipe.headers] if recipe.grouped else list(recipe.headers)
    if headers != expected:
        shown = ["", *recipe.headers] if recipe.grouped else list(recipe.headers)
        raise RecipeError(
            f"the headings {headers} are not QuickBooks' standard "
            f"{recipe.report} layout {shown}; a customized report needs an "
            f"ordinary mapping instead of this recipe")
    if not recipe.grouped:
        rows = [dict(r) for r in records]
        report = {"recipe": recipe.recipe_id, "version": RECIPE_VERSION,
                  "report": recipe.report, "role": recipe.role,
                  "rows_kept": len(rows), "subtotals_checked": 0,
                  "grand_total": None, "totals_disagreeing": [],
                  "missing_required": _missing_required(recipe, rows),
                  "note": recipe.note}
        return (list(headers), rows,
                list(range(first_row, first_row + len(rows))), report)

    detail = list(recipe.headers)
    zero = {c: Decimal("0") for c in recipe.amount_columns}
    group: str | None = None
    group_sum = dict(zero)
    grand = dict(zero)
    subtotals: list[dict] = []
    grand_totals: list[dict] = []
    type_counts: dict[str, dict[str, int]] = {}
    signs: dict[str, dict[str, int]] = {}
    kept: list[dict] = []
    source_rows: list[int] = []

    for sheet_row, raw in enumerate(records, first_row):
        label = (raw.get(GROUP_HEADER) or "").strip()
        filled = any((raw.get(h) or "").strip() for h in detail)
        where = f"sheet row {sheet_row}"
        if grand_totals:
            raise RecipeError(f"{where}: rows continue after the grand TOTAL")
        is_total = label == "TOTAL" or label.startswith("Total for ")
        if label and not is_total:                    # a group heading
            if filled:
                raise RecipeError(f"{where}: group heading {label!r} carries values")
            if group is not None:
                raise RecipeError(f"{where}: group {label!r} starts before "
                                  f"'Total for {group}'")
            group, group_sum = label, dict(zero)
            continue
        if is_total:
            if label == "TOTAL":
                if group is not None:
                    raise RecipeError(f"{where}: TOTAL before 'Total for {group}'")
                grand_totals = [_check("TOTAL", c, sheet_row, grand[c],
                                       parse_decimal(raw.get(c)))
                                for c in recipe.amount_columns]
                continue
            if group is None or label != f"Total for {group}":
                raise RecipeError(f"{where}: unexpected total row {label!r}"
                                  + (f" inside group {group!r}" if group else ""))
            subtotals += [_check(group, c, sheet_row, group_sum[c],
                                 parse_decimal(raw.get(c)))
                          for c in recipe.amount_columns]
            group = None
            continue
        if not filled:
            continue
        if group is None:
            raise RecipeError(f"{where}: a detail row outside any group")
        for column in recipe.amount_columns:
            value = parse_decimal(raw.get(column))
            if value is None:
                raise RecipeError(f"{where}: {column} {raw.get(column)!r} is not a number")
            group_sum[column] += value
            grand[column] += value

        kind = (raw.get(recipe.type_column) or "").strip() if recipe.type_column else ""
        keep = not recipe.types or kind in recipe.types
        if recipe.type_column:
            bucket = type_counts.setdefault(kind or "(blank)", {"kept": 0, "left_out": 0})
            bucket["kept" if keep else "left_out"] += 1
        if not keep:
            continue
        row = {recipe.group_column: group, **{h: raw.get(h, "") for h in detail}}
        if recipe.paid_amount:
            amount = parse_decimal(raw.get("Amount"))
            row[PAID_AMOUNT] = str(abs(amount))
            account = (raw.get(recipe.sign_account_column, "").strip()
                       if recipe.sign_account_column else group)
            tally = signs.setdefault(account or "(blank)", {"negative": 0, "positive": 0, "zero": 0})
            tally["negative" if amount < 0 else "positive" if amount > 0 else "zero"] += 1
        kept.append(row)
        source_rows.append(sheet_row)

    if group is not None:
        raise RecipeError(f"group {group!r} has no 'Total for {group}' row")
    out_headers = [recipe.group_column, *detail] + ([PAID_AMOUNT] if recipe.paid_amount else [])
    report = {
        "recipe": recipe.recipe_id, "version": RECIPE_VERSION,
        "report": recipe.report, "role": recipe.role,
        "rows_kept": len(kept),
        "subtotals_checked": len(subtotals),
        "grand_total": grand_totals or None,
        "totals_disagreeing": [t for t in subtotals + grand_totals if not t["agrees"]],
        "missing_required": _missing_required(recipe, kept),
        "note": recipe.note,
    }
    if recipe.type_column:
        report["transaction_types"] = type_counts
    if recipe.paid_amount:
        report["amount_signs_by_account"] = signs
    return out_headers, kept, source_rows, report


def _missing_required(recipe: Recipe, rows: list[dict]) -> list[dict]:
    """Kept rows whose required key is blank: normalization will quarantine
    them. Said before approval, so the reviewer is not surprised after."""
    out = []
    for field_name in _REQUIRED.get(recipe.role, ()):
        heading = recipe.column_map.get(field_name)
        if heading is None:
            continue
        blank = sum(1 for row in rows if not (row.get(heading) or "").strip())
        if blank:
            out.append({"field": field_name, "heading": heading,
                        "rows": blank, "of": len(rows)})
    return out


def _check(name: str, column: str, sheet_row: int, computed: Decimal,
           stated: Decimal | None) -> dict:
    """QuickBooks writes totals as binary floats (234.41000000000003); the
    comparison is to the cent, and both figures are kept as written."""
    computed = computed.quantize(_CENT)
    return {"group": name, "column": column, "sheet_row": sheet_row,
            "computed": str(computed),
            "stated": None if stated is None else str(stated),
            "agrees": stated is not None and stated.quantize(_CENT) == computed}


# --------------------------------------------------------------------------
# The AP control-account tie: one balance from each side, both footed.

GL_REPORT = "General Ledger"
GL_HEADERS = ("Distribution account", "Transaction date", "Transaction type", "Num",
              "Name", "Description", "Split", "Amount", "Balance")
AP_ACCOUNT = "Accounts Payable (A/P)"
_MONTHS = ("January|February|March|April|May|June|July|August|September|"
           "October|November|December")
_PERIOD = re.compile(rf"(?:({_MONTHS})\s+)?(\d{{1,2}}),\s*(\d{{4}})")


def _cells(row: list[str]) -> list[str]:
    cells = [c.strip() for c in row]
    while cells and not cells[-1]:
        cells.pop()
    return cells


def title_block(rows: list[list[str]]) -> dict:
    """Company, report name, period line and footer of a QuickBooks export."""
    first = [(_cells(r) or [""])[0] for r in rows[:3]] + ["", "", ""]
    footer = next((c[0] for c in (_cells(r) for r in reversed(rows)) if c), "")
    return {"company": first[0], "report": first[1], "period": first[2],
            "footer": footer}


def last_date(text: str) -> str | None:
    """The last date a QuickBooks period or footer line names, as ISO.

    "September 1-23, 2026" -> 2026-09-23; "January 1-September 23, 2026" ->
    2026-09-23; "As of June 30, 2026" -> 2026-06-30. A range's end day has
    no month of its own, so the nearest month named before it applies.
    """
    months = _MONTHS.split("|")
    found = list(_PERIOD.finditer(text or ""))
    if not found:
        return None
    match = found[-1]
    month = match.group(1)
    if month is None:
        named = re.findall(rf"({_MONTHS})", text[:match.start()])
        if not named:
            return None
        month = named[-1]
    return date(int(match.group(3)), months.index(month) + 1,
                int(match.group(2))).isoformat()


def is_general_ledger(rows: list[list[str]]) -> bool:
    if title_block(rows)["report"] != GL_REPORT:
        return False
    return any(tuple(_cells(r)[1:]) == GL_HEADERS and not _cells(r)[0]
               for r in rows[:12] if _cells(r))


def gl_account_balance(rows: list[list[str]], account: str = AP_ACCOUNT) -> dict:
    """One account's ending balance from a General Ledger export, footed.

    Ending = the Beginning Balance row + the period's activity. The activity
    printed on "Total for <account>" is recomputed from the detail rows, and
    the last running Balance must equal the ending balance; a disagreement
    or an unexpected layout (an account with sub-accounts) is refused, not
    worked around.
    """
    if not is_general_ledger(rows):
        raise RecipeError("this is not QuickBooks' standard General Ledger export")
    header = next(i for i, r in enumerate(rows)
                  if _cells(r) and not _cells(r)[0] and tuple(_cells(r)[1:]) == GL_HEADERS)
    amount_col = 1 + GL_HEADERS.index("Amount")
    balance_col = 1 + GL_HEADERS.index("Balance")

    def cell(row: list[str], col: int) -> str:
        return row[col].strip() if col < len(row) else ""

    start = next((i for i in range(header + 1, len(rows))
                  if cell(rows[i], 0) == account), None)
    if start is None:
        raise RecipeError(f"the ledger has no {account!r} account")
    beginning = Decimal("0")
    activity = Decimal("0")
    detail = 0
    last_balance: Decimal | None = None
    stated: Decimal | None = None
    for i in range(start + 1, len(rows)):
        row = rows[i]
        label = cell(row, 0)
        sheet_row = i + 1
        if label == f"Total for {account}":
            stated = parse_decimal(cell(row, amount_col))
            total_row = sheet_row
            break
        if label:
            raise RecipeError(
                f"sheet row {sheet_row}: {account!r} has sub-account {label!r}; "
                f"an account with sub-accounts is not read yet")
        if cell(row, 1) == "Beginning Balance":
            beginning = parse_decimal(cell(row, balance_col)) or Decimal("0")
            last_balance = beginning
            continue
        if not any(c.strip() for c in row):
            continue
        amount = parse_decimal(cell(row, amount_col))
        if amount is None:
            raise RecipeError(f"sheet row {sheet_row}: amount is not a number")
        activity += amount
        detail += 1
        last_balance = parse_decimal(cell(row, balance_col))
    else:
        raise RecipeError(f"{account!r} has no 'Total for {account}' row")
    ending = (beginning + activity).quantize(_CENT)
    checks = [_check(account, "Amount", total_row, activity, stated)]
    if last_balance is not None:
        checks.append(_check(account, "Balance", total_row, ending, last_balance))
    bad = [c for c in checks if not c["agrees"]]
    if bad:
        raise RecipeError(f"the ledger's {account} does not foot: {bad}")
    block = title_block(rows)
    return {"account": account, "beginning": str(beginning.quantize(_CENT)),
            "activity": str(activity.quantize(_CENT)), "ending": str(ending),
            "detail_rows": detail, "period": block["period"],
            "as_of": last_date(block["period"]),
            "basis": block["footer"].split(" ", 1)[0] if block["footer"].startswith(
                ("Accrual", "Cash")) else None,
            "checks": checks}


# QuickBooks reports that are recognized but deliberately have no recipe.
# Naming them stops a filename guess from mapping them as a flat table.
_NO_RECIPE = {
    GL_REPORT: "QuickBooks General Ledger: no mapping recipe (accounts nest "
               "sub-accounts and open with a Beginning Balance row). It is "
               "read by the AP subledger-to-ledger tie; do not map it as a table.",
    "Bills and Applied Payments": "QuickBooks Bills and Applied Payments: no "
               "mapping recipe, because nothing in it links a payment to the "
               "bill it settled.",
}


def unsupported_report(rows: list[list[str]]) -> str | None:
    """A note for a recognized QuickBooks export that has no recipe, else None."""
    report = title_block(rows)["report"]
    if report not in _NO_RECIPE:
        return None
    heading = next((c for c in (_cells(r) for r in rows[3:12]) if c), [])
    return _NO_RECIPE[report] if heading and not heading[0] else None
