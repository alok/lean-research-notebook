# Build the notebook by hand

This guide is a manual reconstruction exercise. Read the rendered notebook alongside its source,
then build a small version yourself. The interesting part is how evidence travels through the
system: an authored question acquires a checked design, an executable experiment, recorded
observations, and a revised question. Each transition has a different kind of justification.

## 1. Understand the system we are extending

Lean is both a programming language and a proof assistant. A proposition is a type, and a proof is
a term of that type. Lean's elaborator turns notation, tactics, implicit arguments, and convenient
source syntax into core terms. Its kernel checks those terms against their types. The compiler
then erases proof fields when building executable programs.

Verso is a document language implemented inside Lean. A `#doc (Manual)` command parses markup,
elaborates extensions, and constructs a typed document tree. An ordinary `lean` code block uses the
same elaboration environment as the document. It can add declarations and retain highlighting,
types, diagnostics, and tactic proof states. The generated browser hovers display those recorded
annotations. They do not execute a new Lean session in the browser.

This lets us extend the document language without replacing its parser, editor support, proof
checking, or renderer. The official textbook example already demonstrates the main technique:
wrap a checked code block in an extension containing its source, then traverse the document to
extract marked cells. We adapt that licensed implementation and add a numerical evidence block.

Keep three mechanisms distinct as you work:

1. **Elaboration** creates the document and checks authored Lean declarations.
2. **Extraction and execution** turn selected cells into a standalone program and run fixed tools.
3. **Rendering** turns the document and validated numerical evidence into HTML.

That separation makes the result reproducible and keeps a browser report from pretending to be a
live notebook kernel. It also makes stale-result handling an explicit part of the design.

## 2. Set up the smallest Lean/Verso package

Start with `lean-toolchain`, `lakefile.lean`, and a single document. Pin a Lean release and a matching
Verso release commit. Verso follows Lean releases; arbitrary combinations can fail because Lean's
elaboration APIs evolve. Commit the generated `lake-manifest.json` to pin transitive dependencies.

The package has a `ResearchNotebook` library and a `notebook` executable rooted at `NotebookMain`.
The library imports `VersoManual`, opens `Verso.Genre.Manual`, and contains the document. The
executable imports the document and calls `manualMain`. At this stage, a one-paragraph notebook
and an ordinary checked Lean cell are enough. Build before adding scientific logic.

On machines where global cache directories are unwritable, set `LAKE_CACHE_DIR` to a writable
project-local path. Our runner uses `_out/lake-cache` and disables remote artifact downloads. This
is a build-environment choice, not a change to proof trust. Dependency fetching still uses the
public Git repositories recorded in the manifest.

## 3. Implement the saved Lean cell

Read `ResearchNotebook/Meta/Cells.lean`. The extension payload is intentionally small: one string
containing the authored cell source. Its HTML and TeX handlers delegate rendering of child blocks
to Verso. The expander calls `InlineLean.lean` before creating the wrapper, so source extraction
never replaces checking.

The important shape is:

```lean
@[code_block labLean]
def labLean : CodeBlockExpanderOf InlineLean.LeanBlockConfig
  | args, code => do
    let checked ← InlineLean.lean args code
    ``(Block.other (Block.labLean $(quote code.getString)) #[$checked])
```

The quotation constructs Lean syntax for the document term. The antiquotation inserts the already
expanded Lean block. `quote` turns the source string into a Lean literal. The block extension's
`data` field serializes that string into the document tree.

Write one `labLean` cell with a definition and a second cell using that definition. Build the
document, then inspect the highlighted output. This checks the real dependency behavior between
cells. It also reveals a subtle point: declarations inside cells share the document's Lean
environment. Put scientific declarations in a namespace, and avoid a root-level `main` that would
collide with the renderer's executable entry point.

## 4. Extract from the elaborated document

Read `cellSources` in `NotebookMain.lean`. The document has nested parts and blocks: ordinary
paragraphs, code, quotations, lists, description lists, and extension blocks. A correct extraction
pass visits all of them. Looking for Markdown fences with a regular expression would lose that
structure and could disagree with what Verso actually checked.

For our wrapper, collect its source string. For other blocks, recursively visit their children.
Join the marked sources in document order and prepend `import Lean`. Append a root `main`
delegating to `Lab.exportMain`. The result is `_out/Research.lean`, a standalone program that can
run without loading Verso's document machinery.

