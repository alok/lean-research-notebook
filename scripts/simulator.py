"""Synthetic measurement provider. Parameters are never passed to the proposer."""

from __future__ import annotations

from collections import Counter
import random

from harness import Design, Observation


def measure(design: Design, seed: int, round_id: int, interaction: bool = True) -> tuple[Observation, ...]:
    design.validate()
    rng = random.Random(seed)
    order = list(design.cells)
    rng.shuffle(order)
    if Counter(order) != Counter(design.cells):
        raise ValueError("execution order must preserve the certified cells")
    rows = (-6.0, -2.0, 2.0, 6.0)
    columns = (-3.0, -1.0, 1.0, 3.0)
    effects = (0.0, 1.0, 2.0, 3.0)
    observations: list[Observation] = []
    for trial, cell in enumerate(order):
        hidden_interaction = 8.0 if interaction and cell.row == 3 and cell.treatment == 3 else 0.0
        response = (10.0 + rows[cell.row] + columns[cell.column] + effects[cell.treatment] +
                    hidden_interaction + rng.gauss(0.0, 0.25))
        observations.append(Observation(round_id, design.shift, trial, cell.row, cell.column,
                                        cell.treatment, round(response, 9)))
    return tuple(observations)
