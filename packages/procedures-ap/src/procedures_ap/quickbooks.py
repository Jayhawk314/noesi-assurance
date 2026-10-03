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

List reports (trial balance, A/R aging, inventory valuation) have no
groups: their TOTAL row is recomputed and compared the same way, a row's own
total is footed against its parts, and a nested row (a category or parent
customer heading) is refused, since that layout was not seen in a real
export. Some recipes add columns computed from the exported ones (an account
number, a signed balance, an entry name and line number); the originals stay.

Recognition is exact: the report name in the title block and the heading
row must match the standard layout the recipe was built from (verified
against real QuickBooks Online exports, tests/fixtures/quickbooks/ and
tests/fixtures/quickbooks/kestrel_qbo/). A
report with customized columns is not recognized and falls back to the
ordinary header mapping, which the user checks as usual. A recipe is
part of the mapping the user confirms, and its id is part of the spec's
digest.

What QuickBooks does not export is refused, not invented: bills usually
carry no number (Num is blank unless someone typed the vendor's invoice
number), vendors are identified by name, and no standard vendor report
states which bill a payment settled (Bills and Applied Payments lists them
side by side, in no consistent order). Rows missing a required key are
quarantined by normalization with the reason.

Not yet covered: the General Ledger export nests sub-accounts inside
accounts and opens each with a Beginning Balance row; it is read for one
account's balance (the A/P tie), not mapped as a table. The Reconciliation
Report has no Excel export at all (QuickBooks offers it as PDF only).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from procedures_ap.ingest import _REQUIRED, parse_date_text, parse_decimal

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
    label_column: str = ""          # flat list whose first heading is blank: its name
    totals: bool = False            # flat list closed by a TOTAL row, checked
    row_total: tuple[str, tuple[str, ...]] | None = None   # per-row footing check
    derive: str = ""                # columns computed from the as-exported ones
    blank_amounts: bool = False     # a blank amount is zero (debit/credit columns)
    # Changes when this recipe's reading of a file changes, so a spec approved
    # under the old reading is refused, not silently re-read.
    version: str = RECIPE_VERSION

    @property
    def grouped(self) -> bool:
        return bool(self.group_column)

    @property
    def blank_first(self) -> bool:
        """The heading row opens with an empty cell (groups or row labels)."""
        return bool(self.group_column or self.label_column)

    @property
    def label(self) -> str:
        return f"QuickBooks {self.report} → {self.role}"


_TX_BY_VENDOR = ("Date", "Track 1099", "Transaction type", "Num", "Posting (Y/N)",
                 "Memo", "Account full name", "Item split account", "Amount")
_BILL_PAYMENTS = ("Bill Payment (Check)", "Bill Payment (Credit Card)")
_NO_BILL_NUMBER = ("Bills are identified by Num, which QuickBooks leaves blank "
                   "unless the vendor's invoice number was typed in; bills "
                   "without one are quarantined, not numbered for you.")

# Columns a recipe computes from the as-exported ones (the originals stay).
ACCOUNT = "Account"            # account number, or the full name when it has none
BALANCE = "Balance"            # Debit - Credit
ENTRY = "Entry"                # date, type, num and name: how an auditor names an entry
LINE = "Line"
CREATED_DATE = "Created date"
TRANSACTION_ID = "Transaction ID"
_JOURNAL = ("Transaction date", "Transaction type", "Num", "Name", "Description",
            "Account Name", "Debit", "Credit")
_JOURNAL_MAP = {"entry_id": ENTRY, "line": LINE, "entry_date": "Transaction date",
                "account": ACCOUNT, "debit": "Debit", "credit": "Credit",
                "description": "Description", "source": "Transaction type",
                "document_number": "Num"}
_JOURNAL_NOTE = ("QuickBooks groups each transaction's lines under its own "
                 "transaction ID and closes it with a debit/credit total, checked here. "
                 "An entry is named by date, type, Num and name (Num alone repeats "
                 "across types and is blank for deposits); two transactions that "
                 "would share a name are told apart by their transaction ID.")
