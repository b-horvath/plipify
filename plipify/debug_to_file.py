"""
DEBUG helper — remove together with the DEBUG blocks in core.py.

Runs Structure.from_pdbfile on one PDB file and saves everything it prints
(the [residues] / [from_pdbfile] debug output and the get_residue_by prints)
to plipify/output/<pdb name>.txt, followed by a [pdb lines] section that shows
every line of the PDB file next to the Python object(s) it became.

Usage (from the repo root):
    python -m plipify.debug_to_file                   # defaults to 6F8B.pdb
    python -m plipify.debug_to_file 1A1E.pdb          # file in plipify/data/sample_pdbs/
    python -m plipify.debug_to_file path/to/any.pdb   # any other path
"""
import contextlib
import sys
import traceback
from collections import defaultdict
from pathlib import Path

from plipify.core import Structure

PACKAGE_DIR = Path(__file__).parent
SAMPLE_PDBS_DIR = PACKAGE_DIR / "data" / "sample_pdbs"
OUTPUT_DIR = PACKAGE_DIR / "output"

## Begin section to add the repr

# What non-coordinate PDB records are, since no Python object is created for them
RECORD_NOTES = {
    "ANISOU": "anisotropic B-factors of the atom above; not read by PLIP/plipify",
    "TER": "end of chain marker",
    "CONECT": "explicit bond record; OpenBabel uses it for connectivity",
    "LINK": "inter-residue bond; PLIP reads these into pdbcomplex.covalent -> CovalentInteraction",
    "END": "end of file",
}


def _atom_serials(value):
    """Interaction *_IDX fields hold one atom serial, *_IDX_LIST fields hold several."""
    if isinstance(value, int):
        return [value]
    if isinstance(value, (list, tuple)):
        return [int(v) for v in value]
    if isinstance(value, str):
        return [int(v) for v in value.split(",") if v.strip().isdigit()]
    return []


def describe_pdb_lines(structure, pdb_path):
    """
    Print every line of the PDB file next to the Python object(s) it ended up as:
    the OpenBabel atom, the plipify ProteinResidue / PLIP ligand, and the interactions
    that reference this exact atom (by serial number).
    """
    from openbabel import pybel

    # OpenBabel reads ATOM/HETATM lines in file order, so the k-th coordinate line is atoms[k]
    # keep a reference to the Molecule: if it is garbage-collected, its atoms point at freed memory
    ob_mol = next(pybel.readfile("pdb", str(pdb_path)))
    ob_atoms = ob_mol.atoms

    residues_by_key = {(r.name, r.seq_index, r.chain): r for r in structure.residues}
    ligands_by_member = {}
    for ligand in structure.ligands:
        for member in ligand.members:  # e.g. ('CXH', 'A', 403), ('ZN', 'A', 402)
            ligands_by_member[member] = ligand
    ignored_by_member = {m: lig for lig in structure.ignored_ligands for m in lig.members}

    # atom serial -> interactions that name it in any *_IDX / *_IDX_LIST field
    used_in = defaultdict(list)
    for bs in structure.binding_sites:
        for itype, interactions in bs.interactions.items():
            for interaction in interactions:
                for field, value in interaction.interaction.items():
                    if field.endswith("IDX") or field.endswith("IDX_LIST"):
                        for serial in _atom_serials(value):
                            used_in[serial].append(f"{type(interaction).__name__}.{field}@{bs.name}")

    print(f"\n[pdb lines] ===== every line of {pdb_path} and the object it became =====")
    print(f"[pdb lines] OpenBabel read {len(ob_atoms)} atoms")
    atom_i = 0
    with open(pdb_path) as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            record = line[:6].strip()

            if record in ("ATOM", "HETATM"):
                serial = int(line[6:11])
                resname, chain, resnum = line[17:20].strip(), line[21], int(line[22:26])
                key = (resname, resnum, chain)

                ob_atom = ob_atoms[atom_i] if atom_i < len(ob_atoms) else None
                atom_i += 1
                if ob_atom is None:
                    atom_desc = "atom=<not read by OpenBabel>"
                else:
                    # pybel.Atom has no useful repr (just a memory address), so show its contents
                    ob_serial = ob_atom.OBAtom.GetResidue().GetSerialNum(ob_atom.OBAtom)
                    mismatch = "" if ob_serial == serial else f" SERIAL MISMATCH ob={ob_serial}"
                    atom_desc = f"atom=<pybel.Atom idx={ob_atom.idx} type={ob_atom.type}{mismatch}>"

                if key in residues_by_key:
                    obj_desc = repr(residues_by_key[key])
                elif (resname, chain, resnum) in ligands_by_member:  # members are (name, chain, number)
                    lig = ligands_by_member[(resname, chain, resnum)]
                    obj_desc = (f"ligand(longname={lig.longname!r}, type={lig.type!r}, "
                                f"hetid={lig.hetid!r}, chain={lig.chain!r}, position={lig.position})")
                elif (resname, chain, resnum) in ignored_by_member:
                    lig = ignored_by_member[(resname, chain, resnum)]
                    obj_desc = f"ignored ligand {lig.longname!r} (ligand_name filter)"
                elif resname == "HOH":
                    obj_desc = "water: no plipify object"
                else:
                    obj_desc = "NOT in structure.residues or structure.ligands"

                uses = used_in.get(serial)
                uses_desc = f" used_in={uses}" if uses else ""
                print(f"{lineno:>5} | {line:<80} | {atom_desc} {obj_desc}{uses_desc}")
            else:
                note = RECORD_NOTES.get(record, "header/metadata record, no Python object")
                print(f"{lineno:>5} | {line:<80} | ({note})")


## end section to add the repr

def main(pdb="6F8B.pdb"):
    pdb_path = Path(pdb)
    if not pdb_path.exists():
        pdb_path = SAMPLE_PDBS_DIR / pdb
    if not pdb_path.exists():
        sys.exit(f"PDB file not found: {pdb} (also looked in {SAMPLE_PDBS_DIR})")

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{pdb_path.stem}.txt"

    # https://docs.python.org/3/library/contextlib.html#contextlib.redirect_stdout
    # https://docs.python.org/3/library/contextlib.html#contextlib.redirect_stderr
    # redirect_stdout and _stderr are used to redirect the output that would be found in the terminal, to be then output to a file
    with open(out_path, "w") as out, contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            structure = Structure.from_pdbfile(str(pdb_path))
            print(f"\n[debug_to_file] finished OK: {structure!r}")
            describe_pdb_lines(structure, pdb_path) # line to add the repr
        except Exception:
            print("\n[debug_to_file] from_pdbfile raised:")
            traceback.print_exc(file=out)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
