"""Verification driver for the generated protocol SDK projects.

For every qualifying project under D:\\code this runs the five gates the forge
promises (compile, pytest, ruff lint, ruff format, mypy) with the interpreter that
is executing this script and the project directory as the working directory, then
prints one status line per project, a per-gate summary, and the captured output of
every failing gate.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path("D:/code")
MAX_LINES = 60

PROJECTS = [
    # certledger qualifies the way the shells do (ROADMAP.md + pyproject.toml) and has real code
    # since phase 0, so it carries the same five gates. asn1core is absent because it plans in
    # PLAN.md/VECTORS.md and so fails qualifies(); widening that predicate is a separate decision,
    # recorded in PORTFOLIO.md section 10.
    "certledger",
    "rpkit",
    "rtrkit",
    "asnkit",
    "h3tunnel",
    "dnssd-srp",
    "turnkit",
    "leasespy",
    "cwmp",
    "devicespy",
    "ohttp",
    "ntspy",
    "tacacs",
    "signeddata",
    "pgpenv",
    "syslogkit",
    "sfields",
    "shaken",
    "srtpkit",
    "pkix",
    "revokekit",
    "enrollkit",
    "ctspy",
    "pathattr",
    "bmpkit",
    "rpslkit",
    "bgpfeed",
    "routevalid",
    "lgc",
]

GATES = ["compile", "pytest", "ruff", "format", "mypy"]


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, *cmd],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def qualifies(name: str) -> Path | None:
    cwd = ROOT / name
    if (
        cwd.is_dir()
        and (cwd / "ROADMAP.md").is_file()
        and (cwd / "pyproject.toml").is_file()
    ):
        return cwd
    return None


def main() -> int:
    failures: list[tuple[str, str, str, str]] = []
    counts = {gate: {"OK": 0, "FAIL": 0} for gate in GATES}
    skipped: list[str] = []
    checked = 0

    for name in PROJECTS:
        cwd = qualifies(name)
        if cwd is None:
            skipped.append(name)
            continue
        checked += 1
        pkg = name.replace("-", "_")
        specs = [
            ("compile", ["-m", "compileall", "-q", pkg]),
            ("pytest", ["-m", "pytest", "-q", "-p", "no:cacheprovider"]),
            ("ruff", ["-m", "ruff", "check", "."]),
            ("format", ["-m", "ruff", "format", "--check", "."]),
            ("mypy", ["-m", "mypy", pkg]),
        ]
        results = []
        for gate, cmd in specs:
            code, out, err = run(cmd, cwd)
            status = "OK" if code == 0 else "FAIL"
            counts[gate][status] += 1
            results.append(f"{gate}={status}")
            if status == "FAIL":
                failures.append((name, gate, out, err))
        print(f"{name} " + " ".join(results), flush=True)

    print()
    print("summary")
    for gate in GATES:
        print(f"  {gate:8s} OK={counts[gate]['OK']:3d} FAIL={counts[gate]['FAIL']:3d}")
    print(f"  projects checked = {checked}")
    if skipped:
        print(
            f"  skipped (missing ROADMAP.md/pyproject.toml or absent) = {', '.join(skipped)}"
        )

    if failures:
        print()
        print("failure output")
        for name, gate, out, err in failures:
            print()
            print("=" * 72)
            print(f"FAIL {name} :: {gate}")
            print("=" * 72)
            for label, text in (("stdout", out), ("stderr", err)):
                lines = text.splitlines()
                if not lines:
                    continue
                suffix = f", capped at {MAX_LINES}" if len(lines) > MAX_LINES else ""
                print(f"--- {label} ({len(lines)} lines{suffix}) ---")
                for line in lines[:MAX_LINES]:
                    print(line)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
