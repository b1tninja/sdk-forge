HEADERS = ("Project", "Protocol", "Primary documents", "Nearest live project")


def index_rows(projects):
    rows = []
    for project in projects:
        docs = []
        for spec in project["docs"][:4]:
            docs.append(spec.get("label") or ("RFC " + spec["n"]))
        nearest = project["prior"][0]["name"]
        summary = project["desc"].split(":")[0]
        rows.append((project["name"], summary, ", ".join(docs), nearest))
    return table(HEADERS, rows)


def write_index(projects):
    tpl = TPL_DIR / "index.md.tpl"
    text = tpl.read_text(encoding="utf-8")
    text = text.replace("TABLE", index_rows(projects))
    text = text.replace("SURVEY_DATE", SURVEY_DATE)
    write(ROOT / "protocol-sdks.md", text)


def run():
    written = 0
    notes = []
    for project in ALL_PROJECTS:
        written = written + build(project)
        notes += project.get("polish", [])
        print(project["name"], "ready", len(project["api"]), "obligations")
    write_index(ALL_PROJECTS)
    print("projects", len(ALL_PROJECTS), "files", written)
    for note in notes:
        print("polish:", note)
    if not notes:
        print("polish: every project came out clean")
    return 0
