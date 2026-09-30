import VersoManual
import ResearchNotebook.Meta.Cells

open Verso.Genre Manual
open Verso.Genre.Manual.InlineLean
open ResearchNotebook

set_option verso.code.warnLineLength 100

#doc (Manual) "A checked research loop" =>

%%%
authors := ["Alok Singh"]
%%%

This notebook extends Verso. Edit its Lean source, run the local harness, and regenerate the
document. The loop is question, checked design, execution, observation, revision, and follow-up.
Hover over Lean code to inspect types and proof states. Execution happens through the local CLI.

# Question and assumptions
%%%
tag := "question"
%%%

Which of four synthetic treatments raises a numerical response after accounting for row and
column effects? The initial working model is additive: baseline plus row plus column plus treatment
plus independent Gaussian noise. The noise and no-interaction conditions are assumptions, not
theorems. The simulator deliberately tests what happens when the additive assumption fails.

A Latin square uses sixteen observations to balance two four-level nuisance factors. Each treatment
appears once per row and once per column. This property does not establish causality or efficacy.
The [NIST design reference](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3321.htm)
explains the corresponding no-interaction assumption.

# Kernel-checked design
%%%
tag := "design"
%%%

These are actual Lean declarations elaborated by Verso. The custom cell also preserves source for
the standalone executable. The finite proofs use kernel-reduced decision procedures.

```labLean
namespace Lab

open Lean

abbrev Level := Fin 4

def treatment (shift row col : Level) : Level :=
  ⟨(row.val + col.val + shift.val) % 4, Nat.mod_lt _ (by decide)⟩

def RowBalanced (s : Level) : Prop :=
  ∀ r t : Level, ∃ c : Level, treatment s r c = t ∧
    ∀ c' : Level, treatment s r c' = t → c' = c

def ColumnBalanced (s : Level) : Prop :=
  ∀ c t : Level, ∃ r : Level, treatment s r c = t ∧
    ∀ r' : Level, treatment s r' c = t → r' = r

theorem all_rows_balanced : ∀ s : Level, RowBalanced s := by
  unfold RowBalanced
  decide
theorem all_columns_balanced : ∀ s : Level, ColumnBalanced s := by
  unfold ColumnBalanced
  decide

def levels : List Level := [0, 1, 2, 3]

def assignments (s : Level) : List Level :=
  levels.flatMap (fun r ↦ levels.map (fun c ↦ treatment s r c))

theorem four_per_treatment :
    ∀ s t : Level, (assignments s).count t = 4 := by decide

theorem complete_coverage :
    ∀ r c t : Level, ∃ s : Level, treatment s r c = t ∧
      ∀ s' : Level, treatment s' r c = t → s' = s := by decide

theorem order_preserves_counts (xs ys : List Level) (h : xs.Perm ys) (t : Level) :
    xs.count t = ys.count t := h.count_eq t
```

All four allowed cyclic shifts are balanced. Together they cover every row/column/treatment
combination exactly once. Randomizing execution order preserves treatment counts when it is a
permutation; the Python runner separately checks that its shuffle preserves the actual cells.

# A symbolic model claim
%%%
tag := "model"
%%%

Under an additive integer model, summing a treatment's four observations cancels the row and
column contributions in a contrast. This theorem states its assumption in its definition.
It does not include noise, interactions, real arithmetic, or a probability model.

```labLean
def additiveTotal (baseline : Int) (rows cols : Int × Int × Int × Int) (effect : Int) : Int :=
  4 * baseline + rows.1 + rows.2.1 + rows.2.2.1 + rows.2.2.2 +
    cols.1 + cols.2.1 + cols.2.2.1 + cols.2.2.2 + 4 * effect

def levelEffect (values : Int × Int × Int × Int) (level : Level) : Int :=
  match level.val with
  | 0 => values.1
  | 1 => values.2.1
  | 2 => values.2.2.1
  | _ => values.2.2.2

def treatmentTotal (t : Level) (baseline : Int) (rows cols : Int × Int × Int × Int)
    (effect : Int) : Int :=
  (levels.flatMap fun r ↦ levels.filterMap fun c ↦
    if treatment 0 r c == t then
      some (baseline + levelEffect rows r + levelEffect cols c + effect)
    else none).foldl (· + ·) 0

theorem additive_contrast (baseline : Int) (rows cols : Int × Int × Int × Int)
    (a b : Int) :
    treatmentTotal 3 baseline rows cols a - treatmentTotal 0 baseline rows cols b =
      4 * (a - b) := by
  change
    (0 + (baseline + rows.1 + cols.2.2.2 + a) +
      (baseline + rows.2.1 + cols.2.2.1 + a) +
      (baseline + rows.2.2.1 + cols.2.1 + a) +
      (baseline + rows.2.2.2 + cols.1 + a)) -
    (0 + (baseline + rows.1 + cols.1 + b) +
      (baseline + rows.2.1 + cols.2.2.2 + b) +
      (baseline + rows.2.2.1 + cols.2.2.1 + b) +
      (baseline + rows.2.2.2 + cols.2.1 + b)) = 4 * (a - b)
  omega
```