_ACCOUNT_NUMBER = re.compile(r"^(\d[\d.\-]*)\s+\S")

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
        column_map={"voucher_number": "Num", "invoice_number": "Num",
                    "vendor_number": "Vendor",
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
        recipe_id="qbo.transaction_list_by_vendor.direct_payments",
        report="Transaction List by Vendor", role="Direct_payments",
        headers=_TX_BY_VENDOR, group_column="Vendor",
        column_map={"payment_number": "Num", "vendor_number": "Vendor",
                    "payment_amount": PAID_AMOUNT, "payment_date": "Date"},
        type_column="Transaction type", types=("Check", "Expense"),
        paid_amount=True, sign_account_column="Account full name",
        note="Checks and expenses paid straight to a vendor, without a bill; "
             "bill payments are the Payments recipe."),
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
        column_map={"voucher_number": "Num", "invoice_number": "Num",
                    "vendor_number": "Vendor",
                    "voucher_amount": "Amount", "voucher_date": "Date"},
        note="Open bills only. The grand TOTAL of Open balance is the AP "
             "subledger balance, to compare with the ledger's Accounts "
             "Payable. " + _NO_BILL_NUMBER),
    Recipe(
        recipe_id="qbo.vendor_contact_list.vendors", report="Vendor Contact List",
        role="Vendors", version="qbo-v2",   # v2: a row with values but no Vendor is refused
        headers=("Vendor", "Phone numbers", "Email", "Full name",
                 "Billing address", "Account #"),
        column_map={"vendor_number": "Vendor", "vendor_name": "Vendor",
                    "address": "Billing address", "phone": "Phone numbers"},
        amount_columns=(),
        note="QuickBooks identifies vendors by display name, so the name "
             "is also the vendor key. 'Account #' is your account number "
             "with the vendor, not a vendor id."),
    Recipe(
        recipe_id="qbo.trial_balance.trial_balance", report="Trial Balance",
        role="Trial_balance", headers=("Account Name", "Debit", "Credit"),
        amount_columns=("Debit", "Credit"), totals=True, derive="trial_balance",
        column_map={"account": ACCOUNT, "description": "Account Name",
                    "balance": BALANCE},
        note="One period only, with no statement line: map the lines on the "
             "line-mapping screen, and build the trial balance from two exports "
             "(this year and last) for prior-year balances. 'Account' is the "
             "account number when the name starts with one, else the full name; "
             "'Balance' is Debit minus Credit."),
    Recipe(
        recipe_id="qbo.ar_aging_summary.ar_listing", report="A/R Aging Summary Report",
        role="AR_listing", label_column="Customer",
        headers=("CURRENT", "1 - 30", "31 - 60", "61 - 90", "91 AND OVER", "Total"),
        amount_columns=("CURRENT", "1 - 30", "31 - 60", "61 - 90", "91 AND OVER",
                        "Total"),
        totals=True, row_total=("Total", ("CURRENT", "1 - 30", "31 - 60", "61 - 90",
                                          "91 AND OVER")),
        column_map={"customer_number": "Customer", "customer_name": "Customer",
                    "balance": "Total", "current": "CURRENT", "days_1_30": "1 - 30",
                    "days_31_60": "31 - 60", "days_61_90": "61 - 90",
                    "days_over_90": "91 AND OVER"},
        note="QuickBooks identifies customers by display name, so the name is also "
             "the customer key. Buckets count days past due, not days since the "
             "invoice date. Sub-customers (nested rows) are not read yet."),
    Recipe(
        recipe_id="qbo.inventory_valuation_summary.inventory_listing",
        report="Inventory Valuation Summary", role="Inventory_listing",
        label_column="Item", headers=("SKU", "Qty", "Asset Value", "Calc. Avg"),
        amount_columns=("Qty", "Asset Value"), totals=True,
        column_map={"stock_number": "SKU", "description": "Item", "quantity": "Qty",
                    "unit_cost": "Calc. Avg", "cost": "Asset Value"},
        note="'Calc. Avg' is QuickBooks' average cost, the unit cost it carries the "
             "item at. Items grouped under categories are not read yet."),
    Recipe(
        recipe_id="qbo.journal.journal_entries", report="Journal",
        role="Journal_entries", headers=_JOURNAL, group_column=TRANSACTION_ID,
        amount_columns=("Debit", "Credit"), derive="journal", blank_amounts=True,
        column_map=_JOURNAL_MAP,
        note=_JOURNAL_NOTE + " This layout has no 'Created on' or 'Created by': "
             "posted-after-period-end and unauthorized-user tests need the report "
             "customized to add them."),
    Recipe(
        recipe_id="qbo.journal_created.journal_entries", report="Journal",
        role="Journal_entries", headers=(*_JOURNAL, "Created on", "Created by"),
        group_column=TRANSACTION_ID, amount_columns=("Debit", "Credit"),
        derive="journal", blank_amounts=True,
        column_map={**_JOURNAL_MAP, "posted_date": CREATED_DATE,
                    "posted_by": "Created by"},
        note=_JOURNAL_NOTE + " 'Created on' is a timestamp; 'Created date' is its "
             "date, read by the posted-date tests."),
)}


