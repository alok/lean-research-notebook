# Primary sources and technology review

Reviewed 2026-09-30. The following are links and design precedents, not model integrations.

- [Quine announcement, 2026-09-29](https://www.microsoft.com/en-us/research/blog/introducing-quine-an-ai-research-system-designed-for-the-complexity-of-biology/):
  distinguishes a biology world model from an interactive harness, with experimental feedback guiding
  new questions. This prototype implements a small local harness loop only.
- [Official Quine overview](https://microsoft.github.io/quine/): describes the research program and
  phased access through Fellows and collaborations. The reviewed public pages do not expose a
  reusable Quine API, SDK, model weights, or harness source.
- [Quine research journey](https://microsoft.github.io/quine/blog/our-research-journey/index.html):
  links work on scientific-tool orchestration, confounding, evaluation, and experimental feedback.
- [NOVA paper](https://proceedings.mlr.press/v297/vaidya26a.html) and
  [public NOVA source](https://github.com/microsoft/nova-agent): an MIT-licensed CodeAct/smolagents
  tool orchestration precedent. Its `SimpleCodeAgent` separates model configuration, tool selection,
  final-answer checks, execution settings, and a step budget. We inspected those interfaces and
  replaced model-driven code execution with a bounded typed data proposal. No NOVA source or
  pathology/GPU dependencies are incorporated. NOVA is not a public Quine SDK.
- [Verso](https://github.com/leanprover/verso) and
  [extension documentation](https://verso.lean-lang.org/doc/latest/Extensions/): the authoring foundation.
  The prototype extends code blocks in the existing Manual genre and delegates Lean elaboration
  and rendering to Verso. Verso is Apache-2.0.
- [Official textbook template](https://github.com/leanprover/verso-templates/tree/main/textbook):
  demonstrates saved Lean cells and an extraction pass. To preserve explicit licensing, this project
  adapts the corresponding Apache-licensed
  [DemoTextbook source in Verso v4.34.0](https://github.com/leanprover/verso/tree/v4.34.0/test-projects/textbook)
  rather than copying unlicensed template files. Attribution is in `NOTICE` and source headers.
- [NIST: Latin square and related designs](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3321.htm):
  row/column nuisance blocking, additive model estimates, and the no-interaction assumption.
  These motivate the numerical baseline and the interaction counterexample.

## Local ecosystem inspection

Existing local Verso and Lean checkouts and the user's general project instructions were inspected
to identify the established stack. Their source was not copied. The public upstream Verso release
and its licensed example supplied the extension baseline. No private project content, credentials,
or personal data is included in this repository.

## Deliberately deferred technologies

- [Lean REPL](https://github.com/leanprover-community/repl): useful for a future persistent-session
  kernel; separate lifecycle, state, and recovery work is unnecessary for the reproducible CLI slice.
- [ProofWidgets](https://github.com/leanprover-community/ProofWidgets4): possible typed interactive
  views, deferred until there is a concrete editing need beyond Verso hovers and reports.
- [SciLean](https://github.com/lecopivo/SciLean): a potential formal/numerical extension. The initial
  experiment uses integer proofs and Python's standard library to keep the trust boundary small.
- [Verso Blueprint](https://github.com/PatrickMassot/verso-blueprint): relevant to formalization plans;
  the scientific observation/proposal loop has a different immediate need.
