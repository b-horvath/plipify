"""
core.py

This module collects the base objects that will be
used across the different stages of the pipeline.

Namely:

- Interaction, which "connects" two residues
- Residue, the most basic interacting component
- Structure, a list of binding sites
- BindingSite, a list of residues, within a Structure
- Dataset, a collection of structures
"""

from collections import defaultdict, Counter
from pathlib import Path

from Bio.Data import IUPACData
import pandas as pd

###
# Interaction Types
###


class BaseInteraction:
    """
    This the base class for all interaction types

    Parameters
    ----------
    interaction : dict
        Unspecified schema. Might be different per interaction type!
        For example, HBonds might have donor and acceptors,
        but hydrophobic are not aware of such a concept.
    """

    shorthand = ""

    def __init__(self, interaction):
        self.interaction = interaction

    def __getitem__(self, value):
        return self.interaction[value]

    def __repr__(self):
        return f"<{self.__class__.__name__} with {self.interaction}>"

    def to_dataframe(self):
        return pd.DataFrame.from_dict(self.interaction, orient="index").T

    def _ipython_display_(self):
        if self.interaction:
            from IPython.display import display

            display(self.to_dataframe())


"""
Shall we derive the RGB values from plip(to make it more consistent with plip)?
https://github.com/pharmai/plip/blob/2f4911d307490479ac023b22d6faa8f59b577ca8/DOCUMENTATION.md#L154-L161
or where did these original values come from
"""
class HydrophobicInteraction(BaseInteraction):
    """
    HydrophobicInteraction, a subclass of BaseInteraction
    """

    shorthand = "hydrophobic"
    color_rgb = 0.90, 0.10, 0.29


class HbondInteraction(BaseInteraction):
    """
    HbondInteraction, a subclass of BaseInteraction
    """

    shorthand = "hbond"
    color_rgb = 0.26, 0.83, 0.96


class HbondDonorInteraction(HbondInteraction):
    """
    HbondInteraction, a subclass of BaseInteraction
    """

    shorthand = "hbond-don"
    color_rgb = 0.26, 0.83, 0.96


class HbondAcceptorInteraction(HbondInteraction):
    """
    HbondInteraction, a subclass of BaseInteraction
    """

    shorthand = "hbond-acc"
    color_rgb = 0.26, 0.83, 0.96


class WaterbridgeInteraction(BaseInteraction):
    """
    WaterbridgeInteraction, a subclass of BaseInteraction
    """

    shorthand = "waterbridge"
    color_rgb = 1.00, 0.88, 0.10


class SaltbridgeInteraction(BaseInteraction):
    """
    SaltbridgeInteraction, a subclass of BaseInteraction
    """

    shorthand = "saltbridge"
    color_rgb = 0.67, 1.00, 0.76


class PistackingInteraction(BaseInteraction):
    """
    PistackingInteraction, a subclass of BaseInteraction
    """

    shorthand = "pistacking"
    color_rgb = 0.75, 0.94, 0.27


class PicationInteraction(BaseInteraction):
    """
    PicationInteraction, a subclass of BaseInteraction
    """

    shorthand = "pication"
    color_rgb = 0.27, 0.60, 0.56


class HalogenInteraction(BaseInteraction):
    """
    HalogenInteraction, a subclass of BaseInteraction
    """

    shorthand = "halogen"
    color_rgb = 0.94, 0.20, 0.90


class MetalInteraction(BaseInteraction):
    """
    MetalInteraction, a subclass of BaseInteraction
    """

    shorthand = "metal"
    color_rgb = 0.90, 0.75, 1.00


class CovalentInteraction(BaseInteraction):
    """
    CovalentInteraction, a subclass of BaseInteraction
    """

    shorthand = "covalent"
    color_rgb = 0, 0, 0


###
#  Structural objects
###