def _heading_row(rows: list[list[str]], recipe: Recipe) -> int | None:
    for index, row in enumerate(rows, start=1):
        cells = [c.strip() for c in row]
        while cells and not cells[-1]:
            cells.pop()
        if recipe.blank_first:
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
    expected = ([GROUP_HEADER, *recipe.headers] if recipe.blank_first
                else list(recipe.headers))
    if headers != expected:
        shown = ["", *recipe.headers] if recipe.blank_first else list(recipe.headers)
        raise RecipeError(
            f"the headings {headers} are not QuickBooks' standard "
            f"{recipe.report} layout {shown}; a customized report needs an "
            f"ordinary mapping instead of this recipe")
    if not recipe.grouped:
        return _apply_flat(recipe, headers, records, first_row)

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
            blank = not (raw.get(column) or "").strip()
            value = Decimal("0") if blank and recipe.blank_amounts else parse_decimal(
                raw.get(column))
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
    if recipe.derive:
        out_headers, kept = _DERIVE[recipe.derive](out_headers, kept, source_rows)
    report = {
        "recipe": recipe.recipe_id, "version": recipe.version,
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


def _apply_flat(recipe: Recipe, headers: list[str], records: list[dict],
                first_row: int) -> tuple[list[str], list[dict], list[int], dict]:
    """A list report: one row per item, optionally closed by a TOTAL row.

    The TOTAL is recomputed from the rows for every amount column; a row's own
    total (the aging's Total) is footed against its buckets. Nested rows (a
    category or parent customer heading, or a 'Total for' subtotal) are a
    layout this reader was not built on, and are refused rather than flattened.
    """
    label_col = recipe.label_column
    detail = list(recipe.headers)
    grand = {c: Decimal("0") for c in recipe.amount_columns}
    grand_totals: list[dict] = []
    row_checks: list[dict] = []
    kept: list[dict] = []
    source_rows: list[int] = []
    for sheet_row, raw in enumerate(records, first_row):
        where = f"sheet row {sheet_row}"
        first = ((raw.get(GROUP_HEADER) if label_col else raw.get(detail[0])) or "").strip()
        rest = detail if label_col else detail[1:]
        filled = any((raw.get(h) or "").strip() for h in rest)
        if not first and not filled:
            continue
        if grand_totals:
            raise RecipeError(f"{where}: rows continue after the grand TOTAL")
        if recipe.totals and first == "TOTAL":
            grand_totals = [_check("TOTAL", c, sheet_row, grand[c],
                                   parse_decimal(raw.get(c))
                                   if (raw.get(c) or "").strip() else Decimal("0"))
                            for c in recipe.amount_columns]
            continue
        if first.startswith("Total for "):
            raise RecipeError(
                f"{where}: {first!r} is a subtotal; this {recipe.report} layout "
                f"(sub-items or categories) is not read yet")
        if label_col and first and not filled:
            # Not guessed either way: a category heading would be misread as
            # an item, and no export seen prints an item with every cell blank.
            raise RecipeError(
                f"{where}: {first!r} has no values: a nested heading (sub-items or "
                f"categories, not read yet) or an item with every cell blank. If it "
                f"is an item, enter 0 in its amounts and export again")
        if not first:
            raise RecipeError(f"{where}: a row with values but no "
                              f"{label_col or detail[0]}")
        for column in recipe.amount_columns:
            value = parse_decimal(raw.get(column)) if (raw.get(column) or "").strip() \
                else Decimal("0")
            if value is None:
                raise RecipeError(f"{where}: {column} {raw.get(column)!r} is not a number")
            grand[column] += value
        if recipe.row_total:
            total_col, parts = recipe.row_total
            computed = sum((parse_decimal(raw.get(p)) or Decimal("0")) for p in parts)
            row_checks.append(_check(first, total_col, sheet_row, computed,
                                     parse_decimal(raw.get(total_col)) or Decimal("0")))
        row = ({label_col: first} if label_col else {}) | {h: raw.get(h, "") for h in detail}
        kept.append(row)
        source_rows.append(sheet_row)
    if recipe.totals and not grand_totals:
        raise RecipeError(f"the {recipe.report} has no grand TOTAL row")
    out_headers = ([label_col] if label_col else []) + detail
    if recipe.derive:
        out_headers, kept = _DERIVE[recipe.derive](out_headers, kept, source_rows)
    report = {"recipe": recipe.recipe_id, "version": recipe.version,
              "report": recipe.report, "role": recipe.role,
              "rows_kept": len(kept), "subtotals_checked": 0,
              "rows_footed": len(row_checks),
              "grand_total": grand_totals or None,
              "totals_disagreeing": [t for t in row_checks + grand_totals
                                     if not t["agrees"]],
              "missing_required": _missing_required(recipe, kept),
              "note": recipe.note}
    return out_headers, kept, source_rows, report


def account_key(name: str) -> str:
    """The account number a QuickBooks account name starts with ("10100
    Checking" -> "10100"), else the whole name: QuickBooks without account
    numbers names accounts only by name."""
    name = " ".join((name or "").split())
    match = _ACCOUNT_NUMBER.match(name)
    return match.group(1) if match else name


def _derive_trial_balance(headers, rows, source_rows):
    seen: dict[str, int] = {}
    for row, sheet_row in zip(rows, source_rows):
        key = account_key(row["Account Name"])
        if key in seen:
            raise RecipeError(f"sheet row {sheet_row}: account {key!r} also appears on "
                              f"sheet row {seen[key]}")
        seen[key] = sheet_row
        debit = parse_decimal(row.get("Debit")) or Decimal("0")
        credit = parse_decimal(row.get("Credit")) or Decimal("0")
        row[ACCOUNT] = key
        row[BALANCE] = str((debit - credit).quantize(_CENT))
    return [*headers, ACCOUNT, BALANCE], rows


def _derive_journal(headers, rows, source_rows):
    """Name each transaction as the auditor would, number its lines, and give
    each line the account number. Date, type, Num and name repeat on every
    line of a transaction; a line that disagrees is refused."""
    first: dict[str, dict] = {}
    names: dict[str, set] = {}
    for row, sheet_row in zip(rows, source_rows):
        txn = row[TRANSACTION_ID]
        ident = tuple((row.get(h) or "").strip() for h in
                      ("Transaction date", "Transaction type", "Num", "Name"))
        if txn in first and first[txn]["ident"] != ident:
            raise RecipeError(f"sheet row {sheet_row}: transaction {txn} changes its "
                              f"date, type, Num or name between lines")
        if txn not in first:
            when = parse_date_text(ident[0])
            if when is None:
                raise RecipeError(f"sheet row {sheet_row}: transaction date "
                                  f"{ident[0]!r} is not a date")
            label = " ".join(x for x in (when.isoformat(), ident[1],
                                         ident[2] or "(no num)", ident[3]) if x)
            first[txn] = {"ident": ident, "label": label, "lines": 0}
            names.setdefault(label, set()).add(txn)
    created = "Created on" in headers
    for row, sheet_row in zip(rows, source_rows):
        entry = first[row[TRANSACTION_ID]]
        entry["lines"] += 1
        shared = len(names[entry["label"]]) > 1
        row[ENTRY] = (f"{entry['label']} [txn {row[TRANSACTION_ID]}]" if shared
                      else entry["label"])
        row[LINE] = str(entry["lines"])
        row[ACCOUNT] = account_key(row.get("Account Name", ""))
        if created:
            stamp = (row.get("Created on") or "").strip()
            row[CREATED_DATE] = stamp.split(" ", 1)[0]
            if stamp and parse_date_text(row[CREATED_DATE]) is None:
                raise RecipeError(f"sheet row {sheet_row}: Created on {stamp!r} "
                                  f"does not start with a date")
    return [*headers, ENTRY, LINE, ACCOUNT] + ([CREATED_DATE] if created else []), rows


_DERIVE = {"trial_balance": _derive_trial_balance, "journal": _derive_journal}


def combine_trial_balances(current: list[dict], prior: list[dict] | None) -> list[dict]:
    """This year's and last year's Trial Balance exports (each flattened by the
    trial-balance recipe) as one schedule: Account, Description, Balance,
    Prior Balance. An account on only one side is 0.00 on the other, which is
    what QuickBooks' omission of a zero-balance account means."""
    out: dict[str, dict] = {}
    for row in current:
        out[row[ACCOUNT]] = {"Account": row[ACCOUNT], "Description": row["Account Name"],
                             "Balance": row[BALANCE], "Prior Balance": "0.00"}
    for row in prior or []:
        item = out.setdefault(row[ACCOUNT], {"Account": row[ACCOUNT],
                                             "Description": row["Account Name"],
                                             "Balance": "0.00"})
        item["Prior Balance"] = row[BALANCE]
    if prior is None:
        for item in out.values():
            item.pop("Prior Balance")
    return list(out.values())


def _missing_required(recipe: Recipe, rows: list[dict]) -> list[dict]:
    """Kept rows whose required key is blank: normalization will quarantine
    them. Said with the mapping, before anything is loaded."""
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
# Full names on screen and in PDF titles; QuickBooks' Excel titles abbreviate
# ("As of Jun 30, 2026").
_MONTHS = (r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
           r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?(?![A-Za-z])")
_PERIOD = re.compile(rf"(?:({_MONTHS})\s+)?(\d{{1,2}}),\s*(\d{{4}})")
_WHOLE_MONTH = re.compile(rf"({_MONTHS}),?\s+(\d{{4}})")


def _month_number(name: str) -> int:
    return ("jan feb mar apr may jun jul aug sep oct nov dec".split()
            .index(name.strip(".")[:3].lower()) + 1)


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
    2026-09-23; "As of June 30, 2026" and "As of Jun 30, 2026" -> 2026-06-30.
    A range's end day has no month of its own, so the nearest month named
    before it applies. A period of whole months names no day ("April-June,
    2026", "August 2026"): it ends on the last day of its last month.
    A date that cannot exist ("June 31, 2026") gives None, as unreadable text does.
    """
    text = text or ""
    found = list(_PERIOD.finditer(text))
    # A whole month named after the last dated day ends the range:
    # "Jan 1, 2026 - Mar 2026" ends 2026-03-31, not on January 1.
    whole = [m for m in _WHOLE_MONTH.finditer(text)
             if not found or m.start() >= found[-1].end()]
    try:
        if whole:
            year, month = int(whole[-1].group(2)), _month_number(whole[-1].group(1))
            following = date(year + month // 12, month % 12 + 1, 1)
            return date.fromordinal(following.toordinal() - 1).isoformat()
        if not found:
            return None
        match = found[-1]
        month = match.group(1)
        if month is None:
            named = re.findall(_MONTHS, text[:match.start()])
            if not named:
                return None
            month = named[-1]
        return date(int(match.group(3)), _month_number(month),
                    int(match.group(2))).isoformat()
    except ValueError:
        return None


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
