"""Dempster-Shafer theory of evidence.

Audited port of the KOMPOSOS ``categorical.dempster_shafer`` module (same
author, dual-licensed Apache-2.0). Operation order and dict-insertion order
are preserved exactly so fused belief/plausibility/conflict floats — and
therefore fusion receipt hashes — match the prototype bit-for-bit.

Key concepts: a MassFunction distributes belief mass over hypothesis subsets
(mass on the full frame is ignorance); Belief is the lower probability bound,
Plausibility the upper; Dempster's rule combines independent sources and
reports their conflict degree instead of hiding it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MassFunction:
    """Basic Probability Assignment over subsets of hypotheses."""

    masses: dict[frozenset, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.masses.pop(frozenset(), None)
        total = sum(self.masses.values())
        if total > 0 and abs(total - 1.0) > 1e-9:
            self.masses = {k: v / total for k, v in self.masses.items()}

    @property
    def frame(self) -> frozenset:
        all_elements: set = set()
        for key in self.masses:
            all_elements.update(key)
        return frozenset(all_elements)

    def belief(self, hypothesis: frozenset) -> float:
        """Bel(A): sum of masses of all subsets of A (lower bound)."""
        total = 0.0
        for focal, mass in self.masses.items():
            if focal <= hypothesis:
                total += mass
        return total

    def plausibility(self, hypothesis: frozenset) -> float:
        """Pl(A): sum of masses of sets intersecting A (upper bound)."""
        total = 0.0
        for focal, mass in self.masses.items():
            if focal & hypothesis:
                total += mass
        return total

    def uncertainty(self, hypothesis: frozenset) -> float:
        return self.plausibility(hypothesis) - self.belief(hypothesis)

    def pignistic_probability(self, hypothesis_element: str) -> float:
        """BetP(x): point probability for decision-making."""
        total = 0.0
        for focal, mass in self.masses.items():
            if hypothesis_element in focal and len(focal) > 0:
                total += mass / len(focal)
        return total


def combine(m1: MassFunction, m2: MassFunction) -> tuple[MassFunction, float]:
    """Dempster's rule: orthogonal sum of two sources plus conflict degree."""
    combined_masses: dict[frozenset, float] = {}
    conflict = 0.0

    for a, m_a in m1.masses.items():
        for b, m_b in m2.masses.items():
            intersection = a & b
            product = m_a * m_b
            if not intersection:
                conflict += product
            else:
                combined_masses[intersection] = (
                    combined_masses.get(intersection, 0.0) + product
                )

    if abs(conflict - 1.0) < 1e-12:
        raise ValueError(
            "Total conflict between evidence sources (K=1). "
            "The sources are completely contradictory.")

    normalization = 1.0 - conflict
    normalized = {k: v / normalization
                  for k, v in combined_masses.items() if v > 0}
    return MassFunction(masses=normalized), conflict


def discount(m: MassFunction, reliability: float) -> MassFunction:
    """Discount a source by reliability; lost mass becomes ignorance."""
    reliability = max(0.0, min(1.0, reliability))
    frame = m.frame

    new_masses: dict[frozenset, float] = {}
    for focal, mass in m.masses.items():
        if focal == frame:
            new_masses[focal] = reliability * mass + (1.0 - reliability)
        else:
            new_masses[focal] = reliability * mass

    if frame not in new_masses and frame:
        new_masses[frame] = 1.0 - reliability

    new_masses = {k: v for k, v in new_masses.items() if v > 1e-12}
    return MassFunction(masses=new_masses)
