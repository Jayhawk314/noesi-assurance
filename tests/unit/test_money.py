"""Decimal money: exactness, parsing boundary, currency refusal."""

from decimal import Decimal

import pytest

from assurance_domain.money import (
    CurrencyMismatchError, Money, fnum, parse_amount, sum_amounts,
)


def test_parse_handles_strings_floats_ints_exactly():
    assert parse_amount("1,250.50") == Decimal("1250.50")
    assert parse_amount("10000") == Decimal("10000")
    assert parse_amount(100.0) == Decimal("100.0")  # via str(), no binary junk
    assert parse_amount(99) == Decimal("99")


def test_parse_refuses_junk_without_guessing():
    assert parse_amount(True) is None
    assert parse_amount("n/a") is None
    assert parse_amount("") is None
    assert parse_amount(None) is None
    assert parse_amount(float("nan")) is None


def test_decimal_arithmetic_has_no_float_drift():
    total = sum_amounts([parse_amount("0.1"), parse_amount("0.2")])
    assert total == Decimal("0.3")  # 0.1 + 0.2 != 0.3 in the old float engine


def test_mixed_currency_aggregation_is_refused():
    usd = Money(Decimal("10.00"), "USD")
    eur = Money(Decimal("10.00"), "EUR")
    with pytest.raises(CurrencyMismatchError):
        usd + eur


def test_quantize_rounds_half_even_to_cents():
    assert parse_amount("2.005", quantize=True) == Decimal("2.00")
    assert parse_amount("2.015", quantize=True) == Decimal("2.02")


def test_fnum_is_the_only_float_boundary():
    assert fnum(Decimal("5000.0")) == 5000.0
    assert fnum(None) is None
