# `plipify/_version.py`

## Purpose

**Auto-generated boilerplate — do not edit by hand.** Produced by
[versioneer](https://github.com/warner/python-versioneer) 0.18. Its only job is to derive the
package version string (and full git revision) at runtime, so that
`plipify.__version__` reflects the nearest git tag plus any commits-since / dirty-tree suffix,
without a hard-coded version number anywhere in the source tree.

The header comment ([_version.py:2-9](../_version.py#L2-L9)) explains the three delivery modes it
supports: a git checkout, a `git archive` tarball (where `$Format:...$` placeholders are expanded
by git), and an sdist/build directory (where `setup.py` writes a short static replacement instead).

Configuration lives in `setup.cfg` under `[versioneer]` (`VCS = git`, `style = pep440`,
`tag_prefix = ''`, `versionfile_source = plipify/_version.py`).

## Imports

Standard library only: `errno`, `os`, `re`, `subprocess`, `sys`.

## Key functions

| Symbol | Role |
|---|---|
| `get_keywords()` ([:20](../_version.py#L20)) | returns the `$Format:%d$` / `%H$` / `%ci$` strings that `git archive` substitutes |
| `class VersioneerConfig` ([:33](../_version.py#L33)) | plain container for the config values |
| `get_config()` ([:37](../_version.py#L37)) | builds a `VersioneerConfig` with the values baked in from `setup.cfg` |
| `class NotThisMethod(Exception)` ([:51](../_version.py#L51)) | raised when a given version-detection strategy doesn't apply |
| `register_vcs_handler(vcs, method)` ([:59](../_version.py#L59)) | decorator that registers a function in the `HANDLERS` table |
| `run_command(commands, args, ...)` ([:70](../_version.py#L70)) | thin `subprocess.Popen` wrapper that tries each candidate executable name |
| `versions_from_parentdir(parentdir_prefix, root, verbose)` ([:107](../_version.py#L107)) | infers the version from the source directory's name (tarball fallback) |
| `git_get_keywords(versionfile_abs)` ([:133](../_version.py#L133)) | reads the `$Format$` keywords back out of this file |
| `git_versions_from_keywords(keywords, tag_prefix, verbose)` ([:162](../_version.py#L162)) | parses a version out of expanded `git archive` keywords |
| `git_pieces_from_vcs(tag_prefix, root, verbose, ...)` ([:217](../_version.py#L217)) | the main path: runs `git describe` and assembles the raw "pieces" dict |
| `plus_or_dot(pieces)` ([:308](../_version.py#L308)) | formatting helper for the local-version separator |
| `render_pep440*` / `render_git_describe*` ([:315-443](../_version.py#L315-L443)) | turn the "pieces" dict into a version string in the various supported styles |
| `render(pieces, style)` ([:445](../_version.py#L445)) | dispatches to the right `render_*` based on `style` (`pep440` here) |
| `get_versions()` ([:477](../_version.py#L477)) | public entry point — tries keyword, then VCS, then parentdir strategies and returns `{"version": ..., "full-revisionid": ..., "dirty": ..., "error": ..., "date": ...}` |

## Consumers

`plipify/__init__.py` calls `get_versions()` at import time to populate `__version__` and
`__git_revision__`. `setup.py` also imports `versioneer` (the repo-root copy) to stamp the version
at build time. `setup.cfg`'s coverage config omits this file from coverage reports.
