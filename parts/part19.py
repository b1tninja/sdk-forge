# ---------------------------------------------------------------------------
# Part 19: agent instruction files (AGENTS.md + .clinerules + a Cline workflow)
#
# Design notes, grounded in the specs rather than in habit:
#
#   * AGENTS.md (agents.md, now stewarded by the Agentic AI Foundation under the
#     Linux Foundation) is plain Markdown with no required fields. Nested files
#     are resolved by nearest-file precedence, and an explicit prompt in chat
#     overrides all of it. That makes a workspace-level file plus one per project
#     the right shape for a directory of sibling repositories.
#   * Cline reads AGENTS.md, ~/.agents/AGENTS.md, .clinerules/ and .cline/rules/,
#     combining the files found in a rules directory. Conditional rules take a
#     `paths:` glob in YAML front matter and activate when a matching file is in
#     context, so the rfclib procedure can load exactly when protocol code is
#     being edited rather than permanently occupying the context window.
#   * Both agent-guidance sources say the same thing about length: an
#     instruction file should hold only what the agent cannot infer from the
#     repository, and it should give the agent a check it can run. Everything
#     below is therefore commands, invariants and errata pointers; module lists,
#     dependencies and design prose stay in README.md and docs/.
# ---------------------------------------------------------------------------


AGENTS_WORKSPACE = r'''# Instructions for coding agents

`D:\code` is a workspace of sibling projects, not a repository. Each subdirectory
is its own git repository, and the workspace root has no git history.

## Rules that apply everywhere

- Never run a formatter, linter or cache cleaner from this directory. A recursive
  `ruff format .` started here rewrites every unrelated project in the workspace.
  Change into the project directory first, and pass paths relative to it.
- If a test result or a type-check error contradicts the file you just read, clear
  `__pycache__` and re-run before believing it. Bytecode is validated by
  second-resolution mtime plus size, so a regenerated file of identical length can
  look unchanged to the interpreter.
- For any protocol question, use the `rfclib` MCP tools. Never state an RFC number,
  section number or normative wording from memory: the spine is recorded in each
  project's `docs/rfc-map.md`, and `rfclib.info` confirms status and successor.
- Python is 3.12 or newer. `from __future__ import annotations` at the top, ABCs
  from `collections.abc`, `X | None` rather than `Optional[X]`, and
  `datetime.UTC` rather than `datetime.timezone.utc`.
- Let `ruff format` decide line breaks. Do not wrap comments by hand.
- Commit messages take no `Co-Authored-By` trailer or any other AI attribution,
  even though older commits in some of these repositories have one.

## Inside a project

Each project directory has its own `AGENTS.md` with the commands and the invariants that
apply there. That file takes precedence over this one for work in that project, so read it
before editing.

## Plan directories are not projects

`asn1core/`, `certledger/` and `keyproof/` hold plans, trust models and
conformance-corpus specifications. They have no package, no `pyproject.toml` and no test
suite, so **there is no command in them that will run**. If a task asks for work there, the
deliverable is a document or a decision, not scaffolding: creating a `pyproject.toml` in a
plan directory ahead of its wave turns a plan into a shell nobody maintains, which is the
failure mode `PORTFOLIO.md` section 7 exists to prevent.

`PORTFOLIO.md` at this root is the authority on sequencing - which projects are worked on, in
what order, and what is deliberately not built. Each generated project also carries
`docs/plan.md` recording its tier, its wave and the dependencies that block it. When a plan
says a dependency "does not exist yet", that means blocked, and work on the dependent project
should not start.

'''


