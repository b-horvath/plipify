# tests/test_visualization.py
import pytest
import pandas as pd
from plipify.visualization import _prepare_tabledata, fingerprint_barplot, fingerprint_heatmap


class TestPrepareTableData:
    """Tests for the _prepare_tabledata helper function."""
    
    def test_prepare_tabledata_basic(self, sample_fingerprint_df):
        """Test basic functionality of _prepare_tabledata."""
        fingerprint, interaction_index, residues = _prepare_tabledata(sample_fingerprint_df)
        
        # Check structure
        assert isinstance(fingerprint, list)
        assert isinstance(interaction_index, dict)
        assert isinstance(residues, list)
        
        # Check dimensions
        assert len(residues) == 4  # 4 residues
        assert len(fingerprint) == 4  # 4 rows
        assert len(interaction_index) == 16  # 4 residues × 4 interaction types
        
    def test_prepare_tabledata_residues(self, sample_fingerprint_df):
        """Test that residue order is preserved."""
        _, _, residues = _prepare_tabledata(sample_fingerprint_df)
        assert residues == [1, 2, 3, 4]
        
    def test_prepare_tabledata_interaction_index(self, sample_fingerprint_df):
        """Test that interaction_index maps correctly."""
        _, interaction_index, _ = _prepare_tabledata(sample_fingerprint_df)
        
        # Check mapping structure
        assert interaction_index[0] == "hydrophobic"
        assert interaction_index[4] == "hydrophobic"  # repeats for each residue
        assert interaction_index[1] == "hbond-don"
        
    def test_prepare_tabledata_values(self, sample_fingerprint_df):
        """Test that fingerprint values match input dataframe."""
        fingerprint, _, _ = _prepare_tabledata(sample_fingerprint_df)
        
        # First residue should be [1, 0, 1, 0]
        assert fingerprint[0] == [1, 0, 1, 0]
        # Second residue should be [2, 1, 0, 0]
        assert fingerprint[1] == [2, 1, 0, 0]


class TestFingerprintBarplot:
    """Tests for fingerprint_barplot visualization."""
    
    def test_barplot_returns_figure(self, sample_fingerprint_df):
        """Test that barplot returns a Plotly Figure object."""
        fig = fingerprint_barplot(sample_fingerprint_df)
        
        # Check type
        import plotly.graph_objects as go
        assert isinstance(fig, go.Figure)
        
    def test_barplot_has_correct_traces(self, sample_fingerprint_df):
        """Test that barplot has the correct number of traces (one per interaction type)."""
        fig = fingerprint_barplot(sample_fingerprint_df)
        
        # Should have one trace per interaction type (4 in this case)
        assert len(fig.data) == 4
        
    def test_barplot_trace_names(self, sample_fingerprint_df):
        """Test that each trace has the correct interaction type name."""
        fig = fingerprint_barplot(sample_fingerprint_df)
        
        trace_names = {trace.name for trace in fig.data}
        expected_names = {"hydrophobic", "hbond-don", "hbond-acc", "saltbridge"}
        assert trace_names == expected_names
        
    def test_barplot_layout_properties(self, sample_fingerprint_df):
        """Test that barplot has correct layout."""
        fig = fingerprint_barplot(sample_fingerprint_df)
        
        # Check key layout properties
        assert fig.layout.barmode == "stack"
        assert "Residue" in fig.layout.title.text or "residue" in fig.layout.title.text.lower()


class TestFingerprintHeatmap:
    """Tests for fingerprint_heatmap visualization."""
    
    def test_heatmap_returns_figure_and_axes(self, sample_fingerprint_df):
        """Test that heatmap returns matplotlib fig and ax."""
        fig, ax = fingerprint_heatmap(sample_fingerprint_df)
        
        # Check types
        import matplotlib.pyplot as plt
        assert isinstance(fig, plt.Figure)
        
    def test_heatmap_default_colormap(self, sample_fingerprint_df):
        """Test heatmap with default colormap."""
        fig, ax = fingerprint_heatmap(sample_fingerprint_df)
        
        # Check that ax has been populated with data
        assert ax.has_data()
        
    def test_heatmap_custom_colormap(self, sample_fingerprint_df):
        """Test heatmap with custom colormap."""
        fig, ax = fingerprint_heatmap(sample_fingerprint_df, cmap="viridis")
        
        assert ax.has_data()
        
    def test_heatmap_axes_labels(self, sample_fingerprint_df):
        """Test that heatmap has correct axis labels."""
        fig, ax = fingerprint_heatmap(sample_fingerprint_df)
        
        assert ax.get_xlabel().lower() == "interaction types"
        assert ax.get_ylabel().lower() == "residues"


# Tests for edge cases
class TestVisualizationEdgeCases:
    """Test edge cases and error handling."""
    
    def test_prepare_tabledata_empty_dataframe(self, empty_fingerprint_df):
        """Test _prepare_tabledata with empty (all zeros) dataframe."""
        fingerprint, interaction_index, residues = _prepare_tabledata(empty_fingerprint_df)
        
        assert len(residues) == 2
        assert all(all(v == 0 for v in row) for row in fingerprint)

    def test_prepare_tabledata_zero_indexed(self, empty_fingerprint_df_start_at_zero):
        """Test with zero-based indexing."""
        fingerprint, interaction_index, residues = _prepare_tabledata(empty_fingerprint_df_start_at_zero)
        
        assert residues == [0, 1]  # Zero-based indexing
        assert len(residues) == 2
        
    def test_prepare_tabledata_one_indexed(self, empty_fingerprint_df_start_at_one):
        """Test with one-based indexing (biology standard)."""
        fingerprint, interaction_index, residues = _prepare_tabledata(empty_fingerprint_df_start_at_one)
        
        assert residues == [1, 2]  # One-based indexing
        assert len(residues) == 2

    def test_barplot_single_residue(self):
        """Test barplot with single residue."""
        df = pd.DataFrame(
            {"hbond": [1], "hydrophobic": [2]},
            index=[1]
        )
        fig = fingerprint_barplot(df)
        
        assert len(fig.data) == 2
        
    def test_heatmap_single_interaction_type(self):
        """Test heatmap with single interaction type."""
        df = pd.DataFrame(
            {"hydrophobic": [1, 2, 3]},
            index=[1, 2, 3]
        )
        fig, ax = fingerprint_heatmap(df)
        
        assert ax.has_data()