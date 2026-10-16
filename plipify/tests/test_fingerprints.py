"""
Draft unit tests for plipify.fingerprints.

These exercise the pure-Python parts of the interaction-fingerprint
machinery: the ``_LabeledValue`` helper, single-structure fingerprint
construction, cumulative accumulation across structures and the top-level
``InteractionFingerprint.calculate_fingerprint`` orchestration.

``InteractionFingerprint.calculate_indices_mapping`` shells out to the
external ``muscle`` aligner, so it is only covered by a single, opt-in
integration test.
"""

import numpy as np
import pytest

from plipify.core import (
    HbondDonorInteraction,
    HydrophobicInteraction,
    ProteinResidue,
    Structure,
)
from plipify.fingerprints import InteractionFingerprint, _LabeledValue


###
# Helpers
###


def make_structure(*specs):
    """specs: ``(name, seq_index, chain, *interactions)`` tuples."""
    residues = []
    for name, seq_index, chain, *interactions in specs:
        residues.append(
            ProteinResidue(
                name=name,
                seq_index=seq_index,
                chain=chain,
                interactions=list(interactions),
            )
        )
    structure = Structure(residues=residues)
    # ``from_pdbfile`` normally sets this; hand-built structures need it so
    # ``repr(structure)`` / ``.description`` stay usable (some code paths log it).
    structure.ignored_ligands = []
    return structure


def any_index(seq_index):
    """The kwargs shape ``get_residue_by`` expects, matching any chain."""
    return {"seq_index": seq_index, "chain": "any"}


###
# _LabeledValue
###


class TestLabeledValue:
    def test_stores_value_and_label(self):
        label = {"type": "hbond-don", "residue": ProteinResidue("ALA", 1, "A")}
        lv = _LabeledValue(3, label=label)
        assert lv.value == 3
        assert lv.label is label

    def test_repr_mentions_value_and_label(self):
        lv = _LabeledValue(2, label={"type": "hydrophobic"})
        text = repr(lv)
        assert "2" in text
        assert "hydrophobic" in text


###
# Construction
###


class TestInit:
    def test_default_interaction_types(self):
        fp = InteractionFingerprint()
        assert fp.indices is None
        assert "hydrophobic" in fp.interaction_types
        assert "covalent" in fp.interaction_types

    def test_custom_interaction_types(self):
        fp = InteractionFingerprint(interaction_types=("hbond-don",))
        assert fp.interaction_types == ("hbond-don",)

    def test_clear_fingerprint(self):
        fp = InteractionFingerprint()
        fp.clear_fingerprint()
        assert fp._fingerprint is None


###
# _calculate_fingerprint_one_structure
###


class TestCalculateFingerprintOneStructure:
    def setup_method(self):
        self.fp = InteractionFingerprint(interaction_types=("hbond-don", "hydrophobic"))
        self.structure = make_structure(
            ("ALA", 1, "A", HbondDonorInteraction({}), HydrophobicInteraction({})),
            ("GLY", 2, "A", HydrophobicInteraction({})),
        )

    def test_unlabeled_returns_counts_array(self):
        out = self.fp._calculate_fingerprint_one_structure(
            self.structure, [any_index(1), any_index(2)], labeled=False
        )
        assert isinstance(out, np.ndarray)
        # [res1 hbond-don, res1 hydrophobic, res2 hbond-don, res2 hydrophobic]
        assert list(out) == [1, 1, 0, 1]

    def test_length_is_residues_times_interaction_types(self):
        out = self.fp._calculate_fingerprint_one_structure(
            self.structure, [any_index(1), any_index(2)], labeled=False
        )
        assert len(out) == 2 * 2

    def test_labeled_returns_labeled_values(self):
        out = self.fp._calculate_fingerprint_one_structure(
            self.structure, [any_index(1)], labeled=True
        )
        assert all(isinstance(x, _LabeledValue) for x in out)
        assert out[0].label["type"] == "hbond-don"
        assert out[0].label["residue"].name == "ALA"
        assert out[0].value == 1

    def test_missing_residue_becomes_gap_with_zeros(self):
        # An empty kwargs dict makes ``get_residue_by`` return None,
        # which the factory backfills with a synthetic GAP residue.
        out = self.fp._calculate_fingerprint_one_structure(
            self.structure, [{}], labeled=True
        )
        assert [x.value for x in out] == [0, 0]
        assert out[0].label["residue"].name == "GAP"


###
# _acumulate_fingerprints
###


