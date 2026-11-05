# ------------------------------------------------------------------ supporting project files

CONTRIBUTING = """
# Contributing

Short version: four gates, and they all have to pass on Linux and Windows.

```bash
ruff check . && ruff format --check .
mypy @PKG@
pytest -q --cov
python -O -m pytest -q
```

## The three rules that cause the most arguments

1. **`assert` belongs in tests and nowhere on a wire path.** The fourth gate strips
   asserts, and a parser whose bounds checks were asserts stops being a parser in
   production. On a parse path, raise a named exception.
2. **A behaviour change updates its ROADMAP row in the same commit.** The row flips to
   `[ok]` only with a named test. A row and a test drift apart within one release, and the
   matrix becomes useless exactly when someone needs it.
3. **Cite the document, not a blog post.** A section number is allowed only if that section
   was read. `docs/rfc-map.md` records what was verified and when.

## Layout

| Tier | Home | Rule |
|---|---|---|
| Core | `@PKG@/` | specification behaviour only; dependency-free unless README says why not |
| Apps | `@PKG@/apps/` | composes core pieces, adds no new protocol surface |
| Examples | `examples/` | one runnable script per use case; never restates library logic |

A pattern graduates from `examples/` to `apps/` on the second user, stated rather than
assumed.

## Tests

Protocol tests are vectors first: bytes in, structure out, with the source of the vector
cited. `hypothesis` is welcome for codecs, and every fuzz-found crash becomes a fixed
regression test rather than only a property.

## Milestones

Pick a row from the matrix, not a feature from your imagination. If the row you want is
missing, add it to the matrix first and argue for it there.
"""

SECURITY = """
# Security policy

## What this project treats as a security property

- **Hostile input is the normal case.** Every decoder has to refuse truncation, over-long
  lengths, nested structures and contradictory fields without raising anything a caller
  cannot name.
- **Bounds before cleverness.** Size, count and depth limits exist on every parse path, and
  they are configuration rather than suggestions.
- **No silent crypto policy.** Weak or deprecated algorithms are refused by an explicit
  policy object rather than accepted because they happen to parse.
- **Provenance is part of the answer.** A result states what was verified, what was cached
  and what was skipped, so a caller cannot mistake an unchecked field for a checked one.

## assert is not a safety mechanism

`python -O` strips asserts. Any invariant that protects a parser boundary or a verification
result must be expressed as a raised exception. CI runs the suite under `-O` for exactly
this reason.

## Reporting

Open a private security advisory on the repository rather than a public issue. The policy is
the Apache Software Foundation's: security support for the main branch and the most recent
release. Because this repository is a pre-alpha shell, a report will often be answered with
"that code does not exist yet", which is a different thing from "it will not be fixed".
"""

CHANGELOG = """
# Changelog

The format follows Keep a Changelog, and this project adheres to Semantic Versioning.

## Unreleased

Nothing yet. This repository is a shell: the public surface exists as typed stubs that raise
`NotImplementedError`, and [ROADMAP.md](ROADMAP.md) lists what has to happen first.

## 0.0.0 - @SURVEY_DATE@

### Added

- Package skeleton, obligation matrix and CI gates for @NAME@.
- `@PKG@.apps` namespace reserved for composition that is not protocol behaviour.
"""

NOTICE = """
@NAME@
Copyright 2026 Justin Capella

This product includes software developed as part of an RFC-anchored protocol SDK portfolio.
Specification text referenced by this project is the work of its authors and is cited by
document number; no normative text is redistributed here beyond short identifiers.
"""

GITIGNORE = """
__pycache__/
*.py[cod]
*.egg-info/
.venv/
build/
dist/
.coverage
htmlcov/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.hypothesis/
*.log
requirements-audit.txt

# Working notes quote other projects' trackers and age faster than a tracked document
# should. Evidence that survives gets promoted into README.md or ROADMAP.md with a date;
# the scratch file itself never gets committed.
docs/research.md
"""

GITATTRIBUTES = """
* text=auto eol=lf
*.py text
*.md text
*.toml text
*.yml text
*.png binary
*.pcap binary
*.der binary
"""

CI = """
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: python -m @PIPIN@ -e ".[dev]"
      - run: ruff check .
      - run: ruff format --check .
      - run: mypy @PKG@
      - run: python tools/check_dist.py

  test:
    # A socket option that exists only on Linux is exactly the bug a Linux-only CI never
    # sees, and multicast, UDP send buffers and interface enumeration differ per platform.
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ["3.12", "3.13", "3.14"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: python -m @PIPIN@ -e ".[dev]"
      - run: python -m pytest -q --cov
      # Asserts stripped: a wire path guarded by assert is unguarded in production.
      - run: python -O -m pytest -q
"""

SECURITY_WF = """
name: security

on:
  push:
    branches: [main]
  schedule:
    - cron: "17 4 * * 2"

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: python -m @PIPIN@ -e ".[dev]" pip-audit
      # The resolved environment is audited rather than the declarations, because the
      # declarations are floors. A file is written by a script rather than shell
      # redirection so the step behaves identically on a self-hosted runner.
      - run: python tools/write_freeze.py requirements-audit.txt
      - run: python -m pip_audit --progress-spinner off -r requirements-audit.txt
"""

STRATEGY = """
# Strategy

The completeness matrix is [../ROADMAP.md](../ROADMAP.md). This document is *why* the rows
are ordered the way they are, and the rules that order has to respect.

## The constitution

1. **The core is the specification implementation.** `@PKG@/` holds codecs, state machines
   and the vocabulary of @NAME@. New core code appears when a document defines the
   behaviour, or when an ordering rule with no document earns an explicit convention label.
2. **Sans-IO before sockets.** Anything decidable from data plus a clock is implemented
   without touching a socket, so every timeout, retry and rollover is testable without
   sleeping or networking.
3. **Dependency-free by default.** An exception needs a sentence in README.md explaining why
   the rule was broken, and a floor with no ceiling.
4. **Positioning is correctness and legibility, not throughput.** The incumbents in this
   corner are usually stale, untyped, or welded to a product. This is the implementation that
   says how it knows what it claims.
5. **Every answer carries its provenance.** Verified or cached, which document, refused or
   believed. An answer without provenance is a guess with a confident type.

## The three tiers

| Tier | Home | Contents | Rule |
|---|---|---|---|
| Core | `@PKG@/` | codecs, state machines, policy objects | RFC-cited or convention-labelled |
| Apps | `@PKG@/apps/` | reusable assemblies that compose core | no new protocol surface |
| Examples | `examples/` | one runnable script per use case | configures; never restates logic |

## Interface grammar

One engine, three drives, never parallel implementations:

- **await** -- the native asyncio surface.
- **blocking** -- a facade owning a private loop, so a call from inside a caller's running
  loop works instead of deadlocking.
- **callback** -- plain callables, no third-party promise type.

## Naming

One string everywhere: the distribution, the import and the console script. A name that
means one thing in the installer, in `import` and on `PATH` is the only arrangement that
cannot surprise anyone, and it is also why this project does not sit one edit away from a
project that already exists.
"""

EXAMPLES = """
# examples

One runnable script per use case. An example configures the library; it never restates
library logic, and the prose in the docs quotes these files rather than duplicating them.

Nothing here runs yet: the package surface is stubs that raise `NotImplementedError`. Each
milestone in [../ROADMAP.md](../ROADMAP.md) adds the example that proves it works.
"""
