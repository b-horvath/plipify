# `plipify/core.py`

## Purpose

Defines the base objects shared across the whole pipeline. Two families:

- **Interaction types** — what connects a residue to a ligand (`BaseInteraction` + subclasses).
- **Structural objects** — the residue / binding-site / structure hierarchy.

Only lightweight imports at load time: `collections.defaultdict`/`Counter`, `pathlib.Path`, and
`Bio.Data.IUPACData` ([core.py:16-19](../core.py#L16-L19)). Everything heavier (`pandas`, `plip`,
`nglview`, `IPython`) is imported lazily inside the methods that need it.

---

## Part 1 — Interaction type classes

### `BaseInteraction` ([core.py:26-58](../core.py#L26-L58))

A thin wrapper around a single PLIP interaction record (a `dict` whose keys differ per interaction
type — H-bonds have donor/acceptor fields, hydrophobic contacts don't).

| Method | Behaviour |
|---|---|
| `__init__(self, interaction)` | stores the dict as `self.interaction` |
| `__getitem__(self, value)` | `obj["RESNR"]` proxies straight into the dict |
| `__repr__` | `<HbondDonorInteraction with {...}>` |
| `to_dataframe(self)` | lazily imports `pandas`, returns a one-row DataFrame (`from_dict(..., orient="index").T`) |
| `_ipython_display_(self)` | Jupyter hook; renders the one-row DataFrame when the dict is non-empty |

Class attribute `shorthand = ""` is the string key PLIP uses (`"hbond"`, `"hydrophobic"`, …).

### The concrete subclasses ([core.py:61-154](../core.py#L61-L154))

Each sets two class attributes only: `shorthand` and `color_rgb` (a 0–1 RGB triple used later for
drawing 3D cylinders).

| Class | shorthand | notes |
|---|---|---|
| `HydrophobicInteraction` | `hydrophobic` | |
| `HbondInteraction` | `hbond` | base for the two below |
| `HbondDonorInteraction` | `hbond-don` | subclass of `HbondInteraction` |
| `HbondAcceptorInteraction` | `hbond-acc` | subclass of `HbondInteraction` |
| `WaterbridgeInteraction` | `waterbridge` | |
| `SaltbridgeInteraction` | `saltbridge` | |
| `PistackingInteraction` | `pistacking` | |
| `PicationInteraction` | `pication` | |
| `HalogenInteraction` | `halogen` | |
| `MetalInteraction` | `metal` | |
| `CovalentInteraction` | `covalent` | no docstring; `color_rgb = 0,0,0` |

The donor/acceptor split matters because PLIP reports both directions in one `hbond` bucket;
plipify promotes them to distinct types via the `PROTISDON` flag (see `from_pdbfile`).

---

## Part 2 — Structural objects

### `BaseResidue` ([core.py:162-181](../core.py#L162-L181))

"A collection of covalently bonded atoms."

- `_ALLOWED_RESIDUE_NAMES = []` — per-subclass whitelist; empty means "accept anything".
- `__init__(self, name)` — sets `self.name = self._check_valid_name(name)`.
- `_check_valid_name(self, name)` — returns `name` unchanged if the whitelist is empty or contains
  it; otherwise raises `ValueError` listing the allowed names.

### `ProteinResidue(BaseResidue)` ([core.py:184-227](../core.py#L184-L227))

A residue in a protein sequence.

- `_ALLOWED_RESIDUE_NAMES` — the 20 standard 3-letter codes.
- `__init__(self, name, seq_index, chain, interactions=None, structure=None)` — assigns
  `self.name = name` **directly**, so `_check_valid_name` is *not* invoked for protein residues.
  Non-standard names like `"GAP"` pass through silently — deliberately, since `from_pdbfile` and
  the fingerprint code create `ProteinResidue("GAP", 0, None)` placeholders. `structure` is a
  back-reference to the owning `Structure`.
- `count_interactions(self)` — `Counter` keyed by each attached interaction's `shorthand`, e.g.
  `Counter({'hydrophobic': 3, 'hbond-acc': 1})`.
- `__repr__` — `<ProteinResidue HIS:41.A, and 4 interactions>` (drops the count if none).
- `identifier` (property) — `"{name}:{seq_index}.{chain}"`, e.g. `HIS:41.A`.
- `is_protein(self)` — `self.name.title()` in Biopython's `protein_letters_3to1`.
- `one_letter_code` (property) — `IUPACData.protein_letters_3to1[self.name.title()]` → `"H"`.
  Raises `KeyError` for non-standard names.
- `three_letter_code` (property) — `self.name.title()` → `"His"`.

### `LigandResidue(BaseResidue)` ([core.py:230-236](../core.py#L230-L236))

Marker subclass — "a small molecule in the vicinity of a binding site." Empty whitelist, no added
behaviour. In practice `from_pdbfile` stores raw PLIP ligand objects, not `LigandResidue`
instances, so this class is currently vestigial.

### `BindingSite` ([core.py:239-258](../core.py#L239-L258))

A container for interactions grouped by type.

- `__init__(self, interactions, name=None)` — `interactions` is `{shorthand: [BaseInteraction, ...]}`;
  `name` is the PLIP site key (e.g. `LIG:A:1`).
- `__repr__` — `<BindingSite with name='LIG:A:1' and 3 interaction types>` (counts non-empty buckets).
- `to_dataframes(self)` — generator; yields `(itype, pd.concat([i.to_dataframe() ...]))` — one
  stacked DataFrame per interaction type.

### `Structure` ([core.py:261-573](../core.py#L261-L573))

The central object: residues + ligands + binding sites for one PDB file.

Class attribute `INTERACTIONS` ([core.py:276-285](../core.py#L276-L285)) — the 8 interaction
classes iterated during parsing. It lists `HbondInteraction` (not the donor/acceptor subclasses)
and omits `CovalentInteraction` (covalent bonds are handled separately).

#### `__init__(self, residues=None, ligands=None, binding_sites=None)` ([core.py:287-292](../core.py#L287-L292))

Stores the three lists (each defaulting to `[]`), plus private `self._path = None` and
`self._pdbcomplex = None`. Direct construction gives an empty shell; the real entry point is the
classmethod.

#### `from_pdbfile(cls, path, ligand_name=None, protonate=True)` ([core.py:294-411](../core.py#L294-L411))

The main factory — reads a PDB file, runs PLIP, and builds the object graph.

1. **Protonation toggle** — if `protonate=False`, sets `plip.basic.config.NOHYDRO`; otherwise PLIP
   adds hydrogens itself.
2. **Load** — imports `PDBComplex`/`BindingSiteReport`, creates `pdbcomplex`, `load_pdb(path)`.
3. **Residues** — for every `pdbcomplex.resis`, build `ProteinResidue(name, seq_index, chain,
   structure=structure)` into `structure.residues`.
4. **Ligands** — iterate `pdbcomplex.ligands`. If `ligand_name` is given and a ligand's `longname`
   doesn't start with it → `ignored_ligands`; otherwise `pdbcomplex.characterize_complex(ligand)`
   (this actually computes the interactions) and keep it.
5. **Binding sites** — for each `pdbcomplex.interaction_sets` (sorted), build a
   `BindingSiteReport`. When `ligand_name` is `None` or the site key matches:
   - For each class in `cls.INTERACTIONS`, take `shorthand`, pull `report.<shorthand>_features`
     (columns) and `report.<shorthand>_info` (rows).
   - Zip each row into a dict; look up the residue via
     `structure.get_residue_by(seq_index=RESNR, chain=RESCHAIN)`.
   - For `hbond`, branch on `interaction_dict["PROTISDON"]` → `HbondDonorInteraction` vs
     `HbondAcceptorInteraction`; every other type → `InteractionType(interaction=...)`.
   - Append the object to both the local `interactions` list **and** `residue.interactions`.
   - Group by `shorthand` into a `defaultdict(list)`, wrap in `BindingSite(..., name=key)`.
6. **Covalent bonds** — for each `pdbcomplex.covalent`, build a site key `id1:chain1:pos1`, decide
   which partner is the protein (name in `ProteinResidue._ALLOWED_RESIDUE_NAMES`), and append a
   `CovalentInteraction` into the matching site's `"covalent"` bucket with normalized
   `RESNR`/`RESTYPE`/`RESCHAIN` (+ `_LIG` variants).
7. **Finalize** — attach `binding_sites`, `ligands`, `ignored_ligands`, `_pdbcomplex`; return the
   structure.

> ⚠️ Lines [352-353](../core.py#L352-L353): `if shorthand == "hbond-acc": shorthand == "hbond"`
> uses `==` instead of `=` — a no-op. Dead code anyway, since `INTERACTIONS` never yields
> `"hbond-acc"`/`"hbond-don"`.

#### `get_residue_by(self, index=None, seq_index=None, chain=None)` ([core.py:413-452](../core.py#L413-L452))

- Nothing supplied → returns `None`.
- Both `index` and `seq_index` → `ValueError`; `index` + a real `chain` → `ValueError`
  (positional lookup can't filter by chain).
- `index` given → `self.residues[index]` (plain list position).
- `seq_index` given → linear scan. If `chain is None`, **prints a warning** and returns the *first*
  residue with that `seq_index` regardless of chain. If `chain` is `"any"` or matches, returns
  that one. `for/else`: if nothing matches, raises `ValueError`.

#### `sequence(self, with_gaps=True)` ([core.py:454-460](../core.py#L454-L460))

- `with_gaps=False` → concatenates `one_letter_code` for residues in list order.
- `with_gaps=True` (default) → builds `{seq_index: one_letter_code}`, finds the max index, joins
  positions `1..max` filling gaps with `"-"`. Used by the alignment step in `fingerprints.py`.
  (`KeyError`s if any residue has a non-standard name.)

#### `identifier` (property) ([core.py:462-465](../core.py#L462-L465))

`Path(self._path).stem` (e.g. `Mpro-x0104`) when loaded from a file, else `None`.

#### `description` (property) ([core.py:467-477](../core.py#L467-L477))

`"Structure with N residues, M ligands (K of which were ignored) and P characterized binding
sites."` plus the source path.

> ⚠️ References `self.ignored_ligands`, which only exists after `from_pdbfile` — calling this on a
> directly-constructed `Structure` raises `AttributeError`.

#### `view(self, ligand_selection_query="ligand", solvent_selection_query="water", use_protonated=True)` ([core.py:479-551](../core.py#L479-L551))

Builds an interactive NGLView widget:

1. Picks the PDB path — the PLIP-generated `*_protonated.pdb` if `use_protonated` and it exists,
   else `self._path`. Bails with a message if no file is accessible.
2. Loads it, adds cartoon, ball-and-stick for the ligand query, lines for solvent, centers on the
   ligand.
3. For every interaction in every binding site: records `RESNR`, and if the record has both
   `LIGCOO` and `PROTCOO`, draws a labeled cylinder between ligand and protein atoms colored by the
   interaction's `color_rgb`.
4. Adds ball-and-stick for the interacting residues' side chains (by chain) and their O/N/S atoms
   (by element).
5. Returns the `nglview.NGLWidget`.

#### `to_dataframes(self)` ([core.py:553-570](../core.py#L553-L570))

Iterates `self.binding_sites`; for each, iterates `bs.to_dataframes()`. If IPython is available,
`display()`s a Markdown header per site and per interaction type plus the DataFrame. Always returns
a flat list of `(binding_site, itype, df)` tuples.

#### `__repr__(self)` ([core.py:572-573](../core.py#L572-L573))

`f"<{self.description}>"` — printing a `Structure` shows the summary sentence.

---

## Data-flow summary

`from_pdbfile` is the only real constructor. It produces a `Structure` holding: `residues` (list of
`ProteinResidue`, each with its own `.interactions` back-filled), `ligands`/`ignored_ligands` (raw
PLIP objects), and `binding_sites` (list of `BindingSite`, each a `{shorthand: [BaseInteraction]}`
dict). `fingerprints.py` then calls `structure.sequence()` and `structure.get_residue_by(...)` to
turn this into per-residue interaction counts; `visualization.py` consumes those.
