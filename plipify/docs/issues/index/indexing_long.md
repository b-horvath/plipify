## Description
When trying to run between different pdb files found in link [here](https://github.com/b-horvath/plipify/commit/64e352057b434f9728de089187b269ada95c5806#diff-58a101629186b04efbf8e99e9661d1eff107e3a001c0309dbf00b20c30ddac4f), the pytests were functional, however, the pytest threw an Exception Error

Wrong order - 548 was being thrown before the other 

Error: 
```
python -m pytest -W "ignore" -v plipify/tests/test_core.py
================================================================================================== test session starts ===================================================================================================
platform darwin -- Python 3.11.13, pytest-9.1.1, pluggy-1.6.0 -- /Users/benhorvath/Desktop/jobs/volkamer/plipify/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/benhorvath/Desktop/jobs/volkamer/plipify
configfile: pyproject.toml
plugins: mock-3.15.1, anyio-4.14.2
collected 39 items                                                                                                                                                                                                       

plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[ALA] PASSED                                                                                                                         [  2%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[ARG] PASSED                                                                                                                         [  5%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[GLY] PASSED                                                                                                                         [  7%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[TRP] PASSED                                                                                                                         [ 10%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[ILE] PASSED                                                                                                                         [ 12%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[VAL] PASSED                                                                                                                         [ 15%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[LYS] PASSED                                                                                                                         [ 17%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[HIS] PASSED                                                                                                                         [ 20%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[ASP] PASSED                                                                                                                         [ 23%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[MET] PASSED                                                                                                                         [ 25%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[THR] PASSED                                                                                                                         [ 28%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[GLN] PASSED                                                                                                                         [ 30%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[LEU] PASSED                                                                                                                         [ 33%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[CYS] PASSED                                                                                                                         [ 35%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[PHE] PASSED                                                                                                                         [ 38%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[TYR] PASSED                                                                                                                         [ 41%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[ASN] PASSED                                                                                                                         [ 43%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[SER] PASSED                                                                                                                         [ 46%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[PRO] PASSED                                                                                                                         [ 48%]
plipify/tests/test_core.py::TestProteinResidue::test_all_allowed_residue_names[GLU] PASSED                                                                                                                         [ 51%]
plipify/tests/test_core.py::TestProteinResidue::test_identifier PASSED                                                                                                                                             [ 53%]
plipify/tests/test_core.py::TestProteinResidue::test_one_and_three_letter_codes PASSED                                                                                                                             [ 56%]
plipify/tests/test_core.py::TestProteinResidue::test_is_protein PASSED                                                                                                                                             [ 58%]
plipify/tests/test_core.py::TestProteinResidue::test_invalid_is_protein PASSED                                                                                                                                     [ 61%]
plipify/tests/test_core.py::TestProteinResidue::test_count_interactions PASSED                                                                                                                                     [ 64%]
plipify/tests/test_core.py::TestProteinResidue::test_repr_with_and_without_interactions PASSED                                                                                                                     [ 66%]
plipify/tests/test_core.py::test_ligand_residue_is_base_residue PASSED                                                                                                                                             [ 69%]
plipify/tests/test_core.py::test_interaction_shorthand[HydrophobicInteraction-hydrophobic] PASSED                                                                                                                  [ 71%]
plipify/tests/test_core.py::test_interaction_shorthand[HbondInteraction-hbond] PASSED                                                                                                                              [ 74%]
plipify/tests/test_core.py::test_interaction_shorthand[HbondDonorInteraction-hbond-don] PASSED                                                                                                                     [ 76%]
plipify/tests/test_core.py::test_interaction_shorthand[HbondAcceptorInteraction-hbond-acc] PASSED                                                                                                                  [ 79%]
plipify/tests/test_core.py::test_interaction_shorthand[CovalentInteraction-covalent] PASSED                                                                                                                        [ 82%]
plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_loads_pdb_format PASSED                                                                                                                          [ 84%]
plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_pdb_format_residues_are_protein_residues PASSED                                                                                                  [ 87%]
plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_pdb_format_loads_across_multiple_sample_files[1AER.pdb] PASSED                                                                                   [ 89%]
plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_pdb_format_loads_across_multiple_sample_files[1dd6.pdb] PASSED                                                                                   [ 92%]
plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_pdb_format_loads_across_multiple_sample_files[6F8B.pdb] FAILED                                                                                   [ 94%]
plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_cif_format_is_not_supported PASSED                                                                                                               [ 97%]
plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_pdb_and_cif_formats_describe_the_same_structure PASSED                                                                                           [100%]

======================================================================================================== FAILURES ========================================================================================================
______________________________________________________________ TestStructureFromPdbfileFormats.test_pdb_format_loads_across_multiple_sample_files[6F8B.pdb] ______________________________________________________________

self = <plipify.tests.test_core.TestStructureFromPdbfileFormats object at 0x10998e0d0>, pdb_path = PosixPath('/Users/benhorvath/Desktop/jobs/volkamer/plipify/plipify/data/sample_pdbs/6F8B.pdb')

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
    
>       structure = Structure.from_pdbfile(str(pdb_path))
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

plipify/tests/test_core.py:175: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
plipify/core.py:374: in from_pdbfile
    residue = structure.get_residue_by(seq_index=seq_index, chain=chain)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <[AttributeError("'Structure' object has no attribute 'ignored_ligands'") raised in repr()] Structure object at 0x10de70c50>, index = None, seq_index = 548, chain = 'A'

    def get_residue_by(self, index=None, seq_index=None, chain=None):
        """
        Access residues by either position in the Python list (index)
        or their sequence identifier in the PDB records (seq_index)
    
        Parameters
        ----------
        index, seq_index : int
        chain : str or None
            If chain is None or "any", behaviour is not specified
            shall there exist more than one residue with that
            seq_index. If None, a warning will be emitted; this
            warning is omitted if chain == "any".
        """
    
        if index is None and seq_index is None:
            return None
        if index is not None and seq_index is not None:
            raise ValueError("Can only specify index OR seq_index, not both")
        if index is not None and chain not in (None, "any"):
            raise ValueError("`index` does not support `chain` spec")
    
        if index is not None:
            return self.residues[index]
        if seq_index is not None:
            for residue in self.residues:
                if residue.seq_index == seq_index:
                    if chain is None:  # TODO: Check there are no other residues with same index!
                        print(
                            "! Warning, you didn't select a chain. "
                            "First match will be returned but there could be more."
                        )
                        break
                    elif chain in ("any", residue.chain):
                        break
            else:  # break not reached!
>               raise ValueError(
                    "No residue with such sequence index: {}, {}!".format(seq_index, chain)
                )
E               ValueError: No residue with such sequence index: 548, A!

plipify/core.py:459: ValueError
================================================================================================ short test summary info =================================================================================================
FAILED plipify/tests/test_core.py::TestStructureFromPdbfileFormats::test_pdb_format_loads_across_multiple_sample_files[6F8B.pdb] - ValueError: No residue with such sequence index: 548, A!
============================================================================================== 1 failed, 38 passed in 4.46s ==============================================================================================
```

## Current Problem:
The current problem is that the current model treats the input pdb exclusively as a ProteinResidue that only takes in the [canonical amino acids](https://github.com/volkamerlab/plipify/blob/master/plipify/core.py#L190-193).

Other problems that could contribute to this is:
1. We know that core.py only handles any inputs solely as ProteinResidues as [LigandResidue](https://github.com/volkamerlab/plipify/blob/master/plipify/core.py#L230-237) is not built out yet:
```
class LigandResidue(BaseResidue):
    """
    A small molecule in the vicinity of a binding site
    """

    # TODO: Fill list in!
    _ALLOWED_RESIDUE_NAMES = []
```
2. Start here - in plip/exchange/report.py, we have this below.... talk about how it's mishandled and need to see how the data structure looks like still
```
interaction_dict = dict(zip(features, interaction_data))
                        print("[DICT]", shorthand, interaction_dict) 
                        seq_index, chain = (
                            interaction_dict["RESNR"],
                            interaction_dict["RESCHAIN"],
                        )
```


Attempted Solutions:

- 