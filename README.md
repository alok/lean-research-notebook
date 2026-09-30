# Lean Research Notebook

A small scientific notebook built as an **actual Verso Manual extension**. Checked Lean cells
become an executable experimental design; a local Python harness produces synthetic measurements,
diagnostics, a revised question, and a validated second experiment. Everything is inspectable in
the generated Verso document.

Inspired by the research harness described in [Microsoft's Quine announcement](https://www.microsoft.com/en-us/research/blog/introducing-quine-an-ai-research-system-designed-for-the-complexity-of-biology/).
This project has no Quine integration, biology world model, trained AI, or biological data.

## Run locally

Install [elan](https://github.com/leanprover/elan), Git, Python 3.11 or newer, and a C toolchain
(`build-essential` on Ubuntu, Xcode command-line tools on macOS). Lean 4.34.0 is pinned in
`lean-toolchain`; Verso and its transitive dependencies are pinned in `lake-manifest.json`.

```sh
git clone https://github.com/alok/lean-research-notebook.git
cd lean-research-notebook
lake update
python3 scripts/reproduce.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8765 --bind 127.0.0.1 --directory _out/html-single
```

Open **http://127.0.0.1:8765/**. The first build compiles Verso; subsequent runs are incremental.
The harness applies a ten-minute build limit and two-minute limits to proof audits/rendering.
It places Lake's artifact cache below `_out/` and disables remote cache downloads.
No Python packages, API keys, paid services, or GPU are required.

## What the example does

The initial question compares four treatments using a 4×4 Latin square with row and column
nuisance effects. Lean checks balance, four observations per treatment, all allowed cyclic
shifts, complete combined coverage, and count preservation under reordered trials. It also proves
that an integer additive contrast computed from the initial design cancels nuisance effects.

Python executes sixteen seeded synthetic observations and fits an additive blocked model.
Residuals challenge that model. An **observation-only deterministic rule** asks whether the effect
depends on row conditions and chooses three more certified squares. Forty-eight further observations
complete row/column/treatment coverage, enabling row-specific comparisons. The notebook records the
next question as an unverified proposal. It does not turn a numerical result into a theorem.

```sh
# Reject stale source, measurements, analysis, proposals, or rendered report inputs.
python3 scripts/reproduce.py --verify-only

# Compare against the separate no-interaction control fixture.
python3 scripts/reproduce.py --additive-control

# Restore the default interaction example.
python3 scripts/reproduce.py
```

## Evidence and artifacts

| Artifact | Meaning |
| --- | --- |
| `ResearchNotebook.lean` | Authored Verso notebook, including actual proof and exporter cells |
| `_out/Research.lean` | Standalone module extracted by the custom `labLean` block |
| `_out/run/design.json` | Assignments computed from proof-carrying Lean designs |
| `_out/run/proof-audit.txt` | Transitive axiom audit of the six advertised theorems |
| `_out/run/observations.json` | All synthetic measurements and execution order |
| `_out/run/summary.json` | Numerical analysis and the observation-linked proposal |
| `_out/run/manifest.json` | Source/toolchain/provider/seed/artifact hashes and assumptions |
| `_out/html-single/index.html` | Generated notebook with Verso's checked code and hovers |

The [checked-in example report](examples/default-report.txt) is a compact snapshot for readers.
The reproducibility command generates the complete provenance record. GitHub Actions tests the
published source and uploads the notebook and run artifacts; no public web hosting is configured.

## Extend it

Read the [architecture](docs/ARCHITECTURE.md), [manual implementation guide](docs/IMPLEMENTATION_GUIDE.md),
[limitations](docs/LIMITATIONS.md), and [source/technology review](docs/SOURCES.md).
The guide explains the surrounding Lean/Verso machinery and walks through implementing the system
by hand. The `Proposer` protocol accepts a numerical evidence view and returns a bounded data plan.
For a human or external proposer, save the same fields as `_out/run/summary.json`'s `proposal` object
to a separate JSON file, preserve its `evidence_hash`, and run:

```sh
python3 scripts/reproduce.py --proposal proposal.json
```

Only the two documented plans are accepted: repeat shift 0, or complete coverage with shifts 1–3.
The provider field identifies who proposed it. There is no invented inference endpoint and no
execution of proposal-supplied commands. Running this trusted Lean/Python project uses local machine
privileges; **the runner is not a sandbox**.

Apache-2.0. The saved-cell and traversal pattern is adapted from the public Verso release's
Apache-licensed textbook example; original notices are retained in [NOTICE](NOTICE).
