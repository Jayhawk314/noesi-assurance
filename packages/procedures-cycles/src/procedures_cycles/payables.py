# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""ap.unrecorded_liabilities_search — search for unrecorded liabilities.

Inputs:
- Unpaid_bills: the year-end accounts payable listing (what the client says
  it owed); Vouchers is read that way when it is not loaded;
- Subsequent_payments: disbursements made after year-end (the subsequent
  check register); Payments is read that way when it is not loaded. A row in
  it dated on or before period end, or undated, is named and left out;
- Disbursement_inspection (auditor evidence): for each inspected payment
  line, the date the liability arose per the receiving report or service
  invoice, the amount owed at that date, and, for a liability recorded
  outside payables (sales tax, accrued expenses), the account it was in.

The engine:
1. selects disbursements — every check whose total exceeds the approved
   threshold, plus a systematic selection (every k-th remaining check from
   a start) when those policies are set — so the selection is reproducible;
2. for each inspected line decides where it belongs: a liability that arose
   on or before period end must be on the listing at the right amount; one
   that arose after must not be;
3. reports selected disbursements not yet inspected, and payments whose
   amount differs from the listed voucher, as open leads.

An inspection row may carry, instead of a date, a recorded conclusion of
"no misstatement" from the team member who did the work; it counts as
inspected (concluded_by_reference) and is not re-evaluated.