AGENTS_PROJECT = '''# Instructions for coding agents

<<SUMMARY>>

Primary documents are listed in `docs/rfc-map.md` with statuses and known errata.
The obligation table in `ROADMAP.md` is the work queue, and `README.md` explains
what the library is for. Read those three before changing anything.

## Commands

    python -m pip install -e ".[dev]"
    python -m pytest -q
    python -m pytest -q tests/test_roadmap_rows.py
    python -m pytest -q tests/test_public_api.py::test_stubs_are_loud
    python -m ruff check .
    python -m ruff format --check .
    python -m mypy <<PKG>>

The first line installs the dev extras. The six commands after it are the gates,
and all six must pass before a change is finished. CI runs the same set on Linux
and Windows, plus the suite under `python -O`.

## Invariants

These are the points where a plausible-looking change makes the project wrong
rather than merely incomplete.

1. **Roadmap honesty.** Never change a `ROADMAP.md` row from `[ ]` to `[x]` unless
   the test named in its `Evidence` cell exists and passes. `tests/test_roadmap_rows.py`
   fails on any row that claims done without a named test, and that check is the
   reason the roadmap can be trusted. Do not weaken it, skip it, or delete it to
   get a green run.
2. **No silent stubs.** Code that is not implemented raises `NotImplementedError`.
   Never return an empty value, an empty collection, or a result object that reports
   success. A protocol library that answers nothing is worse than one that refuses
   to answer, and `tests/test_public_api.py` enforces that every stub is loud.
3. **Normative text is never paraphrased from memory.** Fetch it with `rfclib` and
   cite the section. If the text you fetch does not say what the obligation claims,
   the obligation is wrong: fix the roadmap row and say so in the commit.
4. **Dependencies.** `pyproject.toml` here declares <<DEPS>>. Adding a runtime
   dependency needs a paragraph of justification in `docs/strategy.md` explaining
   why the standard library is not enough.
5. **Scope.** What is deliberately absent is listed under Non-goals in `README.md`.
   An agent that "helpfully" implements a non-goal has expanded the API surface that
   has to be supported forever.

## Read before implementing

<<ERRATA>>

## Protocol work

`.clinerules/10-rfclib.md` describes the `rfclib` calls to make for each obligation
and lists the section refs for this project. If you are not running in Cline, the
same procedure applies: confirm the document, read its errata, pull the normative
statements, then write code.
'''


CLINERULE = '''---
description: Fetch the specification text before changing protocol code
paths:
  - "<<PKG>>/**"
  - "tests/**"
---

# Working from the RFC with rfclib

The `rfclib` MCP server is the authority for what a specification says. Model
knowledge of RFC numbers and wording is not reliable here, and this portfolio has
already had to correct numbers that looked right (DHCPv6 is RFC 9915, not 8415;
RRDP is RFC 8182, not 9183).

<<SPINENOTE>>

Work through the obligations in `ROADMAP.md` one row at a time. For each row:

1. **Confirm the document.** `rfclib.info("<<REF>>")` returns status,
   publication date, the updates/obsoletes graph and an errata summary. If the
   document is obsolete or has a successor, stop and flag the roadmap row before
   writing any code.
2. **Read the errata.** `rfclib.errata("<<REF>>")` gives the verified
   corrections with their replacement text. A verified erratum is the
   specification: an implementation that follows the original text is wrong.
   RFC 4795 carries six, RFC 9162 one, RFC 6960 one.
3. **Pull only the normative statements.** `rfclib.read("<<REF>><<SEC0>>",
   view="normative")` returns the MUST, SHOULD and MAY sentences in that scope.
   Read them before choosing a data structure, not after.
4. **Find the specific rule instead of guessing its name.**
   `rfclib.grep("<<REF>>", pattern="<<FIELD>>")` searches one document for a
   field name, ABNF rule or error code, which is cheaper than reading a section.
5. **Cite rather than paraphrase.** `rfclib.cite("<<REF>><<SEC0>>",
   style="verbose")` yields label, title, date, status, anchor URL and errata
   status. Put that in the docstring or the commit message. Never restate normative
   prose in your own words.

Refs accept a bare document (`RFC9162`), a section (append the section symbol and
number), a paragraph within a section, a line range like `RFC9162:120-140`, and a
table like `RFC9162#table-2`. Reads end with `next: <ref>` when the scope exceeds the
budget, so page through rather than guessing. Paragraph markers are printed on each
paragraph so a single one can be quoted exactly.

To decide *which* document applies, `rfclib.search("...", scope="documents")`
matches titles and abstracts while `scope="sections"` says which passage answers the
question. `rfclib.outline("<<REF>>", contains="security")` lists sections
with their line ranges.

## Section refs for this project

<<DOCS>>

## Traps that have already bitten this portfolio

- A status of `INFORMATIONAL` means the document contains no protocol requirements,
  however normative its prose reads. Check before quoting a MUST.
- Numbers move: 6486 became 9286, 8941 became 9651, 4210 became 9810, 7752 became
  9552. Re-read `docs/rfc-map.md` rather than trusting an older note.
- An empty response is a protocol outcome, not a success value. Distinguish "the
  server said no" from "nothing arrived", or you reproduce the RFC 9849 compression
  failure, where a silent empty value made an optional extension load-bearing.
'''


