"""The generator writes only what it still owns, and a dry run writes nothing at all.

Before the guard, one `python forge.py` would have turned ctspy's sct.py from 8174 bytes of implementation
into a 1398-byte stub, dropped ctspy's six [ok] rows, and replaced the workspace AGENTS.md with a template.
These tests run the real pipeline against a scratch workspace and check the bytes on disk, not the
pipeline's own report of what it did.
"""

from __future__ import annotations

import ast
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

import forge
from forge_data import certificate, naming, position, routing

HERE = pathlib.Path(__file__).resolve().parent
CTSPY = pathlib.Path(os.environ.get("FORGE_ROOT") or "D:/code") / "ctspy"
IMPLEMENTED = (
    b'"""An implemented module."""\n\n\ndef parse_sct(data):\n    return data[:1]\n'
)


@pytest.fixture
def ws(tmp_path, monkeypatch):
    """A scratch workspace, a manifest outside it, and no formatter run (it cannot affect ownership)."""
    root = tmp_path / "ws"
    root.mkdir()
    monkeypatch.setattr(forge, "ROOT", root)
    monkeypatch.setattr(forge, "MANIFEST", tmp_path / "state" / "generated.json")
    monkeypatch.setattr(forge, "polish", lambda name, files: (files, []))
    return root


