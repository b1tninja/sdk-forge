"""Refuse a commit that deletes structure by accident or adds scratch to a tracked tree.

Both checks exist because they were needed, repeatedly, in one working session: markdown headings were
dropped five separate times by replacement edits that matched a heading line and omitted it from the
replacement text, and scratch output landed in repository trees where a later `git add -A` swept it into
a commit. Neither is caught by a linter or a type checker. Both produce a diff that looks like a
documentation edit, so they survive review until someone counts headings, which nobody does.

The rule is deliberately narrow and it never rewrites anything: if headings vanished, the commit stops
and says which ones. Decide on purpose, then commit again with FORGE_ALLOW_HEADING_LOSS=1.

    py check_hygiene.py            # inspect the staged index
    py check_hygiene.py --install  # wire it up as this repository's pre-commit hook
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys
from collections import Counter

# probe_* was the shape scratch actually took here; .log/.out/.err were the redirection targets that got
# committed. Anything matching is refused on the way in, and only reported (not refused) if a commit
# adds nothing new to it.
SCRATCH_RE = re.compile(r"(?:^|/)(?:probe_[^/]+\.py|[^/]+\.(?:log|out|err|diff))$")
HEADING_RE = re.compile(r"^#{1,6} \S.*$", re.MULTILINE)
ALLOW = "FORGE_ALLOW_HEADING_LOSS"


def git(args: list[str], cwd: pathlib.Path) -> str:
    done = subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return done.stdout if done.returncode == 0 else ""


def staged_markdown(cwd: pathlib.Path) -> list[str]:
    """Markdown paths added or modified in the index."""
    out = git(
        ["diff", "--cached", "--name-only", "--diff-filter=ACM", "--", "*.md"], cwd
    )
    return [line for line in out.splitlines() if line]


def staged_scratch(cwd: pathlib.Path) -> list[str]:
    """Newly added files whose names mark them as scratch."""
    out = git(["diff", "--cached", "--name-only", "--diff-filter=A"], cwd)
    return [line for line in out.splitlines() if SCRATCH_RE.search(line)]


def heading_regression(before: str, after: str) -> list[str]:
    """Headings present in `before` and gone from `after`, order-insensitive, duplicates preserved.

    Duplicates matter: a document with the same sub-heading twice loses one silently if the comparison
    is a set difference, which is exactly the case a careless replace produces most often.
    """
    lost: list[str] = []
    remaining = Counter(HEADING_RE.findall(after))
    for heading in HEADING_RE.findall(before):
        if remaining[heading] > 0:
            remaining[heading] -= 1
        else:
            lost.append(heading)
    return lost


def check(cwd: pathlib.Path) -> list[str]:
    """Every reason this staged state should not become a commit."""
    problems: list[str] = []
    if not os.environ.get(ALLOW):
        for path in staged_markdown(cwd):
            before = git(["show", f"HEAD:{path}"], cwd)
            if not before:
                continue  # new file: nothing to regress against
            after = git(["show", f":{path}"], cwd)
            for heading in heading_regression(before, after):
                problems.append(f"{path}: heading vanished: {heading}")
    for path in staged_scratch(cwd):
        problems.append(
            f"{path}: looks like scratch; commit it outside the tree or rename it"
        )
    return problems


HOOK = """#!/bin/sh
# Installed by sdk-forge/check_hygiene.py --install.
# Stops a commit that deletes a markdown heading by accident or adds scratch to the tree.
# Escape hatch: git commit --no-verify, or FORGE_ALLOW_HEADING_LOSS=1 for the heading check only.

# The hooks path lives inside sdk-forge, so the checker is one directory up from this script. Fall
# back to the repo layout and then to a sibling checkout, because the forge is a subtree of the
# workspace here and a standalone clone elsewhere.
FORGE_HOME="${FORGE_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
for guess in "$FORGE_HOME" "$(git rev-parse --show-toplevel)/sdk-forge" "$(git rev-parse --show-toplevel)/../sdk-forge"; do
  if [ -f "$guess/check_hygiene.py" ]; then
    FORGE_HOME="$guess"
    break
  fi
done

# `python` and `py` are not interchangeable on Windows boxes: one is often absent while the other is
# the launcher. A hook that cannot find an interpreter must not silently succeed.
PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=py

if [ ! -f "$FORGE_HOME/check_hygiene.py" ] || ! command -v "$PY" >/dev/null 2>&1; then
  # Deliberately fatal. A gate that cannot run and exits 0 reports the same green as a clean tree,
  # which is how a check becomes decoration without anyone deciding to remove it.
  echo "pre-commit: cannot run sdk-forge hygiene check (FORGE_HOME unresolved or no interpreter)." >&2
  echo "pre-commit: set FORGE_HOME, or bypass with --no-verify if you accept no check ran." >&2
  exit 1
fi
exec "$PY" "$FORGE_HOME/check_hygiene.py"
"""


def install(cwd: pathlib.Path) -> int:
    """Point this repository's hooks path at the forge's githooks directory and write the hook."""
    target = pathlib.Path(__file__).resolve().parent / "githooks"
    target.mkdir(parents=True, exist_ok=True)
    hook = target / "pre-commit"
    if hook.exists() and "# Installed by sdk-forge" not in hook.read_text(
        encoding="utf-8"
    ):
        print(f"refusing to overwrite an existing hook at {hook}", file=sys.stderr)
        return 1
    hook.write_text(HOOK, encoding="utf-8", newline="\n")
    done = subprocess.run(  # noqa: S603
        [
            "git",
            "config",
            "core.hooksPath",
            str(target.relative_to(cwd) if target.is_relative_to(cwd) else target),
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        print(
            f"git config core.hooksPath failed: {done.stderr.strip()}", file=sys.stderr
        )
        return 1
    print(f"hook installed: {cwd} -> {target}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install", action="store_true", help="set core.hooksPath and write the hook"
    )
    parser.add_argument(
        "--repo", default=".", help="repository to inspect or install into"
    )
    args = parser.parse_args()
    cwd = pathlib.Path(args.repo).resolve()

    if args.install:
        return install(cwd)
    problems = check(cwd)
    for problem in problems:
        print(f"hygiene: {problem}", file=sys.stderr)
    if problems:
        print(
            f"{len(problems)} problem(s); {ALLOW}=1 to override the heading check",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
