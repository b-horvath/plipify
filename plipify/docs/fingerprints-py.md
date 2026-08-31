# `plipify/fingerprints.py`

## Purpose

Factories that take one or more `core.Structure` objects, align them, and produce a **per-residue
interaction fingerprint** — a vector of interaction counts, optionally summed across many
structures and returned as a `pandas.DataFrame` indexed by residue.

## Imports ([fingerprints.py:9-19](../fingerprints.py#L9-L19))

`subprocess`, `collections.defaultdict`/`Counter`, `tempfile.TemporaryDirectory`, `pathlib.Path`,
`numpy`, `pandas`, Biopython alignment types (`MultipleSeqAlignment`, `Seq`, `SeqRecord`,
`read`/`write` alignment), and `from .core import ProteinResidue`.

---

## `InteractionFingerprint` ([fingerprints.py:22-277](../fingerprints.py#L22-L277))

The public class. One instance can be reused across multiple `calculate_fingerprint` calls.

### `__init__(self, interaction_types=(...))` ([fingerprints.py:30-46](../fingerprints.py#L30-L46))

`interaction_types` defaults to a 10-tuple: `hydrophobic, hbond-don, hbond-acc, waterbridge,
saltbridge, pistacking, pication, halogen, metal, covalent`. This is the column order of every
fingerprint the instance produces. Also sets `self.indices = None`.

### `calculate_fingerprint(self, structures, residue_indices=None, labeled=True, cumulative=True, as_dataframe=False, remove_non_interacting_residues=False, remove_empty_interaction_types=False, ensure_same_sequence=True)` ([fingerprints.py:48-130](../fingerprints.py#L48-L130))

The main entry point.

1. If `residue_indices is None`, compute the sequence-alignment mapping with
   `self.calculate_indices_mapping(structures)`.
2. Guard: `len(structures)` must equal `len(residue_indices)`, else `ValueError`.
3. For each `(structure, indices)` pair, call `_calculate_fingerprint_one_structure(structure,
   indices.values(), labeled=labeled)` and collect. **Exceptions are caught and printed as a
   warning**, and that structure is silently skipped.
4. If `cumulative`, sum the per-structure fingerprints with `_acumulate_fingerprints(...)`.
   - If additionally `labeled and as_dataframe`: bucket the summed `_LabeledValue`s by
     `label["type"]`, build a DataFrame `{type: [value, ...]}`, set `df.index =
     residue_indices[0].keys()`. Optionally drop all-zero rows
     (`remove_non_interacting_residues`) and/or all-zero columns
     (`remove_empty_interaction_types`). **Return the DataFrame.**
5. Otherwise return the raw `fingerprints` list.

Parameters:

| name | meaning |
|---|---|
| `labeled` | each fp bit is a `_LabeledValue` (carries its residue + type) instead of a plain int |
| `cumulative` | sum the fp across all structures rather than returning one per structure |
| `as_dataframe` | return a DataFrame instead of an array/list (only honoured when `labeled and cumulative`) |
| `remove_non_interacting_residues` | drop residues whose row is all zeros |
| `remove_empty_interaction_types` | drop interaction columns that are all zeros |
| `ensure_same_sequence` | assert each aligned position has the identical residue across structures |

> ⚠️ The `TODO` at [line 94](../fingerprints.py#L94) is real: several boolean combinations aren't
> handled. In particular, when `cumulative=True` but not `(labeled and as_dataframe)`, the function
> falls through and returns the **per-structure** `fingerprints` list, *not* the accumulated
> fingerprint computed just above.

### `_acumulate_fingerprints(self, fingerprints, ensure_same_sequence=True)` ([fingerprints.py:132-174](../fingerprints.py#L132-L174))

Sums a list of fingerprints position-by-position (`for position in zip(*fingerprints)`):

- `total = sum(getattr(x, "value", x) for x in position)` — works for both labeled and plain fps.
- If labeled (`hasattr(position[0], "label")`):
  - collect the `label` dicts;
  - if `ensure_same_sequence`, check `name`/`seq_index`/`chain` are identical across structures for
    this position, else `ValueError` ("Your structures might not be sequence-aligned");
  - check all labels share one `type`, else `ValueError`;
  - build a fresh `ProteinResidue` from the first label and append
    `_LabeledValue(value=total, label={"residue": ..., "type": ...})`.
- Else append the plain `total`.

Returns the summed fingerprint list.

### `_calculate_fingerprint_one_structure(self, structure, indices, labeled=False)` ([fingerprints.py:176-210](../fingerprints.py#L176-L210))

Builds the fingerprint for a single structure.

- `indices` is an iterable of kwarg dicts like `{"seq_index": 1, "chain": "any"}`.
- For each: `residue = structure.get_residue_by(**index_kwargs)`.
  - If found → `counter = residue.count_interactions()`.
  - If not → placeholder `ProteinResidue("GAP", 0, None)` and an empty `Counter` (this is the
    "hacky" `FIXME` at [line 195](../fingerprints.py#L195)).
- For each interaction type in `self.interaction_types`, append either `_LabeledValue(counter[type],
  label={"residue": residue, "type": type})` (labeled) or the plain `counter[type]` int.
- Asserts the final length equals `len(indices) * len(self.interaction_types)`.
- Returns `np.asarray(fingerprint)` when unlabeled, otherwise the list.

### `clear_fingerprint(self)` ([fingerprints.py:212-213](../fingerprints.py#L212-L213))

Sets `self._fingerprint = None`. Vestigial — nothing else reads or writes `_fingerprint`.

### `calculate_indices_mapping(structures)` — staticmethod ([fingerprints.py:215-277](../fingerprints.py#L215-L277))

Aligns the structures' sequences with **MUSCLE** and returns, for each structure, a
`dict[int, {"seq_index": int, "chain": "any"}]` mapping unaligned sequence position → aligned
column (accounting for gaps). Only matching residue types are reported.

Steps: collect `s.sequence()` for each structure, pad to equal length with trailing `-`, wrap in
`SeqRecord`s and a `MultipleSeqAlignment`, write FASTA to a `TemporaryDirectory`, run MUSCLE, read
the aligned FASTA back, then walk the columns comparing the old vs new character to build the
`old2new` mapping.

> ⚠️ Two problems in the MUSCLE call ([lines 246-251](../fingerprints.py#L246-L251)): the command
> string is assigned to `cli` but `subprocess.call(cmd, ...)` passes an **undefined `cmd`** →
> `NameError` at runtime. The command also uses MUSCLE v5 syntax (`muscle -super5 ... -output ...`).
> Because of this, callers currently have to pass `residue_indices` explicitly rather than relying
> on auto-alignment.

---

## `_LabeledValue` ([fingerprints.py:280-291](../fingerprints.py#L280-L291))

A tiny wrapper attaching metadata to one fingerprint bit.

- `__init__(self, value, label)` — `value` is the interaction count; `label` is
  `{"residue": ProteinResidue, "type": str}`.
- `__repr__` — `<LabeledValue 3 labeled with object {...}>`.

`visualization.py` relies on `label["type"]` (column name) and `.value` (cell value) when turning
a labeled cumulative fingerprint into a table or chart.
