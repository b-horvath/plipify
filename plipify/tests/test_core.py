"""
Draft unit tests for plipify.core.
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


class TestProteinResidue:
    """
    Test against ProteinResidue default values and all expected protein residues 
    that should exist)

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
     
