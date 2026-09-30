# Limitations and claim boundaries

| Status | Supported claim | What it does not imply |
| --- | --- | --- |
| Kernel theorem | Four cyclic designs are balanced; combined coverage; permutation counts; integer additive cancellation | Efficacy, causality, physical validity, independence, randomization correctness in Python |
| Numerical calculation | Contrast estimates, residuals, conditional standard errors and intervals | Statistical model truth or Lean-verified floating-point accuracy |
| Synthetic observation | A seeded local generator returned a value | Wet-lab evidence or externally observed biology |
| Assumption | Additivity, iid Gaussian errors, stable nuisance effects, no drift/carryover | A theorem or empirically confirmed condition |
| Unverified proposal | A rule or replay provider proposes a next question/design | An AI discovery, calibrated recommendation, or experimentally established mechanism |

The synthetic interaction case intentionally violates the initial additive model. Nominal confidence
intervals are therefore shown as conditional calculations with a model-challenged label. They are
not valid guarantees of coverage in this fixture. The follow-up reveals a toy row-dependent pattern;
it does not identify the cause of that pattern or supply a biological conclusion.

The integer additive theorem is an exact symbolic illustration. It covers treatment 3 versus 0 in
the initial shift-0 design; the finite balance theorems cover all four shifts. It does not formalize
the numerical least-squares algorithm, floating-point rounding, Gaussian sampling, confidence
interval derivation, estimation after adaptive selection, or the Python implementation. Python
boundary checks and tests complement the formal core but do not become formal proofs.

Allowed shifts preserve the Latin property. They are only a small subset of possible Latin squares.
The example randomizes execution order, not physical treatment allocation or nuisance factors.
There is no physical randomization, independent lab replication, missing-data method, or calibration
study. Completing a 4³ grid removes the initial design's column confounding for row comparisons,
under stable effects; order drift, carryover, and interaction with column could still matter.

The proposer uses a fixed residual threshold and descriptive row-spread threshold. These are explicit
demonstration heuristics, not hypothesis tests or optimal design policies. It cannot inspect the
generator through its typed evidence interface, but this is an API discipline rather than an
operating-system isolation boundary. An external model adapter is deliberately absent.

The notebook is Lean-native authoring and a reproducible local report. Verso hovers are generated
proof-state annotations; they do not provide an interactive browser execution kernel. ProofWidgets,
SciLean, a persistent Lean REPL, model inference, databases, literature retrieval, and real experiment
connectors are possible later additions. None is claimed or required here.

The fixed runner uses subprocess argument lists and time limits. Lean metaprograms and Python code
can still access local files and processes with the user's privileges. Run only source you trust.
The renderer does not accept arbitrary report paths or HTML; report text is escaped.

Reproduction requires the pinned toolchain and public dependencies to be downloaded initially.
The generated report/observations are deterministic for the supported Python standard-library
generator, but toolchain version strings and formatted manifest metadata can vary between Python
minor versions. Tests check the numerical invariants and thresholds, not one platform's manifest
byte sequence. Changing code, seed, data, or assumptions requires a new run.