The extraction target is a fixed local path. We deliberately avoid embedding the author's absolute
file name in a public artifact. A larger notebook system could use explicit module IDs and an
acyclic dependency graph; this prototype has one ordered source stream.

Now run `lake exe notebook --extract`, inspect `_out/Research.lean`, and compile it independently.
That extra compilation catches dependencies accidentally available through the document's imports
but absent from the standalone source. It is stronger than merely showing a highlighted code block.

## 5. Define a finite experimental design

The four-level type is `Fin 4`. A value contains a natural number and a proof that it is less than
four. The treatment function computes `(row + column + shift) % 4`, using `Nat.mod_lt` to justify
the result's bound. A shift is itself a `Fin 4`, so only four allowed designs exist.

Write row balance as a proposition with both existence and uniqueness: for every row and treatment,
there is a column receiving that treatment, and any other such column equals it. Write the column
property symmetrically. This is a specification of the intended Latin-square property rather than
a Boolean with an ambiguous name.

For the finite family, `decide` can construct checked proofs after unfolding the property. This
works because every quantified index ranges over a small finite type. We use ordinary `decide`,
whose proof term is reduced by Lean's kernel, rather than `native_decide`, which introduces a
different computational trust boundary.

Add three further properties:

- the flattened assignments contain each treatment four times;
- the four shifts together contain each row/column/treatment combination exactly once;
- permuting a list of assignments preserves each treatment's count.

The first two are finite computations. The third reuses Lean's existing `List.Perm.count_eq`
theorem. Search the ecosystem before reimplementing facts like this. The property about a
permutation does not prove that Python's particular shuffle is correct; the Python boundary also
compares the before/after cell multisets.

For a useful failure exercise, change the treatment function to ignore column. Recompile the
extracted module. The row-balance theorem should fail. This is the negative mutation tested in CI.

## 6. Connect a symbolic model to actual cells

Balance alone says nothing about observed responses. Introduce an additive integer model with a
baseline, four row effects, four column effects, and a treatment effect. Use `treatmentTotal` to
filter the actual shift-0 cells belonging to a treatment and sum their modeled responses.

The `additive_contrast` theorem compares treatment 3 with treatment 0. Lean reduces the finite
selection to explicit sums, then `omega` proves that the nuisance terms cancel. The statement
allows arbitrary integer nuisance values. It does not assume they are small or zero.

Read the `change` step carefully. It is not an unchecked replacement of the goal: Lean must verify
that the displayed finite sum is definitionally equal to the computation in `treatmentTotal`.
Then the arithmetic proof establishes that the difference is four times the treatment difference.

We keep integer arithmetic because it is a small exact symbolic core. Moving to real-valued
statistical models would require a larger formal library and additional assumptions about random
variables and estimation. The Python analysis below remains a numerical calculation, with that
limitation stated explicitly.

## 7. Export proof-carrying designs

`CertifiedDesign` stores a shift and proofs of both balance properties. The `certified` constructor
uses the family theorems to produce such a value for any allowed shift. The exporter reads its
shift and computes the sixteen cell assignments as JSON.

Why carry proofs if compilation erases them? The constructor prevents an unchecked design from
entering the exporter through the intended Lean API. It ties the executable definition to a checked
specification. The resulting JSON still is not a proof certificate. To trust it, recompile the
source, audit the relevant theorem dependencies, and run the exporter yourself.

The audit rejects `sorry`, custom `axiom`, and `native_decide` constructs in extracted cells and
uses `#print axioms` to inspect transitive proof dependencies. Standard Lean logical axioms are
allowlisted; additional axioms fail the run. A source text scan alone would be insufficient because
an imported declaration could conceal an unwanted dependency.

Python defensively validates the exported cells too. Those runtime checks protect the interface
from stale or edited data; they do not supersede the Lean proof or certify an arbitrary Latin square.
The allowed family remains exactly the one computed by the checked exporter.

## 8. Implement a numerical tool with a narrow interface

Use immutable dataclasses for cells, designs, observations, numerical analysis, and proposals.
Keep the measurement provider in a separate module. It receives a validated design and returns
observations; the proposer receives only the analysis. This API makes it clear where hidden
ground truth belongs and prevents accidental use of it in the default decision rule.