WORKFLOW = '''---
description: Implement one ROADMAP.md obligation, correctly and verifiably
---

Implement the next unchecked row of `ROADMAP.md` in this project, working from
`docs/rfc-map.md` for the document and section.

1. Read the row and quote its spec anchor and evidence cells back. Confirm the
   document with `rfclib.info` and `rfclib.errata` before writing code, and stop if
   it turns out to be obsolete or superseded.
2. Fetch the normative text with `rfclib.read(..., view="normative")`. If what you
   fetch does not state what the row claims, say so and fix the row rather than
   coding to a wrong requirement.
3. Write the test first, using recorded fixtures rather than a live endpoint. Run it
   and watch it fail.
4. Implement the minimum that makes it pass. Anything left unimplemented keeps
   raising `NotImplementedError`.
5. Flip the row to done and name the test in its evidence cell. Do not flip the row
   if the test does not exist and pass.
6. Run every gate listed in `AGENTS.md` and fix what fails.
7. Commit with the citation from `rfclib.cite` in the message body. No
   `Co-Authored-By` trailer.
'''


WORKSPACE_WRITTEN = []


def sub(text, mapping):
    for key, value in mapping.items():
        text = text.replace("<<" + key + ">>", str(value))
    return text


def doc_line(entry):
    number = entry.get("n") or entry.get("rfc") or "?"
    label = entry.get("label") or ("RFC " + str(number))
    bits = [label]
    status = entry.get("status") or ""
    published = entry.get("date") or entry.get("published") or ""
    paren = ", ".join(part for part in (status, published) if part)
    if paren:
        bits.append("(" + paren + ")")
    role = entry.get("role") or ""
    if role:
        bits.append(role)
    return "- " + " ".join(bits)


def docs_block(p):
    lines = []
    for entry in p.get("docs", []):
        number = str(entry.get("n") or entry.get("rfc") or "?")
        lines.append(doc_line(entry))
        quote = chr(34)
        sect = chr(167)
        for section in (entry.get("sections") or [])[:2]:
            lines.append(
                "  - `rfclib.read(" + quote + "RFC" + number + sect + str(section)
                + quote + ", view=" + quote + "normative" + quote + ")`"
            )
        if entry.get("errata"):
            lines.append("  - `rfclib.errata(" + quote + "RFC" + number + quote + ")` first")
    return chr(10).join(lines) if lines else "- see docs/rfc-map.md"


def api_hint(item):
    """Identifier text of one api row, whichever way the row is spelled.

    Rows in the PROJECTS table are tuples of
    (module, kind, name, params, returns, refs); the name and params cells are
    the ones that hold protocol field names. A dict row carries the same text
    under "hint".
    """
    if isinstance(item, dict):
        return str(item.get("hint") or "")
    if isinstance(item, (tuple, list)):
        return " ".join(str(cell) for cell in item[2:4])
    return str(item)


def dep_label(dep):
    """Render one deps entry, which the PROJECTS table spells as (name, version)."""
    if isinstance(dep, (tuple, list)):
        return " ".join(str(part) for part in dep if part)
    return str(dep)


