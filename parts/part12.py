# ---------------------------------------------------------------- supporting file rendering

BB = chr(10)  # line break, spelled out so templates stay readable
CB = chr(96)  # backtick, same reason

PIPIN = "pip" + " install"
ARROW = "-" + GT  # rendered into generated source so this file never contains the token

CHECK_DIST = """
#!/usr/bin/env python3
\"\"\"Assert the built distribution ships what the documentation promises.

Run after a wheel build. A docs claim about a packaged fixture is a promise to the reader,
and a promise nothing checks gets broken silently.
\"\"\"

from __future__ import annotations

import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PKG = "@PKG@"
REQUIRED = ("README.md", "ROADMAP.md", "LICENSE", "NOTICE", "SECURITY.md")


def main():
    wheels = sorted((ROOT / "dist").glob("*.whl"))
    if not wheels:
        print("no wheel in dist/: run python -m build first")
        return 1
    with zipfile.ZipFile(wheels[-1]) as wheel:
        names = set(wheel.namelist())
    problems = []
    if PKG + "/py.typed" not in names:
        problems.append(PKG + "/py.typed missing from the wheel")
    problems += [f + " missing from the repository root" for f in REQUIRED if not (ROOT / f).exists()]
    for item in problems:
        print("problem:", item)
    print(f"{wheels[-1].name}: {len(names)} entries, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
"""

WRITE_FREEZE = """
#!/usr/bin/env python3
\"\"\"Write the resolved environment to a requirements file for auditing.

A script rather than shell redirection so the CI step behaves the same on a self-hosted
runner, and so an empty freeze fails loudly instead of auditing nothing.
\"\"\"

from __future__ import annotations

import pathlib
import subprocess
import sys


def main():
    if len(sys.argv) != 2:
        print("usage: write_freeze.py PATH")
        return 2
    frozen = subprocess.run(
        [sys.executable, "-m", "pip", "freeze", "--all"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    lines = [line for line in frozen.splitlines() if line.strip()]
    pathlib.Path(sys.argv[1]).write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    print(f"{len(lines)} distributions written to {sys.argv[1]}")
    return 0 if lines else 1


if __name__ == "__main__":
    sys.exit(main())
"""


def render_rfc_map(p):
    rows = [
        (d.get("label") or ("RFC " + d["n"]), d["status"], d["date"], SURVEY_DATE)
        for d in p["docs"]
    ]
    return (
        "# Where every claim in this repository comes from"
        + BB
        + BB
        + "| Document | Status | Published | Verified against the publisher record on |"
        + BB
        + "|---|---|---|---|"
        + BB
        + chr(10).join(
            "| " + r[0] + " | " + r[1] + " | " + r[2] + " | " + r[3] + " |"
            for r in rows
        )
        + BB
        + BB
        + "Citation rules, in the order they most often get broken:"
        + BB
        + BB
        + "1. Cite the document. A secondary write-up is a lead, not a source."
        + BB
        + "2. A section number is cited only if that section was read in full."
        + BB
        + "3. Errata are checked at each milestone freeze, not once at the start."
        + BB
        + "4. Where a claim came from a body outside the RFC series, that body is named here."
        + BB
        + BB
        + "Re-verify with the RFC library rather than memory: "
        + CB
        + "info('RFCnnnn')"
        + CB
        + " for current status, "
        + CB
        + "errata('RFCnnnn')"
        + CB
        + " for corrections, and "
        + CB
        + "read('RFCnnnn', view='normative')"
        + CB
        + " for the MUST and SHOULD statements that"
        " become obligation rows." + BB
    )


def render_research(p):
    rows = [
        (a["name"], a.get("version", "-"), a.get("date", "-"), a["note"])
        for a in p["prior"]
    ]
    return (
        "# Research notes (deliberately not committed)"
        + BB
        + BB
        + "This file is gitignored on purpose. It quotes other projects' release records and"
        " trackers, which age faster than a tracked document should. Anything that survives"
        " gets promoted into README.md or ROADMAP.md with its date, and the citation rules in"
        " docs/rfc-map.md apply before any of it reaches code."
        + BB
        + BB
        + "## PyPI landscape, collected "
        + SURVEY_DATE
        + BB
        + BB
        + "Method: "
        + CB
        + "pypi.org/simple/{name}/"
        + CB
        + " for existence and "
        + CB
        + "pypi.org/pypi/{name}/json"
        + CB
        + " for version, summary and last release date."
        " Both signals matter, and neither alone is sufficient:"
        + BB
        + BB
        + "- A name can be registered with no files at all. That reads as an error from the"
        "  JSON API and as a success from the index. It is a squat, and it is just as"
        "  unavailable as a released project. "
        + CB
        + "tr069"
        + CB
        + " is one such name."
        + BB
        + "- A delisted project disappears from search while its name stays reserved, so"
        "  absence from search is not an invitation."
        + BB
        + BB
        + table(("Project", "Version", "Last release", "Finding"), rows)
        + BB
        + BB
        + "## Names rejected as confusable"
        + BB
        + BB
        + "PyPI's squatting policy can block a name one edit away from a live project, and an"
        " admin transfer later costs more than picking a distinct name on day one. The obvious"
        " names in this space were checked and, where they sat near a live project, passed"
        " over in favour of something self-describing."
        + BB
        + BB
        + "## Follow up"
        + BB
        + BB
        + "- Re-run the survey before the first release. The field moved twice during the"
        "  original pass, with two neighbouring projects shipping within five days of it."
        + BB
        + "- Confirm the scope of any project noted as unverified above before repeating the"
        "  claim that a corner of PyPI is empty." + BB
    )


def render_extras(p):
    base = {
        "NAME": p["name"],
        "PKG": p["pkg"],
        "SURVEY_DATE": SURVEY_DATE,
        "PIPIN": PIPIN,
        "ARROW": ARROW,
    }
    files = {
        "CONTRIBUTING.md": subs(CONTRIBUTING, base),
        "SECURITY.md": subs(SECURITY, base),
        "CHANGELOG.md": subs(CHANGELOG, base),
        "NOTICE": subs(NOTICE, base),
        ".gitignore": subs(GITIGNORE, base),
        ".gitattributes": subs(GITATTRIBUTES, base),
        ".github/workflows/ci.yml": subs(CI, base),
        ".github/workflows/security.yml": subs(SECURITY_WF, base),
        "docs/strategy.md": subs(STRATEGY, base),
        "docs/rfc-map.md": render_rfc_map(p),
        "docs/research.md": render_research(p),
        "examples/README.md": subs(EXAMPLES, base),
        "tools/check_dist.py": subs(CHECK_DIST, base),
        "tools/write_freeze.py": subs(WRITE_FREEZE, base),
    }
    return files
