#!/usr/bin/env python3
"""
generate_dependency_graph.py
============================

Builds ``docs/plipify_dependencies.html`` -- a self-contained, interactive
dependency graph of everything under ``plipify/`` plus the ``projects/*.ipynb``
notebooks that consume the package.

It works by parsing the Python source with :mod:`ast` (no imports are executed)
and scanning the notebooks with a regex, so it stays correct as the code
changes.  Re-run it after editing the package::

    python docs/generate_dependency_graph.py

The output HTML has no external dependencies (the force-directed graph is a
small hand-rolled simulation in vanilla JS/SVG), so it opens offline by simply
double-clicking it.
"""

from __future__ import annotations

import ast
import datetime as _dt
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "plipify"
PROJECTS_DIR = REPO_ROOT / "projects"
OUTPUT_HTML = REPO_ROOT / "docs" / "plipify_dependencies.html"

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

STDLIB = {
    "__future__", "abc", "argparse", "ast", "collections", "contextlib", "copy",
    "csv", "datetime", "errno", "functools", "glob", "io", "itertools", "json",
    "math", "os", "pathlib", "pickle", "random", "re", "shutil", "subprocess",
    "sys", "tempfile", "textwrap", "time", "typing", "warnings",
}

# Human-friendly notes for the third-party packages this project leans on.
THIRD_PARTY_NOTES = {
    "Bio": "Biopython -- residue names, sequence alignment I/O",
    "numpy": "numerical arrays for the raw fingerprint vectors",
    "pandas": "DataFrame representation of fingerprints",
    "plip": "Protein-Ligand Interaction Profiler -- the underlying engine",
    "matplotlib": "static plotting (heatmap)",
    "seaborn": "heatmap styling on top of matplotlib",
    "plotly": "interactive stacked bar chart",
    "MDAnalysis": "reads/writes PDB files, per-residue b-factor painting",
    "nglview": "in-notebook 3D structure viewer",
    "ipywidgets": "HTML widget wrapper for the fingerprint table",
    "IPython": "rich display hooks inside Jupyter",
    "tqdm": "progress bars while batch-processing structures",
    "rdkit": "cheminformatics toolkit",
    "requests": "HTTP downloads",
    "pymol": "publication-quality ray-traced images",
    "versioneer": "derives the package version from git tags",
}

# Curated runtime relationships that AST cannot see (paths arrive as arguments).
DATA_EDGES = [
    ("plipify/core.py", "plipify/data", "Structure.from_pdbfile() loads .pdb structures at runtime"),
    ("plipify/_deprecated.py", "plipify/data", "get_plip_data() / read_residues() consume .pdb and .csv inputs"),
    ("plipify/visualization.py", "plipify/data", "fingerprint_writepdb() writes painted .pdb files"),
]

DATA_FILE_NOTES = {
    "MPro_residues.csv": "Pre-defined SARS-CoV-2 Mpro binding-site residue list used by project 01",
    "look_and_say.dat": "Cookiecutter sample data file (unused by plipify)",
    "plipify_modules.PNG": "Hand-drawn module overview shipped in the docs",
    "interactionpic.PNG": "Illustration of PLIP interaction types",
    "ifps.png": "Interaction-fingerprint schematic",
    "ifps_1.png": "Interaction-fingerprint schematic (variant)",
    "plipify_fps.png": "Fingerprint figure used in the README",
    "diamond_xchem_screen_mpro_all_pdbs": "~50 Diamond/XChem Mpro fragment-screen PDB structures + file list",
}

CATEGORY_ORDER = [
    "package", "module", "legacy", "test", "data", "notebook", "missing", "external",
]

# Curated landing-page layout: node id -> (x, y) as a fraction of the canvas.
# Mirrors docs/plipify_dependencies.png so every first load looks the same:
# stale "missing" imports top-left, the notebooks that consume the package in a
# row, the three live modules in the centre feeding data/, and the version /
# test island below.  Nodes without an entry (e.g. external libraries) fall back
# to a spiral placement in the JS.
LANDING_LAYOUT = {
    "plipify/fp_visual.py":            (0.32, 0.15),
    "plipify/plip_fingerprints.py":    (0.29, 0.21),
    "plipify/Plipify.ipynb":           (0.38, 0.28),
    "projects/01/debug.ipynb":         (0.46, 0.28),
    "projects/01/xchem.ipynb":         (0.54, 0.28),
    "projects/02/main.ipynb":          (0.60, 0.28),
    "projects/01/fragalysis.ipynb":    (0.68, 0.29),
    "plipify/fingerprints.py":         (0.40, 0.40),
    "plipify/core.py":                 (0.53, 0.42),
    "plipify/visualization.py":        (0.62, 0.42),
    "plipify/data":                    (0.56, 0.52),
    "plipify/_deprecated.py":          (0.46, 0.54),
    "plipify/tests/__init__.py":       (0.27, 0.56),
    "plipify/tests/test_plipify.py":   (0.30, 0.63),
    "plipify/tests/test_core.py":      (0.18, 0.62),
    "plipify/tests/test_core_draft.py":     (0.17, 0.70),
    "plipify/tests/test_fingerprints.py":   (0.27, 0.72),
    "plipify/tests/test_visualization.py":  (0.20, 0.78),
    "plipify/_version.py":             (0.42, 0.75),
    "plipify/__init__.py":             (0.34, 0.81),
}


