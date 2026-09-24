# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The illustrative accounting path is balanced and tied to its case inputs."""

import csv
import json
from decimal import Decimal
from pathlib import Path


CASE = Path(__file__).resolve().parents[2] / "case-studies" / "harborline-marine"
LEDGER = json.loads((CASE / "learning" / "trace-ledger.json").read_text(encoding="utf-8"))


def _record(filename, field, key):
    with (CASE / "data" / filename).open(newline="", encoding="utf-8") as handle:
        return next(row for row in csv.DictReader(handle) if row[field] == key)


def test_teaching_ledger_ties_to_case_and_balances():
    source = LEDGER["source"]
    po = _record("purchase_orders.csv", "PO Number", source["purchase_order"])
    receipt = _record("goods_receipts.csv", "Receipt Number", source["receipt"])
    voucher = _record("vouchers.csv", "Voucher Number", source["voucher"])
    payment = _record("payments.csv", "Payment Number", source["payment"])
    assert po["PO Number"] == receipt["PO Number"] == voucher["PO Number"]
    assert payment["Voucher Number"] == source["voucher"]
    assert Decimal(source["ordered"]) == Decimal(po["PO Amount"])
    assert Decimal(source["accepted"]) == Decimal(receipt["Received Amount"])
    assert Decimal(source["billed"]) == Decimal(voucher["Voucher Amount"])
    assert Decimal(source["paid"]) == Decimal(payment["Payment Amount"])
    assert Decimal(source["unresolved_difference"]) == (
        Decimal(source["billed"]) - Decimal(source["accepted"]))

    for entry in LEDGER["journal"]:
        debit = sum(Decimal(line["debit"] or 0) for line in entry["lines"])
        credit = sum(Decimal(line["credit"] or 0) for line in entry["lines"])
        assert debit == credit, entry["event"]
    trial = LEDGER["trial_balance"]
    assert sum(Decimal(row["debit"] or 0) for row in trial) == sum(
        Decimal(row["credit"] or 0) for row in trial)

    statement = LEDGER["statement_excerpt"]
    income = statement["income_statement"]
    balance = statement["balance_sheet"]
    assert Decimal(income["security_services_expense"]) == Decimal(source["billed"])
    assert Decimal(balance["cash"]) == Decimal(balance["ending_equity"])
    assert Decimal(balance["cash"]) == (
        Decimal(balance["opening_equity"]) - Decimal(source["paid"]))
    assert Decimal(balance["ending_equity"]) == (
        Decimal(balance["opening_equity"]) - Decimal(income["net_loss"]))
