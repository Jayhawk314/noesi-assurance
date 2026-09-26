# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Sampling arithmetic against published AICPA Audit Sampling guide values."""

from decimal import Decimal

import pytest

from procedures_cycles import sampling as s

# (sample size, deviations) -> CUER % at 10% risk of overreliance (AICPA table)
CUER_10 = {(25, 0): "8.8", (50, 0): "4.6", (50, 2): "10.3", (60, 3): "10.8",
           (100, 1): "3.9", (100, 7): "11.5", (150, 4): "5.3", (200, 6): "5.3"}
# (EPER %, TER %) -> sample size at 10% ARO (AICPA table)
SIZE_10 = {(0, 5): 45, (0, 2): 114, (0.5, 3): 129, (1, 4): 96, (1.5, 8): 48,
           (1.5, 6): 64, (2, 6): 88, (2.5, 5): 158, (3, 10): 52}


@pytest.mark.parametrize("n,k", sorted(CUER_10))
def test_cuer_matches_aicpa_table(n, k):
    assert s.attribute_cuer(n, k, 0.10) == Decimal(CUER_10[(n, k)])


@pytest.mark.parametrize("eper,ter", sorted(SIZE_10))
def test_attribute_sample_size_matches_aicpa_table(eper, ter):
    assert s.attribute_sample_size(eper / 100, ter / 100, 0.10) == SIZE_10[(eper, ter)]


def test_attribute_size_is_none_when_expected_reaches_tolerable():
    assert s.attribute_sample_size(0.05, 0.05, 0.10) is None


def test_nonstatistical_attribute_adds_judged_risk():
    out = s.nonstatistical_attribute(55, 1, 0.04)
    assert out["cuer"] == pytest.approx(1 / 55 + 0.04)


def test_poisson_reliability_factors_rounded_up_like_tables():
    assert [str(s.round_factor(s.poisson_upper_limit(k, 0.20))) for k in range(6)] == \
        ["1.61", "3.00", "4.28", "5.52", "6.73", "7.91"]
    assert str(s.round_factor(s.poisson_upper_limit(0, 0.05))) == "3.00"
    assert str(s.round_factor(s.poisson_upper_limit(0, 0.10))) == "2.31"


@pytest.mark.parametrize("ratio,risk,factor", [
    (0.0, 0.20, "1.61"), (0.05, 0.20, "1.74"), (0.10, 0.20, "1.89"),
    (0.20, 0.05, "4.63"), (0.30, 0.10, "4.33"), (0.10, 0.30, "1.39")])
def test_mus_confidence_factor(ratio, risk, factor):
    assert str(s.round_factor(s.mus_confidence_factor(ratio, risk))) == factor


def test_mus_evaluation_layers_taintings_high_to_low():
    out = s.mus_evaluate(Decimal("1000"), [Decimal("0.1"), Decimal("0.5")], 0.20,
                         large_item_misstatement=Decimal("250"))
    # 1000×1.61 + 500×1.39 + 100×1.28 + 250
    assert out["upper_misstatement_limit"] == Decimal("2683.00")
    assert out["projected_misstatement"] == Decimal("850.00")
    assert [layer["tainting"] for layer in out["layers"]] == ["0.5", "0.1"]


def test_tainting_rounds_away_from_zero():
    assert s.tainting(Decimal("1"), Decimal("3")) == Decimal("0.3334")
    assert s.tainting(Decimal("-1"), Decimal("3")) == Decimal("-0.3334")


def test_z_coefficients_match_worksheet_tables():
    assert [str(s.z_coefficient(r)) for r in (0.10, 0.20, 0.30)] == ["1.28", "0.84", "0.52"]
    assert [str(s.z_coefficient(r, two_sided=True)) for r in (0.20, 0.40, 0.60)] == \
        ["1.28", "0.84", "0.52"]


def test_difference_estimation():
    n = s.difference_sample_size(100, Decimal("50"), Decimal("0.84"), Decimal("0.52"),
                                 Decimal("2000"), Decimal("200"))
    assert n == 15  # (50 × 1.36 × 100 / 1800)² = 14.27 → 15
    out = s.difference_evaluate([Decimal("10"), Decimal("0"), Decimal("-4"),
                                 Decimal("0"), Decimal("6")], 100, Decimal("0.84"),
                                Decimal("2000"))
    assert out["projected_misstatement"] == Decimal("240.00")
    assert out["within_tolerable"] is True
    assert out["lower_limit"] < out["projected_misstatement"] < out["upper_limit"]


def test_selection_helpers():
    assert s.systematic_selection(20, 8, 3) == [3, 11, 19]
    picks = s.monetary_unit_selection([Decimal("500"), Decimal("2500"), Decimal("100")],
                                      Decimal("1000"), Decimal("400"))
    assert [(p["position"], p["repeat"]) for p in picks] == [(1, False), (2, False),
                                                              (2, True)]


def test_ratio_projection_and_allowance():
    projected = s.ratio_projection(Decimal("1200"), Decimal("400000"), Decimal("1200000"))
    assert projected == Decimal("3600.00")
    assert s.allowance_for_sampling_risk(Decimal("50000"), -projected) == Decimal("46400.00")