# ---------------------------------------------------------------------------
# Python module analysis
# ---------------------------------------------------------------------------

def _module_id(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _resolve_relative(mod: str | None, level: int, current: Path) -> str:
    """Resolve a relative import target to a repo-relative .py path string."""
    base = current.parent
    for _ in range(level - 1):
        base = base.parent
    if mod:
        base = base / Path(mod.replace(".", "/"))
    candidate = base.with_suffix(".py") if base.suffix == "" else base
    pkg_init = base / "__init__.py"
    if candidate.exists():
        return _module_id(candidate)
    if pkg_init.exists():
        return _module_id(pkg_init)
    return _module_id(candidate)  # points at a now-missing module


def _first_paragraph(doc: str | None) -> str:
    if not doc:
        return ""
    lines = []
    for raw in doc.strip().splitlines():
        line = raw.strip()
        if not line:
            if lines:
                break
            continue
        if set(line) <= {"-", "=", "~"}:  # RST underline
            continue
        lines.append(line)
    return " ".join(lines)


def analyze_module(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    node = {
        "id": _module_id(path),
        "label": path.name,
        "path": _module_id(path),
        "loc": source.count("\n") + 1,
        "summary": _first_paragraph(ast.get_docstring(tree)),
        "classes": [],
        "functions": [],
        "internal": [],   # list of (target_id, description)
        "external": [],    # list of (top-level pkg, description)
        "lazy": [],        # list of (top-level pkg, description)
    }

    top_level = set(map(id, tree.body))

    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        bases = [ast.unparse(b) for b in cls.bases]
        node["classes"].append({
            "name": cls.name,
            "bases": bases,
            "doc": _first_paragraph(ast.get_docstring(cls)),
        })
    for fn in [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        node["functions"].append({
            "name": fn.name,
            "doc": _first_paragraph(ast.get_docstring(fn)),
        })

    for sub in ast.walk(tree):
        if not isinstance(sub, (ast.Import, ast.ImportFrom)):
            continue
        is_top = id(sub) in top_level
        bucket = "top" if is_top else "lazy"

        if isinstance(sub, ast.ImportFrom) and sub.level:
            target = _resolve_relative(sub.module, sub.level, path)
            names = ", ".join(a.name for a in sub.names)
            desc = f"from {'.' * sub.level}{sub.module or ''} import {names}"
            node["internal"].append((target, desc, bucket))
            continue

        if isinstance(sub, ast.ImportFrom):
            root = (sub.module or "").split(".")[0]
            names = ", ".join(a.name for a in sub.names)
            desc = f"from {sub.module} import {names}"
            if root == "plipify":
                target = _module_id((REPO_ROOT / sub.module.replace(".", "/")).with_suffix(".py"))
                node["internal"].append((target, desc, bucket))
            elif root:
                node[bucket if bucket == "lazy" else "external"].append((root, desc))
            continue

        # plain ``import x, y``
        for alias in sub.names:
            root = alias.name.split(".")[0]
            desc = f"import {alias.name}"
            if root == "plipify":
                target = _module_id((REPO_ROOT / alias.name.replace(".", "/")).with_suffix(".py"))
                node["internal"].append((target, desc, bucket))
            else:
                node[bucket if bucket == "lazy" else "external"].append((root, desc))

    return node


# ---------------------------------------------------------------------------
# Notebook analysis
# ---------------------------------------------------------------------------

_NB_IMPORT_RE = re.compile(
    r"(?:from\s+(plipify(?:\.\w+)*)\s+import\s+([^\n\"']+)|import\s+(plipify(?:\.\w+)*))"
)


def analyze_notebook(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    sources: list[str] = []
    for cell in data.get("cells", []):
        if cell.get("cell_type") == "code":
            sources.append("".join(cell.get("source", [])))
    blob = "\n".join(sources)

    imports: list[tuple[str, str]] = []
    for m in _NB_IMPORT_RE.finditer(blob):
        mod = m.group(1) or m.group(3)
        names = (m.group(2) or "").strip().rstrip("\\").strip()
        desc = f"from {mod} import {names}" if names else f"import {mod}"
        imports.append((mod, desc))

    return {
        "id": _module_id(path),
        "label": path.name,
        "path": _module_id(path),
        "loc": blob.count("\n") + 1,
        "n_code_cells": len(sources),
        "imports": imports,
    }


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> dict:
    nodes: dict[str, dict] = {}
    links: list[dict] = []

    def add_node(**kw):
        nodes[kw["id"]] = {**nodes.get(kw["id"], {}), **kw}

    # --- package __init__ + modules ------------------------------------------------
    py_files = sorted(PACKAGE_DIR.rglob("*.py"))
    module_ids = {_module_id(p) for p in py_files}

    for path in py_files:
        info = analyze_module(path)
        rel = info["id"]
        if path.name == "__init__.py":
            category = "package"
        elif "tests" in path.parts:
            category = "test"
        elif path.name == "_deprecated.py":
            category = "legacy"
        else:
            category = "module"

        add_node(
            id=rel, label=info["label"], category=category, path=rel,
            summary=info["summary"], loc=info["loc"],
            classes=info["classes"], functions=info["functions"],
            external=sorted({r for r, _ in info["external"]}),
            lazy=sorted({r for r, _ in info["lazy"]}),
        )

        seen_edges = set()
        for target, desc, bucket in info["internal"]:
            key = (rel, target)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            missing = target not in module_ids and not (REPO_ROOT / target).exists()
            if missing:
                add_node(id=target, label=Path(target).name + " (missing)",
                         category="missing", path=target,
                         summary="Referenced by an import but no longer present in the package.",
                         loc=0, classes=[], functions=[], external=[], lazy=[])
            links.append({"source": rel, "target": target, "type": "imports",
                          "lazy": bucket == "lazy", "detail": desc})

        for root, desc in info["external"] + info["lazy"]:
            ext_id = f"ext:{root}"
            add_node(id=ext_id, label=root, category="external",
                     kind="standard library" if root in STDLIB else "third-party",
                     note=THIRD_PARTY_NOTES.get(root, ""))
            links.append({"source": rel, "target": ext_id, "type": "external",
                          "lazy": (root, desc) in info["lazy"], "detail": desc})

    # --- data files --------------------------------------------------------------
    data_dir = PACKAGE_DIR / "data"
    if data_dir.is_dir():
        group_id = "plipify/data"
        add_node(id=group_id, label="data/", category="data", path=group_id,
                 summary="Bundled sample data: fragment-screen PDB structures, "
                         "the Mpro residue list, and figures used in the docs.",
                 members=[])
        members = []
        for entry in sorted(data_dir.iterdir()):
            if entry.name in {"README.md"}:
                continue
            if entry.is_dir():
                n = len(list(entry.glob("*")))
                members.append({"name": entry.name + "/", "kind": "directory",
                                "detail": DATA_FILE_NOTES.get(entry.name, ""), "count": n})
            else:
                members.append({"name": entry.name, "kind": entry.suffix.lstrip(".") or "file",
                                "detail": DATA_FILE_NOTES.get(entry.name, "")})
        nodes[group_id]["members"] = members

        for src, dst, desc in DATA_EDGES:
            if src in nodes and dst in nodes:
                links.append({"source": src, "target": dst, "type": "data", "lazy": False, "detail": desc})

    # --- notebooks (in-package + consumers) ------------------------------------
    notebooks = sorted(PACKAGE_DIR.rglob("*.ipynb")) + sorted(PROJECTS_DIR.rglob("*.ipynb"))
    for path in notebooks:
        nb = analyze_notebook(path)
        add_node(id=nb["id"], label=nb["label"], category="notebook", path=nb["path"],
                 summary=f"Jupyter notebook ({nb['n_code_cells']} code cells).",
                 loc=nb["loc"],
                 imports=[d for _, d in nb["imports"]])
        for mod, desc in nb["imports"]:
            target = _module_id((REPO_ROOT / mod.replace(".", "/")).with_suffix(".py"))
            missing = target not in module_ids and not (REPO_ROOT / target).exists()
            if missing:
                add_node(id=target, label=Path(target).name + " (missing)",
                         category="missing", path=target,
                         summary="Imported by a notebook but not present in the current package "
                                 "(renamed or removed).",
                         loc=0, classes=[], functions=[], external=[], lazy=[])
            links.append({"source": nb["id"], "target": target, "type": "consumes",
                          "lazy": False, "detail": desc})

    # de-duplicate links
    uniq = {}
    for l in links:
        key = (l["source"], l["target"], l["type"])
        if key not in uniq:
            uniq[key] = l
    ordered = sorted(
        nodes.values(),
        key=lambda n: (CATEGORY_ORDER.index(n["category"]) if n["category"] in CATEGORY_ORDER else 99, n["id"]),
    )
    return {
        "generated": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "nodes": ordered,
        "links": list(uniq.values()),
        "layout": {k: list(v) for k, v in LANDING_LAYOUT.items() if k in nodes},
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>plipify &mdash; file dependency map</title>
<style>
  :root {
    --bg: #f6f7f9; --panel: #ffffff; --ink: #1b1f24; --muted: #5c6672;
    --border: #d9dee4; --shadow: 0 1px 3px rgba(0,0,0,.12), 0 8px 24px rgba(0,0,0,.08);
    --edge: #9aa4b0; --edge-strong: #4a5563;
    --package:#7c3aed; --module:#2563eb; --legacy:#b45309; --test:#0d9488;
    --data:#65758b; --notebook:#db2777; --missing:#dc2626; --external:#94a3b8;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg:#0f1216; --panel:#171b21; --ink:#e6e9ee; --muted:#9aa4b0;
      --border:#2a313a; --shadow: 0 1px 3px rgba(0,0,0,.4), 0 12px 32px rgba(0,0,0,.45);
      --edge:#4a5563; --edge-strong:#8b97a5;
      --package:#a78bfa; --module:#60a5fa; --legacy:#fbbf24; --test:#2dd4bf;
      --data:#94a3b8; --notebook:#f472b6; --missing:#f87171; --external:#64748b;
    }
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--ink); overflow: hidden;
  }
  #app { display: flex; height: 100vh; width: 100vw; }
  #stage { position: relative; flex: 1 1 auto; overflow: hidden; }
  svg { width: 100%; height: 100%; display: block; cursor: grab; }
  svg.panning { cursor: grabbing; }

  header {
    position: absolute; top: 12px; left: 12px; z-index: 5;
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    box-shadow: var(--shadow); padding: 12px 14px; max-width: 320px;
  }
  header h1 { margin: 0 0 2px; font-size: 15px; letter-spacing: .2px; }
  header p { margin: 0; color: var(--muted); font-size: 12px; }

  #controls {
    position: absolute; top: 12px; right: 12px; z-index: 5;
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    box-shadow: var(--shadow); padding: 10px 12px; width: 232px;
  }
  #controls-head { display: flex; align-items: center; gap: 8px; }
  #controls h2 { margin: 0; font-size: 11px; text-transform: uppercase;
    letter-spacing: .8px; color: var(--muted); flex: 1 1 auto; }
  #controls-body { margin-top: 8px; }
  #controls-toggle {
    flex: 0 0 auto; width: 22px; height: 22px; padding: 0; margin: 0;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid var(--border); border-radius: 6px; background: var(--bg);
    color: var(--ink); font-size: 13px; line-height: 1; cursor: pointer;
  }
  #controls-toggle:hover { border-color: var(--edge-strong); }
  #controls.collapsed { width: auto; padding: 6px; }
  #controls.collapsed #controls-body { display: none; }
  #controls.collapsed #controls-head h2 { display: none; }
  #controls label { display: flex; align-items: center; gap: 8px; padding: 3px 0;
    font-size: 13px; cursor: pointer; user-select: none; }
  #controls .swatch { width: 11px; height: 11px; border-radius: 3px; flex: 0 0 auto; }
  #controls .count { margin-left: auto; color: var(--muted); font-variant-numeric: tabular-nums; }
  #controls hr { border: 0; border-top: 1px solid var(--border); margin: 9px 0; }
  #search {
    width: 100%; padding: 6px 8px; border: 1px solid var(--border); border-radius: 7px;
    background: var(--bg); color: var(--ink); font-size: 13px; margin-bottom: 4px;
  }
  #controls-body button {
    width: 100%; padding: 6px 8px; border: 1px solid var(--border); border-radius: 7px;
    background: var(--bg); color: var(--ink); font-size: 12px; cursor: pointer; margin-top: 6px;
  }
  #controls-body button:hover { border-color: var(--edge-strong); }

  .node circle { stroke: var(--panel); stroke-width: 2px; cursor: pointer; transition: opacity .15s; }
  .node text { font-size: 11px; fill: var(--ink); pointer-events: none;
    paint-order: stroke; stroke: var(--bg); stroke-width: 3px; stroke-linejoin: round; }
  .node.dim { opacity: .12; }
  .link { stroke: var(--edge); fill: none; transition: opacity .15s; }
  .link.consumes { stroke-dasharray: 2 3; }
  .link.data { stroke-dasharray: 1 4; stroke-linecap: round; }
  .link.lazy { stroke-dasharray: 6 4; opacity: .7; }
  .link.hi { stroke: var(--edge-strong); }
  .link.dim { opacity: .05; }

  #detail {
    flex: 0 0 360px; background: var(--panel); border-left: 1px solid var(--border);
    padding: 18px 20px; overflow-y: auto; transform: translateX(100%);
    transition: transform .22s ease; position: absolute; right: 0; top: 0; height: 100%;
    box-shadow: var(--shadow);
  }
  #detail.open { transform: translateX(0); }
  #detail .close { float: right; border: 0; background: none; font-size: 20px;
    color: var(--muted); cursor: pointer; line-height: 1; }
  #detail .kicker { font-size: 11px; text-transform: uppercase; letter-spacing: .8px; }
  #detail h2 { margin: 4px 0 6px; font-size: 18px; word-break: break-all; }
  #detail .path { color: var(--muted); font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; word-break: break-all; }
  #detail .summary { margin: 12px 0; }
  #detail h3 { font-size: 11px; text-transform: uppercase; letter-spacing: .8px;
    color: var(--muted); margin: 18px 0 6px; }
  #detail ul { margin: 0; padding-left: 0; list-style: none; }
  #detail li { padding: 4px 0; border-bottom: 1px dashed var(--border); font-size: 13px; }
  #detail li:last-child { border-bottom: 0; }
  #detail code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px;
    background: var(--bg); padding: 1px 5px; border-radius: 4px; }
  #detail .doc { color: var(--muted); font-size: 12px; display: block; margin-top: 2px; }
  #detail .pill { display: inline-block; padding: 2px 8px; border-radius: 999px;
    font-size: 11px; font-weight: 600; color: #fff; }
  .tooltip {
    position: absolute; z-index: 9; pointer-events: none; background: var(--ink); color: var(--bg);
    padding: 4px 8px; border-radius: 6px; font-size: 12px; opacity: 0; transition: opacity .1s;
    white-space: nowrap; transform: translate(-50%, -140%);
  }
  footer { position: absolute; bottom: 10px; left: 12px; z-index: 5;
    color: var(--muted); font-size: 11px; }
