# `plipify/visualization.py`

## Purpose

Takes a fingerprint `DataFrame` (as produced by `fingerprints.InteractionFingerprint`) and renders
it several ways:

- an interactive stacked bar chart (Plotly),
- a heatmap (seaborn / matplotlib),
- a colour-coded HTML fingerprint table,
- 3D interaction hotspots in NGLView,
- per-residue b-factor "painting" written back to PDB files,
- publication-quality ray-traced images via PyMOL.

## Imports ([visualization.py:12-20](../visualization.py#L12-L20))

`os`, `pathlib.Path`, `matplotlib.pyplot as plt`, `MDAnalysis as mda`,
`plotly.graph_objects as go`, `seaborn as sns`, and `from plipify.core import Structure`. All are
eager (imported at module load) except `nglview`, `ipywidgets`, `matplotlib.cm/colors` and `pymol`,
which are imported inside the functions that use them.

## `INTERACTION_PALETTE` ([visualization.py:22-32](../visualization.py#L22-L32))

Maps the 9 non-covalent interaction shorthands to colourblind-safe hex colours. Used by both the
HTML table and its legend. Note there is **no `"covalent"` entry** — a fingerprint column named
`covalent` will raise `KeyError` in `fingerprint_table`.

---

## `fingerprint_barplot(fingerprint_df)` ([visualization.py:35-63](../visualization.py#L35-L63))

Builds a Plotly `go.Figure` with one `go.Bar` trace per interaction type (columns iterated in
reverse-sorted order), `x = fingerprint_df.index` (residues), `y = column values`. Layout is
`barmode="stack"` with titled axes and a categorical x-axis. Returns the figure.

## `fingerprint_heatmap(fingerprint_df, cmap="YlGnBu")` ([visualization.py:66-79](../visualization.py#L66-L79))

`plt.subplots(figsize=(10, 7))` + `sns.heatmap(fingerprint_df, annot=True, cmap=cmap, fmt="g")`
with "Interaction Types" / "Residues" axis labels. Returns the matplotlib figure.

## `_prepare_tabledata(fingerprint_df)` ([visualization.py:82-108](../visualization.py#L82-L108))

Helper for `fingerprint_table`. Returns a 3-tuple:

- `fingerprint` — `fingerprint_df.values.tolist()` (list of per-residue rows);
- `interaction_index` — `dict[int, str]` mapping each flat fingerprint position to its interaction
  type (columns repeated once per residue);
- `residues` — `list(fingerprint_df.index)`.

## `_TABLE_CSS` ([visualization.py:111-181](../visualization.py#L111-L181))

A CSS string (`.plipify-legend`, `.plipify-interactions`, `.plipify-ttooltip`) injected into the
HTML produced by `fingerprint_table`.

## `fingerprint_table(fingerprint_df, as_widget=True, structure=None)` ([visualization.py:184-279](../visualization.py#L184-L279))

Builds an HTML + CSS table where every non-zero fingerprint bit is a coloured cell with a hover
tooltip naming its interaction type.

- If `structure` is supplied, it tries to build one-letter residue labels (`{seq_index: "H163"}`)
  from `structure.residues` and stashes them in `fingerprint_df.attrs["residues"]`; an
  `AttributeError` (wrong object type) is caught and printed.
- Emits a legend row (only for interaction types present in the DataFrame), then a header row of
  residues, then one nested table per residue with a coloured `<td>` per non-zero bit.
- `as_widget=True` → returns an `ipywidgets.HTML`; otherwise returns the raw HTML string.

> ⚠️ `INTERACTION_PALETTE[interaction_type]` is indexed without a guard, so any fingerprint column
> outside the palette (e.g. `covalent`) raises `KeyError`.

## `fingerprint_nglview(fingerprint_df, structure, fp_index_to_residue_id=None)` ([visualization.py:282-392](../visualization.py#L282-L392))

Renders the fingerprint as 3D hotspots.