The exporter packages designs with proof fields. Python receives computed assignments, not a
Boolean assertion that a design is proved. The harness compiles and audits the extracted module
before consuming that export, then rejects designs outside this exact certified family.

```labLean
structure CertifiedDesign where
  shift : Level
  rowsBalanced : RowBalanced shift
  columnsBalanced : ColumnBalanced shift

def certified (s : Level) : CertifiedDesign :=
  ⟨s, all_rows_balanced s, all_columns_balanced s⟩

def exportDesign (d : CertifiedDesign) : Lean.Json :=
  Lean.Json.mkObj [
    ("shift", toJson d.shift.val),
    ("cells", toJson <| levels.flatMap fun r ↦ levels.map fun c ↦
      Lean.Json.mkObj [("row", toJson r.val), ("column", toJson c.val),
        ("treatment", toJson (treatment d.shift r c).val)])]

def designExport : Lean.Json := Lean.Json.mkObj [
  ("schema", toJson "lean-latin-family/v1"),
  ("levels", toJson (4 : Nat)),
  ("designs", toJson (levels.map (fun s ↦ exportDesign (certified s))))]

def exportMain (args : List String) : IO Unit := do
  let [path] := args | throw <| IO.userError "Expected one output JSON path"
  IO.FS.writeFile path (designExport.pretty ++ "\n")

end Lab
```

# Axiom audit
%%%
tag := "audit"
%%%

The harness inspects the extracted theorems' dependencies and rejects additional axioms.
The foundational axioms listed below are part of Lean's standard logic; they do not establish
anything about the synthetic measurements.

```lean (name := axiomAudit)
#print axioms Lab.all_rows_balanced
#print axioms Lab.all_columns_balanced
#print axioms Lab.four_per_treatment
#print axioms Lab.complete_coverage
#print axioms Lab.order_preserves_counts
#print axioms Lab.additive_contrast
```

# Execute, observe, revise
%%%
tag := "results"
%%%

The numerical tool fits a blocked additive model. Its conditional 95% intervals assume that
model and independent Gaussian errors; residual diagnostics can challenge the assumptions.
The proposer is an explicitly deterministic rule. It sees recorded observations and computed
diagnostics, not simulator parameters. It either repeats the initial design or proposes three
additional certified shifts to investigate row-dependent effects. Every proposal is validated
before execution. These stages run with a fixed seed and a budget of at most sixty-four samples.

```experiment
```

The report is loaded at rendering time. The reproducibility command validates its input hashes
before rendering. A changed measurement requires new analysis and may lead to a different
proposal. An edited report without valid provenance is rejected by the verification command.

# Meaning and limits
%%%
tag := "limits"
%%%

Kernel theorems certify finite balance, coverage, preservation of counts, and an integer additive
identity. Numerical calculations estimate contrasts. Synthetic observations test a toy data
generator. Assumptions govern interpretation. Proposals remain unverified until tested.

This is an extension of the Verso Manual genre, with reproducible local CLI execution. It is
not a live browser kernel or a statistical proof assistant. Running Lean or Python uses your
machine's privileges; the fixed runner is not a sandbox. There is no model inference or API.

The [Quine announcement](https://www.microsoft.com/en-us/research/blog/introducing-quine-an-ai-research-system-designed-for-the-complexity-of-biology/)
motivates a loop connecting questions, tools, and experimental feedback. This project has no
access to Quine or its biology world model. [NOVA](https://github.com/microsoft/nova-agent) is a
public scientific-tool orchestration precedent, not a Quine SDK. The architecture and manual
implementation guide describe where a future human or model proposer could attach.