</style>
</head>
<body>
<div id="app">
  <div id="stage">
    <header>
      <h1>plipify &mdash; file dependency map</h1>
      <p>Every file under <code>plipify/</code> and the notebooks that use it.
         Drag nodes, scroll to zoom, click a node for details. Double-click a node to unpin it.</p>
    </header>
    <div id="controls">
      <div id="controls-head">
        <h2>Show</h2>
        <button id="controls-toggle" type="button" aria-label="Collapse panel" title="Collapse panel">&#8722;</button>
      </div>
      <div id="controls-body">
        <div id="filters"></div>
        <hr>
        <label><input type="checkbox" id="toggle-ext"> external libraries</label>
        <label><input type="checkbox" id="toggle-lazy" checked> lazy (in-function) imports</label>
        <hr>
        <input id="search" type="search" placeholder="Filter by name&hellip;" autocomplete="off">
        <button id="reset">Reset view &amp; layout</button>
      </div>
    </div>
    <svg id="svg">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#8b97a5"></path>
        </marker>
      </defs>
      <g id="viewport">
        <g id="links"></g>
        <g id="nodes"></g>
      </g>
    </svg>
    <div class="tooltip" id="tooltip"></div>
    <footer id="footer"></footer>
  </div>
  <aside id="detail"></aside>
