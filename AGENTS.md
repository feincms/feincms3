# Agent notes

## Tests

- Quick run with the local virtualenv: `.venv/bin/python -m pytest tests/testapp`
- Full matrix: `tox` (environments are listed in `tox.ini`, e.g.
  `tox -e py315-dj61`). CI (`.github/workflows/tests.yml`) runs every
  `py<version>-*` environment for each Python version in its matrix, so keep
  the CI matrix, the tox envlist and the `pyproject.toml` classifiers in sync.

## Conventions

- Add user-facing changes to the "Next version" section of `CHANGELOG.rst`.

## Commits

- Commit feature by feature: one commit per fix or feature, each including
  its tests and changelog entry.
- No attribution lines (no `Co-Authored-By` etc.).
- Keep commit messages short and don't repeat what the diff or changelog
  already says; a concise subject line is usually enough.
