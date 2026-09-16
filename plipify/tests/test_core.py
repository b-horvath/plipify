"""
Draft unit tests for plipify.core.
"""

from pathlib import Path

import pytest

from plipify.core import (
    BaseInteraction,
    HbondInteraction,
    HbondDonorInteraction,
    HbondAcceptorInteraction,
    HydrophobicInteraction,
    CovalentInteraction,
    BaseResidue,
    ProteinResidue,
    LigandResidue,
    BindingSite,
    Structure,
)


class TestProteinResidue:
    """
    Test against ProteinResidue default values and all expected protein residues 
    (that should exist)

    Questions:
    - how do we account for different chains? Missing chains?
    """

    @pytest.mark.parametrize(
        "res_name", ProteinResidue._ALLOWED_RESIDUE_NAMES
    )
    def test_all_allowed_residue_names(self, res_name):
        res = ProteinResidue(name=res_name, seq_index=10, chain="A")
        assert res.name == res_name
        assert res.interactions == [] or None
        assert res.structure is None

    #follows the format of "{}:{}.{}"
    def test_identifier(self):
        res = ProteinResidue(name="HIS", seq_index=41, chain="A")
        assert res.identifier == "HIS:41.A"

    # Assert that 3 letter code is converted
    def test_one_and_three_letter_codes(self):
        res = ProteinResidue(name="ALA", seq_index=1, chain="A")
        assert res.three_letter_code == "Ala"
        assert res.one_letter_code == "A"

    #follow IUPAC standards
    def test_is_protein(self):
        assert ProteinResidue("GLY", 1, "A").is_protein

    def test_invalid_is_protein(self):
        with pytest.raises(ValueError): 
            ProteinResidue("ABC", 1, "A").is_protein

    def test_count_interactions(self):
        res = ProteinResidue(
            name="MET",
            seq_index=1,
            chain="A",
            interactions=[
                HbondInteraction({}),
                HbondInteraction({}),
                HydrophobicInteraction({}),
            ],
        )
        counts = res.count_interactions()
        assert counts["hbond"] == 2
        assert counts["hydrophobic"] == 1

    def test_repr_with_and_without_interactions(self):
        bare = ProteinResidue("ALA", 1, "A")
        assert repr(bare) == "<ProteinResidue ALA:1.A>"
        withint = ProteinResidue("ALA", 1, "A", interactions=[HbondInteraction({})])
        assert "1 interactions" in repr(withint)


def test_ligand_residue_is_base_residue():
    assert issubclass(LigandResidue, BaseResidue)


@pytest.mark.parametrize(
    "cls, shorthand",
    [
        (HydrophobicInteraction, "hydrophobic"),
        (HbondInteraction, "hbond"),
        (HbondDonorInteraction, "hbond-don"),
        (HbondAcceptorInteraction, "hbond-acc"),
        (CovalentInteraction, "covalent"),
    ],
)
def test_interaction_shorthand(cls, shorthand):
    assert cls.shorthand == shorthand


###
# Integration: Structure.from_pdbfile against the two structure file formats
# found in plipify/data (.pdb and .cif, e.g. data/sample_pdbs/6F8B.pdb and
# 6F8B.cif).
###

DATA_DIR = Path(__file__).parents[1] / "data"
SAMPLE_PDBS_DIR = DATA_DIR / "sample_pdbs"
DIAMOND_XCHEM_DIR = DATA_DIR / "diamond_xchem_screen_mpro_all_pdbs"