class BaseResidue:
    """
    A collection of covalently bonded atoms
    """

    _ALLOWED_RESIDUE_NAMES = [] 

    def __init__(self, name):
        self.name = self._check_valid_name(name)

    def _check_valid_name(self, name):
        if not self._ALLOWED_RESIDUE_NAMES:  # TODO: no checks defined!
            return name
        if name in self._ALLOWED_RESIDUE_NAMES:
            return name
        raise ValueError(
            "Residue name {} is not valid! Must be one of ({})".format(
                name, ", ".join(self._ALLOWED_RESIDUE_NAMES)
            )
        )


class ProteinResidue(BaseResidue):
    """
    A residue belonging to a protein sequence
    """

    _ALLOWED_RESIDUE_NAMES = {
        "ALA", "ARG","ASN","ASP","CYS",
        "GLN","GLU","GLY","HIS","ILE",
        "LEU","LYS","MET","PHE","PRO",
        "SER","THR","TRP","TYR","VAL"
    }

    def __init__(self, name, seq_index, chain, interactions=None, structure=None):
        super().__init__(name) # check for valid residue from BaseResidue
        self.seq_index = seq_index
        self.name = name
        self.chain = chain
        self.interactions = interactions or []
        self.structure = structure

    def count_interactions(self):
        interaction_types = [interaction.shorthand for interaction in self.interactions]
        counter = Counter(interaction_types)
        return counter

    def __repr__(self):
        if self.interactions:
            return "<ProteinResidue {}, and {} interactions>".format(
                self.identifier, len(self.interactions)
            )
        return "<ProteinResidue {}>".format(self.identifier)

    @property
    def identifier(self):
        return "{}:{}.{}".format(self.name, self.seq_index, self.chain)

    # Need to find implementation because this method not used anywhere in plipify/
    @property
    def is_protein(self):
        return self.name.title() in IUPACData.protein_letters_3to1

    @property
    def one_letter_code(self):
        return IUPACData.protein_letters_3to1[self.name.title()]

    @property
    def three_letter_code(self):
        return self.name.title()


class LigandResidue(BaseResidue):
    """
    A small molecule in the vicinity of a binding site
    - TODO: needs to have a library of acceptable residues: https://www.wwpdb.org/data/ccd
    - maybe use BioPython -> protein_letters_3to1
    """

    # TODO: Fill list in! 
    _ALLOWED_RESIDUE_NAMES = [] # Is there a database for knowing what residues we can load?
       


class BindingSite:
    """
    A collection of protein residues and ligands
    """

    def __init__(self, interactions, name=None):
        self.interactions = interactions
        self.name = name

    def __repr__(self):
        return "<BindingSite with name='{}' and {} interaction types>".format(
            self.name,
            len([interaction for interaction in self.interactions.values() if interaction]),
        )

    def to_dataframes(self):
        import pandas as pd

        for itype, interactions in self.interactions.items():
            yield itype, pd.concat([i.to_dataframe() for i in interactions])