It cannot see liabilities that were never paid after year-end; the
contract's limitations say so.
"""

from __future__ import annotations

from decimal import Decimal

from procedures_cycles import sampling
from procedures_cycles.common import (
    ZERO, dec, day, key_text, money, policy_date, policy_decimal, receipt, records,
    source_ref, text,
)


NO_MISSTATEMENT = {"no misstatement", "no exception", "no exceptions", "properly included",
                   "properly excluded", "ok"}


def _check_of(payment: dict) -> str:
    check = text(payment.get("check_number"))
    return check or text(payment.get("payment_number"))


def select_disbursements(payments: list[dict], threshold: Decimal,
                         interval: int | None, start: int | None,
                         limit: int | None = None) -> dict:
    """Check-level selection: all above threshold, then every k-th of the rest."""
    checks: dict[str, Decimal] = {}
    order: list[str] = []
    for p in payments:
        check = _check_of(p)
        if check not in checks:
            checks[check] = ZERO
            order.append(check)
        checks[check] += money(p.get("payment_amount"))
    above = [c for c in order if checks[c] > threshold]
    rest = [c for c in order if checks[c] <= threshold]
    systematic: list[str] = []
    if interval and start and rest:
        positions = sampling.systematic_selection(len(rest), interval, start, limit=limit)
        systematic = [rest[i - 1] for i in positions]
    return {"check_totals": checks, "above_threshold": above,
            "systematic": systematic, "remaining_population": len(rest)}


def unrecorded_liabilities_search(tables: dict, policies: dict):
    pid = "ap.unrecorded_liabilities_search"
    period_end = policy_date(policies, "period_end")
    threshold = policy_decimal(policies, "search_threshold")
    interval = dec(policies.get("search_interval"))
    start = dec(policies.get("search_start"))
    limit = dec(policies.get("search_systematic_count"))
    # The year-end listing and the payments after year end each have a role
    # of their own (25 Nov 2026), so an engagement that loads the year's own
    # bills and payments for the other tests can still run the search. Each
    # falls back to the older reading (Vouchers as the listing, Payments as
    # the payments after year end) when it is not loaded.
    # A new role serves when it has rows and the fields the contract asks of
    # it, the rule coverage and the executor apply (review 25 Nov 2026), so
    # the run reads the input set coverage reports.
    from procedures_cycles.contracts import CYCLE_CONTRACTS_BY_ID
    needed = CYCLE_CONTRACTS_BY_ID[pid].required_fields

    def serves(rows, role):
        return bool(rows) and set(needed[role]) <= set().union(*(r.keys() for r in rows))

    unpaid = records(tables, "Unpaid_bills")
    if not serves(unpaid, "Unpaid_bills"):
        unpaid = []
    listing_role = "Unpaid_bills" if unpaid else "Vouchers"
    listing = {key_text(v.get("voucher_number")): v
               for v in (unpaid or records(tables, "Vouchers"))}
    subsequent = records(tables, "Subsequent_payments")
    if not serves(subsequent, "Subsequent_payments"):
        subsequent = []
    payments_role = "Subsequent_payments" if subsequent else "Payments"
    findings = []
    if subsequent:
        # A register of payments after year end that holds one dated by year
        # end, or undated, is mixed: that row is named and left out, never
        # selected as if it were subsequent.
        payments = []
        for p in subsequent:
            paid_on = day(p.get("payment_date"))
            if paid_on is not None and paid_on > period_end:
                payments.append(p)
                continue
            pnum = key_text(p.get("payment_number"))
            findings.append(receipt(
                pid, (pnum, "not_after_period_end"), "AMBIGUOUS",
                f"payment {pnum} in the payments after year end is "
                f"{f'dated {paid_on}, on or before period end {period_end}' if paid_on else 'undated'}"
                "; left out of the search",
                {"finding_class": "REFUSAL", "cycle": "payables", "payment_date": paid_on,
                 "source_rows": [source_ref("Subsequent_payments", p, "payment_number")]}))
    else:
        payments = records(tables, "Payments")
    # The auditor's inspection log is evidence too: two results for one line
    # contradict each other, and a result for a line that does not exist
    # usually hides a keying error. Neither is resolved by row order.
    inspections: dict[str, dict] = {}
    conflicting: set[str] = set()
    for row in records(tables, "Disbursement_inspection"):
        key = key_text(row.get("payment_number"))
        if key in inspections:
            conflicting.add(key)
        inspections[key] = row
    # A register row refused above is named there; an inspection of it is not
    # also an "inspection without payment" (review 25 Nov 2026).
    payment_keys = {key_text(p.get("payment_number")) for p in (subsequent or payments)}
    for key in sorted(conflicting):
        findings.append(receipt(
            pid, (key, "conflicting_inspections"), "AMBIGUOUS",
            f"payment line {key} has more than one inspection result; record one",
            {"finding_class": "REFUSAL", "cycle": "payables"}))
    for key in sorted(set(inspections) - payment_keys):
        findings.append(receipt(
            pid, (key, "inspection_without_payment"), "ORPHAN",
            f"an inspection result names payment line {key}, which is not in the "
            "payments supplied — a keying error can hide an uninspected line",
            {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "payables"}))
    for key in conflicting:
        inspections.pop(key)
    ledger = _ledger_accounts(records(tables, "Trial_balance"))
    credit_used: dict[str, Decimal] = {}   # liabilities already placed in each account
    selection = select_disbursements(payments, threshold,
                                     int(interval) if interval else None,
                                     int(start) if start else None,
                                     int(limit) if limit else None)
    selected = set(selection["above_threshold"]) | set(selection["systematic"])
    outcomes = {"properly_included": 0, "properly_excluded": 0, "unrecorded": 0,
                "improperly_included": 0, "amount_difference": 0,
                "concluded_by_reference": 0, "recorded_outside_payables": 0}
    payment_numbers_by_check: dict[str, set[str]] = {}
    for payment in payments:
        payment_numbers_by_check.setdefault(_check_of(payment), set()).add(
            key_text(payment.get("payment_number")))
    inspected_payment_numbers: set[str] = set()
    net = ZERO  # overstatement positive
    for p in payments:
        pnum = key_text(p.get("payment_number"))
        vnum = key_text(p.get("voucher_number"))
        paid = money(p.get("payment_amount"))
        listed = listing.get(vnum)
        inspection = inspections.get(pnum)
        ref = [source_ref(payments_role, p, "payment_number")]
        if inspection is None:
            if _check_of(p) in selected:
                findings.append(receipt(
                    pid, (pnum, "selected_not_inspected"), "TENSION",
                    f"payment line {pnum} on selected disbursement {_check_of(p)} "
                    "has no inspection result",
                    {"finding_class": "CONJECTURE", "cycle": "payables",
                     "check_number": _check_of(p), "source_rows": ref,
                     "limits": "every payment line on a selected disbursement must "
                               "be inspected"}))
            if listed is not None and money(listed.get("voucher_amount")) != paid:
                diff = money(listed.get("voucher_amount")) - paid
                findings.append(receipt(
                    pid, (pnum, "paid_differs_from_listed"), "TENSION",
                    f"payment {pnum} pays voucher {vnum} {paid}; the year-end listing "
                    f"carries {money(listed.get('voucher_amount'))}",
                    {"finding_class": "CONJECTURE", "cycle": "payables",
                     "difference": diff, "source_rows": ref,
                     "limits": "a discount, partial payment or listing error; inspect"},
                    diff))
            continue
        inspected_payment_numbers.add(pnum)
        arose = day(inspection.get("liability_date"))
        owed = dec(inspection.get("liability_amount"))
        owed = paid if owed is None else owed
        if arose is None:
            conclusion = text(inspection.get("conclusion")).lower()
            if conclusion.replace("_", " ") in NO_MISSTATEMENT:
                # Inspected and concluded by a team member whose workpaper
                # records the result but not the date: relied on, not re-derived.
                outcomes["concluded_by_reference"] += 1
                continue
            findings.append(receipt(pid, (pnum, "no_liability_date"), "AMBIGUOUS",
                                    f"payment {pnum}: inspection records neither the date "
                                    "the liability arose nor a no-misstatement conclusion",
                                    {"finding_class": "REFUSAL", "cycle": "payables"}))
            continue
        evidence = {"cycle": "payables", "voucher_number": vnum, "paid": paid,
                    "liability_date": arose, "liability_amount": owed,
                    "document": text(inspection.get("document")),
                    "period_end": period_end, "source_rows": ref}
        recorded_in = text(inspection.get("recorded_account"))
        if recorded_in:
            evidence["recorded_account"] = recorded_in
        if arose <= period_end:
            if listed is None and recorded_in:
                # The auditor traced the liability to another account at period
                # end (taxes, accrued expenses): it was recorded, outside the
                # payables listing. With a trial balance loaded, that account
                # must be in it and hold at least this much credit (26 Nov
                # 2026); the entry itself is still the auditor's finding.
                found = _find_account(ledger, recorded_in) if ledger else None
                if ledger and found is None:
                    findings.append(receipt(
                        pid, (pnum, "recorded_account_not_in_trial_balance"), "AMBIGUOUS",
                        f"payment {pnum}: the inspection says the {owed} liability was "
                        f"recorded in {recorded_in!r}, which is not an account in the "
                        "trial balance; correct the account or the inspection",
                        {**evidence, "finding_class": "REFUSAL"}))
                    continue
                outcomes["recorded_outside_payables"] += 1
                if found is not None:
                    account, balance = found
                    evidence["recorded_account_balance"] = balance
                    # Liabilities traced to one account share its credit: two
                    # 600 items do not both fit in a 1,000 credit (review 26 Nov).
                    before = credit_used.get(account, ZERO)
                    credit_used[account] = before + owed
                    room = -balance - before
                    if room < owed:
                        evidence["traced_to_account_before"] = before
                        findings.append(receipt(
                            pid, (pnum, "recorded_account_below_liability"), "TENSION",
                            f"payment {pnum}: account {account} is said to hold the {owed} "
                            f"liability, but its period-end balance is {balance}"
                            f"{f' and {before} of other liabilities is already traced to it' if before else ''}; "
                            "inspect the entry",
                            {**evidence, "finding_class": "CONJECTURE",
                             "limits": "the account may hold the liability net of other "
                                       "items, or the balance may be wrong"},
                            owed - max(room, ZERO)))
            elif listed is None:
                outcomes["unrecorded"] += 1
                net -= owed
                findings.append(receipt(
                    pid, (pnum, "unrecorded"), "CLASH",
                    f"payment {pnum}: liability of {owed} arose {arose}, on or before "
                    f"period end, but voucher {vnum or '—'} is not on the year-end listing "
                    "— accounts payable understated",
                    {**evidence, "finding_class": "PROVED_EXCEPTION",
                     "direction": "understatement"}, owed))
            else:
                listed_amount = money(listed.get("voucher_amount"))
                if listed_amount != owed:
                    outcomes["amount_difference"] += 1
                    diff = listed_amount - owed
                    net += diff
                    findings.append(receipt(
                        pid, (pnum, "listed_amount_differs"), "CLASH",
                        f"payment {pnum}: voucher {vnum} listed at {listed_amount}, amount "
                        f"owed at period end {owed}",
                        {**evidence, "finding_class": "PROVED_EXCEPTION",
                         "listed_amount": listed_amount, "difference": diff}, diff))
                else:
                    outcomes["properly_included"] += 1
        else:
            if listed is not None:
                outcomes["improperly_included"] += 1
                listed_amount = money(listed.get("voucher_amount"))
                net += listed_amount
                findings.append(receipt(
                    pid, (pnum, "improperly_included"), "CLASH",
                    f"payment {pnum}: the liability arose {arose}, after period end, yet "
                    f"voucher {vnum} is on the year-end listing — accounts payable "
                    "overstated",
                    {**evidence, "finding_class": "PROVED_EXCEPTION",
                     "direction": "overstatement"}, listed_amount))
            else:
                outcomes["properly_excluded"] += 1
    inspected_checks = {
        check for check, payment_numbers in payment_numbers_by_check.items()
        if payment_numbers and payment_numbers <= inspected_payment_numbers
    }
    stats = {"population": len(payments), "checks": len(selection["check_totals"]),
             "selected_above_threshold": selection["above_threshold"],
             "selected_systematic": selection["systematic"],
             "inspected_checks": sorted(inspected_checks),
             "outcomes": outcomes, "net_misstatement": net,
             "listed_vouchers": len(listing),
             "listing_from": listing_role, "payments_from": payments_role,
             "recorded_accounts_checked": bool(ledger),
             "exceptions": len(findings)}
    return findings, stats


def _ledger_accounts(rows: list[dict]) -> dict[str, tuple[str, str, Decimal]]:
    """Trial balance accounts by number: (account, description, debit-positive
    balance), repeated rows summed."""
    from procedures_cycles.statements import _signed
    out: dict[str, tuple[str, str, Decimal]] = {}
    for row in rows:
        account = key_text(row.get("account"))
        if not account:
            continue
        balance = _signed(row) or ZERO
        _, description, before = out.get(account, (account, text(row.get("description")), ZERO))
        out[account] = (account, description, before + balance)
    return out


def _words(value: str) -> list[str]:
    return _norm(value).split()


def _find_account(ledger: dict, named: str) -> tuple[str, Decimal] | None:
    """The trial balance account an inspection names: by number ("2200"), by
    number and name ("2200 Sales Tax Payable", in either the inspection or the
    trial balance), or by its name alone. Punctuation and spacing do not count
    ("2200 - Sales Tax Payable"). A number whose name disagrees with the
    account's, or a name or number shared by two accounts, names none
    (review 26 Nov 2026)."""
    said = _words(named)
    if not said:
        return None
    candidates = []
    for account, (_, description, balance) in ledger.items():
        words = _words(account)
        number = words[0] if words and any(c.isdigit() for c in words[0]) else ""
        name = words[1:] if number else words
        name = name or _words(description)
        if number and said[0] == number:
            rest = said[1:]
            # "2200" alone, or "2200" with this account's name (or the start of it).
            if not rest or rest == name[:len(rest)]:
                candidates.append((account, balance))
        elif name and said == name:
            candidates.append((account, balance))
    if len(candidates) == 1:
        return candidates[0]
    return None


# --------------------------------------------------------------------------- supplier statements (2026-11-24)
def _norm(value) -> str:
    return " ".join("".join(c if c.isalnum() else " " for c in text(value).lower()).split())


def _ref_keys(value) -> list[str]:
    """How a reference is matched: the whole reference, then its digits alone
    ("INV 1001" = "1001"; "Check #10" = check 10). Never one word of it."""
    whole = _norm(value).replace(" ", "")
    digits = "".join(c for c in text(value) if c.isdigit()).lstrip("0")
    return [k for k in dict.fromkeys([whole, digits]) if k]


_FORWARD = ("balance forward", "opening balance", "brought forward", "previous balance")


def vendor_statement_reconciliation(tables: dict, policies: dict):
    """Reconcile each supplier's statement of account with the books.

    The statement is the supplier's own record, so it can show what the books
    leave out: an invoice the client never recorded (a possible unrecorded
    liability when dated by period end), an amount that differs, a payment the
    supplier never received. Lines are matched to vouchers by the supplier's
    invoice number and to payments by check or payment number, on the whole
    reference or its digits. The vendor is identified by its number or by a name
    that belongs to one vendor only.

    The statement may open with a balance forward; the books are compared from
    the statement's first dated line, with everything earlier as the books'
    opening balance. A payment the supplier has not yet credited is "in transit"
    within ``statement_transit_days`` of the statement date (7 when left empty),
    and a lead after that. Whatever the listed items do not explain is reported.
    """
    pid = "ap.vendor_statement_reconciliation"
    period_end = policy_date(policies, "period_end")
    raw_days = policies.get("statement_transit_days")
    transit_days = int(dec(raw_days)) if raw_days not in (None, "") else 7
    names: dict[str, set[str]] = {}
    numbers: set[str] = set()
    for v in records(tables, "Vendors"):
        numbers.add(key_text(v.get("vendor_number")))
        if text(v.get("vendor_name")):
            names.setdefault(_norm(v.get("vendor_name")), set()).add(key_text(v.get("vendor_number")))
    vouchers, payments = records(tables, "Vouchers"), records(tables, "Payments")
    numbers |= {key_text(r.get("vendor_number")) for r in vouchers + payments}
    findings, per_vendor = [], {}
    statements: dict[str, list[dict]] = {}
    for row in records(tables, "Vendor_statements"):
        raw = row.get("vendor")
        src = [source_ref("Vendor_statements", row, "reference")]
        if key_text(raw) in numbers:
            statements.setdefault(key_text(raw), []).append(row)
            continue
        hits = names.get(_norm(raw), set())
        if len(hits) == 1:
            statements.setdefault(next(iter(hits)), []).append(row)
            continue
        why = (f"belongs to {len(hits)} vendors ({', '.join(sorted(hits))})" if hits
               else "matches no vendor number or name")
        findings.append(receipt(pid, (key_text(raw) or "blank", "vendor_not_identified"), "AMBIGUOUS",
                                f"statement line for {text(raw)!r}: the vendor {why}; map it to one vendor",
                                {"finding_class": "REFUSAL", "cycle": "payables", "source_rows": src}))
    for vnum, lines in sorted(statements.items()):
        as_of = max((d for d in (day(r.get("statement_date")) for r in lines) if d), default=period_end)
        kinds = {id(r): _norm(r.get("item_type")) for r in lines}
        forward = [r for r in lines if any(f in kinds[id(r)] for f in _FORWARD)]
        items = [r for r in lines if r not in forward]
        first = min((d for d in (day(r.get("item_date")) for r in items) if d), default=None)

        def lead(key, verdict, reason, evidence, amount=None, cls="CONJECTURE"):
            findings.append(receipt(pid, (vnum, *key), verdict, reason,
                                    {"finding_class": cls, "cycle": "payables", "vendor": vnum,
                                     "statement_date": as_of, **evidence}, amount))

        def in_scope(d):
            return d is None or d <= as_of

        def before_first(d):
            return first is not None and d is not None and d < first

        v_all = [v for v in vouchers if key_text(v.get("vendor_number")) == vnum and in_scope(day(v.get("voucher_date")))]
        p_all = [p for p in payments if key_text(p.get("vendor_number")) == vnum and in_scope(day(p.get("payment_date")))]
        v_open = [v for v in v_all if before_first(day(v.get("voucher_date")))]
        p_open = [p for p in p_all if before_first(day(p.get("payment_date")))]
        v_rows = [v for v in v_all if v not in v_open]
        p_rows = [p for p in p_all if p not in p_open]
        books_opening = (sum((money(v.get("voucher_amount")) for v in v_open), ZERO)
                         - sum((money(p.get("payment_amount")) for p in p_open), ZERO))
        stmt_opening = sum((money(r.get("amount")) for r in forward), ZERO)
        explained = ZERO
        if (forward or books_opening) and stmt_opening != books_opening:
            explained += stmt_opening - books_opening
            lead(("opening", "opening_balance_differs"), "CLASH",
                 f"vendor {vnum}: the statement opens at {stmt_opening} ("
                 + ("balance forward" if forward else "no balance forward line")
                 + f"); the books carry {books_opening} before {first}",
                 {"statement_opening": stmt_opening, "books_opening": books_opening},
                 stmt_opening - books_opening, cls="PROVED_EXCEPTION")

        def index(rows, fields):
            whole, digits = {}, {}
            for row in rows:
                for field in fields:
                    value = row.get(field)
                    full = _norm(value).replace(" ", "")
                    number = "".join(c for c in text(value) if c.isdigit()).lstrip("0")
                    for mapping, alias in ((whole, full), (digits, number)):
                        if alias:
                            mapping.setdefault(alias, {})[id(row)] = row
            return whole, digits

        def match(indexed, reference, table, src):
            whole, digits = indexed
            full = _norm(reference).replace(" ", "")
            number = "".join(c for c in text(reference) if c.isdigit()).lstrip("0")
            # An exact reference wins. Numeric aliases are a fallback only;
            # unused collisions between aliases are not duplicate records.
            hits = whole.get(full) or digits.get(number) or {}
            if len(hits) > 1:
                lead((full, f"duplicate_{table.lower()}_reference"), "AMBIGUOUS",
                     f"vendor {vnum}: more than one {table.lower()} record answers to reference {reference!r}; the match is refused",
                     {"source_rows": src + [source_ref(table, row, "voucher_number" if table == "Vouchers" else "payment_number") for row in hits.values()]}, cls="REFUSAL")
                return None, True
            return next(iter(hits.values()), None), False

        book_inv = index(v_rows, ("invoice_number", "voucher_number"))
        book_pay = index(p_rows, ("check_number", "payment_number"))
        seen_inv, seen_pay, stmt_refs = set(), set(), {}
        stmt_balance = stmt_opening
        for r in items:
            amount = money(r.get("amount"))
            stmt_balance += amount
            kind = kinds[id(r)]
            keys = _ref_keys(r.get("reference"))
            ref = text(r.get("reference"))
            src = [source_ref("Vendor_statements", r, "reference")]
            is_credit = "credit" in kind
            is_payment = not is_credit and ("pay" in kind or "receipt" in kind or "received" in kind
                                            or (not kind and amount < 0))
            if (is_payment or is_credit) and amount > 0 or not (is_payment or is_credit) and amount < 0:
                explained += amount
                lead((keys[0] if keys else "blank", "sign_does_not_fit_type"), "AMBIGUOUS",
                     f"vendor {vnum}: line {ref!r} ({text(r.get('item_type')) or 'no type'}) carries {amount}, "
                     "the wrong sign for its type; not matched", {"source_rows": src}, cls="REFUSAL")
                continue
            if is_payment:
                hit, ambiguous = match(book_pay, ref, "Payments", src)
                if ambiguous:
                    continue
                if hit is None:
                    explained += amount
                    lead((keys[0] if keys else "blank", "payment_not_in_books"), "ORPHAN",
                         f"vendor {vnum}: the statement credits a payment {ref!r} of {-amount} that the books "
                         "do not show", {"source_rows": src}, -amount, cls="EXPECTED_BUT_MISSING")
                    continue
                seen_pay.add(id(hit))
                paid = money(hit.get("payment_amount"))
                if paid != -amount:
                    explained += amount + paid
                    lead((keys[0], "payment_amount_differs"), "CLASH",
                         f"vendor {vnum}: payment {ref!r} is {paid} in the books; the supplier credited {-amount}",
                         {"source_rows": src}, amount + paid, cls="PROVED_EXCEPTION")
                continue
            k0 = keys[0] if keys else "blank"
            if k0 in stmt_refs:
                explained += amount
                lead((k0, "billed_twice_on_statement"), "CLASH",
                     f"vendor {vnum}: the statement bills {ref!r} twice", {"source_rows": src}, amount,
                     cls="PROVED_EXCEPTION")
                continue
            stmt_refs[k0] = r
            hit, ambiguous = match(book_inv, ref, "Vouchers", src)
            if ambiguous:
                continue
            if hit is None:
                explained += amount
                if is_credit:
                    lead((k0, "credit_not_in_books"), "TENSION",
                         f"vendor {vnum}: the statement gives a credit {ref!r} of {-amount}; no matching credit is recorded in the books: a credit memo the client has not booked?",
                         {"source_rows": src}, -amount)
                    continue
                item_day = day(r.get("item_date"))
                by_pe = item_day is not None and item_day <= period_end
                lead((k0, "invoice_not_in_books"), "TENSION",
                     f"vendor {vnum}: the statement bills {ref!r} for {amount} ({item_day}); the books show no "
                     "such bill"
                     + (": a possible unrecorded liability at period end (or a bill under another vendor or "
                        "number)" if by_pe else ", dated after period end"),
                     {"source_rows": src, "item_date": item_day, "by_period_end": by_pe}, amount)
                continue
            seen_inv.add(id(hit))
            if money(hit.get("voucher_amount")) != amount:
                diff = amount - money(hit.get("voucher_amount"))
                explained += diff
                lead((k0, "amount_differs"), "CLASH",
                     f"vendor {vnum}: {ref!r} is {amount} on the statement and {money(hit.get('voucher_amount'))} "
                     "in the books", {"source_rows": src}, diff, cls="PROVED_EXCEPTION")
        for v in v_rows:
            if id(v) in seen_inv:
                continue
            explained -= money(v.get("voucher_amount"))
            name = text(v.get("invoice_number") or v.get("voucher_number"))
            lead((_ref_keys(name)[0] if _ref_keys(name) else "blank", "bill_not_on_statement"), "TENSION",
                 f"vendor {vnum}: bill {name} ({money(v.get('voucher_amount'))}) is in the books but not on the "
                 "supplier's statement", {"source_rows": [source_ref("Vouchers", v, "voucher_number")]},
                 money(v.get("voucher_amount")))
        in_transit, stale = [], []
        for p in p_rows:
            if id(p) in seen_pay:
                continue
            paid_on = day(p.get("payment_date"))
            amount = money(p.get("payment_amount"))
            explained += amount                     # paid in the books, not yet credited: statement higher
            ref = text(p.get("check_number")) or text(p.get("payment_number"))
            if paid_on and (as_of - paid_on).days <= transit_days:
                in_transit.append(ref)
            else:
                stale.append(ref)
                lead((_ref_keys(ref)[0] if _ref_keys(ref) else "blank", "payment_not_credited"), "TENSION",
                     f"vendor {vnum}: payment {ref} of {amount} ({paid_on}) is not credited on the statement "
                     f"of {as_of}, more than {transit_days} days later: did the supplier receive it?",
                     {"source_rows": [source_ref("Payments", p, "payment_number")]}, amount)
        books_balance = books_opening + (sum((money(v.get("voucher_amount")) for v in v_rows), ZERO)
                                         - sum((money(p.get("payment_amount")) for p in p_rows), ZERO))
        unexplained = stmt_balance - books_balance - explained
        per_vendor[vnum] = {"statement_date": as_of, "statement_balance": stmt_balance,
                            "books_balance": books_balance, "statement_opening": stmt_opening,
                            "books_opening": books_opening, "payments_in_transit": in_transit,
                            "payments_not_credited": stale, "unexplained": unexplained}
        if unexplained != ZERO:
            lead(("balance", "unexplained_difference"), "CLASH",
                 f"vendor {vnum}: statement {stmt_balance} against books {books_balance}; {unexplained} is not "
                 "explained by the items listed", {}, unexplained, cls="PROVED_EXCEPTION")
    stats = {"population": sum(len(v) for v in statements.values()), "vendors": len(statements),
             "period_end": period_end, "transit_days": transit_days,
             "transit_days_source": "default" if raw_days in (None, "") else "policy",
             "per_vendor": per_vendor, "exceptions": len(findings)}
    return findings, stats
