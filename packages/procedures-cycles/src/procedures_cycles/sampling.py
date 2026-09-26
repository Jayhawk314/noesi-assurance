# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Audit sampling arithmetic: attribute, nonstatistical, MUS, difference estimation.

Pure functions, standard library only. Rates are floats (they are
probabilities); money is Decimal. Every function computes a number an
auditor would otherwise read from a table or a worksheet; none of them
decides whether a result is acceptable — the caller compares the bound to
the tolerable amount and records the auditor's conclusion.

Methods follow the AICPA *Audit Sampling* guide and the standard textbook
presentations (see docs/CYCLES-DESIGN.md).
"""

from __future__ import annotations

import math
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from statistics import NormalDist

_CENT = Decimal("0.01")


# ------------------------------------------------------------ distributions

def _binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0 if k < n else 1.0
    return sum(math.comb(n, i) * p ** i * (1.0 - p) ** (n - i)
               for i in range(0, min(k, n) + 1))


def _bisect(f, lo: float, hi: float, iterations: int = 200) -> float:
    """Root of a decreasing function f on [lo, hi] (f(lo) > 0 > f(hi))."""
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _gammainc_lower(a: float, x: float) -> float:
    """Regularized lower incomplete gamma P(a, x) (Numerical Recipes)."""
    if x <= 0:
        return 0.0
    gln = math.lgamma(a)
    if x < a + 1.0:
        term = total = 1.0 / a
        ap = a
        for _ in range(10_000):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return total * math.exp(-x + a * math.log(x) - gln)
    # continued fraction for Q, then P = 1 - Q
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return 1.0 - math.exp(-x + a * math.log(x) - gln) * h


def poisson_upper_limit(misstatements: float, risk: float) -> float:
    """Upper limit on the Poisson mean given `misstatements` observed.

    The mean λ at which P(X <= misstatements) = risk. Non-integer counts are
    allowed (gamma generalization), which the MUS sample-size factor needs.
    """
    _check_risk(risk)
    if misstatements < 0:
        raise ValueError("misstatements cannot be negative")
    a = misstatements + 1.0
    # P(Poisson(λ) <= x) generalizes to Q(x+1, λ) = 1 - P(x+1, λ)
    return _bisect(lambda lam: (1.0 - _gammainc_lower(a, lam)) - risk,
                   0.0, 50.0 + 10.0 * a)


def _check_risk(risk: float) -> None:
    if not 0.0 < risk < 1.0:
        raise ValueError(f"risk must be strictly between 0 and 1, not {risk!r}")


def _check_rate(name: str, rate: float) -> None:
    if not 0.0 <= rate < 1.0:
        raise ValueError(f"{name} must be a rate in [0, 1), not {rate!r}")


# ------------------------------------------------------ attribute sampling

def attribute_upper_rate(sample_size: int, deviations: int, risk: float) -> float:
    """Exact one-sided binomial upper deviation rate (unrounded)."""
    _check_risk(risk)
    if sample_size <= 0:
        raise ValueError("sample size must be positive")
    if not 0 <= deviations <= sample_size:
        raise ValueError("deviations must lie between 0 and the sample size")
    if deviations == sample_size:
        return 1.0
    return _bisect(lambda p: _binom_cdf(deviations, sample_size, p) - risk,
                   0.0, 1.0)


def attribute_cuer(sample_size: int, deviations: int, risk: float) -> Decimal:
    """Computed upper exception rate, in percent, rounded *up* to 0.1%.

    Rounding up is conservative and is how the AICPA evaluation tables are
    presented.
    """
    rate = attribute_upper_rate(sample_size, deviations, risk) * 100.0
    # a tiny epsilon keeps an exact tenth (e.g. 4.5000000001) from rounding up
    return Decimal(repr(rate - 1e-9)).quantize(Decimal("0.1"), rounding=ROUND_CEILING)


def attribute_sample_size(expected_rate: float, tolerable_rate: float,
                          risk: float, *, max_size: int = 5000) -> int | None:
    """Smallest n whose upper bound at ⌈n·EPER⌉ deviations is ≤ TER.

    Returns None when no sample up to `max_size` achieves it (the tables
    print a dash: the expected rate is too close to the tolerable rate).
    """
    _check_risk(risk)
    _check_rate("expected rate", expected_rate)
    _check_rate("tolerable rate", tolerable_rate)
    if tolerable_rate <= expected_rate:
        return None
    for n in range(1, max_size + 1):
        k = math.ceil(n * expected_rate - 1e-9)
        if k >= n:
            continue
        if attribute_upper_rate(n, k, risk) <= tolerable_rate + 1e-12:
            return n
    return None


def nonstatistical_attribute(sample_size: int, deviations: int,
                             estimated_sampling_risk: float) -> dict:
    """Sample exception rate plus the auditor's estimate of sampling risk."""
    if sample_size <= 0:
        raise ValueError("sample size must be positive")
    if not 0 <= deviations <= sample_size:
        raise ValueError("deviations must lie between 0 and the sample size")
    _check_rate("estimated sampling risk", estimated_sampling_risk)
    ser = deviations / sample_size
    return {"sample_exception_rate": ser,
            "estimated_sampling_risk": estimated_sampling_risk,
            "cuer": ser + estimated_sampling_risk}


