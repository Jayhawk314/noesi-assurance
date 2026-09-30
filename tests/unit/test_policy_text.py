# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Every setting the Scope & Policies screen can show says, in words, what it
means and what kind of value it takes (30 Sep 2026: the screen showed bare
codes such as "dit max days", with no unit)."""

from procedures_cycles.contracts import (CYCLE_PROCEDURES, ENGAGEMENT_POLICIES,
                                         OPTIONAL_POLICIES)
from procedures_cycles.policy_text import POLICY_TEXT


def test_every_setting_the_screen_shows_is_in_words():
    shown = ({"clearly_trivial_pct"} | set(OPTIONAL_POLICIES)
             | {p for c in CYCLE_PROCEDURES for p in c.required_policies}) - set(ENGAGEMENT_POLICIES)
    missing = sorted(shown - set(POLICY_TEXT))
    assert not missing, f"settings with no plain-words text: {missing}"
    for name in shown:
        label, kind, meaning = POLICY_TEXT[name]
        assert label and kind and meaning.endswith("."), name


def test_the_catalog_carries_the_text_for_every_setting_it_lists(tmp_path):
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.signing import LocalKeyStore
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    try:
        service = WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                                   ensure_tenant(conn, "firm"),
                                   keystore=LocalKeyStore(tmp_path / "keys"))
        catalog = service.cycle_catalog()
        listed = set(catalog["general_policies"]) | {
            p for a in catalog["areas"] for p in a["required_policies"] + a["optional_policies"]}
        assert listed <= set(catalog["policy_text"])
        assert catalog["policy_text"]["dit_max_days"]["kind"] == "days"
        assert all(t["label"] for t in catalog["policy_text"].values())
    finally:
        conn.close()


def test_the_performance_rate_setting_reaches_the_sad(tmp_path):
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.signing import LocalKeyStore
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant
    import pytest
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    try:
        svc = WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), ensure_tenant(conn, "firm"),
                               keystore=LocalKeyStore(tmp_path / "keys"))
        eid = svc.create_engagement("partner", "Invented Co", "2026-12-31")["engagement_id"]
        svc.update_workflow("partner", eid, "materiality",
                            {"amount": 20000, "basis": "revenue", "rationale": "about 1% of revenue"})
        assert svc.sad(eid)["performance_materiality"] == 15000
        svc.update_workflow("partner", eid, "policy",
                            {"name": "performance_materiality_pct", "value": "60%"})
        assert svc.sad(eid)["performance_materiality"] == 12000
        with pytest.raises(ValueError, match="performance_materiality_pct"):
            svc.update_workflow("partner", eid, "policy",
                                {"name": "performance_materiality_pct", "value": "120"})
    finally:
        conn.close()
