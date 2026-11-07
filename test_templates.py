"""The generator's templates are guarded here, because nothing else exercises them.

`forge.py` writes managed files into every generated project, and its templates are strings: a linter
checks that the Python compiles, not that the CI it emits actually works. Two defects in these strings
were only found when a generated repository ran CI for the first time - `check_dist.py` inspecting a
wheel nothing had built, and an audit that cloned the private project over an anonymous git URL. This
file is where those two stay fixed.

It also guards the shape of the file itself. `forge.py` was assembled by concatenation and its
`__main__` guard must remain at the very end: a guard placed earlier would call run() before the
wrappers that follow had reassigned build, and artefacts would silently stop being written. An
accidental bare `run()` at module scope would rewrite every generated project the moment something
imported the module to inspect it - which is what these tests do.
"""

from __future__ import annotations

import pathlib

import forge

HERE = pathlib.Path(__file__).resolve().parent


def test_ci_template_builds_the_wheel_before_inspecting_it():
    ci = forge.CI
    assert "python -m build --wheel" in ci
    assert ci.index("python -m build --wheel") < ci.index("python tools/check_dist.py")
    # Installing build must precede using it.
    assert ci.index("-m @PIPIN@ build") < ci.index("python -m build --wheel")


def test_freeze_excludes_the_project_under_audit():
    """The audit installs what the freeze lists, so a self-reference becomes an anonymous git clone."""
    script = forge.WRITE_FREEZE
    assert 'line.startswith("-e")' in script
    assert '"git+"' in script
    assert '"file://"' in script
    assert "self-reference" in script


def test_main_guard_is_the_last_statement():
    lines = [
        line
        for line in (HERE / "forge.py").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert lines[-1].strip() == "raise SystemExit(run())"
    assert lines[-2].strip() == 'if __name__ == "__main__":'


def test_importing_this_module_did_not_generate_anything():
    """`import forge` above must not have written files into the workspace."""
    assert callable(forge.run)
    assert not hasattr(forge, "_GENERATED_THIS_IMPORT")


def test_scratch_and_duplicate_templates_are_gone():
    assert not (HERE / "parts").exists(), (
        "parts/ duplicated template strings that forge.py never read"
    )
    assert not sorted(HERE.glob("probe_*.py")), (
        "probe_* is scratch; the workspace rule keeps it out"
    )


def test_hygiene_gate_would_reject_the_scratch_it_shipped_before():
    import check_hygiene as h

    assert h.SCRATCH_RE.search("probe_ber.py")
    assert not h.SCRATCH_RE.search("forge.py")