# --------------------------------------------------------------- selection

def systematic_selection(count: int, interval: int, start: int,
                         *, limit: int | None = None) -> list[int]:
    """1-based positions start, start+interval, ... up to `count` (or `limit` picks)."""
    if count <= 0 or interval <= 0:
        raise ValueError("count and interval must be positive")
    if not 1 <= start <= count:
        raise ValueError("start must be a position within the population")
    picks = list(range(start, count + 1, interval))
    return picks[:limit] if limit is not None else picks


def monetary_unit_selection(amounts: list[Decimal], interval: Decimal,
                            start: Decimal) -> list[dict]:
    """Systematic dollar-unit selection over cumulative amounts.

    Returns one entry per selected dollar unit: the dollar unit, the 1-based
    position of the item containing it, and whether that item was already
    hit (an item larger than the interval can contain several units).
    """
    interval = Decimal(interval)
    start = Decimal(start)
    if interval <= 0:
        raise ValueError("interval must be positive")
    if not 0 < start <= interval:
        raise ValueError("the random start must lie in (0, interval]")
    picks = []
    unit = start
    cumulative = Decimal("0")
    seen: set[int] = set()
    for position, amount in enumerate(amounts, 1):
        amount = Decimal(amount)
        if amount < 0:
            raise ValueError("MUS selects over non-negative amounts; "
                             "handle credit balances separately")
        cumulative += amount
        while unit <= cumulative:
            picks.append({"dollar_unit": unit, "position": position,
                          "repeat": position in seen})
            seen.add(position)
            unit += interval
    return picks


# ----------------------------------------------- nonstatistical (balances)

def nonstatistical_sample_size(book_value: Decimal, tolerable: Decimal,
                               confidence_factor: Decimal) -> int:
    """n = BV × CF / TM for the stratum below tolerable misstatement."""
    book_value, tolerable = Decimal(book_value), Decimal(tolerable)
    if tolerable <= 0:
        raise ValueError("tolerable misstatement must be positive")
    raw = book_value * Decimal(confidence_factor) / tolerable
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def ratio_projection(sample_misstatement: Decimal, sample_value: Decimal,
                     population_value: Decimal) -> Decimal:
    """Projected misstatement = sample misstatement × population $ / sample $."""
    sample_value = Decimal(sample_value)
    if sample_value == 0:
        raise ValueError("sample value cannot be zero")
    return (Decimal(sample_misstatement) * Decimal(population_value)
            / sample_value).quantize(_CENT, rounding=ROUND_HALF_UP)


def allowance_for_sampling_risk(tolerable: Decimal, projected: Decimal) -> Decimal:
    """TM − |projected misstatement| (nonstatistical, judgmental comparison)."""
    return (Decimal(tolerable) - abs(Decimal(projected))).quantize(_CENT)


# --------------------------------------------------- monetary unit sampling

def mus_confidence_factor(expected_to_tolerable: float, risk: float) -> float:
    """Sample-size confidence factor given the ratio of expected to tolerable.

    Solves CF = UL(r·CF) where UL is the Poisson (gamma) upper limit at the
    risk of incorrect acceptance: the expected misstatement, expressed in
    sampling intervals, is r·CF.
    """
    _check_risk(risk)
    if not 0 <= expected_to_tolerable < 1:
        raise ValueError("ratio of expected to tolerable must be in [0, 1)")
    cf = poisson_upper_limit(0.0, risk)
    for _ in range(500):
        nxt = poisson_upper_limit(expected_to_tolerable * cf, risk)
        if abs(nxt - cf) < 1e-12:
            break
        cf = nxt
    else:  # pragma: no cover — the fixed point converges for r < ~0.6
        raise ValueError("the expected misstatement is too close to tolerable")
    return cf


def round_factor(value: float, places: int | None = 2) -> Decimal:
    """Round a reliability factor *up*, as the published MUS tables do."""
    d = Decimal(repr(value))
    if places is None:
        return d
    return (d - Decimal("1e-9")).quantize(Decimal(1).scaleb(-places), rounding=ROUND_CEILING)


def mus_sample_size(population_value: Decimal, tolerable: Decimal,
                    confidence_factor: float) -> int:
    """n = CF / (TM / population), rounded up."""
    tolerable = Decimal(tolerable)
    if tolerable <= 0:
        raise ValueError("tolerable misstatement must be positive")
    raw = Decimal(repr(confidence_factor)) * Decimal(population_value) / tolerable
    return int(raw.quantize(Decimal("1"), rounding=ROUND_CEILING))


def mus_interval(population_value: Decimal, sample_size: int,
                 *, round_down_to: Decimal | None = None) -> Decimal:
    """Sampling interval = population / n, optionally rounded down (e.g. to $100)."""
    if sample_size <= 0:
        raise ValueError("sample size must be positive")
    interval = Decimal(population_value) / Decimal(sample_size)
    if round_down_to:
        step = Decimal(round_down_to)
        return (interval / step).quantize(Decimal("1"), rounding=ROUND_FLOOR) * step
    return interval.quantize(_CENT, rounding=ROUND_FLOOR)