</div>

<script id="graph-data" type="application/json">__GRAPH_DATA__</script>
<script>
(function () {
  "use strict";
  const DATA = JSON.parse(document.getElementById("graph-data").textContent);
  const SVG = document.getElementById("svg");
  const VIEWPORT = document.getElementById("viewport");
  const LINKS_G = document.getElementById("links");
  const NODES_G = document.getElementById("nodes");
  const TOOLTIP = document.getElementById("tooltip");
  const DETAIL = document.getElementById("detail");
  document.getElementById("footer").textContent =
    "generated " + DATA.generated + "  ·  " + DATA.nodes.length + " nodes, " + DATA.links.length + " edges";

  const CATS = {
    package:  { label: "package __init__", color: "var(--package)" },
    module:   { label: "module (.py)",     color: "var(--module)" },
    legacy:   { label: "legacy module",    color: "var(--legacy)" },
    test:     { label: "test",             color: "var(--test)" },
    data:     { label: "data files",       color: "var(--data)" },
    notebook: { label: "notebook",         color: "var(--notebook)" },
    missing:  { label: "missing / renamed",color: "var(--missing)" },
    external: { label: "external library", color: "var(--external)" },
  };

  const R = { package: 13, module: 15, legacy: 12, test: 10, data: 16, notebook: 11, missing: 10, external: 6 };

  // ---- state ----------------------------------------------------------------
  const nodeById = new Map(DATA.nodes.map(n => [n.id, n]));
  const visibleCats = new Set(Object.keys(CATS).filter(c => c !== "external"));
  let showExternal = false, showLazy = true, searchTerm = "";

  // ---- persistence (per-viewer, this artifact's origin only) ---------------
  const LS = { layout: "plipifyDepGraph.v1.layout", collapsed: "plipifyDepGraph.v1.controlsCollapsed" };
  function lsRead(key) { try { return JSON.parse(localStorage.getItem(key)); } catch (e) { return null; } }
  function lsWrite(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }
  function lsRemove(key) { try { localStorage.removeItem(key); } catch (e) {} }

  const W = () => SVG.clientWidth, H = () => SVG.clientHeight;

  // Seed node positions. Priority: a layout this viewer saved earlier ->
  // the curated landing layout shipped in the file -> a spiral fallback
  // (used for external-library nodes, which carry no curated position).
  function placeNodes(preferSaved) {
    const saved = preferSaved ? lsRead(LS.layout) : null;
    const w = W(), h = H();
    DATA.nodes.forEach((n, i) => {
      let f = (saved && saved[n.id]) || (DATA.layout && DATA.layout[n.id]);
      if (!f) {
        const angle = i * 2.399963229728653;
        const rad = 0.14 + 0.02 * Math.sqrt(i);
        f = [0.6 + rad * Math.cos(angle), 0.5 + rad * Math.sin(angle)];
      }
      n.x = f[0] * w; n.y = f[1] * h;
      n.vx = 0; n.vy = 0; n.pinned = false;
    });
  }

  let layoutDirty = false;
  function saveLayout() {
    const w = W(), h = H(), out = {};
    for (const n of DATA.nodes) out[n.id] = [n.x / w, n.y / h];
    lsWrite(LS.layout, out);
    layoutDirty = false;
  }

  placeNodes(true);

  // ---- view transform (zoom / pan) ---------------------------------------
  const view = { x: 0, y: 0, k: 1 };
  function applyView() {
    VIEWPORT.setAttribute("transform", `translate(${view.x},${view.y}) scale(${view.k})`);
  }
  SVG.addEventListener("wheel", (e) => {
    e.preventDefault();
    const rect = SVG.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const factor = Math.exp(-e.deltaY * 0.0015);
    const k2 = Math.min(4, Math.max(0.2, view.k * factor));
    view.x = mx - (mx - view.x) * (k2 / view.k);
    view.y = my - (my - view.y) * (k2 / view.k);
    view.k = k2;
    applyView();
  }, { passive: false });

  let panning = false, panStart = null;
  const drag = { node: null };
  SVG.addEventListener("mousedown", (e) => {
    if (e.target.closest(".node")) return;
    panning = true; panStart = { x: e.clientX - view.x, y: e.clientY - view.y };
    SVG.classList.add("panning");
  });
  window.addEventListener("mousemove", (e) => {
    if (panning) { view.x = e.clientX - panStart.x; view.y = e.clientY - panStart.y; applyView(); }
    if (drag.node) {
      const rect = SVG.getBoundingClientRect();
      drag.node.x = (e.clientX - rect.left - view.x) / view.k;
      drag.node.y = (e.clientY - rect.top - view.y) / view.k;
      drag.node.vx = 0; drag.node.vy = 0; drag.node.pinned = true;
      layoutDirty = true;
      alpha = Math.max(alpha, 0.3);
    }
  });
  window.addEventListener("mouseup", () => {
    panning = false; drag.node = null; SVG.classList.remove("panning");
  });

  // ---- force simulation --------------------------------------------------
  let activeNodes = [], activeLinks = [], alpha = 0;
  const CHARGE = -1400, LINK_DIST = 92, LINK_K = 0.04, CENTER_K = 0.015, DAMP = 0.86;

  function tick() {
    if (alpha > 0.005) {
      alpha *= 0.992;
      const n = activeNodes.length;
      for (let i = 0; i < n; i++) {
        const a = activeNodes[i];
        for (let j = i + 1; j < n; j++) {
          const b = activeNodes[j];
          let dx = b.x - a.x, dy = b.y - a.y;
          let d2 = dx * dx + dy * dy || 0.01;
          if (d2 > 90000) continue;
          const d = Math.sqrt(d2);
          const f = (CHARGE * alpha) / d2;
          const fx = (dx / d) * f, fy = (dy / d) * f;
          a.vx += fx; a.vy += fy; b.vx -= fx; b.vy -= fy;
        }
      }
      for (const l of activeLinks) {
        const s = l.s, t = l.t;
        let dx = t.x - s.x, dy = t.y - s.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 0.01;
        const f = LINK_K * alpha * (d - LINK_DIST);
        const fx = (dx / d) * f, fy = (dy / d) * f;
        s.vx += fx; s.vy += fy; t.vx -= fx; t.vy -= fy;
      }
      const cx = W() / 2, cy = H() / 2;
      for (const a of activeNodes) {
        a.vx += (cx - a.x) * CENTER_K * alpha;
        a.vy += (cy - a.y) * CENTER_K * alpha;
        if (!a.pinned) {
          a.vx *= DAMP; a.vy *= DAMP;
          a.x += a.vx; a.y += a.vy;
        } else { a.vx = 0; a.vy = 0; }
      }
      positionElements();
    } else if (layoutDirty) {
      // simulation has come to rest after a drag -> remember the arrangement
      saveLayout();
    }
    requestAnimationFrame(tick);
  }

  // ---- rendering -------------------------------------------------------
  let linkEls = new Map(), nodeEls = new Map();

  function passesFilter(n) {
    if (!visibleCats.has(n.category)) return false;
    if (n.category === "external" && !showExternal) return false;
    if (searchTerm && !n.id.toLowerCase().includes(searchTerm)) return false;
    return true;
  }
  function linkVisible(l) {
    if (l.lazy && !showLazy) return false;
    return passesFilter(nodeById.get(l.source)) && passesFilter(nodeById.get(l.target));
  }

  function rebuild(reheat = true) {
    activeNodes = DATA.nodes.filter(passesFilter);
    const liveIds = new Set(activeNodes.map(n => n.id));
    activeLinks = DATA.links.filter(l => linkVisible(l) && liveIds.has(l.source) && liveIds.has(l.target))
      .map(l => ({ ...l, s: nodeById.get(l.source), t: nodeById.get(l.target) }));

    LINKS_G.innerHTML = ""; NODES_G.innerHTML = "";
    linkEls = new Map(); nodeEls = new Map();

    activeLinks.forEach((l, i) => {
      const p = document.createElementNS("http://www.w3.org/2000/svg", "line");
      p.setAttribute("class", "link " + l.type + (l.lazy ? " lazy" : ""));
      p.setAttribute("marker-end", "url(#arrow)");
      LINKS_G.appendChild(p);
      linkEls.set(i, p);
      l._el = p;
    });

    activeNodes.forEach(n => {
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.setAttribute("class", "node");
      g.dataset.id = n.id;
      const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      c.setAttribute("r", R[n.category] || 9);
      c.setAttribute("fill", CATS[n.category].color);
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", (R[n.category] || 9) + 4);
      label.setAttribute("y", 4);
      label.textContent = n.label;
      g.appendChild(c); g.appendChild(label);
      NODES_G.appendChild(g);
      nodeEls.set(n.id, g);

      g.addEventListener("mousedown", (e) => { e.stopPropagation(); drag.node = n; });
      g.addEventListener("mouseenter", () => hoverNode(n));
      g.addEventListener("mouseleave", clearHover);
      g.addEventListener("mousemove", (e) => {
        TOOLTIP.style.left = e.clientX + "px";
        TOOLTIP.style.top = e.clientY + "px";
      });
      g.addEventListener("click", (e) => { e.stopPropagation(); showDetail(n); });
      g.addEventListener("dblclick", (e) => { e.stopPropagation(); n.pinned = false; alpha = Math.max(alpha, .3); });
    });

    if (reheat) alpha = Math.max(alpha, 0.6);
    positionElements();
  }

  function positionElements() {
    for (const l of activeLinks) {
      const s = l.s, t = l.t;
      const dx = t.x - s.x, dy = t.y - s.y;
      const d = Math.sqrt(dx * dx + dy * dy) || 1;
      const pad = (R[t.category] || 9) + 7;
      l._el.setAttribute("x1", s.x);
      l._el.setAttribute("y1", s.y);
      l._el.setAttribute("x2", t.x - (dx / d) * pad);
      l._el.setAttribute("y2", t.y - (dy / d) * pad);
    }
    for (const n of activeNodes) {
      const el = nodeEls.get(n.id);
      if (el) el.setAttribute("transform", `translate(${n.x},${n.y})`);
    }
  }

  // ---- hover highlight ------------------------------------------------
  function neighbours(id) {
    const set = new Set([id]);
    for (const l of activeLinks) {
      if (l.source === id) set.add(l.target);
      if (l.target === id) set.add(l.source);
    }
    return set;
  }
  function hoverNode(n) {
    const near = neighbours(n.id);
    for (const [id, el] of nodeEls) el.classList.toggle("dim", !near.has(id));
    for (const l of activeLinks) {
      const on = l.source === n.id || l.target === n.id;
      l._el.classList.toggle("hi", on);
      l._el.classList.toggle("dim", !on);
    }
    TOOLTIP.textContent = n.summary || n.id;
    TOOLTIP.style.opacity = 1;
  }
  function clearHover() {
    for (const el of nodeEls.values()) el.classList.remove("dim");
    for (const l of activeLinks) l._el.classList.remove("hi", "dim");
    TOOLTIP.style.opacity = 0;
  }

  // ---- detail panel -------------------------------------------------
  function esc(s) { return String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

  function showDetail(n) {
    const out = [];
    out.push(`<button class="close" aria-label="close">&times;</button>`);
    out.push(`<div class="kicker" style="color:${CATS[n.category].color}">${esc(CATS[n.category].label)}</div>`);
    out.push(`<h2>${esc(n.label)}</h2>`);
    if (n.path) out.push(`<div class="path">${esc(n.path)}</div>`);
    if (n.summary) out.push(`<p class="summary">${esc(n.summary)}</p>`);

    const meta = [];
    if (n.loc) meta.push(`${n.loc} lines`);
    if (n.kind) meta.push(esc(n.kind));
    if (meta.length) out.push(`<p style="color:var(--muted);font-size:12px;margin:-6px 0 0">${meta.join(" · ")}</p>`);
    if (n.note) out.push(`<p class="summary">${esc(n.note)}</p>`);

    const outgoing = DATA.links.filter(l => l.source === n.id);
    const incoming = DATA.links.filter(l => l.target === n.id);

    if (n.classes && n.classes.length) {
      out.push(`<h3>Classes (${n.classes.length})</h3><ul>`);
      for (const c of n.classes) {
        const bases = c.bases && c.bases.length ? `<span class="doc">extends ${esc(c.bases.join(", "))}</span>` : "";
        out.push(`<li><code>${esc(c.name)}</code>${bases}${c.doc ? `<span class="doc">${esc(c.doc)}</span>` : ""}</li>`);
      }
      out.push(`</ul>`);
    }
    if (n.functions && n.functions.length) {
      out.push(`<h3>Functions (${n.functions.length})</h3><ul>`);
      for (const f of n.functions)
        out.push(`<li><code>${esc(f.name)}()</code>${f.doc ? `<span class="doc">${esc(f.doc)}</span>` : ""}</li>`);
      out.push(`</ul>`);
    }
    if (n.members && n.members.length) {
      out.push(`<h3>Contents</h3><ul>`);
      for (const m of n.members) {
        const cnt = m.count ? ` <span class="doc">(${m.count} files)</span>` : "";
        out.push(`<li><code>${esc(m.name)}</code>${cnt}${m.detail ? `<span class="doc">${esc(m.detail)}</span>` : ""}</li>`);
      }
      out.push(`</ul>`);
    }

    const imp = outgoing.filter(l => l.type === "imports" || l.type === "consumes");
    if (imp.length) {
      out.push(`<h3>Depends on</h3><ul>`);
      for (const l of imp)
        out.push(`<li><code>${esc(nodeById.get(l.target).label)}</code>${l.lazy ? ' <span class="doc">lazy</span>' : ""}<span class="doc">${esc(l.detail)}</span></li>`);
      out.push(`</ul>`);
    }
    const ext = outgoing.filter(l => l.type === "external");
    if (ext.length) {
      out.push(`<h3>External libraries</h3><ul>`);
      for (const l of ext) {
        const tn = nodeById.get(l.target);
        out.push(`<li><code>${esc(tn.label)}</code> <span class="doc">${esc(tn.kind || "")}${tn.note ? " — " + esc(tn.note) : ""}</span><span class="doc">${esc(l.detail)}</span></li>`);
      }
      out.push(`</ul>`);
    }
    const dataOut = outgoing.filter(l => l.type === "data");
    if (dataOut.length) {
      out.push(`<h3>Reads / writes</h3><ul>`);
      for (const l of dataOut)
        out.push(`<li><code>${esc(nodeById.get(l.target).label)}</code><span class="doc">${esc(l.detail)}</span></li>`);
      out.push(`</ul>`);
    }
    if (incoming.length) {
      out.push(`<h3>Used by (${incoming.length})</h3><ul>`);
      for (const l of incoming)
        out.push(`<li><code>${esc(nodeById.get(l.source).label)}</code><span class="doc">${esc(l.detail)}</span></li>`);
      out.push(`</ul>`);
    }

    DETAIL.innerHTML = out.join("");
    DETAIL.classList.add("open");
    DETAIL.querySelector(".close").addEventListener("click", () => DETAIL.classList.remove("open"));
  }
  SVG.addEventListener("click", (e) => { if (!e.target.closest(".node")) DETAIL.classList.remove("open"); });

  // ---- controls ------------------------------------------------------
  const filtersDiv = document.getElementById("filters");
  const counts = {};
  DATA.nodes.forEach(n => counts[n.category] = (counts[n.category] || 0) + 1);
  Object.entries(CATS).forEach(([key, meta]) => {
    if (!counts[key]) return;
    const lbl = document.createElement("label");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = key !== "external";
    cb.addEventListener("change", () => {
      if (cb.checked) visibleCats.add(key); else visibleCats.delete(key);
      if (key === "external") { showExternal = cb.checked; document.getElementById("toggle-ext").checked = cb.checked; }
      rebuild();
    });
    lbl.appendChild(cb);
    const sw = document.createElement("span");
    sw.className = "swatch"; sw.style.background = meta.color;
    lbl.appendChild(sw);
    lbl.appendChild(document.createTextNode(meta.label));
    const c = document.createElement("span");
    c.className = "count"; c.textContent = counts[key];
    lbl.appendChild(c);
    filtersDiv.appendChild(lbl);
  });

  const extToggle = document.getElementById("toggle-ext");
  extToggle.addEventListener("change", () => {
    showExternal = extToggle.checked;
    if (showExternal) visibleCats.add("external"); else visibleCats.delete("external");
    [...filtersDiv.querySelectorAll("label")].forEach(l => {
      if (l.textContent.includes("external library")) l.querySelector("input").checked = showExternal;
    });
    rebuild();
  });
  document.getElementById("toggle-lazy").addEventListener("change", (e) => {
    showLazy = e.target.checked; rebuild();
  });
  document.getElementById("search").addEventListener("input", (e) => {
    searchTerm = e.target.value.trim().toLowerCase(); rebuild();
  });
  document.getElementById("reset").addEventListener("click", () => {
    view.x = 0; view.y = 0; view.k = 1; applyView();
    lsRemove(LS.layout);           // forget this viewer's arrangement
    placeNodes(false);             // back to the curated landing layout
    alpha = showExternal ? 0.25 : 0;
    rebuild(false);
  });

  // ---- collapsible controls panel (state persisted per viewer) -----------
  const controlsEl = document.getElementById("controls");
  const controlsToggle = document.getElementById("controls-toggle");
  function setControlsCollapsed(collapsed) {
    controlsEl.classList.toggle("collapsed", collapsed);
    controlsToggle.textContent = collapsed ? "☰" : "−";
    controlsToggle.title = collapsed ? "Show controls" : "Collapse panel";
    controlsToggle.setAttribute("aria-label", controlsToggle.title);
    lsWrite(LS.collapsed, collapsed ? 1 : 0);
  }
  controlsToggle.addEventListener("click", () =>
    setControlsCollapsed(!controlsEl.classList.contains("collapsed")));
  setControlsCollapsed(lsRead(LS.collapsed) === 1);

  applyView();
  rebuild(false);
  tick();
})();
</script>
</body>
</html>
"""


def main() -> None:
    graph = build_graph()
    html = HTML_TEMPLATE.replace("__GRAPH_DATA__", json.dumps(graph, separators=(",", ":")))
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    n_ext = sum(1 for n in graph["nodes"] if n["category"] == "external")
    print(f"Wrote {OUTPUT_HTML.relative_to(REPO_ROOT)}")
    print(f"  {len(graph['nodes']) - n_ext} package/notebook nodes + {n_ext} external libs")
    print(f"  {len(graph['links'])} edges")


if __name__ == "__main__":
    main()
