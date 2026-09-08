import pytest
import pandas as pd
import numpy as np


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