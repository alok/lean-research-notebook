/-
Copyright (c) 2024-2025 Lean FRO LLC. All rights reserved.
Copyright (c) 2026 Alok Singh.
Released under Apache 2.0 license as described in LICENSE.
Adapted from DemoTextbookMain.lean by David Thrane Christiansen.
Changes: collect into one standalone module, fixed path, extract-only command.
-/
import ResearchNotebook

open Verso Doc
open Verso.Genre Manual

partial def cellSources : Part Manual → Array String
  | .mk _ _ _ intro parts => intro.flatMap block ++ parts.flatMap cellSources
where
  block : Block Manual → Array String
    | .other ext contents =>
      let own := if ext.name == ``ResearchNotebook.Block.labLean then
        match ext.data with
        | .str source => #[source]
        | _ => #[]
      else #[]
      own ++ contents.flatMap block
    | .concat bs | .blockquote bs => bs.flatMap block
    | .ol _ items | .ul items => items.flatMap (fun item => item.contents.flatMap block)
    | .dl items => items.flatMap (fun item => item.desc.flatMap block)
    | .para .. | .code .. => #[]

def extract : IO Unit := do
  IO.FS.createDirAll "_out"
  let cells := cellSources (%doc ResearchNotebook)
  if cells.isEmpty then throw <| IO.userError "Notebook contains no labLean cells"
  IO.FS.writeFile "_out/Research.lean" <|
    "-- Generated from the Verso notebook. Edit ResearchNotebook.lean, then extract again.\n\
     import Lean\n\n" ++ "\n\n".intercalate cells.toList ++
      "\n\ndef main := Lab.exportMain\n"

def config : RenderConfig where
  emitTeX := false
  emitHtmlSingle := .immediately
  emitHtmlMulti := .no

def main (args : List String) : IO UInt32 := do
  extract
  if args == ["--extract"] then return 0
  let checked ← IO.Process.output {
    cmd := "python3", args := #["scripts/reproduce.py", "--verify-only"] }
  if checked.exitCode != 0 then
    throw <| IO.userError ("Research run validation failed; reproduce first.\n" ++ checked.stderr)
  manualMain (%doc ResearchNotebook) (config := config) (options := args)
