# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Aging layouts (K5): a five-column aging (Current, 1-30, 31-60, 61-90,
91 and over) foots and takes five allowance rates; a four-column one still
takes four; bad rates are refused when set, not at run time."""

from decimal import Decimal as D

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from procedures_ap.ingest import detect_columns
from procedures_cycles.common import PolicyError
from procedures_cycles.engines import execute_procedure
from procedures_cycles.roles import ROLE_SCHEMAS

TB = [{"account": "1100", "balance": D("1500"), "side": "DR", "line": "receivables"},
      {"account": "1110", "balance": D("30"), "side": "CR", "line": "allowance"}]
FIVE = [  # the third customer is a net credit: nothing to reserve against
    {"customer_number": "A", "balance": D("1000"), "current": D("500"), "days_1_30": D("300"),
     "days_31_60": D("100"), "days_61_90": D("50"), "days_over_90": D("50")},
    {"customer_number": "B", "balance": D("600"), "current": D("0"), "days_1_30": D("0"),
     "days_31_60": D("0"), "days_61_90": D("0"), "days_over_90": D("600")},
    {"customer_number": "C", "balance": D("-100"), "current": D("-100")},
]


def keys(findings):
    return {f.key[1:] for f in findings}


def test_quickbooks_aging_headers_map_to_five_buckets():
    headers = ["Customer", "Current", "1 - 30", "31 - 60", "61 - 90", "91 and over", "Total"]
    mapping = detect_columns(headers, ROLE_SCHEMAS["AR_listing"])
    assert mapping["days_1_30"] == "1 - 30"
    assert mapping["days_over_90"] == "91 and over"
    assert mapping["current"] == "Current"


def test_a_five_column_aging_foots_and_takes_five_rates():
    findings, stats = execute_procedure(
        "ar.listing_tie", {"AR_listing": FIVE, "Trial_balance": TB},
        {"ar_allowance_rates": "0.01,0.02,0.05,0.15,0.40"})
    assert not any(k[0] == "aging_does_not_foot" for k in keys(findings))
    # A: 5 + 6 + 5 + 7.5 + 20 = 43.5; B: 240; C (credit) left out -> 283.50
    assert stats["allowance_required"] == "283.50"
    assert ("allowance_estimate",) in keys(findings)


def test_a_four_column_aging_still_takes_four_rates():
    four = [{"customer_number": "A", "balance": D("1000"), "current": D("600"),
             "days_31_60": D("300"), "days_61_90": D("100"), "days_over_90": D("0")}]
    _, stats = execute_procedure("ar.listing_tie", {"AR_listing": four, "Trial_balance": TB},
                                 {"ar_allowance_rates": "0.03,0.10,0.15,0.30"})
    assert stats["allowance_required"] == "63.00"
    with pytest.raises(PolicyError, match="4 columns"):
        execute_procedure("ar.listing_tie", {"AR_listing": four, "Trial_balance": TB},
                          {"ar_allowance_rates": "0.01,0.02,0.05,0.15,0.40"})


def test_an_all_blank_1_30_column_still_keeps_the_five_rate_layout():
    five = [{"customer_number": "A", "balance": D("100"), "current": D("10"),
             "days_1_30": None, "days_31_60": D("20"), "days_61_90": D("30"),
             "days_over_90": D("40")}]
    tb = [{"account": "1100", "balance": D("100"), "side": "DR",
           "line": "receivables"},
          {"account": "1110", "balance": D("8"), "side": "CR",
           "line": "allowance"}]
    findings, stats = execute_procedure(
        "ar.listing_tie", {"AR_listing": five, "Trial_balance": tb},
        {"ar_allowance_rates": "0.01,0.02,0.05,0.15,0.40"})
    assert stats["allowance_required"] == "21.60"  # 0.10 + 1.00 + 4.50 + 16.00
    assert ("allowance_estimate",) in keys(findings)
    with pytest.raises(PolicyError, match="5 columns"):
        execute_procedure("ar.listing_tie", {"AR_listing": five, "Trial_balance": tb},
                          {"ar_allowance_rates": "0.01,0.02,0.05,0.15"})


def test_bad_rates_are_refused_when_set(tmp_path):
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "m"))
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.update_workflow("pa", eid, "cycles", {"cycles": ["receivables"]})
    for bad in ("0.01,0.02,0.05", "0.1,0.2,x,0.4", "0.1,0.2,0.3,1.5"):
        with pytest.raises(ValueError, match="four or five rates"):
            svc.update_workflow("pa", eid, "policy",
                                {"name": "ar_allowance_rates", "value": bad})
    svc.update_workflow("pa", eid, "policy",
                        {"name": "ar_allowance_rates", "value": "0.01,0.02,0.05,0.15,0.40"})
    conn.close()
