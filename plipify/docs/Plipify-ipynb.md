# `plipify/Plipify.ipynb`

## Purpose

The **original tutorial / demonstration notebook** for the package, written for the SARS-CoV-2 Main
Protease (MPro) use case. It walks from background theory through a full cumulative interaction
fingerprint calculation and visualization on the Diamond/XChem MPro fragment screen. It predates
the `projects/` layout — the current, maintained versions of this workflow are
`projects/01/fragalysis.ipynb` and `projects/01/xchem.ipynb`.

42 cells, roughly half Markdown narrative and half code. The file is large (~4 MB) because it still
contains saved cell outputs and embedded PNGs.

## Structure

| Section | Cells | Content |
|---|---|---|
| Title + contents | 0–1 | project abstract, table of contents |
| Background | 2–4 | what PLIP is, what molecular / interaction fingerprints are, a module-structure diagram (`data/plipify_modules.PNG`) |
| Data | 5–6 | the Diamond/XChem MPro fragment screen, `6YB7` reference |
| Fingerprint calculation | 7–18 | imports, parameters (`structure_folder`, `name_file`, `residue_file`, `ligand_identifier`), a `calculate_fingerprints(...)` helper, and the MPro run (68 pre-defined residues × 8 interaction types) |
| Fingerprint visualization | 19–26 | `ipywidgets` dropdowns driving `fingerprint_barplot` / `fingerprint_heatmap` and `fingerprint_table` (bar/heatmap, count/frequency, full/non-empty) |
| Results | 27–28 | narrative findings (71 interactions across 13 residues; hotspots GLU166, HIS41, GLN189) and an "open ends" list |
| Optional / appendix | 29–41 | dump all PLIP data as DataFrames; a second, older `frequency_fingerprint(...)` implementation |

## Key code cells

- **cell 10 / 34** — `from plipify.plip_fingerprints import read_residues`, `from plipify.core
  import Structure`, `from plipify.fingerprints import InteractionFingerprint`.
- **cell 12 / 37** — the four input parameters, all pointing under `./data/`.
- **cell 15** — `calculate_fingerprints()` reads the manifest `.dat`, builds a `Structure` per PDB
  via `Structure.from_pdbfile(...)`, and returns count/frequency fingerprints.
- **cell 22 / 25** — `from plipify.fp_visual import fingerprint_barplot, fingerprint_heatmap,
  fingerprint_table`.
- **cells 23 / 26** — `ipywidgets` UI: dropdowns + a "Display" button whose callback clears output
  and renders the chosen plot/table.
- **cell 30 / 41** — `from plipify.plip_fingerprints import get_plip_data, show_plip_data` to print
  every PLIP interaction as a DataFrame.

## ⚠️ This notebook is stale

It imports two module names that **no longer exist** in the package:

| notebook import | current module |
|---|---|
| `plipify.plip_fingerprints` (`read_residues`, `get_plip_data`, `show_plip_data`) | `plipify._deprecated` |
| `plipify.fp_visual` (`fingerprint_barplot`, `fingerprint_heatmap`, `fingerprint_table`) | `plipify.visualization` |

So the notebook will `ModuleNotFoundError` on a fresh checkout without edits. It also assumes a
working-directory of `plipify/` (all paths are `./data/...`) and relies on the MUSCLE-based
alignment path, which currently has a bug (see [`fingerprints-py.md`](fingerprints-py.md)). Treat
it as historical documentation of the intended workflow rather than runnable code.
