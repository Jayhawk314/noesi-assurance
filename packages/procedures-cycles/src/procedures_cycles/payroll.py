# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Payroll: register re-performance, ghost and terminated-employee leads,
and the register's gross pay against the ledger.

The employee master (status, termination date, bank account, address) is
the client's HR record. The engine compares it with who was paid; whether a
payment after termination was a legitimate final check is the auditor's
inquiry, which is why the grace period is a policy.
"""

from __future__ import annotations

from datetime import date, timedelta

from procedures_cycles.common import (
    ZERO, PolicyError, dec, day, key_text, money, period_start, policy_date, receipt,
    records, source_ref, text,
)
from procedures_cycles.statements import _signed

REGISTER, MASTER = "Payroll_register", "Payroll_master"


def register_tests(tables: dict, policies: dict):
    pid = "payroll.register_tests"
    grace = dec(policies.get("payroll_final_pay_days"))
    master = {key_text(e.get("employee_id")): e for e in records(tables, MASTER)}
    findings = []
    counts: dict[str, int] = {}

    def lead(key, verdict, reason, evidence, amount=None, cls="CONJECTURE"):
        counts[key[-1]] = counts.get(key[-1], 0) + 1
        findings.append(receipt(pid, key, verdict, reason,
                                {"finding_class": cls, "cycle": "payroll", **evidence},
                                amount))

    paid_on: dict[tuple[str, date | None], list[dict]] = {}
    rows = records(tables, REGISTER)
    for row in rows:
        emp = key_text(row.get("employee_id"))
        paid = day(row.get("pay_date"))
        gross, net = money(row.get("gross")), money(row.get("net"))
        ref = text(row.get("check_number")) or f"row-{row.get('source_row')}"
        base = {"employee": emp, "pay_date": paid, "gross": gross, "net": net,
                "source_rows": [source_ref(REGISTER, row, "employee_id")]}
        paid_on.setdefault((emp, paid), []).append(row)
        withheld = [dec(row.get(f)) for f in ("tax_withheld", "deductions")]
        if any(w is not None for w in withheld):
            expected = gross - sum((w or ZERO for w in withheld), ZERO)
            if money(expected) != net:
                lead((emp, ref, "net_pay_differs"), "CLASH",
                     f"employee {emp} paid {paid}: gross {gross} less deductions gives "
                     f"{money(expected)}, but net pay is {net}", base,
                     money(expected) - net, cls="PROVED_EXCEPTION")
        hours, rate = dec(row.get("hours")), dec(row.get("pay_rate"))
        if hours is not None and rate is not None and money(hours * rate) != gross:
            lead((emp, ref, "gross_pay_differs"), "CLASH",
                 f"employee {emp} paid {paid}: {hours} hours at {rate} is "
                 f"{money(hours * rate)}, but gross pay is {gross}", base,
                 money(hours * rate) - gross, cls="PROVED_EXCEPTION")
        person = master.get(emp)
        if person is None:
            lead((emp, ref, "not_on_employee_master"), "ORPHAN",
                 f"employee {emp} was paid {net} on {paid} but is not on the employee "
                 "master — a fictitious employee? Trace to HR records", base, net,
                 cls="EXPECTED_BUT_MISSING")
            continue
        ended = day(person.get("termination_date"))
        if ended is not None and paid is not None and paid > ended + timedelta(
                days=int(grace or 0)):
            lead((emp, ref, "paid_after_termination"), "TENSION",
                 f"employee {emp} terminated {ended} but was paid {net} on {paid}"
                 + (f", more than {int(grace)} days later" if grace else "")
                 + " — a final check, or a payment that should have stopped?",
                 {**base, "termination_date": ended}, net)
    for (emp, paid), same in paid_on.items():
        if len(same) > 1:
            lead((emp, str(paid), "paid_twice_same_date"), "TENSION",
                 f"employee {emp} has {len(same)} payments dated {paid}",
                 {"employee": emp, "pay_date": paid, "payments": len(same),
                  "source_rows": [source_ref(REGISTER, r, "employee_id") for r in same]},
                 sum((money(r.get("net")) for r in same), ZERO))
    for field, label in (("bank_account", "bank account"), ("address", "address")):
        sharing: dict[str, list[str]] = {}
        for emp, person in master.items():
            value = " ".join(text(person.get(field)).lower().split())
            if value:
                sharing.setdefault(value, []).append(emp)
        for value, emps in sorted(sharing.items()):
            if len(emps) > 1:
                lead((",".join(sorted(emps)), f"shared_{field}"), "TENSION",
                     f"employees {', '.join(sorted(emps))} share one {label}",
                     {"employees": sorted(emps), field: value})
    stats = {"population": len(rows), "employees_on_master": len(master),
             "final_pay_grace_days": int(grace) if grace is not None else 0,
             "leads_by_test": counts, "exceptions": len(findings)}
    return findings, stats


def register_to_ledger(tables: dict, policies: dict):
    pid = "payroll.register_to_ledger"
    pe = policy_date(policies, "period_end")
    accounts = [key_text(a) for a in text(policies.get("payroll_expense_accounts"))
                .replace(";", ",").split(",") if a.strip()]
    if not accounts:
        raise PolicyError("policy 'payroll_expense_accounts' is not set; name the trial "
                          "balance accounts that carry gross wages")
    start = period_start(pe)
    register = ZERO
    outside = 0
    for row in records(tables, REGISTER):
        paid = day(row.get("pay_date"))
        if paid is None or not start <= paid <= pe:
            outside += 1
            continue
        register += money(row.get("gross"))
    tb = {key_text(r.get("account")): _signed(r) or ZERO
          for r in records(tables, "Trial_balance")}
    missing = [a for a in accounts if a not in tb]
    ledger = money(sum((tb.get(a, ZERO) for a in accounts), ZERO))
    difference = money(register - ledger)
    findings = []
    if missing:
        findings.append(receipt(
            pid, ("accounts_not_on_trial_balance",), "AMBIGUOUS",
            f"payroll expense account(s) {', '.join(missing)} are not on the trial "
            "balance", {"finding_class": "REFUSAL", "cycle": "payroll",
                        "accounts": missing}))
    if difference != 0:
        findings.append(receipt(
            pid, ("register_to_ledger",), "TENSION",
            f"gross pay in the register for {start} to {pe} is {money(register)}; the "
            f"ledger's wage accounts carry {ledger} (difference {difference}). "
            "Accrued wages at either end explain some of this; the rest is unexplained",
            {"finding_class": "CONJECTURE", "cycle": "payroll", "register": register,
             "ledger": ledger, "difference": difference, "accounts": accounts},
            difference))
    stats = {"population": len(records(tables, REGISTER)), "period_start": start,
             "period_end": pe, "register_gross": money(register), "ledger_wages": ledger,
             "difference": difference, "payments_outside_period": outside,
             "exceptions": len(findings)}
    return findings, stats
