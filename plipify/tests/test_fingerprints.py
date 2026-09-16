"""
Potential unit/integration tests for plipify.fingerprints.InteractionFingerprint.

Structures are loaded through PLIP via the session-scoped fixtures defined
in conftest.py (structure_1dd6, structure_mpro_x0072, structure_mpro_x0104),
which read real files from plipify/data/sample_pdbs and
plipify/data/diamond_xchem_screen_mpro_all_pdbs. Each test is marked
`integration` and skips gracefully when plip, the sample files, or (for the
alignment test) the `muscle` CLI are unavailable.
"""

import numpy as np
import pandas as pd
import pytest

from plipify.fingerprints import InteractionFingerprint


@pytest.mark.integration
def test_calculate_fingerprint_single_structure_has_expected_length(structure_1dd6):
    """
    A non-cumulative, unlabeled fingerprint for a single structure should be
    a single numpy array whose length equals the number of requested
    residues times the number of interaction types.
    """
    fp = InteractionFingerprint()
    indices = {
        r.seq_index: {"seq_index": r.seq_index, "chain": r.chain}
        for r in structure_1dd6.residues[:5]
    }

    result = fp.calculate_fingerprint(
        [structure_1dd6], residue_indices=[indices], cumulative=False, labeled=False
    )

    assert len(result) == 1
    assert isinstance(result[0], np.ndarray)
    assert result[0].shape == (len(indices) * len(fp.interaction_types),)


@pytest.mark.integration
def test_calculate_fingerprint_labeled_as_dataframe(structure_mpro_x0072):
    """
    With labeled=True, cumulative=True and as_dataframe=True, the fingerprint
    should be returned as a DataFrame indexed by the requested residues, with
    one column per interaction type present in the results.
    """
    fp = InteractionFingerprint()
    indices = {
        r.seq_index: {"seq_index": r.seq_index, "chain": r.chain}
        for r in structure_mpro_x0072.residues[:15]
    }

    df = fp.calculate_fingerprint(
        [structure_mpro_x0072],
        residue_indices=[indices],
        cumulative=True,
        labeled=True,
        as_dataframe=True,
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(indices)
    assert set(df.columns) <= set(fp.interaction_types)


@pytest.mark.integration
def test_calculate_indices_mapping_aligns_two_diamond_xchem_structures(
    structure_mpro_x0072, structure_mpro_x0104, muscle_available
):
    """
    calculate_indices_mapping should run Muscle on two Mpro structures from
    the Diamond XChem screen and return one seq-index mapping per structure.
    Since both are near-identical protein constructs, the two mappings
    should cover a similar number of residues.
    """
    if not muscle_available:
        pytest.skip("muscle CLI not available on PATH")

    mapping = InteractionFingerprint.calculate_indices_mapping(
        [structure_mpro_x0072, structure_mpro_x0104]
    )

    assert len(mapping) == 2
    for one_mapping in mapping:
        assert one_mapping
        for value in one_mapping.values():
            assert set(value) == {"seq_index", "chain"}
    assert abs(len(mapping[0]) - len(mapping[1])) < 10


@pytest.mark.integration
def test_calculate_fingerprint_raises_on_mismatched_sequences(
    structure_1dd6, structure_mpro_x0072
):
    """
    1dd6 (sample_pdbs) and Mpro-x0072 (diamond_xchem) are unrelated proteins
    that both happen to have residues at sequence positions 4-8. Reusing the
    same positional seq_index mapping for both and asking for a cumulative,
    labeled fingerprint with ensure_same_sequence=True should raise a
    ValueError, since the residue names at each shared position differ.
    """
    fp = InteractionFingerprint()
    shared_positions = range(4, 9)
    indices_1dd6 = {i: {"seq_index": i, "chain": "any"} for i in shared_positions}
    indices_mpro = {i: {"seq_index": i, "chain": "any"} for i in shared_positions}

    with pytest.raises(ValueError):
        fp.calculate_fingerprint(
            [structure_1dd6, structure_mpro_x0072],
            residue_indices=[indices_1dd6, indices_mpro],
            cumulative=True,
            labeled=True,
            ensure_same_sequence=True,
        )


@pytest.mark.integration
def test_calculate_fingerprint_removes_empty_rows_and_columns(structure_mpro_x0072):
    """
    With remove_non_interacting_residues=True and
    remove_empty_interaction_types=True, the resulting DataFrame should
    contain no all-zero rows or columns, even though the full residue list
    was requested.
    """
    fp = InteractionFingerprint()
    indices = {
        r.seq_index: {"seq_index": r.seq_index, "chain": r.chain}
        for r in structure_mpro_x0072.residues
    }

    df = fp.calculate_fingerprint(
        [structure_mpro_x0072],
        residue_indices=[indices],
        cumulative=True,
        labeled=True,
        as_dataframe=True,
        remove_non_interacting_residues=True,
        remove_empty_interaction_types=True,
    )

    assert not df.empty
    assert (df.sum(axis=1) != 0).all()
    assert (df.sum(axis=0) != 0).all()
