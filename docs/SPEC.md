# Prototype specification

Build a Lean-native scientific notebook that extends Verso's Manual genre. A document combines a
research question, explicit assumptions, kernel-checked design claims, executable numerical tools,
recorded measurements, and a revised question. The first example is synthetic and public.

The inspiration is the question/design/measurement/revision loop described in Microsoft's Quine
announcement of 2026-09-29. This project implements a small harness; it has no Quine integration,
biology world model, trained inference model, or medical claims.

## End-to-end example

1. Propose a four-treatment cyclic Latin square with row and column nuisance factors.
2. Lean proves row/column balance, treatment counts, and additive contrast cancellation.
3. Extract the document's checked Lean cells into a standalone Lean exporter.
4. Export the certified design, then execute a seeded synthetic experiment in Python's standard
   library. Fit an additive blocked model and report residuals and conditional uncertainty.
5. A deterministic proposer sees only observations and diagnostics. If residuals are large, propose
   three further allowed cyclic squares that complete row/column/treatment coverage.
6. Validate every follow-up design against the Lean export, execute, and compare row-specific
   contrasts. Record an observation-driven revised question without turning it into a theorem.
7. Render the evidence in the same Verso notebook and save a provenance manifest.

## Extension and trust boundaries

- Adapt the Apache-2.0 Verso release's `DemoTextbook` saved-code block and extraction pattern.
- Keep Verso's elaboration, highlighted Lean, proof-state display, navigation, and HTML generation.
- Add a `labLean` block and an `experiment` report block; do not build a separate notebook UI.
- Use ordinary kernel-checked `decide` and arithmetic proofs; no `sorry`, custom axioms, or
  `native_decide` in design claims.
- Clearly distinguish kernel theorems, numerical calculations, synthetic observations, assumptions,
  and unverified proposals. Proof of balance is not proof of efficacy or statistical independence.
- Hash source, exported designs, configuration, measurements, and reports. Recompute derived results
  when observations change; reject stale reports and designs outside the certified family.
- Execute only fixed local Lean/Python tools with bounded timeouts. This is not a code sandbox.
- No API key, paid model, GPU, private data, copied private project source, or shared Mac UI.

## Acceptance

Fresh-clone installation instructions, pinned Lean and Verso, reproducible numerical results,
mutation tests for bad balance and stale/changed observations, kernel axiom audit, rendered report,
CI on the published commit, architecture/limitations and a manual implementation guide.