def snapshot(root: pathlib.Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def make_done_row(root: pathlib.Path, name: str) -> None:
    """Flip the first obligation row of a generated ROADMAP.md to [ok]."""
    roadmap = root / name / "ROADMAP.md"
    lines = roadmap.read_text(encoding="utf-8").split("\n")
    row = next(
        i for i, line in enumerate(lines) if line.startswith("| `") and "`[ ]`" in line
    )
    lines[row] = lines[row].replace("`[ ]`", "`[ok]`")
    roadmap.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------- dry run


def test_a_dry_run_writes_nothing(ws, capsys):
    forge.run(["--project", "ntspy"])
    (ws / "ntspy" / "README.md").write_text("edited by hand\n", encoding="utf-8")
    (ws / "ntspy" / "NOTICE").unlink()
    before = snapshot(ws)
    manifest = forge.MANIFEST.read_bytes()

    code = forge.run(["--check", "--diff"])

    assert snapshot(ws) == before
    assert forge.MANIFEST.read_bytes() == manifest
    assert code == 1, "a dry run with differences must exit 1"
    out = capsys.readouterr().out
    assert "would create rpkit/ROADMAP.md" in out
    assert "would create ./protocol-sdks.md" in out
    assert "keep ntspy/README.md - edited since the generator last wrote it" in out
    assert "+++ b/ntspy/NOTICE" in out  # --diff shows the change it would make


def test_a_dry_run_of_an_empty_workspace_creates_nothing(ws):
    assert forge.run(["--dry-run", "--project", "pkix"]) == 1
    assert snapshot(ws) == {}
    assert not forge.MANIFEST.exists()


def test_a_second_run_finds_nothing_to_do(ws, capsys):
    assert forge.run(["--project", "rpkit"]) == 0
    capsys.readouterr()
    assert forge.run(["--check", "--project", "rpkit"]) == 0
    assert "would change 0," in capsys.readouterr().out


# ---------------------------------------------------------------- ownership (D17)


def test_an_implemented_ctspy_like_module_is_not_overwritten(ws):
    forge.run(["--project", "ctspy"])
    sct = ws / "ctspy" / "ctspy" / "sct.py"
    assert b"NotImplementedError" in sct.read_bytes()
    sct.write_bytes(IMPLEMENTED)

    forge.run(["--project", "ctspy"])
    assert sct.read_bytes() == IMPLEMENTED


def test_a_module_with_no_stub_left_is_kept_even_when_adopted(ws, capsys):
    """--adopt takes over unrecorded files, but never an implemented module."""
    forge.run(["--project", "ctspy"])
    sct = ws / "ctspy" / "ctspy" / "sct.py"
    sct.write_bytes(IMPLEMENTED)
    forge.MANIFEST.unlink()

    forge.run(["--project", "ctspy", "--adopt"])
    assert sct.read_bytes() == IMPLEMENTED
    assert "no NotImplementedError left" in capsys.readouterr().out


def test_a_done_row_makes_the_project_hand_owned_except_its_plan(ws):
    forge.run(["--project", "rpkit"])
    make_done_row(ws, "rpkit")
    readme = ws / "rpkit" / "README.md"
    readme.write_bytes(readme.read_bytes() + b"\nhand note\n")
    (ws / "rpkit" / "docs" / "plan.md").write_text("stale\n", encoding="utf-8")
    forge.MANIFEST.unlink()  # even adoption cannot reclaim a project with a done row
    roadmap = (ws / "rpkit" / "ROADMAP.md").read_bytes()

    forge.run(["--project", "rpkit", "--adopt"])

    assert readme.read_bytes().endswith(b"hand note\n")
    assert (ws / "rpkit" / "ROADMAP.md").read_bytes() == roadmap
    assert (
        (ws / "rpkit" / "docs" / "plan.md")
        .read_text(encoding="utf-8")
        .startswith("# Portfolio position")
    )


def test_an_unrecorded_file_is_kept_until_adopted(ws):
    forge.run(["--project", "turnkit"])
    notice = ws / "turnkit" / "NOTICE"
    notice.write_text("older generator output\n", encoding="utf-8")
    forge.MANIFEST.unlink()

    forge.run(["--project", "turnkit"])
    assert notice.read_text(encoding="utf-8") == "older generator output\n"

    forge.run(["--project", "turnkit", "--adopt"])
    assert notice.read_text(encoding="utf-8") != "older generator output\n"


def test_an_unrecorded_plan_with_the_generated_header_is_regenerated(ws):
    forge.run(["--project", "tacacs", "--only", "plan"])
    plan = ws / "tacacs" / "docs" / "plan.md"
    plan.write_text(
        plan.read_text(encoding="utf-8") + "\nstale tail\n", encoding="utf-8"
    )
    forge.MANIFEST.unlink()

    forge.run(["--project", "tacacs", "--only", "plan"])
    assert "stale tail" not in plan.read_text(encoding="utf-8")


def test_d17_named_roadmaps_are_hand_owned(ws):
    for name in ("pkix", "ctspy"):
        forge.run(["--project", name])
        roadmap = ws / name / "ROADMAP.md"
        roadmap.write_text("hand-maintained\n", encoding="utf-8")
        forge.MANIFEST.unlink()
        forge.run(["--project", name, "--adopt"])
        assert roadmap.read_text(encoding="utf-8") == "hand-maintained\n"


def test_adopt_refuses_the_whole_workspace(ws, capsys):
    with pytest.raises(SystemExit):
        forge.run(["--adopt"])
    assert "--adopt needs --project" in capsys.readouterr().err


@pytest.mark.skipif(
    not (CTSPY / "ctspy" / "sct.py").is_file(), reason="needs the ctspy checkout"
)
def test_build_on_a_copy_of_ctspy_leaves_its_implementation_byte_identical(ws):
    shutil.copytree(
        CTSPY,
        ws / "ctspy",
        ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".*_cache", ".venv", "*.egg-info", "dist", "build"
        ),
    )
    before = snapshot(ws / "ctspy")

    forge.run(["--project", "ctspy"])
    forge.run(["--project", "ctspy", "--adopt"])

    after = snapshot(ws / "ctspy")
    for rel in (
        "ctspy/sct.py",
        "ctspy/sth.py",
        "ctspy/merkle.py",
        "ROADMAP.md",
        "README.md",
    ):
        assert after[rel] == before[rel], rel
    changed = sorted(rel for rel in after if before.get(rel) != after[rel])
    assert changed in ([], ["docs/plan.md"]), changed


# ---------------------------------------------------------------- --only and --project


def test_only_plan_writes_only_docs_plan(ws):
    assert forge.run(["--only", "plan", "--project", "pkix"]) == 0
    assert sorted(snapshot(ws)) == ["pkix/docs/plan.md"]