def doc_number(entry):
    """RFC number of one docs entry, or "" when the entry is a non-IETF document.

    Non-RFC entries in the PROJECTS table carry a "label" ("TR-069 (CWMP)",
    "LGC and LGS protocol") and no number, which is how the spine of a
    deliberately non-IETF project is recorded.
    """
    return str(entry.get("n") or entry.get("rfc") or "")


def spine_facts(p):
    docs = p.get("docs", [])
    first = docs[0] if docs else {}
    # The ref used inside the rfclib call examples has to be one rfclib can
    # resolve, so it is the first numbered entry of the map rather than the first
    # entry: on a non-IETF project the primary document is a Broadband Forum,
    # UPnP or ATIS specification, and rfclib has no such document.
    spine = next((entry for entry in docs if doc_number(entry)), None)
    spinenote = ""
    if spine is None:
        # Nothing in the map is an RFC. Fall back to the note below and keep the
        # label as the ref; never invent a number for a document that has none.
        ref = str(first.get("label") or "docs/rfc-map.md")
        section = ""
    else:
        ref = "RFC" + doc_number(spine)
        sections = spine.get("sections") or []
        section = chr(167) + str(sections[0]) if sections else ""
    if not doc_number(first):
        spinenote = (
            "The primary document of this project is "
            + str(first.get("label") or "docs/rfc-map.md")
            + ", which is not an RFC, so the `rfclib` calls below resolve only the RFC\n"
            "refs listed under \"Section refs for this project\"; read the non-RFC\n"
            "specification from its own publisher."
        )
    field = "extensions"
    for item in p.get("api", []):
        for token in re.split(r"[^A-Za-z]+", api_hint(item).replace("()", " ")):
            if token.isalpha() and token.islower() and len(token) > 4:
                field = token
                break
        else:
            continue
        break
    return {"REF": ref, "SEC0": section, "FIELD": field, "SPINENOTE": spinenote}


def errata_block(p):
    notes = [n for n in p.get("errata", []) if n]
    if not notes:
        notes = [
            "Run `rfclib.errata` on every document listed in `docs/rfc-map.md` "
            "before implementing its rows."
        ]
    return chr(10).join("- " + n for n in notes)


def agents_files(p):
    pkg = p["pkg"]
    desc = p.get("desc") or p.get("title") or p["name"]
    deps = p.get("deps") or []
    if deps:
        deps_text = "these runtime dependencies: " + ", ".join(dep_label(d) for d in deps)
    else:
        deps_text = "no runtime dependencies"
    project = sub(
        AGENTS_PROJECT,
        {
            "SUMMARY": desc.strip().rstrip(".") + ".",
            "PKG": pkg,
            "DEPS": deps_text,
            "ERRATA": errata_block(p),
        },
    )
    rule = sub(CLINERULE, spine_facts(p))
    rule = sub(rule, {"PKG": pkg, "DOCS": docs_block(p)})
    rule = re.sub(r"\n{3,}", chr(10) + chr(10), rule)
    return {
        "AGENTS.md": project,
        ".clinerules/10-rfclib.md": rule,
        ".cline/workflows/implement-obligation.md": WORKFLOW,
    }


def write_agent_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = textwrap.dedent(text).strip() + chr(10)
    path.write_text(body, encoding="utf-8", newline="")


_ORIG_BUILD = build


def build(p):
    count = _ORIG_BUILD(p)
    if not WORKSPACE_WRITTEN:
        write_agent_text(ROOT / "AGENTS.md", AGENTS_WORKSPACE)
        WORKSPACE_WRITTEN.append(True)
    root = ROOT / p["name"]
    for relative, text in agents_files(p).items():
        write_agent_text(root / relative, text)
        count += 1
    return count


# No __main__ guard here. The guard belongs to the last part in parts/, because a
# guard placed here would call run() before the wrappers that follow this file have
# reassigned build, and every artefact those parts own would silently stop being
# written. Assembled files are concatenated in numeric order, so the last part wins.

