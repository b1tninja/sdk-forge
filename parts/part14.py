TPL_DIR = HERE / "templates"
DQ = chr(34)
H2 = chr(35) + chr(35) + " "


def deps_note(p):
    if not p.get("deps"):
        return ""
    note = p["deps_note"]
    head = H2 + "Why this project has a runtime dependency"
    tail = (
        "Declared as a floor with no ceiling: the application that installs this "
        "library resolves the final set, and a ceiling inside a library guarantees a "
        "conflict the first time something else needs a newer line."
    )
    return BB + BB + head + BB + BB + note + BB + BB + tail


def readme_mapping(p):
    pairs = [
        ("NAME", p["name"]),
        ("PKG", p["pkg"]),
        ("ORG", ORG),
        ("TITLE", p["title"]),
        ("DESC", p["desc"]),
        ("WHY", p["why"]),
        ("SURVEY_DATE", SURVEY_DATE),
        ("PRIOR", prior_rows(p["prior"])),
        ("GAPS", bullets(p["gaps"])),
        ("DOCS", spine_rows(p["docs"])),
        ("ERRATA", bullets(p["errata"])),
        ("MODULES", modules_table(p)),
        ("NONGOALS", bullets(p["nongoals"])),
        ("DEPSNOTE", deps_note(p)),
    ]
    return dict(pairs)


def render_readme(p):
    return subs(README, readme_mapping(p))


def roadmap_mapping(p):
    fallback = ["none recorded yet"]
    pairs = [
        ("NAME", p["name"]),
        ("ROWS", obligation_rows(p)),
        ("STEPS", steps_block(p)),
        ("ERRATA", bullets(p["errata"])),
        ("NONGOALSROWS", nongoal_rows(p)),
        ("OPEN", bullets(OPEN_QUESTIONS.get(p["name"], fallback))),
    ]
    return dict(pairs)


def render_roadmap(p):
    return subs(ROADMAP, roadmap_mapping(p))


def render_tests(p):
    rows = []
    for entry in p["api"]:
        rows.append(
            "    ("
            + DQ
            + entry[0]
            + DQ
            + ", "
            + DQ
            + entry[2]
            + DQ
            + ", "
            + DQ
            + entry[5]
            + DQ
            + "),"
        )
    surface = "[" + BB + BB.join(rows) + BB + "]"
    files = {}
    for name in ("test_public_api.py", "test_roadmap_rows.py"):
        text = (TPL_DIR / (name + ".tpl")).read_text(encoding="utf-8")
        files["tests/" + name] = subs(text, {"PKG": p["pkg"], "SURFACE": surface})
    return files


def normalize(p):
    for key in ("why", "desc", "title"):
        value = p.get(key)
        if isinstance(value, (list, tuple)):
            p[key] = " ".join(value)
    return p


def polish(root: pathlib.Path) -> list[str]:
    """Normalise a written project in place, tolerating a tool that refuses to cooperate.

    The formatter and the import/name fixes are mechanical, so the generator does not
    reimplement them: it runs the same tools a contributor would. A failure here is
    reported rather than raised, because the verification run is the authority.
    """
    notes = []
    for cmd in (
        ["-m", "ruff", "format", "."],
        ["-m", "ruff", "check", "--fix", "--select", "I001,F401,RUF022", "."],
    ):
        try:
            done = subprocess.run(
                [sys.executable, *cmd],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as error:  # the tool is missing; verification will say so loudly
            notes.append(root.name + ": " + cmd[2] + " could not run: " + str(error))
            continue
        if done.returncode != 0:
            tail = (done.stdout or done.stderr or "").strip().splitlines()[-1:]
            notes.append(
                root.name
                + ": "
                + " ".join(cmd[1:])
                + " exited "
                + str(done.returncode)
                + (" :: " + tail[0] if tail else "")
            )
    return notes


def build(p):
    p = normalize(p)
    root = ROOT / p["name"]
    files = {
        "pyproject.toml": render_pyproject(p),
        "README.md": render_readme(p),
        "ROADMAP.md": render_roadmap(p),
    }
    files.update(render_extras(p))
    files.update(render_package(p))
    files.update(render_tests(p))
    for rel, text in files.items():
        write(root / rel, text)
    shutil.copyfile(LICENSE_SRC, root / "LICENSE")
    p["polish"] = polish(root)
    return len(files)
