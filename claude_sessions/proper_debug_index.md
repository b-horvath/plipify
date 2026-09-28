


```
                    features = getattr(report, shorthand + "_features")
                    # list of BaseInteraction Subclasses (depending on type)
                    for interaction_data in getattr(report, shorthand + "_info"):
                        #TODO: main index problem - embedding the pdb correctly
                        # Generate a dictionary, with the features being the key and the interaction_data being the values
                        interaction_dict = dict(zip(features, interaction_data))
                        print("[DICT]", shorthand, interaction_dict) 
```

This block is what stops 6F8B from crashing. Without it, a water that holds a metal ion gets treated like an amino acid, and plipify fails trying to find it among the protein residues.

### The problem it solves
1. **plipify only stores protein residues.** `structure.residues` is built from `pdbcomplex.resis`. For 6F8B that's ALA 1 … PRO 298. The 414 waters (HOH 501–914), the metal ions (CA 401, ZN 402) and the ligands (CXH 403/404) are never added.

2. **PLIP's metal-complex report can name non-protein partners.** When PLIP finds a metal ion, it lists every atom within about 3 Å that coordinates it. That can be:
   - a protein atom (`LOCATION = "protein.sidechain"` or `"protein.mainchain"`)
   - a **water oxygen** (`LOCATION = "water"`)
   - a ligand atom (`LOCATION = "ligand"`)

   Each contact's `RESNR` is the residue number of that atom in the PDB file ([detection.py:474](.venv/lib/python3.11/site-packages/plip/structure/detection.py#L474)).

3. **So in 6F8B:** the calcium (CA 401) is held by ASP 136, GLU 172, GLU 175, ASP 183 and LEU 185, **plus water HOH 548**. PLIP puts the water first, so the first metal contact plipify reads is `RESNR=548, RESTYPE=HOH, LOCATION=water`.

4. **Without this block**, the code runs `structure.get_residue_by(seq_index=548, chain="A")`. That searches the 298 protein residues, finds nothing and raises `ValueError: No residue with such sequence index: 548, A!`, which is the error from your test.

### What each line does
```python
if not interaction_dict.get("LOCATION", "protein").startswith("protein"):
```
- This asks whether the partner is something other than protein.
- Only metal interactions have a `LOCATION` key. For every other type (hbond, hydrophobic, …), `.get(..., "protein")` returns `"protein"`, so the condition is False and those interactions run exactly as before.
- For metals, it's True only for `"water"` or `"ligand"`.

```python
    interactions.append(InteractionType(interaction=interaction_dict))
```
- This **keeps** the contact on the binding site, so the calcium complex still shows all its coordinating partners (e.g. in `to_dataframes()`). No information is thrown away.

```python
    continue
```
- This skips the rest of the loop for this contact: no `get_residue_by` lookup, and no `residue.interactions.append(...)`.
- Fingerprints are built from `residue.interactions`, so a water never counts as a residue in the fingerprint.

The debug print inside only logs each skip to your output file.

### Why this approach and not something else
It matches PLIP's own behaviour. PLIP keeps waters and ligand atoms in its metal-complex report, but leaves them out of its list of interacting residues ([preparation.py:857-858](.venv/lib/python3.11/site-packages/plip/structure/preparation.py#L857-L858): `if i.restype not in ['LIG', 'HOH']`). The alternatives were worse:
- **Wrap the lookup in `try/except ValueError`.** That would also hide real bugs, like a protein residue that genuinely went missing.
- **Add waters to `structure.residues`.** `ProteinResidue` rejects non-amino-acid names, and the fingerprints would fill up with water "residues".

### Current state of the file
You stopped me partway through the cleanup, and it didn't finish the way you asked:
- **Removed by me:** one edit went through before you stopped me. It deleted the per-site and per-interaction-type debug prints (`=== SITE ...`, `-- type ...`, `N x metal`). Those are part of the output file, which you now want to keep.
- **Also gone:** the `(setup)`, `(residue lookup)` and `(pending error)` debug blocks. That looks like your own edit.
- **Still present:** the `(residue loading)` block, the `(non-protein partner)` print, and `plipify/debug_to_file.py`.

Running `debug_to_file` will therefore now only list the residues loaded and the non-protein skips, not the per-interaction trace. Want me to put back the blocks you're missing from the file output?