"""Bounded, allowlisted local execution; requires trusted source and is not a sandbox."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any

from harness import (Observation, ReplayProposer, ResidualProposer, analyze, canonical, file_digest,
                     read_family, render_report, validate_proposal)
from simulator import measure

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_out" / "run"
THEOREMS = ("all_rows_balanced", "all_columns_balanced", "four_per_treatment",
            "complete_coverage", "order_preserves_counts", "additive_contrast")
SOURCES = ("ResearchNotebook.lean", "ResearchNotebook/Meta/Cells.lean", "NotebookMain.lean",
           "scripts/harness.py", "scripts/simulator.py", "scripts/reproduce.py", "lean-toolchain",
           "lakefile.lean", "lake-manifest.json")
SEED = 20260930


def run_lake(args: list[str], timeout: int = 600) -> str:
    env = dict(os.environ, LAKE_CACHE_DIR=str(ROOT / "_out" / "lake-cache"), LEAN_NUM_THREADS="4",
               LAKE_NO_CACHE="1", LAKE_ARTIFACT_CACHE="false")
    result = subprocess.run(["lake", *args], cwd=ROOT, env=env, text=True,
                            capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"lake {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_bytes(canonical(value))


def source_hashes() -> dict[str, str]:
    return {name: file_digest(ROOT / name) for name in SOURCES}


def audit() -> str:
    # Inspect transitive dependencies of each proof in the extracted environment.
    source = (ROOT / "_out/Research.lean").read_text()
    if re.search(r"\b(sorry|axiom|native_decide)\b", source):
        raise ValueError("unapproved proof construct in extracted source")
    audit_path = ROOT / "_out/Audit.lean"
    audit_path.write_text(source + "\n" + "\n".join(f"#print axioms Lab.{t}" for t in THEOREMS))
    output = run_lake(["env", "lean", str(audit_path)], 120)
    # Lean's command prints either `does not depend on any axioms` or a bracketed list.
    entries = re.findall(r"'Lab\.[^']+' (?:depends on axioms: \[([^]]*)\]|does not depend on any axioms)", output)
    if len(entries) != len(THEOREMS):
        raise ValueError("could not verify all proof audit results: " + output)
    standard = {"propext", "Classical.choice", "Quot.sound"}
    for entry in entries:
        if any(a.strip() not in standard for a in entry.split(",") if a.strip()):
            raise ValueError("nonstandard axiom dependency: " + entry)
    return output


def reproduce(proposal_path: Path | None, interaction: bool) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Building Verso notebook and extracting checked Lean cells...", flush=True)
    run_lake(["build"])
    run_lake(["exe", "notebook", "--extract"])
    (OUT / "proof-audit.txt").write_text(audit())
    run_lake(["env", "lean", "--run", "_out/Research.lean", "_out/run/design.json"], 120)
    family = read_family(OUT / "design.json")
    first = measure(family[0], SEED, 1, interaction)
    initial = analyze(first)
    proposer = ReplayProposer(proposal_path) if proposal_path else ResidualProposer()
    proposal = proposer.propose(initial)
    validate_proposal(proposal, initial, family)
    observations = first
    for index, shift in enumerate(proposal.shifts, start=2):
        observations += measure(family[shift], SEED + index, index, interaction)
    final = analyze(observations)
    write_json("observations.json", [asdict(o) for o in observations])
    write_json("summary.json", {"initial": asdict(initial), "proposal": asdict(proposal),
                               "final": asdict(final)})
    (OUT / "report.txt").write_text(render_report(initial, final, proposal))
    outputs = ("design.json", "observations.json", "summary.json", "report.txt", "proof-audit.txt")
    write_json("manifest.json", {
        "schema": "lean-research-run/v1", "seed": SEED, "provider": proposal.provider,
        "measurement_provider": "synthetic-gaussian/v1", "interaction_fixture": interaction,
        "python": platform.python_version(), "lean": run_lake(["env", "lean", "--version"]).strip(),
        "source_sha256": source_hashes(),
        "extracted_source_sha256": file_digest(ROOT / "_out/Research.lean"),
        "artifact_sha256": {name: file_digest(OUT / name) for name in outputs},
        "proof_scope": list(THEOREMS),
        "assumptions": ["additive row/column/treatment model", "iid Gaussian errors",
                        "stable nuisance levels across squares", "no drift or carryover"],
        "proof_empirical_boundary": "Kernel claims do not certify measurements or statistical assumptions."
    })
    verify()
    run_lake(["exe", "notebook"], 120)
    print(render_report(initial, final, proposal))
    print("Notebook: _out/html-single/index.html; provenance: _out/run/manifest.json")


def verify() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text())
    if manifest["source_sha256"] != source_hashes():
        raise ValueError("stale run: source changed; reproduce before rendering")
    if manifest["extracted_source_sha256"] != file_digest(ROOT / "_out/Research.lean"):
        raise ValueError("stale or edited extracted source")
    for name, expected in manifest["artifact_sha256"].items():
        if file_digest(OUT / name) != expected:
            raise ValueError("stale or edited artifact: " + name)
    family = read_family(OUT / "design.json")
    raw = json.loads((OUT / "observations.json").read_text())
    observations = tuple(Observation(**o) for o in raw)
    first = tuple(o for o in observations if o.round == 1)
    initial, final = analyze(first), analyze(observations)
    summary = json.loads((OUT / "summary.json").read_text())
    # A replay provider is preserved; it is not silently relabeled as deterministic inference.
    from harness import Proposal
    proposal_raw = summary["proposal"]
    proposal = Proposal(**{**proposal_raw, "shifts": tuple(proposal_raw["shifts"])})
    validate_proposal(proposal, initial, family)
    actual_plan = tuple(observations[i].shift for i in range(16, len(observations), 16))
    if actual_plan != proposal.shifts:
        raise ValueError("observations do not execute the validated proposal")
    if canonical(summary) != canonical({"initial": asdict(initial), "proposal": asdict(proposal),
                                        "final": asdict(final)}):
        raise ValueError("analysis does not match current observations")
    if (OUT / "report.txt").read_text() != render_report(initial, final, proposal):
        raise ValueError("report does not match current analysis")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="reject stale or changed run artifacts")
    parser.add_argument("--proposal", type=Path, help="replay a bounded, observation-linked JSON proposal")
    parser.add_argument("--additive-control", action="store_true", help="run a no-interaction control fixture")
    args = parser.parse_args()
    if args.verify_only:
        verify()
        print("Source, artifacts, observations, analysis, and proposal verified.")
    else:
        reproduce(args.proposal, not args.additive_control)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
