# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Cash: bank reconciliation re-performance and interbank transfer analysis.

Bank_reconciliation rows carry one item each (item_type):
  bank_balance, book_balance, deposit_in_transit, outstanding_check,
  bank_adjustment (+/- to the bank side), book_adjustment (+/- to books),
  last_check_issued (reference = the last check number written in the period).
Cutoff_statement rows are the items that cleared the bank after period end,
as shown on a cutoff statement the auditor obtained directly from the bank.

cash.bank_reconciliation re-foots each reconciliation and tests its
outstanding checks and deposits in transit against the cutoff statement.
cash.interbank_transfers tests each transfer's four dates against period
end and against the reconciliations (kiting, transfers in transit).
"""

from __future__ import annotations

from procedures_cycles.common import (
    ZERO, day, key_text, money, policy_date, receipt, records, source_ref, text,
)

ITEM_TYPES = ("bank_balance", "book_balance", "deposit_in_transit", "outstanding_check",
              "bank_adjustment", "book_adjustment", "last_check_issued")


def _norm_type(value) -> str:
    return text(value).lower().replace(" ", "_").replace("-", "_")


def _recs(tables: dict) -> dict[str, dict]:
    accounts: dict[str, dict] = {}
    for r in records(tables, "Bank_reconciliation"):
        acct = key_text(r.get("account"))
        a = accounts.setdefault(acct, {"items": {t: [] for t in ITEM_TYPES}, "unknown": []})
        kind = _norm_type(r.get("item_type"))
        (a["items"][kind] if kind in a["items"] else a["unknown"]).append(r)
    return accounts


def _num(value) -> int | None:
    try:
        return int(key_text(value))
    except ValueError:
        return None


def bank_reconciliation(tables: dict, policies: dict):
    pid = "cash.bank_reconciliation"
    period_end = policy_date(policies, "period_end")
    findings, per_account = [], {}
    cutoff: dict[str, list[dict]] = {}
    for c in records(tables, "Cutoff_statement"):
        cutoff.setdefault(key_text(c.get("account")), []).append(c)
    for acct, rec in _recs(tables).items():
        items = rec["items"]
        for r in rec["unknown"]:
            findings.append(receipt(pid, (acct, "unknown_item", key_text(r.get("reference"))),
                                    "AMBIGUOUS",
                                    f"account {acct}: item type {text(r.get('item_type'))!r} "
                                    f"is not one of {', '.join(ITEM_TYPES)}",
                                    {"finding_class": "REFUSAL", "cycle": "cash"}))
        total = {t: sum((money(r.get("amount")) for r in items[t]), ZERO) for t in ITEM_TYPES}
        if not items["bank_balance"] or not items["book_balance"]:
            findings.append(receipt(pid, (acct, "incomplete"), "AMBIGUOUS",
                                    f"account {acct}: the reconciliation lacks a bank or "
                                    "book balance", {"finding_class": "REFUSAL",
                                                     "cycle": "cash"}))
            continue
        adjusted_bank = (total["bank_balance"] + total["deposit_in_transit"]
                         - total["outstanding_check"] + total["bank_adjustment"])
        adjusted_book = total["book_balance"] + total["book_adjustment"]
        if adjusted_bank != adjusted_book:
            findings.append(receipt(
                pid, (acct, "does_not_reconcile"), "CLASH",
                f"account {acct}: adjusted bank {adjusted_bank} ≠ adjusted books "
                f"{adjusted_book}", {"finding_class": "PROVED_EXCEPTION", "cycle": "cash"},
                adjusted_bank - adjusted_book))
        cleared = {}
        for c in cutoff.get(acct, []):
            cleared.setdefault(key_text(c.get("reference")), []).append(c)
        last = None
        if items["last_check_issued"]:
            last = _num(items["last_check_issued"][0].get("reference"))
        listed_checks = set()
        oc_results = {"cleared": 0, "not_cleared": 0, "amount_differs": 0}
        for oc in items["outstanding_check"]:
            ref = key_text(oc.get("reference"))
            listed_checks.add(ref)
            amount = money(oc.get("amount"))
            number = _num(ref)
            source = [source_ref("Bank_reconciliation", oc, "reference")]
            if last is not None and number is not None and number > last:
                findings.append(receipt(
                    pid, (acct, "check_after_period", ref), "CLASH",
                    f"account {acct}: check {ref} is listed outstanding but is numbered "
                    f"after the last check of the period ({last})",
                    {"finding_class": "PROVED_EXCEPTION", "cycle": "cash",
                     "source_rows": source}, amount))
            hits = cleared.get(ref, [])
            if not hits:
                oc_results["not_cleared"] += 1
                findings.append(receipt(
                    pid, (acct, "outstanding_not_cleared", ref), "TENSION",
                    f"account {acct}: outstanding check {ref} ({amount}) did not clear on "
                    "the cutoff statement — follow up (subsequent statement, voided, stale)",
                    {"finding_class": "CONJECTURE", "cycle": "cash", "source_rows": source}))
                continue
            paid = money(hits[0].get("amount"))
            if paid != amount:
                oc_results["amount_differs"] += 1
                findings.append(receipt(
                    pid, (acct, "cleared_amount_differs", ref), "CLASH",
                    f"account {acct}: check {ref} listed at {amount} cleared for {paid}",
                    {"finding_class": "PROVED_EXCEPTION", "cycle": "cash",
                     "source_rows": source}, amount - paid))
            else:
                oc_results["cleared"] += 1
        omitted = []
        for ref, hits in cleared.items():
            hit = hits[0]
            kind = _norm_type(hit.get("item_type"))
            if kind.startswith("dep"):
                continue
            number = _num(ref)
            cleared_on = day(hit.get("cleared_date"))
            if ref in listed_checks or number is None or last is None or number > last:
                continue
            if cleared_on is not None and cleared_on <= period_end:
                continue
            omitted.append(ref)
            findings.append(receipt(
                pid, (acct, "omitted_outstanding_check", ref), "ORPHAN",
                f"account {acct}: check {ref} (written in the period, ≤ {last}) cleared "
                f"after period end but is not on the outstanding-check list — cash may be "
                "overstated", {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "cash",
                               "amount": money(hit.get("amount"))},
                money(hit.get("amount"))))
        deposits = [c for c in cutoff.get(acct, [])
                    if _norm_type(c.get("item_type")).startswith("dep")]
        dit_unmatched = []
        pool = list(deposits)
        for dit in items["deposit_in_transit"]:
            amount = money(dit.get("amount"))
            match = next((d for d in pool if money(d.get("amount")) == amount), None)
            if match is None:
                dit_unmatched.append(str(amount))
                findings.append(receipt(
                    pid, (acct, "deposit_not_cleared", str(amount)), "TENSION",
                    f"account {acct}: deposit in transit {amount} is not on the cutoff "
                    "statement", {"finding_class": "CONJECTURE", "cycle": "cash",
                                  "source_rows": [source_ref("Bank_reconciliation", dit,
                                                             "reference")]}))
            else:
                pool.remove(match)
        per_account[acct] = {
            "totals": total, "adjusted_bank": adjusted_bank, "adjusted_book": adjusted_book,
            "outstanding_checks": len(items["outstanding_check"]), **oc_results,
            "last_check_issued": last, "omitted_outstanding_checks": omitted,
            "deposits_in_transit_not_cleared": dit_unmatched}
    return findings, {"population": len(records(tables, "Bank_reconciliation")),
                      "accounts": per_account, "exceptions": len(findings)}


def interbank_transfers(tables: dict, policies: dict):
    pid = "cash.interbank_transfers"
    pe = policy_date(policies, "period_end")
    recs = _recs(tables)
    findings, rows = [], []
    for t in records(tables, "Transfers"):
        tid = key_text(t.get("transfer_id"))
        amount = money(t.get("amount"))
        frm, to = key_text(t.get("from_account")), key_text(t.get("to_account"))
        d_books, d_bank = day(t.get("disbursed_books")), day(t.get("disbursed_bank"))
        r_books, r_bank = day(t.get("received_books")), day(t.get("received_bank"))
        src = [source_ref("Transfers", t, "transfer_id")]
        missing = [n for n, v in (("disbursed_books", d_books), ("disbursed_bank", d_bank),
                                  ("received_books", r_books), ("received_bank", r_bank))
                   if v is None]
        if missing:
            findings.append(receipt(pid, (tid, "incomplete"), "AMBIGUOUS",
                                    f"transfer {tid}: missing {', '.join(missing)}",
                                    {"finding_class": "REFUSAL", "cycle": "cash"}))
            continue
        row = {"transfer": tid, "amount": amount, "issues": []}
        base = {"cycle": "cash", "amount": amount, "from_account": frm, "to_account": to,
                "disbursed_books": d_books, "disbursed_bank": d_bank,
                "received_books": r_books, "received_bank": r_bank, "source_rows": src}
        if r_books <= pe < d_books:
            row["issues"].append("kiting")
            findings.append(receipt(
                pid, (tid, "kiting"), "CLASH",
                f"transfer {tid}: the receipt is booked in the period ({r_books}) but the "
                f"disbursement only after period end ({d_books}) — cash is counted twice "
                f"(overstated by {amount})",
                {**base, "finding_class": "PROVED_EXCEPTION", "direction": "overstatement"},
                amount))
        if d_books <= pe < r_books:
            row["issues"].append("receipt_not_booked")
            findings.append(receipt(
                pid, (tid, "receipt_not_booked"), "CLASH",
                f"transfer {tid}: the disbursement is booked in the period ({d_books}) but "
                f"the receipt only after period end ({r_books}) — cash understated by "
                f"{amount}", {**base, "finding_class": "PROVED_EXCEPTION",
                              "direction": "understatement"}, amount))
        if d_books <= pe < d_bank:
            refs = {key_text(r.get("reference"))
                    for r in recs.get(frm, {}).get("items", {}).get("outstanding_check", [])}
            if tid not in refs:
                row["issues"].append("missing_outstanding_check")
                findings.append(receipt(
                    pid, (tid, "missing_outstanding_check"), "CLASH",
                    f"transfer {tid}: disbursed per books {d_books} but cleared the bank "
                    f"{d_bank}; it should be an outstanding check on the {frm} "
                    "reconciliation and is not", {**base,
                                                  "finding_class": "PROVED_EXCEPTION"},
                    amount))
        if r_books <= pe < r_bank:
            dits = [money(r.get("amount")) for r in
                    recs.get(to, {}).get("items", {}).get("deposit_in_transit", [])]
            if amount not in dits:
                row["issues"].append("missing_deposit_in_transit")
                findings.append(receipt(
                    pid, (tid, "missing_deposit_in_transit"), "CLASH",
                    f"transfer {tid}: received per books {r_books} but by the bank "
                    f"{r_bank}; it should be a deposit in transit on the {to} "
                    "reconciliation and is not", {**base,
                                                  "finding_class": "PROVED_EXCEPTION"},
                    amount))
        if r_bank <= pe < r_books:
            row["issues"].append("receipt_unrecorded_in_books")
            findings.append(receipt(
                pid, (tid, "receipt_unrecorded_in_books"), "TENSION",
                f"transfer {tid}: the bank received it {r_bank} but the books only {r_books}; "
                f"the {to} reconciliation needs a book-side adjustment",
                {**base, "finding_class": "CONJECTURE"}))
        if d_bank <= pe < d_books:
            row["issues"].append("disbursement_unrecorded_in_books")
            findings.append(receipt(
                pid, (tid, "disbursement_unrecorded_in_books"), "TENSION",
                f"transfer {tid}: cleared the {frm} bank {d_bank} but was booked "
                f"{d_books}; investigate", {**base, "finding_class": "CONJECTURE"}))
        rows.append(row)
    return findings, {"population": len(records(tables, "Transfers")),
                      "transfers": rows, "period_end": pe, "exceptions": len(findings)}


__all__ = ["bank_reconciliation", "interbank_transfers", "ITEM_TYPES"]
