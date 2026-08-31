"""
Draft unit tests for plipify.core.

These cover the plain-Python building blocks (interaction types, residues,
binding sites and the Structure helper methods) that do not require PLIP.
The ``Structure.from_pdbfile`` classmethod is exercised by a single, opt-in
integration test that needs the ``plip`` dependency and a sample PDB file.
"""

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


###
# Interaction types
###


class TestBaseInteraction:
    def test_getitem_delegates_to_dict(self):
        interaction = BaseInteraction({"RESNR": 42, "RESCHAIN": "A"})
        assert interaction["RESNR"] == 42
        assert interaction["RESCHAIN"] == "A"

    def test_getitem_missing_key_raises(self):
        interaction = BaseInteraction({})
        with pytest.raises(KeyError):
            interaction["nope"]

    def test_repr_mentions_class_and_payload(self):
        interaction = HbondInteraction({"a": 1})
        text = repr(interaction)
        assert "HbondInteraction" in text
        assert "{'a': 1}" in text

    def test_to_dataframe_single_row(self):
        pd = pytest.importorskip("pandas")
        interaction = BaseInteraction({"x": 1, "y": 2})
        df = interaction.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["x", "y"]
        assert len(df) == 1


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


def test_hbond_subclasses_inherit_from_hbond():
    assert issubclass(HbondDonorInteraction, HbondInteraction)
    assert issubclass(HbondAcceptorInteraction, HbondInteraction)


###
# Residues
###


class TestBaseResidue:
    def test_no_allowed_names_accepts_anything(self):
        assert BaseResidue("ZZZ").name == "ZZZ"

    def test_subclass_with_whitelist_rejects_unknown(self):
        class Restricted(BaseResidue):
            _ALLOWED_RESIDUE_NAMES = {"ALA"}

        assert Restricted("ALA").name == "ALA"
        with pytest.raises(ValueError):
            Restricted("XXX")


class TestProteinResidue:
    def test_defaults(self):
        res = ProteinResidue(name="ALA", seq_index=10, chain="A")
        assert res.interactions == []
        assert res.structure is None

    def test_identifier(self):
        res = ProteinResidue(name="HIS", seq_index=41, chain="A")
        assert res.identifier == "HIS:41.A"

    def test_one_and_three_letter_codes(self):
        res = ProteinResidue(name="ALA", seq_index=1, chain="A")
        assert res.three_letter_code == "Ala"
        assert res.one_letter_code == "A"

    def test_is_protein(self):
        assert ProteinResidue("GLY", 1, "A").is_protein()
        assert not ProteinResidue("ZZZ", 1, "A").is_protein()

    def test_count_interactions(self):
        res = ProteinResidue(
            name="ALA",
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


###
# BindingSite
###


class TestBindingSite:
    def test_repr_counts_non_empty_interaction_types(self):
        site = BindingSite(
            {"hbond": [HbondInteraction({})], "hydrophobic": [], "metal": []},
            name="LIG:A:1",
        )
        text = repr(site)
        assert "name='LIG:A:1'" in text
        assert "1 interaction types" in text

    def test_to_dataframes_yields_type_and_frame(self):
        pytest.importorskip("pandas")
        site = BindingSite({"hbond": [HbondInteraction({"RESNR": 1})]})
        results = list(site.to_dataframes())
        assert len(results) == 1
        itype, df = results[0]
        assert itype == "hbond"
        assert len(df) == 1


###
# Structure helper methods
###


def make_structure(*specs):
    """specs: tuples of (name, seq_index, chain)."""
    residues = [ProteinResidue(name=n, seq_index=i, chain=c) for n, i, c in specs]
    return Structure(residues=residues)


class TestStructureConstruction:
    def test_empty_defaults(self):
        s = Structure()
        assert s.residues == []
        assert s.ligands == []
        assert s.binding_sites == []

    def test_identifier_none_without_path(self):
        assert Structure().identifier is None


class TestGetResidueBy:
    def setup_method(self):
        self.structure = make_structure(
            ("ALA", 1, "A"), ("GLY", 2, "A"), ("HIS", 2, "B")
        )

    def test_returns_none_when_nothing_requested(self):
        assert self.structure.get_residue_by() is None

    def test_by_list_index(self):
        assert self.structure.get_residue_by(index=1).name == "GLY"

    def test_index_and_seq_index_are_mutually_exclusive(self):
        with pytest.raises(ValueError):
            self.structure.get_residue_by(index=0, seq_index=1)

    def test_index_rejects_chain(self):
        with pytest.raises(ValueError):
            self.structure.get_residue_by(index=0, chain="A")

    def test_by_seq_index_with_chain(self):
        res = self.structure.get_residue_by(seq_index=2, chain="B")
        assert res.name == "HIS"

    def test_by_seq_index_without_chain_warns_and_returns_first(self, capsys):
        res = self.structure.get_residue_by(seq_index=2)
        assert res.name == "GLY"
        assert "didn't select a chain" in capsys.readouterr().out

    def test_by_seq_index_any_chain(self):
        res = self.structure.get_residue_by(seq_index=2, chain="any")
        assert res.name == "GLY"

    def test_missing_seq_index_raises(self):
        with pytest.raises(ValueError):
            self.structure.get_residue_by(seq_index=999, chain="A")


class TestSequence:
    def test_without_gaps_is_concatenation(self):
        s = make_structure(("ALA", 1, "A"), ("GLY", 3, "A"))
        assert s.sequence(with_gaps=False) == "AG"

    def test_with_gaps_fills_missing_positions(self):
        s = make_structure(("ALA", 1, "A"), ("GLY", 3, "A"))
        assert s.sequence(with_gaps=True) == "A-G"


###
# Integration: from_pdbfile (needs plip + sample data)
###


@pytest.mark.integration
def test_from_pdbfile_smoke():
    pytest.importorskip("plip")
    from pathlib import Path

    pdb = (
        Path(__file__).parents[1]
        / "data"
        / "diamond_xchem_screen_mpro_all_pdbs"
        / "Mpro-x0689.pdb"
    )
    if not pdb.exists():
        pytest.skip(f"sample PDB not available: {pdb}")

    structure = Structure.from_pdbfile(str(pdb), protonate=True)
    assert isinstance(structure, Structure)
    assert structure.residues
    assert structure.identifier == "Mpro-x0689"
    assert "residues" in structure.description
