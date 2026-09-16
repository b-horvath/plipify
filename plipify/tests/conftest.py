import shutil
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parents[1] / "data"
SAMPLE_PDBS_DIR = DATA_DIR / "sample_pdbs"
DIAMOND_XCHEM_DIR = DATA_DIR / "diamond_xchem_screen_mpro_all_pdbs"


@pytest.fixture(scope="session")
def sample_pdbs_dir():
    """Directory holding the small, mixed-origin sample PDB/CIF files."""
    return SAMPLE_PDBS_DIR


@pytest.fixture(scope="session")
def diamond_xchem_dir():
    """Directory holding the Diamond XChem Mpro fragment-screen PDB files."""
    return DIAMOND_XCHEM_DIR


@pytest.fixture(scope="session")
def structure_1dd6():
    """A plipify.core.Structure parsed from sample_pdbs/1dd6.pdb, shared
    across tests to avoid re-running PLIP's (slow) structure preparation."""
    pytest.importorskip("plip")
    from plipify.core import Structure

    pdb = SAMPLE_PDBS_DIR / "1dd6.pdb"
    if not pdb.exists():
        pytest.skip(f"sample PDB not available: {pdb}")
    return Structure.from_pdbfile(str(pdb))


@pytest.fixture(scope="session")
def structure_mpro_x0072():
    """A Structure parsed from diamond_xchem_screen_mpro_all_pdbs/Mpro-x0072.pdb."""
    pytest.importorskip("plip")
    from plipify.core import Structure

    pdb = DIAMOND_XCHEM_DIR / "Mpro-x0072.pdb"
    if not pdb.exists():
        pytest.skip(f"sample PDB not available: {pdb}")
    return Structure.from_pdbfile(str(pdb))


@pytest.fixture(scope="session")
def structure_mpro_x0104():
    """A second Structure from the diamond XChem Mpro screen, used together
    with structure_mpro_x0072 for cross-structure alignment/fingerprint tests."""
    pytest.importorskip("plip")
    from plipify.core import Structure

    pdb = DIAMOND_XCHEM_DIR / "Mpro-x0104.pdb"
    if not pdb.exists():
        pytest.skip(f"sample PDB not available: {pdb}")
    return Structure.from_pdbfile(str(pdb))


@pytest.fixture
def muscle_available():
    """True if the `muscle` CLI (needed for sequence alignment) is on PATH."""
    return shutil.which("muscle") is not None


@pytest.fixture
def sample_fingerprint_df():
    """Create a simple fingerprint dataframe for testing."""
    data = {
        "hydrophobic": [1, 2, 0, 1],
        "hbond-don": [0, 1, 2, 0],
        "hbond-acc": [1, 0, 1, 2],
        "saltbridge": [0, 0, 1, 0],
    }
    df = pd.DataFrame(data, index=[1, 2, 3, 4])
    df.index.name = "residue_id"
    return df


@pytest.fixture
def empty_fingerprint_df():
    """Create an empty fingerprint dataframe (all zeros)."""
    data = {
        "hydrophobic": [0, 0],
        "hbond-don": [0, 0],
    }
    return pd.DataFrame(data, index=[1, 2])


@pytest.fixture
def empty_fingerprint_df_start_at_zero():
    """Empty fingerprint starting at index 0 (array-style)."""
    data = {
        "hydrophobic": [0, 0],
        "hbond-don": [0, 0],
    }
    return pd.DataFrame(data, index=[0, 1])


@pytest.fixture
def empty_fingerprint_df_start_at_one():
    """Empty fingerprint starting at index 1 (biology-style)."""
    data = {
        "hydrophobic": [0, 0],
        "hbond-don": [0, 0],
    }
    return pd.DataFrame(data, index=[1, 2])


@pytest.fixture
def large_fingerprint_df():
    """Create a larger fingerprint dataframe."""
    interactions = [
        "hydrophobic", "hbond-don", "hbond-acc", "waterbridge",
        "saltbridge", "pistacking", "pication", "halogen", "metal"
    ]
    data = {interaction: np.random.randint(0, 3, 10) for interaction in interactions}
    return pd.DataFrame(data, index=range(1, 11))