def test_only_plan_leaves_every_other_file_of_a_built_project_alone(ws):
    forge.run(["--project", "pkix"])
    (ws / "asn1core" / "asn1core").mkdir(
        parents=True
    )  # asn1core gains code: pkix's plan text changes
    (ws / "asn1core" / "asn1core" / "__init__.py").write_text(
        "x = 1\n", encoding="utf-8"
    )
    (ws / "asn1core" / "tests").mkdir()
    (ws / "asn1core" / "tests" / "test_a.py").write_text(
        "def test_a(): pass\n", encoding="utf-8"
    )
    (ws / "pkix" / "README.md").write_text(
        "would be reverted by a full run\n", encoding="utf-8"
    )
    forge.MANIFEST.unlink()
    before = snapshot(ws)

    forge.run(["--only", "plan", "--project", "pkix", "--adopt"])

    after = snapshot(ws)
    changed = sorted(rel for rel in after if before.get(rel) != after[rel])
    assert changed == ["pkix/docs/plan.md"]
    assert b"Gated by coverage" in after["pkix/docs/plan.md"]


def test_project_selection_skips_the_index_and_other_projects(ws):
    forge.run(["--project", "sfields,ohttp"])
    assert {rel.split("/")[0] for rel in snapshot(ws)} == {"sfields", "ohttp"}


def test_unknown_project_or_kind_is_refused(ws):
    for argv in (["--project", "nosuch"], ["--only", "everything"]):
        with pytest.raises(SystemExit):
            forge.run(argv)
    assert snapshot(ws) == {}


# ---------------------------------------------------------------- the workspace AGENTS.md


def test_a_full_run_writes_the_index_and_never_the_workspace_agents_md(ws):
    (ws / "AGENTS.md").write_text("hand-maintained workspace rules\n", encoding="utf-8")
    forge.run([])
    assert (ws / "AGENTS.md").read_text(
        encoding="utf-8"
    ) == "hand-maintained workspace rules\n"
    assert (ws / "protocol-sdks.md").is_file()
    assert not hasattr(forge, "AGENTS_WORKSPACE")


def test_forge_root_comes_from_the_environment(tmp_path):
    env = dict(os.environ, FORGE_ROOT=str(tmp_path), PYTHONDONTWRITEBYTECODE="1")
    done = subprocess.run(
        [sys.executable, "-c", "import forge; print(forge.ROOT)"],
        cwd=str(HERE),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert pathlib.Path(done.stdout.strip()) == tmp_path


# ---------------------------------------------------------------- the data move


def test_forge_data_is_data_only():
    """WP12-WP14 edit these files; a function or class in one would be logic hiding in the data."""
    for path in sorted((HERE / "forge_data").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        logic = [
            node
            for node in ast.walk(tree)
            if isinstance(
                node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda
            )
        ]
        assert not logic, path.name


def test_every_project_lives_in_exactly_one_cluster_in_the_recorded_order():
    names = [p["name"] for m in (routing, naming, certificate) for p in m.PROJECTS]
    assert len(names) == len(set(names))
    assert sorted(names) == sorted(forge.PROJECT_ORDER)
    assert [p["name"] for p in forge.ALL_PROJECTS] == list(forge.PROJECT_ORDER)
    assert set(forge.POSITION) == set(names)
    assert forge.POSITION is position.POSITION


def test_the_clusters_hold_what_their_work_packages_edit():
    assert {p["name"] for p in certificate.PROJECTS} >= {
        "revokekit",
        "enrollkit",
        "signeddata",
        "pgpenv",
        "shaken",
        "srtpkit",
    }
    assert {p["name"] for p in routing.PROJECTS} >= {
        "rpkit",
        "asnkit",
        "bgpfeed",
        "routevalid",
        "lgc",
    }
    # miblang joined this cluster on 2026-11-07: network management sits with the operations
    # projects, not with naming or certificates. Count tripwire, so a split of the cluster
    # has to say so here rather than fail as an unexplained diff.
    assert len(routing.PROJECTS) == 10
    assert len(naming.PROJECTS) == 11
    for module in (routing, naming, certificate):
        own = {p["name"] for p in module.PROJECTS}
        assert set(module.OPEN_QUESTIONS) <= own, module.__name__