Our synthetic provider has fixed nuisance and treatment effects, independent seeded Gaussian
noise, and an optional row/treatment interaction. It randomizes trial order and records the actual
order. Each response is rounded to nine decimal places for stable artifacts. Its parameters are
public code for transparency, but they are not passed to `Proposer.propose`.

The additive analysis uses balanced-design mean formulas rather than a general matrix package.
Compute the grand mean and row, column, and treatment means. For each observation, predict
`row mean + column mean + treatment mean − 2 × grand mean`. Residuals are observation minus fit.
Sum squared residuals and divide by `N − 10` for the conditional residual variance estimate.

Treatment contrasts are treatment means minus the control mean. For each contrast, the standard
error is `sqrt(2 × MSE / count per treatment)`. The 95% interval uses the appropriate Student-t
quantile. This calculation requires the additive model and iid Gaussian errors. In the interaction
fixture those assumptions are challenged, so we label intervals as diagnostic only.

Test an exactly additive noiseless dataset with large nuisance effects. The residuals should be
zero and known treatment differences should be recovered exactly. This checks both cancellation
and the numerical implementation independently of the stochastic example.

## 9. Make the second round depend on evidence

The `Proposer` protocol accepts an `Analysis`, not the simulator or a general execution context.
The default implementation is explicitly called `deterministic-residual-rule/v1`. There is no LLM,
inference claim, or guessed Quine endpoint.

If residual RMS exceeds 0.9, propose completing the family with shifts 1–3. Otherwise, propose
replicating shift 0. Return the evidence hash, reason, revised question, provider, action, and shifts.
The threshold is a demonstration heuristic, not an optimal design method or a significance test.

Validate the proposal before executing anything: match its initial-observation hash, require one of
the two exact plans, validate all designs, and enforce the sixty-four-sample total budget. The
proposal contains data only. Do not execute commands supplied by a human or future model adapter.

When all four shifts have run, every row/treatment group contains all four columns. Comparing
treatment 3 with control within a row then uses complete column coverage. The toy interaction
case produces a much larger contrast in row 3. The next question asks whether that row-dependent
pattern replicates under independent blocks. It does not claim a discovered mechanism.

On the low-residual replication path, column coverage within each row/treatment group remains
incomplete. Suppress row-specific interpretation there. This is a concrete example of allowing
the experimental design to limit what the report says.

## 10. Record provenance and reject stale conclusions

Serialize JSON canonically and hash the bytes. Record hashes of the source, dependency lock,
toolchain, extracted module, designs, measurements, analysis, proposal, report, and proof audit.
Record the seed, versions, provider, assumptions, and proof scope. Avoid private machine paths.

Verification should do more than rehash a summary. Recompute analysis from the recorded
observations, validate their assignment tables and rounds, check that executed shifts match the
proposal, and regenerate the text report. A modified response cannot retain its old proposal
because the initial observation hash changes.

The `experiment` block loads report text when rendering, instead of embedding it while compiling
the document. The notebook executable calls the verifier first. This avoids a common notebook
failure: old displayed results surviving a changed source or input file. The hashes are local
consistency checks, not cryptographic signatures against a malicious author.

Try the mutation tests by hand: break one treatment assignment; edit a recorded response; remove
one observation; reuse a proposal after a decision-relevant change. Each should fail at the
corresponding boundary. Also change an additive control response substantially and confirm that
the rule selects the complete-coverage plan. Invalidation should affect decisions, not just labels.

## 11. Render and publish a reviewable result

Regenerate the default fixture, run the mutation tests, verify provenance again, and serve the
generated HTML over localhost. Verso's proof-state hovers load supporting JSON, so use a server
instead of opening the file directly. Read the question, checked design, symbolic claim, numerical
report, revised question, and limitations in one document.

The CI workflow repeats these steps from public pinned dependencies and uploads generated evidence.
It runs with read-only repository permission and no model credentials. A successful local run and
a successful CI run on the published SHA are separate pieces of evidence; check both.

Possible next extensions include a persistent Lean REPL, a custom research genre with typed evidence
nodes, SciLean numerical functions, literature references with provenance, or real measurement
adapters. Add one only after choosing a concrete research question and clarifying its trust boundary.
The existing extension is intentionally small enough to understand and rebuild by hand.
