# `plipify/` file reference

One Markdown summary per file in the root of the `plipify/` package (`__pycache__/`, `data/` and
`tests/` are intentionally excluded). Each file follows the same shape: purpose, imports, a
function-by-function / class-by-class walkthrough, and any bugs or gotchas worth knowing.

| Doc | Source | What it is |
|---|---|---|
| [core-py.md](core-py.md) | [`core.py`](../core.py) | Base objects: interaction types and the residue / binding-site / `Structure` hierarchy. `Structure.from_pdbfile` is the main entry point. |
| [fingerprints-py.md](fingerprints-py.md) | [`fingerprints.py`](../fingerprints.py) | `InteractionFingerprint` — turns one or more `Structure`s into a per-residue interaction fingerprint DataFrame, with MUSCLE sequence alignment. |
| [visualization-py.md](visualization-py.md) | [`visualization.py`](../visualization.py) | Renders a fingerprint DataFrame as a Plotly bar chart, seaborn heatmap, HTML table, NGLView 3D hotspots, B-factor PDBs, and PyMOL images. |
| [_deprecated-py.md](_deprecated-py.md) | [`_deprecated.py`](../_deprecated.py) | The original pre-refactor, function-only pipeline. Not imported anywhere; kept for reference. |
| [_version-py.md](_version-py.md) | [`_version.py`](../_version.py) | Auto-generated versioneer 0.18 file. Derives `plipify.__version__` from git. Do not edit. |
| [__init__-py.md](__init__-py.md) | [`__init__.py`](../__init__.py) | Minimal package initializer — sets `__version__` / `__git_revision__` only. |
| [Plipify-ipynb.md](Plipify-ipynb.md) | [`Plipify.ipynb`](../Plipify.ipynb) | Original MPro tutorial notebook. Stale — imports module names that were since renamed. |

## Dependency map

There is also an interactive dependency graph of the whole package at
[`../../docs/plipify_dependencies.html`](../../docs/plipify_dependencies.html), regenerated with
`python ../../docs/generate_dependency_graph.py`.
