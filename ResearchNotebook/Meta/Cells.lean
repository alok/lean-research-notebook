/-
Copyright (c) 2025 Lean FRO LLC. All rights reserved.
Copyright (c) 2026 Alok Singh.
Released under Apache 2.0 license as described in LICENSE.
Adapted from DemoTextbook/Meta/Lean.lean by David Thrane Christiansen.
Changes: fixed extraction target, research evidence wrapper, runtime report inclusion.
-/
import VersoManual

open Verso.Genre Manual
open Verso.Doc Elab
open Verso.ArgParse
open Lean

namespace ResearchNotebook

block_extension Block.labLean (source : String) where
  data := .str source
  traverse _ _ _ := pure none
  toTeX := some fun _ goB _ _ contents => contents.mapM goB
  toHtml := some fun _ goB _ _ contents => contents.mapM goB

/-- Elaborate a Lean cell with Verso, preserving its source for standalone extraction. -/
@[code_block labLean]
def labLean : CodeBlockExpanderOf InlineLean.LeanBlockConfig
  | args, code => do
    let checked ← InlineLean.lean args code
    ``(Block.other (Block.labLean $(quote code.getString)) #[$checked])

block_extension Block.experiment where
  data := .null
  traverse _ _ _ := pure none
  toTeX := none
  extraCss := [r##"
.experiment-evidence {
  border-left: 4px solid #11756c;
  padding: 1.1rem 1.4rem;
  margin: 2rem 0;
  background: #edf6f3;
  border-radius: 0 8px 8px 0;
  color: #152b27;
}
.experiment-evidence h3 { color: #12665e; margin-top: 0; }
.experiment-report {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 0.85rem;
  line-height: 1.65;
  background: transparent;
  padding: 0;
}
"##]
  toHtml := some fun _ _ _ _ _ => do
    let path : System.FilePath := "_out/run/report.txt"
    let report ← if ← path.pathExists then IO.FS.readFile path
      else pure "No numerical run yet. Run python3 scripts/reproduce.py, then rebuild this report."
    pure <| .tag "section" #[("class", "experiment-evidence")] <|
      .tag "h3" #[] (.text true "Numerical run · synthetic observations · unverified proposals") ++
      .tag "pre" #[("class", "experiment-report")] (.text true report)

/-- Include the current local numerical report at render time, avoiding stale elaboration caches. -/
@[code_block experiment]
def experiment : CodeBlockExpanderOf Unit
  | (), code => do
    unless code.getString.trimAscii.toString.isEmpty do
      throwErrorAt code "The experiment block takes no source; it displays the validated local run."
    ``(Block.other Block.experiment #[])

end ResearchNotebook
