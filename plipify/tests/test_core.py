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
     
