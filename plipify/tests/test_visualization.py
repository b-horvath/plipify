"""
Recall that we're pulling data from conftest.py
"""

import pytest
import matplotlib.pyplot as plt
import pandas as pd
from plipify.visualization import _prepare_tabledata, fingerprint_barplot, fingerprint_heatmap
import plotly.graph_objects as go


class TestFingerprintBarplot:
    """Tests for fingerprint_barplot visualization."""

    def test_barplot_has_correct_traces(self, sample_fingerprint_df):
        """
        Test that barplot has the correct number of traces (one per interaction type).

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig = fingerprint_barplot(sample_fingerprint_df)

        # Should have one trace per interaction type (4 in this case)
        assert len(fig.data) == 4

    def test_barplot_trace_names(self, sample_fingerprint_df):
        """
        Test that each trace has the correct interaction type name.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig = fingerprint_barplot(sample_fingerprint_df)

        trace_names = {trace.name for trace in fig.data}
        expected_names = {"hydrophobic", "hbond-don", "hbond-acc", "saltbridge"}
        assert trace_names == expected_names

    def test_barplot_layout_properties(self, sample_fingerprint_df):
        """
        Test that barplot has correct layout and x and y-axis.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig = fingerprint_barplot(sample_fingerprint_df)

        # Check key layout properties
        assert fig.layout.barmode == "stack"
        assert "Residue Interactions" in fig.layout.title.text
        assert fig.layout.xaxis.title.text == "Residues"
        assert fig.layout.yaxis.title.text == "Interactions"

    def test_barplot_returns_figure(self, sample_fingerprint_df):
        """
        Test that barplot returns a Plotly Figure object.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig = fingerprint_barplot(sample_fingerprint_df)
        assert isinstance(fig, go.Figure)

    def test_barplot_trace_order(self, sample_fingerprint_df):
        """
        Test that traces are sorted by interaction type in reverse alphabetical order.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig = fingerprint_barplot(sample_fingerprint_df)

        trace_names = [trace.name for trace in fig.data]
        expected_order = sorted(sample_fingerprint_df.columns, reverse=True)
        assert trace_names == expected_order

    def test_barplot_trace_data_values(self, sample_fingerprint_df):
        """
        Test that each trace's x/y values match the source dataframe.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig = fingerprint_barplot(sample_fingerprint_df)

        for trace in fig.data:
            assert list(trace.x) == list(sample_fingerprint_df.index)
            assert list(trace.y) == list(sample_fingerprint_df[trace.name])

    def test_barplot_xaxis_type_is_category(self, sample_fingerprint_df):
        """
        Test that the x-axis is treated as categorical, not numeric.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig = fingerprint_barplot(sample_fingerprint_df)
        assert fig.layout.xaxis.type == "category"

    def test_barplot_empty_dataframe(self, empty_fingerprint_df):
        """
        Test that an all-zero fingerprint still produces one trace per column.

        Parameters
        ----------
        empty_fingerprint_df : pd.DataFrame
            All-zero fingerprint fixture with 2 interaction-type columns.
        """
        fig = fingerprint_barplot(empty_fingerprint_df)

        assert len(fig.data) == len(empty_fingerprint_df.columns)
        for trace in fig.data:
            assert list(trace.y) == list(empty_fingerprint_df[trace.name])

    def test_barplot_large_dataframe(self, large_fingerprint_df):
        """
        Test that barplot scales to more interaction types.

        Parameters
        ----------
        large_fingerprint_df : pd.DataFrame
            Fingerprint fixture with all 9 interaction-type columns.
        """
        fig = fingerprint_barplot(large_fingerprint_df)
        assert len(fig.data) == len(large_fingerprint_df.columns)

class TestFingerprintHeatmap:
    """Tests for fingerprint_heatmap visualization."""

    def test_heatmap_returns_figure_and_axes(self, sample_fingerprint_df):
        """
        Test that heatmap returns matplotlib fig and ax.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig, ax = fingerprint_heatmap(sample_fingerprint_df)
        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)

    def test_heatmap_default_colormap(self, sample_fingerprint_df):
        """
        Test heatmap with default colormap.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig, ax = fingerprint_heatmap(sample_fingerprint_df)

        # Check that ax has been populated with data
        assert ax.has_data()
        assert ax in fig.axes

    def test_heatmap_custom_colormap(self, sample_fingerprint_df):
        """
        Test that the custom cmap argument is applied to the plot.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        _, ax = fingerprint_heatmap(sample_fingerprint_df, cmap="viridis")

        # Ensure color mapping is consistent
        assert ax.collections[0].get_cmap().name == "viridis"

    def test_heatmap_axes_labels(self, sample_fingerprint_df):
        """
        Test that heatmap has correct axis labels.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        _, ax = fingerprint_heatmap(sample_fingerprint_df)

        assert ax.get_xlabel() == "Interaction Types"
        assert ax.get_ylabel() == "Residues"

    def test_heatmap_figsize(self, sample_fingerprint_df):
        """
        Test that the figure is created with the expected size.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fig, _ = fingerprint_heatmap(sample_fingerprint_df)

        assert tuple(fig.get_size_inches()) == (10, 7)

    def test_heatmap_annotations_present(self, sample_fingerprint_df):
        """
        Test that annot=True draws a text label for each cell.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        _, ax = fingerprint_heatmap(sample_fingerprint_df)

        n_cells = sample_fingerprint_df.shape[0] * sample_fingerprint_df.shape[1]
        assert len(ax.texts) == n_cells

    def test_heatmap_empty_dataframe(self, empty_fingerprint_df):
        """
        Test that an all-zero fingerprint still renders without error.

        Parameters
        ----------
        empty_fingerprint_df : pd.DataFrame
            All-zero fingerprint fixture with 2 interaction-type columns.
        """
        fig, ax = fingerprint_heatmap(empty_fingerprint_df)

        assert isinstance(fig, plt.Figure)
        assert ax.has_data()


class TestPrepareTableData:
    """Tests for _prepare_tabledata helper function."""

    def test_returns_three_values(self, sample_fingerprint_df):
        """
        Test that the function returns fingerprint, interaction_index, residues.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        result = _prepare_tabledata(sample_fingerprint_df)
        assert len(result) == 3

    def test_residues_match_dataframe_index(self, sample_fingerprint_df):
        """
        Test that residues list matches the dataframe index.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        _, _, residues = _prepare_tabledata(sample_fingerprint_df)
        assert residues == list(sample_fingerprint_df.index)

    def test_fingerprint_matches_dataframe_values(self, sample_fingerprint_df):
        """
        Test that fingerprint matches the dataframe values as a list of lists.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        fingerprint, _, _ = _prepare_tabledata(sample_fingerprint_df)
        assert fingerprint == sample_fingerprint_df.values.tolist()

    def test_interaction_index_length(self, sample_fingerprint_df):
        """
        Test that interaction_index has one entry per fingerprint bit.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        _, interaction_index, residues = _prepare_tabledata(sample_fingerprint_df)
        n_interactions = len(sample_fingerprint_df.columns)
        assert len(interaction_index) == len(residues) * n_interactions

    def test_interaction_index_maps_correct_types(self, sample_fingerprint_df):
        """
        Test that interaction_index cycles through column names in order.

        Parameters
        ----------
        sample_fingerprint_df : pd.DataFrame
            Fingerprint fixture with 4 interaction-type columns.
        """
        _, interaction_index, _ = _prepare_tabledata(sample_fingerprint_df)
        interaction_types = list(sample_fingerprint_df.columns)

        for fp_index, interaction_type in interaction_index.items():
            assert interaction_type == interaction_types[fp_index % len(interaction_types)]

    def test_empty_fingerprint_df(self, empty_fingerprint_df):
        """
        Test that an all-zero fingerprint still produces correctly shaped output.

        Parameters
        ----------
        empty_fingerprint_df : pd.DataFrame
            All-zero fingerprint fixture with 2 interaction-type columns.
        """
        fingerprint, interaction_index, residues = _prepare_tabledata(empty_fingerprint_df)

        assert residues == list(empty_fingerprint_df.index)
        assert fingerprint == empty_fingerprint_df.values.tolist()
        assert len(interaction_index) == len(residues) * len(empty_fingerprint_df.columns)
