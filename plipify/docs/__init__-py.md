# `plipify/__init__.py`

## Purpose

The package initializer. It is deliberately minimal: it does **not** re-export the public API
(users import from the submodules directly, e.g. `from plipify.core import Structure`), so its only
real job is to expose the package version.

## Contents ([__init__.py:1-13](../__init__.py#L1-L13))

```python
"""
plipify
PLIPify project
"""

from ._version import get_versions

versions = get_versions()
__version__ = versions["version"]
__git_revision__ = versions["full-revisionid"]
del get_versions, versions
```

Step by step:

1. Module docstring — the one-line package description picked up by `setup.py`
   (`short_description = __doc__.split("\n")`).
2. `from ._version import get_versions` — pulls in the versioneer helper (see
   [`_version-py.md`](_version-py.md)).
3. `versions = get_versions()` — runs the git/keyword/parentdir version detection **at import
   time**.
4. `__version__` / `__git_revision__` — the standard dunder attributes, set from the returned dict.
5. `del get_versions, versions` — tidies the namespace so `plipify.get_versions` and
   `plipify.versions` don't leak as public attributes.

## Notes

- Importing `plipify` therefore has the side effect of shelling out to `git` once (cheap, cached by
  the interpreter for the process lifetime).
- `pyproject.toml` declares a console entry point `plipify = "plipify:main"`, but **no `main`
  function is defined here** — running the `plipify` command would raise `AttributeError`. This
  looks like leftover scaffolding from the project template.
- The test `plipify/tests/test_plipify.py` only checks that `import plipify` succeeds (`"plipify"
  in sys.modules`).
