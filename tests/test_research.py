"""Meaningful trust-boundary and numerical mutation tests; run after reproduction."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from harness import (Cell, Design, Observation, ResidualProposer, analyze, canonical, read_family,
                     validate_proposal)
from reproduce import OUT, run_lake, verify
from simulator import measure


class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.family = read_family(OUT / "design.json")

    def test_design_balance_mutation_rejected(self) -> None:
        design = self.family[0]
        cells = list(design.cells)
        cells[0] = replace(cells[0], treatment=1)
        with self.assertRaisesRegex(ValueError, "balance"):
            Design(0, tuple(cells)).validate()

    def test_other_balanced_family_rejected(self) -> None:
        design = self.family[0]
        renamed = tuple(replace(c, treatment=(3 - c.treatment)) for c in design.cells)
        with self.assertRaisesRegex(ValueError, "outside"):
            Design(0, renamed).validate()

    def test_full_followup_coverage(self) -> None:
        cells = Counter((c.row, c.column, c.treatment)
                        for d in self.family.values() for c in d.cells)
        self.assertEqual(len(cells), 64)
        self.assertEqual(set(cells.values()), {1})

    def test_additive_exact_contrasts_and_residuals(self) -> None:
        observations = tuple(Observation(1, 0, i, c.row, c.column, c.treatment,
                                        10.0 + 7 * c.row - 4 * c.column + 2 * c.treatment)
                             for i, c in enumerate(self.family[0].cells))
        result = analyze(observations)
        self.assertAlmostEqual(result.residual_rms, 0.0, places=12)
        self.assertEqual([c.estimate for c in result.contrasts], [2.0, 4.0, 6.0])
        self.assertEqual(result.residual_df, 6)

    def test_interaction_drives_observation_only_followup(self) -> None:
        initial = analyze(measure(self.family[0], 20260930, 1))
        proposal = ResidualProposer().propose(initial)
        validate_proposal(proposal, initial, self.family)
        self.assertEqual(proposal.shifts, (1, 2, 3))
        observations = measure(self.family[0], 20260930, 1)
        for i, shift in enumerate(proposal.shifts, 2):
            observations += measure(self.family[shift], 20260930 + i, i)
        result = analyze(observations)
        self.assertIsNotNone(result.row_contrasts)
        assert result.row_contrasts is not None
        for contrast in result.row_contrasts[:3]:
            self.assertAlmostEqual(contrast, 3.0, delta=0.7)
        self.assertAlmostEqual(result.row_contrasts[3], 11.0, delta=0.7)
        self.assertEqual(result.count, 64)
        self.assertEqual(result.residual_df, 54)

    def test_changed_measurement_changes_decision_and_invalidates_proposal(self) -> None:
        control = measure(self.family[0], 20260930, 1, interaction=False)
        before = analyze(control)
        original = ResidualProposer().propose(before)
        self.assertEqual(original.action, "replicate")
        changed = (replace(control[0], response=control[0].response + 20), *control[1:])
        after = analyze(changed)
        self.assertNotEqual(before.observation_hash, after.observation_hash)
        self.assertEqual(ResidualProposer().propose(after).action, "complete_coverage")
        with self.assertRaisesRegex(ValueError, "stale"):
            validate_proposal(original, after, self.family)

    def test_seed_replay(self) -> None:
        self.assertEqual(measure(self.family[2], 41, 1), measure(self.family[2], 41, 1))

    def test_edited_observations_cannot_keep_cached_analysis(self) -> None:
        path = OUT / "observations.json"
        saved = path.read_bytes()
        try:
            records = json.loads(saved)
            records[0]["response"] += 1.0
            path.write_bytes(canonical(records))
            with self.assertRaisesRegex(ValueError, "edited artifact"):
                verify()
        finally:
            path.write_bytes(saved)
        verify()

    def test_missing_observation_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "sixteen"):
            analyze(measure(self.family[0], 41, 1)[:-1])

    def test_lean_balance_mutation_fails_in_kernel(self) -> None:
        source = (ROOT / "_out/Research.lean").read_text()
        changed = source.replace("row.val + col.val + shift.val", "row.val + shift.val")
        self.assertNotEqual(changed, source)
        with tempfile.TemporaryDirectory(dir=ROOT / "_out") as directory:
            path = Path(directory) / "Broken.lean"
            path.write_text(changed)
            with self.assertRaisesRegex(RuntimeError, "failed"):
                run_lake(["env", "lean", str(path)], 120)


if __name__ == "__main__":
    unittest.main()