def tainting(misstatement: Decimal, book_value: Decimal) -> Decimal:
    """misstatement / book value, rounded *away from zero* to four places."""
    book_value = Decimal(book_value)
    if book_value == 0:
        raise ValueError("book value cannot be zero")
    raw = Decimal(misstatement) / book_value
    rounded = abs(raw).quantize(Decimal("0.0001"), rounding=ROUND_CEILING)
    return rounded if raw >= 0 else -rounded


def mus_evaluate(interval: Decimal, taintings: list[Decimal], risk: float, *,
                 large_item_misstatement: Decimal = Decimal("0"),
                 factor_places: int = 2) -> dict:
    """Upper misstatement limit for overstatements (textbook layering).

    basic precision = SI × UL(0); each tainting, ranked high to low, times
    SI times its incremental factor UL(i) − UL(i−1); misstatements found in
    items at or above the interval are added unprojected. Factors are
    rounded *up* to `factor_places`, as published tables are (None = exact).

    Only overstatement taintings (> 0) enter the layering; understatement
    taintings are reported separately and must be evaluated on their own —
    they are not netted against overstatements here.
    """
    interval = Decimal(interval)
    over = sorted((Decimal(t) for t in taintings if Decimal(t) > 0), reverse=True)
    under = [Decimal(t) for t in taintings if Decimal(t) < 0]

    def factor(k: int) -> Decimal:
        return round_factor(poisson_upper_limit(float(k), risk), factor_places)

    basic_factor = factor(0)
    basic = (interval * basic_factor).quantize(_CENT, rounding=ROUND_HALF_UP)
    layers = []
    previous = basic_factor
    for i, t in enumerate(over, 1):
        current = factor(i)
        increment = current - previous
        projected = (t * interval).quantize(_CENT, rounding=ROUND_HALF_UP)
        layers.append({"rank": i, "tainting": str(t), "projected": projected,
                       "incremental_factor": increment,
                       "bound": (projected * increment).quantize(_CENT, rounding=ROUND_HALF_UP)})
        previous = current
    large = Decimal(large_item_misstatement).quantize(_CENT)
    projected_total = sum((row["projected"] for row in layers), Decimal("0")) + large
    upper = basic + sum((row["bound"] for row in layers), Decimal("0")) + large
    return {"basic_precision": basic, "basic_factor": basic_factor, "layers": layers,
            "large_item_misstatement": large,
            "projected_misstatement": projected_total.quantize(_CENT),
            "upper_misstatement_limit": upper.quantize(_CENT),
            "understatement_taintings": [str(t) for t in under]}


# --------------------------------------------------- difference estimation

def z_coefficient(risk: float, *, two_sided: bool = False, places: int = 2) -> Decimal:
    """Normal confidence coefficient: one-sided for ARIA, two-sided for ARIR."""
    _check_risk(risk)
    tail = risk / 2.0 if two_sided else risk
    z = NormalDist().inv_cdf(1.0 - tail)
    return Decimal(repr(z)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def difference_sample_size(population_count: int, estimated_sd: Decimal,
                           z_a: Decimal, z_r: Decimal, tolerable: Decimal,
                           expected: Decimal) -> int:
    """n = (SD·(Z_A + Z_R)·N / (TM − E*))², rounded up."""
    margin = Decimal(tolerable) - Decimal(expected)
    if margin <= 0:
        raise ValueError("tolerable misstatement must exceed the expected misstatement")
    base = Decimal(estimated_sd) * (Decimal(z_a) + Decimal(z_r)) * population_count / margin
    return int((base * base).quantize(Decimal("1"), rounding=ROUND_CEILING))


def difference_evaluate(differences: list[Decimal], population_count: int,
                        z_a: Decimal, tolerable: Decimal) -> dict:
    """Point estimate, precision interval and confidence limits.

    `differences` holds one value per sampled item (zero for items with no
    misstatement), overstatements positive.
    """
    n = len(differences)
    if n < 2:
        raise ValueError("difference estimation needs at least two sample items")
    if n > population_count:
        raise ValueError("sample cannot exceed the population")
    values = [Decimal(d) for d in differences]
    total = sum(values, Decimal("0"))
    mean = total / n
    ss = sum((d - mean) ** 2 for d in values)
    sd = (ss / (n - 1)).sqrt()
    projected = mean * population_count
    fpc = (Decimal(population_count - n) / population_count).sqrt()
    precision = population_count * Decimal(z_a) * sd / Decimal(n).sqrt() * fpc
    upper, lower = projected + precision, projected - precision
    tolerable = Decimal(tolerable)
    return {"sample_size": n, "total_misstatement": total.quantize(_CENT),
            "mean_misstatement": mean.quantize(_CENT),
            "standard_deviation": sd.quantize(_CENT),
            "projected_misstatement": projected.quantize(_CENT),
            "precision_interval": precision.quantize(_CENT),
            "upper_limit": upper.quantize(_CENT),
            "lower_limit": lower.quantize(_CENT),
            "within_tolerable": bool(upper <= tolerable and lower >= -tolerable)}
