"""Typed research loop and numerical analysis. No model inference or simulator internals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any, Literal, Protocol

LEVELS = 4
RESIDUAL_THRESHOLD = 0.9


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Cell:
    row: int
    column: int
    treatment: int


@dataclass(frozen=True)
class Design:
    shift: int
    cells: tuple[Cell, ...]

    def validate(self) -> None:
        """Defensive boundary check; the proof remains in the Lean source."""
        if type(self.shift) is not int or self.shift not in range(LEVELS):
            raise ValueError("shift outside the certified finite family")
        if len(self.cells) != LEVELS**2:
            raise ValueError("expected sixteen cells")
        for cell in self.cells:
            if any(type(v) is not int or v not in range(LEVELS) for v in asdict(cell).values()):
                raise ValueError("invalid level")
        if {(c.row, c.column) for c in self.cells} != {
            (r, c) for r in range(LEVELS) for c in range(LEVELS)
        }:
            raise ValueError("missing or duplicate experimental unit")
        for level in range(LEVELS):
            for attr in ("row", "column"):
                values = [c.treatment for c in self.cells if getattr(c, attr) == level]
                if sorted(values) != list(range(LEVELS)):
                    raise ValueError("broken treatment balance")
        if any(c.treatment != (c.row + c.column + self.shift) % LEVELS for c in self.cells):
            raise ValueError("balanced design outside the Lean-certified cyclic family")


def read_family(path: Path) -> dict[int, Design]:
    raw = json.loads(path.read_text())
    if raw["schema"] != "lean-latin-family/v1" or raw["levels"] != LEVELS:
        raise ValueError("unsupported Lean design export")
    designs = [Design(d["shift"], tuple(Cell(**c) for c in d["cells"])) for d in raw["designs"]]
    if len(designs) != LEVELS or {d.shift for d in designs} != set(range(LEVELS)):
        raise ValueError("incomplete certified family")
    for design in designs:
        design.validate()
    return {d.shift: d for d in designs}


@dataclass(frozen=True)
class Observation:
    round: int
    shift: int
    trial: int
    row: int
    column: int
    treatment: int
    response: float


def validate_observations(observations: tuple[Observation, ...]) -> None:
    if not observations or len(observations) > 64:
        raise ValueError("observation budget must be between one and sixty-four")
    for obs in observations:
        if not math.isfinite(obs.response):
            raise ValueError("non-finite response")
        if any(type(v) is not int or v not in range(LEVELS)
               for v in (obs.row, obs.column, obs.treatment, obs.shift)):
            raise ValueError("invalid observation level")
        if obs.treatment != (obs.row + obs.column + obs.shift) % LEVELS:
            raise ValueError("observation does not match certified assignment")
    for round_id in sorted({o.round for o in observations}):
        group = [o for o in observations if o.round == round_id]
        if len(group) != 16 or sorted(o.trial for o in group) != list(range(16)):
            raise ValueError("each recorded square needs sixteen distinct trials")
        Design(group[0].shift, tuple(Cell(o.row, o.column, o.treatment) for o in group)).validate()
        if len({o.shift for o in group}) != 1:
            raise ValueError("one shift per recorded square")


@dataclass(frozen=True)
class Contrast:
    treatment: int
    estimate: float
    standard_error: float
    conditional_ci95: tuple[float, float]


@dataclass(frozen=True)
class Analysis:
    observation_hash: str
    count: int
    residual_df: int
    residual_rms: float
    residual_sd: float
    contrasts: tuple[Contrast, ...]
    row_contrasts: tuple[float, ...] | None
    assumption_flag: Literal["challenged", "not_detected"]
    interval_status: str


def analyze(observations: tuple[Observation, ...]) -> Analysis:
    """Closed-form least squares for balanced additive row/column/treatment designs."""
    validate_observations(observations)
    n = len(observations)
    grand = mean(o.response for o in observations)
    row_means = [mean(o.response for o in observations if o.row == r) for r in range(4)]
    col_means = [mean(o.response for o in observations if o.column == c) for c in range(4)]
    treatment_means = [mean(o.response for o in observations if o.treatment == t) for t in range(4)]
    residuals = [o.response - (row_means[o.row] + col_means[o.column] +
                 treatment_means[o.treatment] - 2 * grand) for o in observations]
    sse = sum(e * e for e in residuals)
    # Intercept + three levels for each of the three factors = ten parameters.
    df = n - 10
    if df not in (6, 22, 54):
        raise ValueError("supported plans contain one, two, or four complete squares")
    mse = sse / df
    se = math.sqrt(2 * mse / (n / 4))
    # Student-t 0.975 quantiles for the three supported degrees of freedom.
    critical = {6: 2.446911851, 22: 2.073873068, 54: 2.004879289}[df]
    contrasts = tuple(Contrast(t, treatment_means[t] - treatment_means[0], se,
                      (treatment_means[t] - treatment_means[0] - critical * se,
                       treatment_means[t] - treatment_means[0] + critical * se))
                      for t in range(1, 4))
    complete = all({o.column for o in observations if o.row == r and o.treatment == t} == set(range(4))
                   for r in range(4) for t in range(4))
    row_contrasts = tuple(
        mean(o.response for o in observations if o.row == r and o.treatment == 3) -
        mean(o.response for o in observations if o.row == r and o.treatment == 0)
        for r in range(4)) if complete else None
    flag: Literal["challenged", "not_detected"] = (
        "challenged" if math.sqrt(sse / n) > RESIDUAL_THRESHOLD else "not_detected")
    return Analysis(digest([asdict(o) for o in observations]), n, df,
                    math.sqrt(sse / n), math.sqrt(mse), contrasts, row_contrasts, flag,
                    "conditional on additive model and iid Gaussian noise; " +
                    ("model challenged: intervals are diagnostic only" if flag == "challenged"
                     else "no detected violation is not validation of assumptions"))


@dataclass(frozen=True)
class Proposal:
    provider: str
    action: Literal["complete_coverage", "replicate"]
    shifts: tuple[int, ...]
    reason: str
    revised_question: str
    evidence_hash: str


class Proposer(Protocol):
    """Human/replay/model adapters may supply data, never commands or arbitrary code."""
    def propose(self, observed: Analysis) -> Proposal: ...


class ResidualProposer:
    def propose(self, observed: Analysis) -> Proposal:
        if observed.residual_rms > RESIDUAL_THRESHOLD:
            return Proposal("deterministic-residual-rule/v1", "complete_coverage", (1, 2, 3),
                            f"Observed residual RMS {observed.residual_rms:.3f} exceeds 0.900.",
                            "Is the treatment-3 contrast row-dependent under complete column coverage?",
                            observed.observation_hash)
        return Proposal("deterministic-residual-rule/v1", "replicate", (0,),
                        f"Observed residual RMS {observed.residual_rms:.3f} is at most 0.900.",
                        "Does the treatment ranking replicate in another blocked square?",
                        observed.observation_hash)


class ReplayProposer:
    def __init__(self, path: Path) -> None:
        self.path = path

    def propose(self, observed: Analysis) -> Proposal:
        raw = json.loads(self.path.read_text())
        raw["shifts"] = tuple(raw["shifts"])
        return Proposal(**raw)


def validate_proposal(proposal: Proposal, observed: Analysis, family: dict[int, Design]) -> None:
    if proposal.evidence_hash != observed.observation_hash:
        raise ValueError("stale proposal: observations changed")
    plans = {"complete_coverage": (1, 2, 3), "replicate": (0,)}
    if proposal.action not in plans or proposal.shifts != plans[proposal.action]:
        raise ValueError("proposal outside the two bounded allowed plans")
    if not proposal.provider or not proposal.reason or not proposal.revised_question:
        raise ValueError("proposal needs provider, reason, and revised question")
    for shift in proposal.shifts:
        family[shift].validate()
    if observed.count + 16 * len(proposal.shifts) > 64:
        raise ValueError("proposal exceeds measurement budget")


def next_question(analysis: Analysis) -> str:
    if analysis.row_contrasts is None:
        return "Does the replicated ranking persist in new randomized blocks and nuisance levels?"
    spread = max(analysis.row_contrasts) - min(analysis.row_contrasts)
    if spread > 2.0:
        return ("Which row conditions modify the treatment-3 effect, and does that pattern "
                "replicate with independent blocks? This is an unverified proposal.")
    return "Does a common treatment effect persist under independent replicated blocks?"


def render_report(initial: Analysis, final: Analysis, proposal: Proposal) -> str:
    lines = ["QUESTION: Which treatment raises the synthetic response after blocking?",
             "KERNEL THEOREMS: balance of all shifts; counts; coverage; additive integer identity.",
             "ASSUMPTIONS: additive effects; iid Gaussian noise; fixed nuisance levels.",
             "PROVIDER: " + proposal.provider + " (no AI inference)", "",
             "ROUND 1 · NUMERICAL CALCULATION FROM 16 SYNTHETIC OBSERVATIONS",
             f"Residual RMS: {initial.residual_rms:.6f}; residual df: {initial.residual_df}.",
             f"Additive assumption: {initial.assumption_flag}."]
    for contrast in initial.contrasts:
        lo, hi = contrast.conditional_ci95
        lines.append(f"T{contrast.treatment} − T0: {contrast.estimate:.6f}; "
                     f"conditional 95% CI [{lo:.6f}, {hi:.6f}].")
    lines += [initial.interval_status, "", "REVISED QUESTION · UNVERIFIED PROPOSAL",
              proposal.revised_question, "Reason: " + proposal.reason,
              "Validated follow-up shifts: " + ", ".join(map(str, proposal.shifts)), "",
              f"FOLLOW-UP · {final.count - initial.count} NEW SYNTHETIC OBSERVATIONS",
              f"Combined N: {final.count}; residual RMS: {final.residual_rms:.6f}."]
    if final.row_contrasts is not None:
        lines.append("T3 − T0 by row, with all four columns represented in each mean:")
        lines.extend(f"  Row {r}: {value:.6f}" for r, value in enumerate(final.row_contrasts))
    else:
        lines.append("Repeated initial design; row-specific comparisons remain column-confounded.")
    lines += ["", "NEXT QUESTION · UNVERIFIED PROPOSAL", next_question(final), "",
              "SYNTHETIC EVIDENCE ONLY: neither efficacy nor model assumptions are proved.",
              "PROVENANCE: see manifest.json, observations.json, summary.json and proof-audit.txt.",
              "Observation SHA-256: " + final.observation_hash]
    return "\n".join(lines) + "\n"
