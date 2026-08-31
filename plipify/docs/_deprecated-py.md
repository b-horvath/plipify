# `plipify/_deprecated.py`

## Purpose

The **original, pre-refactor implementation** of the plipify pipeline, kept for reference. It is a
flat collection of functions (no classes) that goes straight from a directory of PDB files to a
frequency fingerprint. Nothing in the package imports it — `core.py`, `fingerprints.py` and
`visualization.py` are the current replacements. The leading underscore marks it private/legacy.

## Imports ([_deprecated.py:1-7](../_deprecated.py#L1-L7))

`csv`, `os`, `pandas`, `tqdm.auto.tqdm`, `plip.structure.preparation.PDBComplex`,
`plip.exchange.report.BindingSiteReport`, `IPython.display.display`/`Markdown`.

## Module-level state ([_deprecated.py:11-20](../_deprecated.py#L11-L20))

`interaction_types` — a fixed list of 8 interaction names
(`hydrophobic, hbond, waterbridge, saltbridge, pistacking, pication, halogen, metal`). Note this
uses a single combined `hbond` (no donor/acceptor split) and no `covalent`, unlike the current
`fingerprints.py`.

---

## Preparation helpers

### `read_residues(path)` ([_deprecated.py:23-31](../_deprecated.py#L23-L31))

Reads a one-line CSV of residue numbers (e.g. `data/MPro_residues.csv`) and returns them as a
`list[int]` — the pre-defined binding-site residues to build the fingerprint over.

### `divide_list(list_name, n)` ([_deprecated.py:34-39](../_deprecated.py#L34-L39))

Generator that yields successive `n`-sized chunks of a list.

### `residue_dictionary(residues)` ([_deprecated.py:42-49](../_deprecated.py#L42-L49))

Builds `dict[residue_number, list[int]]` where each value is the block of flat fingerprint indices
belonging to that residue (one slot per interaction type). Effectively the row layout of the
fingerprint vector.

### `interaction_dictionary(interaction_types)` ([_deprecated.py:52-58](../_deprecated.py#L52-L58))

Builds `dict[interaction_name, int]` — the column offset of each interaction type within a
residue's block.

Together these two dictionaries let `interaction_fingerprint` compute a flat index as
`residue_dictionary[res][interaction_dictionary[itype]]`.

---

## PLIP data

### `analyze_interactions(pdbfile)` ([_deprecated.py:62-86](../_deprecated.py#L62-L86))

Loads one PDB with `PDBComplex`, calls `characterize_complex` on every ligand, and for each
interaction site builds a `BindingSiteReport`. Returns `dict[site_key, dict[itype, list]]` where
each `itype` value is `[features_tuple] + info_rows` (header row followed by data rows).

### `site_to_dataframes(site)` ([_deprecated.py:90-108](../_deprecated.py#L90-L108))

Converts one site's `{itype: [header, *rows]}` structure into `{itype: DataFrame | None}` (`None`
when there are no rows for that type).

### `get_plip_data(data, name_file)` ([_deprecated.py:111-124](../_deprecated.py#L111-L124))

Reads a manifest file (`name_file`) listing PDB filenames under directory `data`, runs
`analyze_interactions` on each (with a `tqdm` progress bar), and returns
`dict[filename, sites_dict]`. Missing files are reported and skipped.

### `show_plip_data(interactions)` ([_deprecated.py:127-137](../_deprecated.py#L127-L137))

Pretty-prints the nested `interactions` structure in a notebook: a Markdown header per structure,
per site, per interaction type, followed by the DataFrame. Only sites whose key starts with `LIG`
are shown (others are treated as crystallographic artefacts).

---

## Fingerprints

### `interaction_fingerprint(residue_dictionary, interaction_dict, residue_list, interaction_type)` ([_deprecated.py:141-150](../_deprecated.py#L141-L150))

Builds one structure's fingerprint for a **single interaction type**: a zero vector of length
`n_residues * n_interaction_types`, incremented at `residue_dictionary[res][interaction_dict[itype]]`
for every residue in `residue_list`.

### `interaction_fingerprint_list(interactions, residue_dict, interaction_dict)` ([_deprecated.py:153-169](../_deprecated.py#L153-L169))

Iterates all structures/sites/interaction-DataFrames, pulls the `RESNR` column, and calls
`interaction_fingerprint` for each, returning a flat `list` of per-(structure, type) fingerprints.

> ⚠️ [Line 158](../_deprecated.py#L158) iterates `for sites in interactions.items():` then does
> `sites.items()` again — `sites` is a `(key, value)` tuple, so this raises `AttributeError`. The
> function is broken as written.

### `frequency_interaction_fingerprint(fp_list)` ([_deprecated.py:172-178](../_deprecated.py#L172-L178))

Sums the list of fingerprints position-wise (`zip(*fp_list)`) and divides by `len(fp_list)` to give
a per-position interaction **frequency** (0–1).

---

## Relationship to the current code

| legacy (`_deprecated.py`) | current equivalent |
|---|---|
| `analyze_interactions`, `get_plip_data` | `core.Structure.from_pdbfile` |
| `residue_dictionary` / `interaction_dictionary` | `fingerprints.InteractionFingerprint.calculate_indices_mapping` |
| `interaction_fingerprint*` | `fingerprints.InteractionFingerprint._calculate_fingerprint_one_structure` |
| `frequency_interaction_fingerprint` | `fingerprints.InteractionFingerprint._acumulate_fingerprints` |
| `show_plip_data` | `core.Structure.to_dataframes` |

The old design keyed everything by integer residue numbers and never aligned sequences across
structures; the rewrite introduced `Structure`/`Residue` objects and a MUSCLE alignment step.
