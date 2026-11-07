"""verify.py: where it looks, how long it waits, and the project list other modules import from it."""

from __future__ import annotations

import importlib

import verify


def test_root_is_read_from_forge_root(monkeypatch, tmp_path):
    before = verify.ROOT
    monkeypatch.setenv("FORGE_ROOT", str(tmp_path))
    try:
        assert importlib.reload(verify).ROOT == tmp_path
    finally:
        monkeypatch.undo()
        importlib.reload(verify)
    assert verify.ROOT == before


def test_a_gate_that_hangs_is_killed_and_reported_as_a_failure(tmp_path):
    code, out, err = verify.run(
        ["-c", "import sys, time; print('started', flush=True); time.sleep(30)"],
        tmp_path,
        timeout=1,
    )
    assert code != 0
    assert "timed out after 1 seconds" in err


def test_a_gate_that_finishes_reports_its_own_status(tmp_path):
    code, out, err = verify.run(
        ["-c", "import sys; print('ok'); sys.exit(3)"], tmp_path, timeout=60
    )
    assert (code, out.strip(), err) == (3, "ok", "")


def test_qualifies_needs_both_the_matrix_and_the_package(monkeypatch, tmp_path):
    monkeypatch.setattr(verify, "ROOT", tmp_path)
    project = tmp_path / "demo"
    project.mkdir()
    (project / "ROADMAP.md").write_text("# Roadmap\n", encoding="utf-8")
    assert verify.qualifies("demo") is None
    (project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    assert verify.qualifies("demo") == project
    assert verify.qualifies("absent") is None


def test_projects_stays_importable_and_covers_every_generated_shell():
    # deps.py and test_templates.py import this name; it must stay a plain list of directory names.
    from verify import PROJECTS

    assert isinstance(PROJECTS, list)
    assert all(isinstance(name, str) and name for name in PROJECTS)
    assert len(PROJECTS) == len(set(PROJECTS))
    import forge

    assert set(forge.POSITION) <= set(PROJECTS)
    assert "certledger" in PROJECTS
