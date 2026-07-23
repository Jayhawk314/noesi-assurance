"""Decimal money: the canonical arithmetic boundary.

The prototype computed on binary floats (P1 defect). Here all arithmetic is
``Decimal``; floats are accepted at the parsing boundary via ``str(value)``
(so ``100.0`` becomes ``Decimal('100.0')``, never the binary artifact) and
produced only at the serialization boundary for receipt compatibility.

Aggregation across currencies is refused, never silent.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

CENT = Decimal("0.01")


class CurrencyMismatchError(ValueError):
    """Aggregating mixed or unknown currencies is refused, not guessed."""


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Money.amount must be a Decimal")
        if not self.amount.is_finite():
            raise ValueError("Money.amount must be finite")
        if not self.currency.strip():
            raise ValueError("Money.currency must be non-empty")

    def _check(self, other: "Money") -> None:
        if not isinstance(other, Money):
            raise TypeError("Money combines only with Money")
        if other.currency != self.currency:
            raise CurrencyMismatchError(
                f"cannot combine {self.currency} with {other.currency}")

    def __add__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def quantized(self) -> "Money":
        return Money(self.amount.quantize(CENT, rounding=ROUND_HALF_EVEN),
                     self.currency)


def parse_amount(value, *, quantize: bool = False) -> Decimal | None:
    """Parse one monetary amount to Decimal; None when unparseable.

    Mirrors the prototype's `_number` boundary (bools rejected, bad text is
    None) so engines keep their skip-don't-guess behavior, minus the float
    representation.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, (int, float)):
        parsed = Decimal(str(value))
    elif isinstance(value, str):
        text = value.strip().replace(",", "")
        if not text:
            return None
        try:
            parsed = Decimal(text)
        except InvalidOperation:
            return None
    else:
        return None
    if not parsed.is_finite():
        return None
    return parsed.quantize(CENT, rounding=ROUND_HALF_EVEN) if quantize else parsed


def fnum(value: Decimal | None) -> float | None:
    """Serialization boundary: one exact Decimal -> float conversion.

    Used only when writing receipts/reasons so v2 output stays diffable
    against the float-era goldens. Arithmetic never happens on the result.
    """
    return None if value is None else float(value)


def sum_amounts(values, default: Decimal = Decimal("0")) -> Decimal:
    total = default
    for value in values:
        if value is not None:
            total += value
    return total
