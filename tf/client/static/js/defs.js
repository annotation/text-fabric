export const DEBUG = false

export const BOOL = "boolean"
export const NUMBER = "number"
export const STRING = "string"
export const OBJECT = "object"

export const QUWINDOW = 10
export const MAXINPUT = 1000

export const DEFAULTJOB = "search"

export const RESULTCOL = "nr"

export const BUTTON = {
  simple: { on: "🔎", off: "🛠" },
  nodeseq: { on: "nodes start at 1", off: "nodes as in text-fabric" },
  autoexec: { on: "auto search", off: "use button to search" },
  exporthl: {
    on: "mark matches in export with « »",
    off: "don't mark matches in export with « »",
  },
  exportsr: {
    on: "use columns for extra layers (export only)",
    off: "use rows for extra layers (export only)",
  },
  multihl: {
    no: "cannot highlight colours per (group)",
    on: "highlight colours per (group)",
    off: "single highlight color",
  },
  exec: { no: " ", on: "⚫️", off: "🔴" },
  visible: { on: "🔵", off: "⚪️" },
  expand: {
    on: "-",
    off: "+",
    no: "",
  },
}

export const FOCUSTEXT = { r: "focus", a: "context", d: "content" }

export const FLAGSDEFAULT = { i: true, m: true, s: false }

export const SEARCH = {
  dirty: "fetch results",
  exe: "fetching ...",
  done: "up to date",
  failed: "failed",
}

export const TIP = {
  simple: `🛠 expert interface
OR
🔎 minimalistic interface`,
  nodeseq: `node numbers start at 1 for each node types
OR
node numbers are exactly as in Text Fabric`,
  autoexec: `search automatically after each change
OR
only search after you hit the search button`,
  exporthl: `when exporting we could mark the matches by means of « »
OR
we can refrain from doing so`,
  exportsr: `when exporting, if there are multiple layers in a level,
we could show them in separate ROWS:
this violates the 1-result-1-row principle, but the results maybe easier to read.
OR
we can show them in additional columns:
this keeps every result in a single row, but rows may grow very wide`,
  multihl: `highlight sub matches for the parts between () with different colours
OR
use a single highlight color for the complete match
N.B.: this might not be supported in your browser`,
  expand: "whether to show inactive layers",
  focus: "make this the focus level",
  exec: "whether this pattern is used in the search",
  visible: "whether this layer is visible in the results",
  visibletp: "whether node numbers are visible in the results",
  flagm: `multiline: ^ and $ match:
ON: around newlines
OFF: at start and end of whole text`,
  flags: `single string: . matches all characters:
ON: including newlines
OFF: excluding newlines"`,
  flagi: `ignore
ON: case-insensitive
OFF: case-sensitive"`,
  corpus: `to the online presence of this node`,
}

export const htmlEsc = text => text.replaceAll("&", "&amp;").replaceAll("<", "&lt;")
