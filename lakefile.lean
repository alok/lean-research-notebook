import Lake
open Lake DSL

package «lean-research-notebook» where
  version := v!"0.1.0"

require verso from git "https://github.com/leanprover/verso" @
  "cad4b633e75ea769b851f12f9ca3b4f0dfcc625f"

@[default_target]
lean_lib ResearchNotebook

@[default_target]
lean_exe notebook where
  root := `NotebookMain
  supportInterpreter := true