1. Calls `structure.view(solvent_selection_query="NOT all")` to get a base NGLView widget.
2. For each residue row: sorts `(column, value)` descending; if `fp_index_to_residue_id` is given,
   remaps the row id to the structure's residue via `structure.get_residue_by(...)` (skipping and
   printing when a residue isn't found); builds a tooltip string like `"3xHydrophobic, 1xHbond-Acc"`.
3. Adds ball-and-stick for the interacting residues (coloured by chain) and their O/N/S atoms
   (coloured by element).
4. Injects two JavaScript snippets via `view._js(...)` — one patching NGL hover tooltips, one
   patching click-info — so hovering an atom shows its residue's interaction summary.
5. Returns the widget.

## `nglview_color_side_chains_by_frequency(fp_focused, selected_structure_pdb, ligand="LIG")` ([visualization.py:395-440](../visualization.py#L395-L440))

Adapted from a gist by Dominique Sydow. Adds a `sum` column to a copy of the fingerprint, builds a
`Reds` colormap scaled to the max interaction count, maps each residue to a hex colour, wraps it in
`nglview.color._ColorScheme`, then builds a fresh `NGLWidget` showing the protein cartoon and
selected side chains coloured by that scheme, plus the ligand as ball-and-stick, centred on the
ligand. Uses `matplotlib.cm.get_cmap`, which is deprecated in recent matplotlib.

## `fingerprint_writepdb(fingerprint_df, structure, output_path, ligand=False, ligand_name="LIG", summed=False, verbose=True) -> dict` ([visualization.py:443-553](../visualization.py#L443-L553))

Writes the interaction counts into PDB B-factor columns so they can be visualised in any molecular
viewer.

- Creates `<output_path>/interaction_pdbs/`.
- For each interaction column: loads `MDAnalysis.Universe(structure._path)`, adds a `tempfactors`
  topology attribute, selects `protein` (or `protein or resname <ligand_name>` when `ligand=True`),
  sets each residue's B-factor to its interaction count, writes `sys_int_<column>.pdb`, and reloads
  it as a `Structure.from_pdbfile(...)`.
- If `summed=True`, repeats once more with the row-sums → `sys_summed_interactions.pdb`.
- Returns `dict[str, Structure]` keyed by interaction type (plus `"summed_interactions"`).

> ⚠️ Uses `Series.iteritems()` ([lines 504, 534](../visualization.py#L504)), removed in pandas 2.0
> — this function breaks on modern pandas (use `.items()`).

## `class PymolVisualizer` ([visualization.py:556-869](../visualization.py#L556-L869))

Tools to produce publication-ready images with PyMOL.

- `__init__(self, pdb, ligand_interactions=True, verbose=True)` — imports `pymol`, launches a
  quiet headless session (`pymol -qc`), loads `pdb` (raises `FileNotFoundError` if missing),
  renames the loaded object to `"system"`, and strips `HOH`/`SOL`/`NA`/`CL`.
- `set_style(...)` — sets ambient light, ambient-occlusion mode/scale, background colour,
  antialiasing, orthographic view, ray-trace mode, and flat-sheet cartoons.
- `create_image(...)` — a large keyword surface controlling highlight style, spectrum colouring by
  B-factor, optional surface, protein/ligand styles and colours, carbon-only colouring, and the
  camera (centred on the ligand or an 18-float `get_view` string). Special-cases proline when
  showing hotspot side chains.
- `render(self, name, save_path="./", dpi=300)` — creates the output dir, ray-traces, and writes
  `<name>.png`.

> ⚠️ This class is **not functional as written**. `__init__` contains
> `self._self._cmd = self._cmd` / `self._self._util = self._util`
> ([lines 584-585](../visualization.py#L584-L585)), which are self-referential and raise
> `AttributeError`; `create_image` then relies on `self._cmd` / `self._util` (never validly set)
> and expressions like `self._cmd.self._util.cbay`. It needs repair before use.

---

## How it fits in

`fingerprints.InteractionFingerprint.calculate_fingerprint(..., as_dataframe=True)` produces the
DataFrame that every function here consumes. The project notebooks (`projects/01/*.ipynb`,
`projects/02/main.ipynb`) import `fingerprint_barplot` and friends directly.