class TestAcumulateFingerprints:
    def setup_method(self):
        self.fp = InteractionFingerprint(interaction_types=("hbond-don", "hydrophobic"))

    def _labeled(self, structure):
        return self.fp._calculate_fingerprint_one_structure(
            structure, [any_index(1)], labeled=True
        )

    def test_unlabeled_sums_positionwise(self):
        a = np.array([1, 0, 2, 0])
        b = np.array([0, 3, 1, 0])
        out = self.fp._acumulate_fingerprints([a, b])
        assert list(out) == [1, 3, 3, 0]

    def test_labeled_sums_and_rebuilds_residue(self):
        s1 = make_structure(("ALA", 1, "A", HbondDonorInteraction({})))
        s2 = make_structure(
            ("ALA", 1, "A", HbondDonorInteraction({}), HbondDonorInteraction({}))
        )
        out = self.fp._acumulate_fingerprints([self._labeled(s1), self._labeled(s2)])
        assert [x.value for x in out] == [3, 0]
        assert isinstance(out[0], _LabeledValue)
        assert out[0].label["residue"].name == "ALA"

    def test_labeled_mismatched_residues_raise(self):
        s1 = make_structure(("ALA", 1, "A", HbondDonorInteraction({})))
        s2 = make_structure(("GLY", 1, "A", HbondDonorInteraction({})))
        with pytest.raises(ValueError):
            self.fp._acumulate_fingerprints([self._labeled(s1), self._labeled(s2)])

    def test_labeled_mismatch_ignored_when_disabled(self):
        s1 = make_structure(("ALA", 1, "A", HbondDonorInteraction({})))
        s2 = make_structure(("GLY", 1, "A", HbondDonorInteraction({})))
        out = self.fp._acumulate_fingerprints(
            [self._labeled(s1), self._labeled(s2)], ensure_same_sequence=False
        )
        assert [x.value for x in out] == [2, 0]

    def test_labeled_conflicting_types_raise(self):
        residue = ProteinResidue("ALA", 1, "A")
        pos_a = _LabeledValue(1, label={"residue": residue, "type": "hbond-don"})
        pos_b = _LabeledValue(1, label={"residue": residue, "type": "hydrophobic"})
        with pytest.raises(ValueError):
            self.fp._acumulate_fingerprints([[pos_a], [pos_b]])


###
# calculate_fingerprint (orchestration)
###


class TestCalculateFingerprint:
    def setup_method(self):
        self.fp = InteractionFingerprint(interaction_types=("hbond-don", "hydrophobic"))
        self.structure = make_structure(
            ("ALA", 1, "A", HbondDonorInteraction({})),
            ("GLY", 2, "A"),
        )
        self.mapping = {
            1: {"seq_index": 1, "chain": "any"},
            2: {"seq_index": 2, "chain": "any"},
        }

    def test_indices_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            self.fp.calculate_fingerprint(
                [self.structure], residue_indices=[self.mapping, self.mapping]
            )

    def test_non_cumulative_returns_per_structure_list(self):
        out = self.fp.calculate_fingerprint(
            [self.structure],
            residue_indices=[self.mapping],
            labeled=False,
            cumulative=False,
        )
        assert len(out) == 1
        assert list(out[0]) == [1, 0, 0, 0]

    def test_labeled_dataframe(self):
        df = self.fp.calculate_fingerprint(
            [self.structure],
            residue_indices=[self.mapping],
            labeled=True,
            cumulative=True,
            as_dataframe=True,
        )
        assert list(df.columns) == ["hbond-don", "hydrophobic"]
        assert list(df.index) == [1, 2]
        assert df.loc[1, "hbond-don"] == 1
        assert df.loc[2].tolist() == [0, 0]

    def test_remove_non_interacting_residues(self):
        df = self.fp.calculate_fingerprint(
            [self.structure],
            residue_indices=[self.mapping],
            labeled=True,
            cumulative=True,
            as_dataframe=True,
            remove_non_interacting_residues=True,
        )
        assert list(df.index) == [1]

    def test_remove_empty_interaction_types(self):
        df = self.fp.calculate_fingerprint(
            [self.structure],
            residue_indices=[self.mapping],
            labeled=True,
            cumulative=True,
            as_dataframe=True,
            remove_empty_interaction_types=True,
        )
        assert list(df.columns) == ["hbond-don"]

    def test_missing_residue_indices_triggers_auto_mapping(self, monkeypatch):
        seen = {}

        def fake_mapping(structures):
            seen["count"] = len(structures)
            return [self.mapping]

        monkeypatch.setattr(
            InteractionFingerprint,
            "calculate_indices_mapping",
            staticmethod(fake_mapping),
        )
        df = self.fp.calculate_fingerprint(
            [self.structure], labeled=True, cumulative=True, as_dataframe=True
        )
        assert seen["count"] == 1
        assert list(df.index) == [1, 2]

    def test_structure_processing_error_is_warned_and_skipped(self, capsys):
        # ``seq_index=99`` matches no residue, so the per-structure factory
        # raises and ``calculate_fingerprint`` swallows it with a warning.
        bad_mapping = {1: {"seq_index": 99, "chain": "A"}}
        out = self.fp.calculate_fingerprint(
            [self.structure],
            residue_indices=[bad_mapping],
            labeled=False,
            cumulative=False,
        )
        assert out == []
        assert "could not process structure" in capsys.readouterr().out


###
# Integration: calculate_indices_mapping (needs Biopython + muscle)
###


@pytest.mark.integration
def test_calculate_indices_mapping_smoke():
    pytest.importorskip("Bio")
    import shutil

    if shutil.which("muscle") is None:
        pytest.skip("muscle aligner not installed")

    structures = []
    for name in ("a", "b"):
        s = make_structure(("ALA", 1, "A"), ("GLY", 2, "A"), ("HIS", 3, "A"))
        s._path = f"{name}.pdb"
        structures.append(s)

    mapping = InteractionFingerprint.calculate_indices_mapping(structures)
    assert len(mapping) == len(structures)
    assert all(isinstance(m, dict) for m in mapping)
