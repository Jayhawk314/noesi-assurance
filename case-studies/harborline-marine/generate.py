# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Generate the Harborline Marine Group integrated audit practice case.

An original teaching case in the tradition of published integrated audit
practice sets. Every figure here is fabricated. Deterministic: a fixed seed
means regenerating produces byte-identical files, so the instructor answer
key stays true.

    python case-studies/harborline-marine/generate.py

Design rule: the *clean* population is generated first and is internally
coherent end to end (PO -> goods receipt -> voucher -> payment -> bank + GL).
Exceptions are then injected deliberately, one block per audit procedure, so
the answer key is a consequence of the code rather than a claim about it.
"""

from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

SEED = 20261231
FY_START = date(2026, 1, 1)
FY_END = date(2026, 12, 31)

DATA = Path(__file__).resolve().parent / "data"

# Injected exceptions accumulate here so the answer key can be generated from
# the same run that produces the data.
FINDINGS: list[dict] = []


def note(procedure: str, ref: str, detail: str, amount: Decimal | None = None):
    FINDINGS.append({
        "procedure": procedure, "reference": ref,
        "detail": detail, "amount": amount,
    })


def money(low: float, high: float) -> Decimal:
    """A plausible invoice amount, to the cent."""
    return Decimal(str(round(random.uniform(low, high), 2)))


def day(start: date = FY_START, end: date = FY_END) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


# --------------------------------------------------------------- people

CLERKS = [
    ("E204", "Dana Whitfield"), ("E211", "Marcus Ojo"),
    ("E218", "Priya Raman"), ("E223", "Tomas Lindqvist"),
    ("E227", "Alice Bergeron"), ("E231", "Ken Nakashima"),
]
APPROVERS = [
    ("E102", "Rosalind Achebe"), ("E108", "Gerald Sun"),
    ("E115", "Nadia Petrov"), ("E119", "Owen Castellanos"),
]
BUYERS = [
    ("E305", "Hector Villalobos"), ("E312", "June Park"),
    ("E318", "Samir Haddad"),
]

# --------------------------------------------------------------- vendors

VENDOR_NAMES = [
    "Atlantic Diesel Works", "Blue Ridge Marine Electronics",
    "Cormorant Rigging Co", "Deepwater Hull Coatings",
    "Eastport Fastener Supply", "Fathom Navigation Systems",
    "Gulfstream Propulsion", "Halyard Canvas & Upholstery",
    "Inlet Hydraulics", "Jetty Point Fuel Depot",
    "Keelson Composite Materials", "Lantern Bay Paint Supply",
    "Mainsail Textile Group", "Northpoint Trailer Manufacturing",
    "Offshore Safety Equipment", "Pelican Bay Woodworks",
    "Quarterdeck Instruments", "Riptide Engine Components",
    "Seaward Metal Fabrication", "Transom Machine Shop",
    "Undertow Dive Supply", "Vessel Glass & Acrylic",
    "Windward Chandlery", "Yardarm Industrial Coatings",
    "Zephyr Sailmakers", "Anchorline Freight Services",
    "Beacon Hill Insurance Brokers", "Channel Marker Printing",
    "Dockside Waste Management", "Estuary Environmental Testing",
    "Ferryman Logistics", "Groundswell Marketing",
    "Harbormaster Software Licensing", "Ironwood Pallet Company",
    "Jubilee Uniform & Workwear", "Kingfisher Security Services",
    "Longshore Staffing Partners", "Marlinspike Tool Rental",
]

TWIN_PAIRS = [
    ("Harbor Marine Supply LLC", "Harbour Marine Supply, L.L.C."),
    ("Nautical Parts Inc", "Nautical Parts, Inc."),
    ("Coastal Fuel & Marine Services", "Coastal Fuel and Marine Svcs"),
]


def build_vendors() -> list[dict]:
    vendors = []
    number = 1000
    for name in VENDOR_NAMES:
        vendors.append({
            "Vendor Number": f"V{number}", "Vendor Name": name,
            "Remit City": random.choice(
                ["Norfolk", "Annapolis", "Charleston", "Savannah",
                 "New Bedford", "Portland", "Mobile"]),
            "Tax ID": f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}",
            "Status": "Active",
        })
        number += 1

    # Relational twins: near-identical identities sharing a remit address.
    for original, twin in TWIN_PAIRS:
        city = random.choice(["Norfolk", "Annapolis", "Charleston"])
        tax = f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
        first = f"V{number}"
        vendors.append({
            "Vendor Number": first, "Vendor Name": original,
            "Remit City": city, "Tax ID": tax, "Status": "Active",
        })
        number += 1
        second = f"V{number}"
        vendors.append({
            "Vendor Number": second, "Vendor Name": twin,
            "Remit City": city, "Tax ID": tax, "Status": "Active",
        })
        note("ap.vendor_relational_twins", f"{first} / {second}",
             f"Near-duplicate vendor identities '{original}' and '{twin}' "
             f"share remit city {city} and tax ID {tax}.")
        number += 1
    return vendors


# --------------------------------------------------- the coherent backbone

def build_chains(vendors: list[dict], count: int) -> list[dict]:
    """PO -> goods receipt -> voucher -> payment, internally consistent."""
    chains = []
    for index in range(1, count + 1):
        vendor = random.choice(vendors)
        amount = money(240, 46000)
        po_date = day(FY_START, FY_END - timedelta(days=45))
        receipt_date = po_date + timedelta(days=random.randint(3, 21))
        voucher_date = receipt_date + timedelta(days=random.randint(0, 10))
        payment_date = voucher_date + timedelta(days=random.randint(5, 40))
        buyer = random.choice(BUYERS)[0]
        clerk = random.choice(CLERKS)[0]
        approver = random.choice(APPROVERS)[0]
        chains.append({
            "po_number": f"PO-2026-{index:04d}",
            "receipt_number": f"GRN-2026-{index:04d}",
            "voucher_number": f"VCH-2026-{index:04d}",
            "payment_number": f"PAY-2026-{index:04d}",
            "check_number": f"CHK-{20000 + index}",
            "vendor_number": vendor["Vendor Number"],
            "po_amount": amount,
            "received_amount": amount,
            "voucher_amount": amount,
            "payment_amount": amount,
            "po_date": po_date,
            "receipt_date": receipt_date,
            "voucher_date": voucher_date,
            "payment_date": payment_date,
            "buyer": buyer,
            "clerk": clerk,
            "approver": approver,
            # Flags consumed when the tables are written out.
            "skip_receipt": False,
            "skip_voucher": False,
            "skip_bank": False,
            "skip_gl": False,
            "orphan_voucher_ref": False,
            "orphan_po_ref": False,
            "bank_amount": None,
            "gl_amount": None,
        })
    return chains


# ------------------------------------------------------ exception injection

def inject(chains: list[dict], vendors: list[dict]) -> None:
    """One block per procedure. Each block records its own answer-key note."""

    # -- ap.payment_voucher_reference: payment cites a voucher that does not exist
    for chain in random.sample(chains, 3):
        chain["orphan_voucher_ref"] = True
        ghost = f"VCH-2026-9{random.randint(100, 999)}"
        chain["cited_voucher"] = ghost
        note("ap.payment_voucher_reference", chain["payment_number"],
             f"Payment cites voucher {ghost}, which is absent from the "
             f"voucher population.", chain["payment_amount"])

    # -- ap.voucher_po_reference: voucher cites a PO that does not exist
    for chain in random.sample([c for c in chains if not c["orphan_voucher_ref"]], 3):
        chain["orphan_po_ref"] = True
        ghost = f"PO-2026-8{random.randint(100, 999)}"
        chain["cited_po"] = ghost
        note("ap.voucher_po_reference", chain["voucher_number"],
             f"Voucher cites purchase order {ghost}, which is absent from the "
             f"purchase-order population.", chain["voucher_amount"])

    # -- ap.document_chain: amount escalation and a date that runs backwards
    clean = [c for c in chains
             if not (c["orphan_voucher_ref"] or c["orphan_po_ref"])]
    for chain in random.sample(clean, 3):
        overpay = (chain["voucher_amount"] * Decimal("0.18")).quantize(
            Decimal("0.01"))
        chain["payment_amount"] = chain["voucher_amount"] + overpay
        note("ap.document_chain", chain["payment_number"],
             f"Payment of {chain['payment_amount']} exceeds voucher "
             f"{chain['voucher_number']} of {chain['voucher_amount']} by "
             f"{overpay}.", overpay)

    for chain in random.sample(
            [c for c in clean if c["payment_amount"] == c["voucher_amount"]], 2):
        chain["payment_date"] = chain["voucher_date"] - timedelta(
            days=random.randint(4, 15))
        note("ap.document_chain", chain["payment_number"],
             f"Payment dated {chain['payment_date']} precedes its voucher "
             f"date of {chain['voucher_date']}.")

    # -- ap.segregation_of_duties: one person both raises and approves
    for chain in random.sample(chains, 5):
        chain["approver"] = chain["clerk"]
        who = dict(CLERKS).get(chain["clerk"], chain["clerk"])
        note("ap.segregation_of_duties", chain["payment_number"],
             f"{who} ({chain['clerk']}) both entered and approved this "
             f"payment.", chain["payment_amount"])

    # -- cash.bank_clearing: never cleared, and cleared for the wrong amount
    for chain in random.sample(chains, 4):
        chain["skip_bank"] = True
        note("cash.bank_clearing", chain["payment_number"],
             "Recorded payment has no corresponding bank clearing.",
             chain["payment_amount"])
    # Two clearing differences straddling the engine's 2% tolerance band: one
    # comfortably outside it, one deliberately inside. The second is *not*
    # expected to raise a finding — it teaches that a silent procedure means
    # "within tolerance", not "nothing there".
    inside, outside = random.sample(
        [c for c in chains if not c["skip_bank"]], 2)

    drift = (outside["payment_amount"] * Decimal("0.035")).quantize(
        Decimal("0.01"))
    outside["bank_amount"] = outside["payment_amount"] + drift
    note("cash.bank_clearing", outside["payment_number"],
         f"Bank cleared {outside['bank_amount']} against a recorded payment "
         f"of {outside['payment_amount']} — 3.5%, outside tolerance, so the "
         f"engine reports it.", drift)

    drift = (inside["payment_amount"] * Decimal("0.009")).quantize(
        Decimal("0.01"))
    inside["bank_amount"] = inside["payment_amount"] + drift
    note("cash.bank_clearing", inside["payment_number"],
         f"Bank cleared {inside['bank_amount']} against a recorded payment of "
         f"{inside['payment_amount']} — 0.9%, INSIDE the engine's 2% "
         f"tolerance, so no finding is raised. Expected silence.", drift)

    # -- gl.payment_posting: unposted, and posted at the wrong amount
    for chain in random.sample([c for c in chains if not c["skip_bank"]], 3):
        chain["skip_gl"] = True
        note("gl.payment_posting", chain["payment_number"],
             "Payment never posted to the general ledger.",
             chain["payment_amount"])
    # Both well outside the 2% tolerance, so both are expected to be reported.
    for chain, pct in zip(
            random.sample(
                [c for c in chains
                 if not c["skip_gl"] and not c["skip_bank"]
                 and c["bank_amount"] is None], 2),
            (Decimal("0.045"), Decimal("0.062"))):
        drift = (chain["payment_amount"] * pct).quantize(Decimal("0.01"))
        chain["gl_amount"] = chain["payment_amount"] - drift
        note("gl.payment_posting", chain["payment_number"],
             f"General ledger posts {chain['gl_amount']} for a payment of "
             f"{chain['payment_amount']} — {pct:.1%}, outside tolerance.",
             drift)

    # -- ap.three_way_receipt_match: no receipt, and a short receipt
    for chain in random.sample(clean, 4):
        chain["skip_receipt"] = True
        note("ap.three_way_receipt_match", chain["voucher_number"],
             "Voucher paid with no evidence of goods received.",
             chain["voucher_amount"])
    for chain in random.sample(
            [c for c in clean if not c["skip_receipt"]], 3):
        short = (chain["voucher_amount"] * Decimal("0.25")).quantize(
            Decimal("0.01"))
        chain["received_amount"] = chain["voucher_amount"] - short
        note("ap.three_way_receipt_match", chain["voucher_number"],
             f"Goods received value {chain['received_amount']} is short of "
             f"the invoiced {chain['voucher_amount']} by {short}.", short)


def build_split_payments(chains: list[dict], vendor_number: str) -> list[dict]:
    """A cluster of payments sitting just under a $10,000 approval limit."""
    base = date(2026, 9, 14)
    extra = []
    start = len(chains) + 1
    for offset, amount in enumerate(
            ["9850.00", "9720.00", "9905.00", "9640.00", "9880.00"]):
        index = start + offset
        pay_date = base + timedelta(days=offset * 2)
        value = Decimal(amount)
        extra.append({
            "po_number": f"PO-2026-{index:04d}",
            "receipt_number": f"GRN-2026-{index:04d}",
            "voucher_number": f"VCH-2026-{index:04d}",
            "payment_number": f"PAY-2026-{index:04d}",
            "check_number": f"CHK-{20000 + index}",
            "vendor_number": vendor_number,
            "po_amount": value, "received_amount": value,
            "voucher_amount": value, "payment_amount": value,
            "po_date": pay_date - timedelta(days=20),
            "receipt_date": pay_date - timedelta(days=12),
            "voucher_date": pay_date - timedelta(days=8),
            "payment_date": pay_date,
            "buyer": "E312", "clerk": "E211", "approver": "E108",
            "skip_receipt": False, "skip_voucher": False, "skip_bank": False,
            "skip_gl": False, "orphan_voucher_ref": False,
            "orphan_po_ref": False, "bank_amount": None, "gl_amount": None,
        })
    total = sum(Decimal(a) for a in
                ["9850.00", "9720.00", "9905.00", "9640.00", "9880.00"])
    note("ap.split_payment_review", vendor_number,
         f"Five payments totalling {total} to one vendor within nine days, "
         f"each just below the $10,000 approval threshold.", total)
    return extra


# ------------------------------------------------------------- value flows

def build_value_flows(vendors: list[dict]) -> list[dict]:
    flows = []
    index = 1
    for _ in range(48):
        vendor = random.choice(vendors)
        flows.append({
            "Flow ID": f"VF-{index:04d}",
            "Source Entity": "Harborline Marine Group",
            "Target Entity": vendor["Vendor Name"],
            "Amount": str(money(500, 38000)),
            "Flow Date": day().isoformat(),
            "Relation": "disbursement",
        })
        index += 1

    # A closed round trip: money leaves and comes back through two hops.
    ring = ["Harborline Marine Group", "Bayview Advisory Partners",
            "Meridian Holdings LC", "Harborline Marine Group"]
    ring_date = date(2026, 11, 3)
    for step in range(3):
        flows.append({
            "Flow ID": f"VF-{index:04d}",
            "Source Entity": ring[step],
            "Target Entity": ring[step + 1],
            "Amount": "48500.00",
            "Flow Date": (ring_date + timedelta(days=step * 2)).isoformat(),
            "Relation": "consulting" if step == 0 else "transfer",
        })
        index += 1
    note("forensic.closed_value_flow", "VF ring via Bayview / Meridian",
         "48,500.00 leaves Harborline as a consulting payment and returns "
         "through Meridian Holdings LC within four days.", Decimal("48500.00"))
    return flows


# ------------------------------------------------------------------ writing

def write_csv(name: str, rows: list[dict], columns: list[str]) -> None:
    path = DATA / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})
    print(f"  {name:28} {len(rows):>4} rows")


def main() -> None:
    random.seed(SEED)
    DATA.mkdir(parents=True, exist_ok=True)

    vendors = build_vendors()
    chains = build_chains(vendors, 118)
    inject(chains, vendors)

    # The split-payment vendor is one of the twin identities, so the two
    # procedures interact the way they would in a real file.
    split_vendor = next(v["Vendor Number"] for v in vendors
                        if v["Vendor Name"] == "Coastal Fuel & Marine Services")
    chains += build_split_payments(chains, split_vendor)

    # ---- purchase orders
    write_csv("purchase_orders.csv", [
        {
            "PO Number": c["po_number"], "Vendor Number": c["vendor_number"],
            "PO Amount": str(c["po_amount"]), "PO Date": c["po_date"].isoformat(),
            "Created By": c["buyer"], "Approved By": c["approver"],
        } for c in chains
    ], ["PO Number", "Vendor Number", "PO Amount", "PO Date",
        "Created By", "Approved By"])

    # ---- goods receipts
    write_csv("goods_receipts.csv", [
        {
            "Receipt Number": c["receipt_number"], "PO Number": c["po_number"],
            "Received Amount": str(c["received_amount"]),
            "Receipt Date": c["receipt_date"].isoformat(),
        } for c in chains if not c["skip_receipt"]
    ], ["Receipt Number", "PO Number", "Received Amount", "Receipt Date"])

    # ---- vouchers
    write_csv("vouchers.csv", [
        {
            "Voucher Number": c["voucher_number"],
            "PO Number": c.get("cited_po") if c["orphan_po_ref"] else c["po_number"],
            "Vendor Number": c["vendor_number"],
            "Voucher Amount": str(c["voucher_amount"]),
            "Voucher Date": c["voucher_date"].isoformat(),
            "Created By": c["clerk"], "Approved By": c["approver"],
        } for c in chains if not c["skip_voucher"]
    ], ["Voucher Number", "PO Number", "Vendor Number", "Voucher Amount",
        "Voucher Date", "Created By", "Approved By"])

    # ---- payments
    write_csv("payments.csv", [
        {
            "Payment Number": c["payment_number"],
            "Voucher Number": (c.get("cited_voucher")
                               if c["orphan_voucher_ref"] else c["voucher_number"]),
            "Vendor Number": c["vendor_number"],
            "Payment Amount": str(c["payment_amount"]),
            "Payment Date": c["payment_date"].isoformat(),
            "Created By": c["clerk"], "Approved By": c["approver"],
            "Check Number": c["check_number"],
        } for c in chains
    ], ["Payment Number", "Voucher Number", "Vendor Number", "Payment Amount",
        "Payment Date", "Created By", "Approved By", "Check Number"])

    # ---- bank
    bank = []
    for index, c in enumerate(
            [c for c in chains if not c["skip_bank"]], start=1):
        amount = c["bank_amount"] if c["bank_amount"] is not None \
            else c["payment_amount"]
        bank.append({
            "Bank Txn ID": f"BNK-{index:05d}",
            "Payment Number": c["payment_number"],
            "Amount": str(amount),
            "Bank Date": (c["payment_date"]
                          + timedelta(days=random.randint(1, 6))).isoformat(),
        })
    write_csv("bank.csv", bank,
              ["Bank Txn ID", "Payment Number", "Amount", "Bank Date"])

    # ---- general ledger
    gl = []
    for index, c in enumerate(
            [c for c in chains if not c["skip_gl"]], start=1):
        amount = c["gl_amount"] if c["gl_amount"] is not None \
            else c["payment_amount"]
        gl.append({
            "GL Entry ID": f"GL-{index:05d}", "Account": "2000",
            "Reference": c["payment_number"], "Amount": str(amount),
            "GL Date": c["payment_date"].isoformat(),
        })
    write_csv("gl.csv", gl,
              ["GL Entry ID", "Account", "Reference", "Amount", "GL Date"])

    # ---- AP control balance: subledger deliberately off the control account
    subledger = sum(
        c["voucher_amount"] for c in chains if not c["skip_voucher"])
    variance = Decimal("18450.00")
    write_csv("ap_control_balance.csv", [{
        "Period End": FY_END.isoformat(),
        "Subledger Balance": str(subledger.quantize(Decimal("0.01"))),
        "GL Balance": str((subledger + variance).quantize(Decimal("0.01"))),
    }], ["Period End", "Subledger Balance", "GL Balance"])
    note("ap.subledger_gl_balance_tie", "2026-12-31",
         f"AP subledger of {subledger.quantize(Decimal('0.01'))} does not tie "
         f"to the general ledger control account; variance {variance}.",
         variance)

    # ---- vendors, employees, value flows
    write_csv("vendors.csv", vendors,
              ["Vendor Number", "Vendor Name", "Remit City", "Tax ID", "Status"])
    write_csv("employees.csv", [
        {"Employee Number": num, "Employee Name": name, "Function": role}
        for num, name, role in
        [(n, m, "AP clerk") for n, m in CLERKS]
        + [(n, m, "Approver") for n, m in APPROVERS]
        + [(n, m, "Buyer") for n, m in BUYERS]
    ], ["Employee Number", "Employee Name", "Function"])
    write_csv("value_flows.csv", build_value_flows(vendors),
              ["Flow ID", "Source Entity", "Target Entity", "Amount",
               "Flow Date", "Relation"])

    write_answer_key(chains)
    write_learning_ledger(chains)


def write_answer_key(chains: list[dict]) -> None:
    path = Path(__file__).resolve().parent / "instructor" / "ANSWER-KEY.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    by_procedure: dict[str, list[dict]] = {}
    for finding in FINDINGS:
        by_procedure.setdefault(finding["procedure"], []).append(finding)

    quantified = [f["amount"] for f in FINDINGS if f["amount"] is not None]
    total = sum(quantified, Decimal("0"))

    lines = [
        "# Instructor answer key — Harborline Marine Group",
        "",
        "> Do not distribute with the student materials.",
        "",
        "Generated by `generate.py` (seed "
        f"`{SEED}`). Regenerating the data regenerates this file, so the key "
        "cannot drift from the population.",
        "",
        f"**{len(FINDINGS)} exceptions were planted** across "
        f"{len(by_procedure)} procedures. Quantified exposure across "
        f"{len(quantified)} of them totals **{total.quantize(Decimal('0.01'))}**.",
        "",
        "A learner working only from the data should be able to reach every "
        "row below. Anything they find beyond this list is either a "
        "false positive worth discussing or a genuine emergent coincidence in "
        "the generated population — both are useful teaching moments.",
        "",
    ]
    for procedure in sorted(by_procedure):
        items = by_procedure[procedure]
        lines.append(f"## `{procedure}` — {len(items)} planted")
        lines.append("")
        lines.append("| Reference | Exception | Amount |")
        lines.append("|---|---|---:|")
        for item in items:
            amount = (f"{item['amount']:,.2f}"
                      if item["amount"] is not None else "—")
            lines.append(
                f"| `{item['reference']}` | {item['detail']} | {amount} |")
        lines.append("")

    lines += [
        "## Population totals",
        "",
        f"- Purchase orders: {len(chains)}",
        f"- Vouchers: {len([c for c in chains if not c['skip_voucher']])}",
        f"- Payments: {len(chains)}",
        f"- Goods receipts: {len([c for c in chains if not c['skip_receipt']])}",
        f"- Bank clearings: {len([c for c in chains if not c['skip_bank']])}",
        f"- GL postings: {len([c for c in chains if not c['skip_gl']])}",
        "",
    ]
    appendix = (path.parent / "REVISION-KEY.md").read_text(encoding="utf-8")
    path.write_text("\n".join(lines) + "\n" + appendix, encoding="utf-8")
    planted = [{**item, "amount": (str(item["amount"])
                                    if item["amount"] is not None else None)}
               for item in FINDINGS]
    (path.parent / "PLANTED-EXCEPTIONS.json").write_text(
        json.dumps(planted, indent=2) + "\n", encoding="utf-8")
    print(f"\n  instructor/ANSWER-KEY.md     {len(FINDINGS)} planted exceptions")


def write_learning_ledger(chains: list[dict]) -> None:
    """A balanced miniature ledger for one case purchase, clearly illustrative.

    Harborline's supplied GL contains payment-side AP postings only. This
    teaching ledger therefore models what booking the full bill would do; it
    must never be presented as observed Harborline GL or a real statement.
    """
    chain = next(c for c in chains if c["voucher_number"] == "VCH-2026-0009")
    opening_cash = Decimal("10000.00")
    billed = chain["voucher_amount"]
    accepted = chain["received_amount"]
    paid = chain["payment_amount"]
    closing_cash = opening_cash - paid
    closing_ap = billed - paid
    assert closing_cash >= 0 and closing_ap == 0
    fmt = lambda value: f"{value:.2f}"
    path = Path(__file__).resolve().parent / "learning" / "trace-ledger.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    scenario = {
        "label": "Illustrative isolated ledger, not Harborline's complete books",
        "assumption": "The full voucher was booked as security-services expense and AP; the receipt difference remains unresolved.",
        "source": {
            "purchase_order": chain["po_number"],
            "receipt": chain["receipt_number"],
            "voucher": chain["voucher_number"],
            "payment": chain["payment_number"],
            "ordered": fmt(chain["po_amount"]),
            "accepted": fmt(accepted),
            "billed": fmt(billed),
            "paid": fmt(paid),
            "unresolved_difference": fmt(billed - accepted),
        },
        "journal": [
            {"event": "Opening teaching balance", "date": "2026-01-01",
             "lines": [
                 {"account": "1010 Cash", "debit": fmt(opening_cash), "credit": ""},
                 {"account": "3000 Opening equity", "debit": "", "credit": fmt(opening_cash)},
             ]},
            {"event": "Model the full invoice", "date": chain["voucher_date"].isoformat(),
             "lines": [
                 {"account": "6100 Security-services expense", "debit": fmt(billed), "credit": ""},
                 {"account": "2000 Accounts Payable", "debit": "", "credit": fmt(billed)},
             ]},
            {"event": "Model the bill payment", "date": chain["payment_date"].isoformat(),
             "lines": [
                 {"account": "2000 Accounts Payable", "debit": fmt(paid), "credit": ""},
                 {"account": "1010 Cash", "debit": "", "credit": fmt(paid)},
             ]},
        ],
        "trial_balance": [
            {"account": "1010 Cash", "debit": fmt(closing_cash), "credit": ""},
            {"account": "2000 Accounts Payable", "debit": "", "credit": ""},
            {"account": "6100 Security-services expense", "debit": fmt(billed), "credit": ""},
            {"account": "3000 Opening equity", "debit": "", "credit": fmt(opening_cash)},
        ],
        "statement_excerpt": {
            "income_statement": {"security_services_expense": fmt(billed),
                                 "net_loss": fmt(billed)},
            "balance_sheet": {"cash": fmt(closing_cash), "accounts_payable": fmt(closing_ap),
                              "opening_equity": fmt(opening_cash),
                              "current_loss": fmt(billed),
                              "ending_equity": fmt(opening_cash - billed)},
        },
    }
    path.write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")
    print(f"  learning/trace-ledger.json   1 illustrative ledger")


if __name__ == "__main__":
    main()