class TestStructureFromPdbfileFormats:
    """
    Questions:
    - PLIP's loader hardcodes the OpenBabel input format to "pdb" regardless
      of file extension, so it has no real CIF support yet. Loading a .cif
      file currently makes PLIP call sys.exit(1) instead of raising a
      catchable parsing error, so that's what we assert on below.
    """

    # Test with python3 -m pytest -W "ignore::pytest.PytestUnknownMarkWarning" plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_loads_pdb_format -s -v
    @pytest.mark.integration
    def test_loads_pdb_format(self):
        """Test to see if load_pdb is functional to load one .pdb file"""
        pytest.importorskip("plip")
        pdb = SAMPLE_PDBS_DIR / "1dd6.pdb"
        # pdb = DIAMOND_XCHEM_DIR / "Mpro-x1012.pdb"
        if not pdb.exists():
            pytest.skip(f"sample PDB not available: {pdb}")
        structure = Structure.from_pdbfile(str(pdb))
        assert isinstance(structure, Structure)
        assert structure.residues
        assert structure.ligands

        # should print [<ProteinResidue SER:1.A>, <ProteinResidue GLY:2.A>, ...]
        print(f"\nResidues: ({len(structure.residues)}):\n", structure.residues[1:5])
        print(f"\nLigands: ({len(structure.ligands)}):")
        lig = structure.ligands[1]
        print(f"ligand: {lig.hetid} chain={lig.chain} pos={lig.position} n_waters={len(lig.water)}")
        for lig in structure.ligands:
            print(f"ligand: {lig.hetid} chain={lig.chain} pos={lig.position} n_waters={len(lig.water)}")
       

    # Test with python3 -m pytest -W plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_pdb_format_residues_are_protein_residues -s -v
    @pytest.mark.integration
    def test_pdb_format_residues_are_protein_residues(self):
        pytest.importorskip("plip")
        pdb = DIAMOND_XCHEM_DIR / "Mpro-x0072.pdb"
        if not pdb.exists():
            pytest.skip(f"sample PDB not available: {pdb}")

        structure = Structure.from_pdbfile(str(pdb))

        not_protein_residues = [r for r in structure.residues if not isinstance(r, ProteinResidue)]
        wrong_structure_refs = [r for r in structure.residues if r.structure is not structure]
        print(f"residues ({len(structure.residues)}): all ProteinResidue? {not not_protein_residues}")
        print(f"non-ProteinResidue count: {len(not_protein_residues)}")
        print(f"residues with wrong .structure ref: {len(wrong_structure_refs)}")

        assert all(isinstance(r, ProteinResidue) for r in structure.residues)
        assert all(r.structure is structure for r in structure.residues)

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "pdb_path", sorted(SAMPLE_PDBS_DIR.glob("*.pdb")), ids=lambda p: p.name
    )
    def test_pdb_format_loads_across_multiple_sample_files(self, pdb_path):
        """
        Generic over whatever .pdb files happen to live in the target directory.
        """
        pytest.importorskip("plip")
        if not pdb_path.exists():
            pytest.skip(f"sample PDB not available: {pdb_path}")

        structure = Structure.from_pdbfile(str(pdb_path))
        assert structure.residues

    @pytest.mark.integration
    def test_cif_format_is_not_supported(self):
        pytest.importorskip("plip")
        cif = SAMPLE_PDBS_DIR / "6F8B.cif"
        if not cif.exists():
            pytest.skip(f"sample CIF not available: {cif}")

        with pytest.raises(SystemExit):
            Structure.from_pdbfile(str(cif))

    #TODO
    @pytest.mark.integration
    def test_pdb_and_cif_formats_describe_the_same_structure(self):
        """
        PLIP itself only understands .pdb (see test_cif_format_is_not_supported
        above), so to actually load *both* formats of the same structure we
        reach for Biopython's format-specific parsers instead: PDBParser for
        the .pdb file and MMCIFParser for its .cif counterpart. Both should
        agree on the chains and residues of the underlying structure (6F8B),
        confirming the two files are legitimate, consistent representations
        of the same protein rather than just independently readable.
        """
        Bio_PDB = pytest.importorskip("Bio.PDB")
        pdb_path = SAMPLE_PDBS_DIR / "6F8B.pdb"
        cif_path = SAMPLE_PDBS_DIR / "6F8B.cif"
        if not pdb_path.exists() or not cif_path.exists():
            pytest.skip(f"sample 6F8B pdb/cif pair not available in {SAMPLE_PDBS_DIR}")

        pdb_structure = Bio_PDB.PDBParser(QUIET=True).get_structure("6F8B", str(pdb_path))
        cif_structure = Bio_PDB.MMCIFParser(QUIET=True).get_structure("6F8B", str(cif_path))

        pdb_chain_ids = {chain.id for model in pdb_structure for chain in model}
        cif_chain_ids = {chain.id for model in cif_structure for chain in model}
        assert pdb_chain_ids
        assert pdb_chain_ids == cif_chain_ids

        pdb_residue_count = sum(1 for _ in pdb_structure.get_residues())
        cif_residue_count = sum(1 for _ in cif_structure.get_residues())
        assert pdb_residue_count == cif_residue_count