class Structure:
    """
    A collection of ProteinResidue objects, and potentially LigandResidue
    objects, which can define one or more BindingSite objects.

    Parameters
    ----------
    residues : list of ProteinResidue
        Order is relevant, it's assumed that the order of the residues
        dictate the sequence of the protein.
    ligands: list of PLIP Ligand objects
    binding_sites: dict of {str: }

    """

    INTERACTIONS = (
        HydrophobicInteraction,
        HbondInteraction,
        WaterbridgeInteraction,
        SaltbridgeInteraction,
        PistackingInteraction,
        PicationInteraction,
        HalogenInteraction,
        MetalInteraction,
        # CovalentInteraction - TODO: buggy- needs further looking into
    )

    def __init__(self, residues=None, ligands=None, binding_sites=None):
        self.residues = residues or []
        self.ligands = ligands or []
        self.binding_sites = binding_sites or []
        self._path = None
        self._pdbcomplex = None

    @classmethod
    def from_pdbfile(cls, path, ligand_name=None, protonate=True):
        """
        Read pdb file and then collect and process PLIP data.

        Parameters
        ----------
        path : str
            Path to an existing PDB file
        ligand_name : str or tuple of str
            A string that the binding site names start with, when they are ligand binding sites.
            If filled, only binding sites with this identifier will be considered.
        protonate : bool, optional=True
            Whether to allow PLIP to automatically protonate the structure or not. If you
            choose False, take into account that you should provide already protonated
            structures for accurate results.
        """
        if not protonate:
            from plip.basic import config

            config.NOHYDRO = not protonate
        from plip.structure.preparation import PDBComplex
        from plip.exchange.report import BindingSiteReport

        #Use plip to generate an object for the pdb complex
        pdbcomplex = PDBComplex()
        pdbcomplex.load_pdb(path)

        structure = cls()
        structure._path = path

        residues = []

        #TODO: source of the problem - understand why the water at index 548 (why was the rest skipped)
        for r in pdbcomplex.resis:
            #recall that ProteinResidue only allows for the 20 amino acid list 
            residue = ProteinResidue(
                name=r.GetName(),
                seq_index=r.GetNum(),
                chain=r.GetChain(),
                structure=structure,
            )
            print(residue)
            residues.append(residue)

        structure.residues = residues

        # >>>>> DEBUG START (residue loading) — remove this whole block
        # Walk every residue OpenBabel read from the file and say whether it became a ProteinResidue
        from plip.structure.preparation import pybel
        _dbg_loaded = {(r.GetName(), r.GetNum(), r.GetChain()) for r in pdbcomplex.resis}
        _dbg_skipped = defaultdict(list)
        print(f"\n[residues] ===== residue loading for {path} =====")
        for _dbg_i, _dbg_r in enumerate(pybel.ob.OBResidueIter(pdbcomplex.protcomplex.OBMol)):
            _dbg_key = (_dbg_r.GetName(), _dbg_r.GetNum(), _dbg_r.GetChain())
            _dbg_status = "LOADED as ProteinResidue" if _dbg_key in _dbg_loaded else "not a protein residue -> skipped"
            print(f"[residues] #{_dbg_i:<4} {_dbg_key[0]:>4} {_dbg_key[1]:>5} chain={_dbg_key[2]} "
                  f"atoms={_dbg_r.GetNumAtoms():<3} {_dbg_status}")
            if _dbg_key not in _dbg_loaded:
                _dbg_skipped[_dbg_key[0]].append(_dbg_key[1])
        print(f"[residues] loaded {len(residues)} protein residues")
        for _dbg_name, _dbg_nums in sorted(_dbg_skipped.items()):
            print(f"[residues] skipped {len(_dbg_nums)} x {_dbg_name}: seq_index {min(_dbg_nums)}..{max(_dbg_nums)}")
        # <<<<< DEBUG END (residue loading)

        ligands = []
        ignored_ligands = []
        for ligand in pdbcomplex.ligands:
            #TODO: non-ligand like things that should be ignored 
            #This creates a non-exhaustive list, but needs to include some exceptions(ie. metal fingerprints) 
            #TODO: create non-exhaustive list of artifacts in PDB files that should be ignored? 
            #Hamza suggested that if it's not a ligand, it will just be ignored
            #EXCLUDE_LIGANDS = {"EDO", "GOL", "SO4", "ACT", "FMT", "PEG", "DMS", "CL", "NA"}
            if ligand_name is not None and not ligand.longname.startswith(ligand_name):
                ignored_ligands.append(ligand)
                continue
            pdbcomplex.characterize_complex(ligand)
            ligands.append(ligand)

        binding_sites = []
        #TODO: create print flow mechanism of how the binding sites are processed
        for key, site in sorted(pdbcomplex.interaction_sets.items()):
            report = BindingSiteReport(site)
            interactions = []
            if ligand_name is None or key.startswith(ligand_name):
                for InteractionType in cls.INTERACTIONS:
                    shorthand = InteractionType.shorthand
                    if shorthand == "hbond-acc": #why are we reassigning this here
                        shorthand == "hbond"
                    elif shorthand == "hbond-don":
                        continue  # skip, we processed it already
                    features = getattr(report, shorthand + "_features")
                    # list of BaseInteraction Subclasses (depending on type)
                    for interaction_data in getattr(report, shorthand + "_info"):
                        #TODO: main index problem - embedding the pdb correctly
                        # Generate a dictionary, with the features being the key and the interaction_data being the values
                        interaction_dict = dict(zip(features, interaction_data))
                        print("[DICT]", shorthand, interaction_dict) 
                        seq_index, chain = (
                            interaction_dict["RESNR"],
                            interaction_dict["RESCHAIN"],
                        )

                        # # SUGGESTED FIX: metal complexes can name a water (LOCATION="water") or the
                        # # ligand itself (LOCATION="ligand") as the coordinating partner. PLIP keeps
                        # # those contacts in the complex but leaves HOH/LIG out of its interacting
                        # # residues (PLINteraction.interacting_res), so we do the same: keep the
                        # # interaction on the binding site, but don't attach it to a protein residue.
                        # if not interaction_dict.get("LOCATION", "protein").startswith("protein"):
                        #     # >>>>> DEBUG START (non-protein partner) — remove this whole block
                        #     print(f"[from_pdbfile]      skipping residue lookup for non-protein partner: "
                        #           f"{interaction_dict['RESTYPE']} {seq_index}:{chain} "
                        #           f"LOCATION={interaction_dict['LOCATION']}")
                        #     # <<<<< DEBUG END (non-protein partner)
                        #     interactions.append(InteractionType(interaction=interaction_dict))
                        #     continue
                        
                        if not interaction_dict.get("LOCATION", "protein").startswith("protein"):
                            interactions.append(InteractionType(interaction=interaction_dict))
                            continue
                        # ORIGINAL (restore below line when removing debug):
                        residue = structure.get_residue_by(seq_index=seq_index, chain=chain)
                        if shorthand == "hbond":
                            if interaction_dict["PROTISDON"]:
                                interaction_obj = HbondDonorInteraction(
                                    interaction=interaction_dict
                                )
                            else:
                                interaction_obj = HbondAcceptorInteraction(
                                    interaction=interaction_dict
                                )
                        else:
                            interaction_obj = InteractionType(interaction=interaction_dict)
                        interactions.append(interaction_obj)
                        residue.interactions.append(interaction_obj)

                interactions_by_type = defaultdict(list)
                for i in interactions:
                    interactions_by_type[i.shorthand].append(i)

                binding_site = BindingSite(interactions_by_type, name=key)
                binding_sites.append(binding_site)

        for cov in pdbcomplex.covalent:
            covkey = f"{cov.id1}:{cov.chain1}:{cov.pos1}"
            ligand_idx, prot_idx = 1, 2
            if cov.id1.upper() in ProteinResidue._ALLOWED_RESIDUE_NAMES:
                ligand_idx, prot_idx = 2, 1

            for bs in binding_sites:
                if bs.name == covkey:
                    bs.interactions["covalent"].append(
                        CovalentInteraction(
                            {
                                "RESNR": getattr(cov, f"pos{prot_idx}"),
                                "RESTYPE": getattr(cov, f"id{prot_idx}"),
                                "RESCHAIN": getattr(cov, f"chain{prot_idx}"),
                                "RESNR_LIG": getattr(cov, f"pos{ligand_idx}"),
                                "RESTYPE_LIG": getattr(cov, f"id{ligand_idx}"),
                                "RESCHAIN_LIG": getattr(cov, f"chain{ligand_idx}"),
                            }
                        )
                    )

        structure.binding_sites = binding_sites
        structure.ligands = ligands
        structure.ignored_ligands = ignored_ligands
        structure._pdbcomplex = pdbcomplex
        return structure

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
                raise ValueError(
                    "No residue with such sequence index: {}, {}!".format(seq_index, chain)
                )
            return residue

    def sequence(self, with_gaps=True):
        if not with_gaps:
            return "".join([r.one_letter_code for r in self.residues])

        aabypos = {r.seq_index: r.one_letter_code for r in self.residues}
        max_residue = max(r.seq_index for r in self.residues)
        return "".join([aabypos.get(i, "-") for i in range(1, max_residue + 1)])

    @property
    def identifier(self):
        if self._path:
            return Path(self._path).stem

    @property
    def description(self):
        s = (
            f"{self.__class__.__name__} with {len(self.residues)} residues, "
            f"{len(self.ligands) + len(self.ignored_ligands)} ligands "
            f"({len(self.ignored_ligands)} of which were ignored) "
            f"and {len(self.binding_sites)} characterized binding sites."
        )
        if self._path:
            s += f" (loaded from file `{self._path}`)"
        return s

    def view(
        self, ligand_selection_query="ligand", solvent_selection_query="water", use_protonated=True
    ):
        """
        Show structure in NGLView

        Parameters
        ----------
        ligand_selection_query : str
            NGL selection query for the ligand(s) that should be depicted
            as ball&stick and centered.
        solvent_selection_query : str
            NGL selection query for the solvent molecules that should
            be depicted as lines.
        use_protonated : bool
            Try to to load the automatically protonated structure
            generated by PLIP before the original one (which might lack hydrogens)

        Returns
        -------
        nglview.NGLWidget
        """
        path = None
        if use_protonated:
            path = (
                Path(self._pdbcomplex._output_path)
                / f"{Path(self._pdbcomplex.sourcefiles['filename']).stem}_protonated.pdb"
            )
            if not path.exists():
                path = None
        if path is None:
            path = Path(self._path)

        if not path.exists():
            print(
                "3D View only available for structures loading from existing files."
                f"Path {path} cannot be accessed.."
            )
            return

        import nglview as nv

        with open(self._path) as f:
            v = nv.show_file(f, ext=path.suffix[1:], default_representation=False)
            v.add_cartoon()
            v.add_ball_and_stick(ligand_selection_query)
            v.add_line(solvent_selection_query)
            v.center(ligand_selection_query)
            interacting_residues = set()

            for bs in self.binding_sites:
                for interaction_type, interactions in bs.interactions.items():
                    for i in interactions:
                        interacting_residues.add(i["RESNR"])
                        if "LIGCOO" in i.interaction and "PROTCOO" in i.interaction:
                            label = (
                                f"{interaction_type.title()}: "
                                f"{i['RESTYPE']}.{i['RESNR']}:{i['RESCHAIN']}-"
                                f"{i['RESTYPE_LIG']}.{i['RESNR_LIG']}:{i['RESCHAIN_LIG']}"
                            )
                            v.shape.add_cylinder(
                                i["LIGCOO"], i["PROTCOO"], i.color_rgb, [0.1], label
                            )

            # Display interacting residues
            sidechains = " or ".join([f"({r} and not _H)" for r in interacting_residues])
            non_carbon_atoms = " or ".join(
                [f"({r} and ((_O) or (_N) or (_S)))" for r in interacting_residues]
            )
            v.add_ball_and_stick(sele=sidechains, colorScheme="chainindex", aspectRatio=1.5)
            v.add_ball_and_stick(sele=non_carbon_atoms, colorScheme="element", aspectRatio=1.5)

        return v

    def to_dataframes(self):
        try:
            from IPython.display import display, Markdown

            with_ipython = True
        except ImportError:
            with_ipython = False

        dfs = []
        for bs in self.binding_sites:
            if with_ipython:
                display(Markdown(f"### {bs.name}"))
            for itype, df in bs.to_dataframes():
                if with_ipython:
                    display(Markdown(f"#### {itype.title()}"))
                    display(df)
                dfs.append((bs, itype, df))
        return dfs

    def __repr__(self) -> str:
        return f"<{self.description}>"
