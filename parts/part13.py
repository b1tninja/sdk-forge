# ---------------------------------------------------------------------- package rendering

import ast
import re

# The annotation vocabulary a generated module may name, split by where the name comes
# from. Which module owns each alias is ruff's call, not ours: UP035 rejects the typing
# spelling of the ABC aliases, so they are imported from collections.abc.
BUILTIN_NAMES = {
    "bool",
    "bytearray",
    "bytes",
    "complex",
    "dict",
    "float",
    "frozenset",
    "int",
    "list",
    "None",
    "True",
    "False",
    "object",
    "property",
    "set",
    "slice",
    "str",
    "super",
    "tuple",
    "type",
}
ABC_NAMES = {
    "AsyncGenerator",
    "AsyncIterable",
    "AsyncIterator",
    "Awaitable",
    "ByteString",
    "Callable",
    "Coroutine",
    "ItemsView",
    "Iterable",
    "Iterator",
    "KeysView",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Reversible",
    "Sequence",
    "ValuesView",
}
TYPING_NAMES = {"Any", "IO", "Optional", "Union"}
DATETIME_NAMES = {"date", "datetime", "timedelta", "timezone", "tzinfo"}
# A name used as an attribute path (ssl.SSLContext) is a module, so it is imported at
# runtime rather than named inside the TYPE_CHECKING block.
MODULE_NAMES = {
    "base64",
    "datetime",
    "decimal",
    "hashlib",
    "hmac",
    "http",
    "ipaddress",
    "pathlib",
    "secrets",
    "socket",
    "ssl",
    "struct",
    "urllib",
}
PLACEHOLDER = "# placeholder: give it a real type in the milestone that needs it"

DOTTED = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*[A-Za-z_][A-Za-z0-9_]*")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PARENTHETICAL = re.compile(r"\s*\([^()]*\)")
BARE_DATETIME = re.compile(r"(?<![\w.])datetime(?!\s*\.)")
VALUE = r"[A-Za-z_][A-Za-z0-9_.]*(?:\[[^][]*\])?"
GENERIC_RULES = (
    (re.compile(r"\bdict of (" + VALUE + r") to (" + VALUE + r")"), r"dict[\1, \2]"),
    (re.compile(r"\btuple of (" + VALUE + r") and (" + VALUE + r")"), r"tuple[\1, \2]"),
    (re.compile(r"\bset of (" + VALUE + r")"), r"set[\1]"),
    (re.compile(r"\blist of (" + VALUE + r")"), r"list[\1]"),
)
# A context hint is written by a person, so it may be prose, and prose never survives
# sanitising: a parenthetical tail is dropped, the first ';' or '.' or dash ends it, and
# anything that still does not parse becomes Any.
PROSE_CUTS = (";", " - ", ". ")

MODULE_BODY = (
    "Every object in this module is a placeholder until the milestone named in ROADMAP.md "
    "lands. A stub raises instead of returning a plausible empty value: a protocol library "
    "that silently answers nothing is worse than one that refuses to answer."
)
FUNC_TAIL = (
    "Not implemented yet. See the ``{pair}()`` row in ROADMAP.md; this stub raises on "
    "purpose so nothing downstream mistakes it for working code."
)

APPS_DOC = (
    "Composition that assembles core pieces and adds no protocol behaviour.",
    'Importing from here says "I am assembling", which is the distinction the project '
    "cares about. Nothing in this package may know how the wire format works: if it does, "
    "it belongs one level up, cited against a document.",
)
CLI_DOC = (
    "Command line entry point for {name}.",
    "The CLI is how most people meet a protocol library, so it is part of the public "
    "surface and gets the same typing and testing discipline as the rest of the package.",
)
MAIN_DOC = "Allow python -m {name} without installing the console script."
CONFTEST_DOC = (
    "Make the project root importable when pytest is run from anywhere.",
    "The package lives at the repository root, so with this file present pytest inserts "
    "that root on sys.path and importing the package works however the test command was "
    "invoked.",
)
STUB_MAIN = """def main(argv=None):
{DOC}
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_usage(sys.stderr)
    print("{name}: no protocol behaviour is implemented yet; see ROADMAP.md", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())"""


def _member_key(name: str) -> tuple[int, str]:
    """Order imported members the way isort does: constants, classes, then lowercase."""
    if name.isupper():
        return (0, name)
    if name[:1].isupper():
        return (1, name)
    return (2, name)


def import_block(module: str, members: set[str], indent: str, width: int) -> list[str]:
    """Render one from-import, exploded only when the single line would overflow."""
    names = sorted(members, key=_member_key)
    one = indent + "from " + module + " import " + ", ".join(names)
    if len(one) <= width:
        return [one]
    lines = [indent + "from " + module + " import ("]
    lines += [indent + "    " + name + "," for name in names]
    lines.append(indent + ")")
    return lines


def _wellformed(annotation: str) -> bool:
    """True when the annotation parses and every name in it can be resolved or aliased."""
    try:
        tree = ast.parse(annotation, mode="eval")
    except SyntaxError:
        return False
    known = BUILTIN_NAMES | ABC_NAMES | TYPING_NAMES | DATETIME_NAMES | MODULE_NAMES
    for node in ast.walk(tree):
        if not isinstance(node, ast.Name):
            continue
        if node.id in known or re.fullmatch(r"[A-Z][A-Za-z0-9]*", node.id):
            continue
        return False
    return True


def _optional(annotation: str) -> str:
    """Rewrite Optional[X] as X | None, the only spelling the lint set accepts."""
    marker = "Optional["
    while marker in annotation:
        start = annotation.find(marker)
        depth = 0
        index = start + len(marker) - 1
        while index < len(annotation):
            if annotation[index] == "[":
                depth += 1
            elif annotation[index] == "]":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        if index >= len(annotation):
            return ""
        inner = annotation[start + len(marker) : index]
        inner = _optional(inner)
        if "," in inner:
            inner = "(" + inner + ") | None"
        else:
            inner = inner + " | None"
        annotation = annotation[:start] + inner + annotation[index + 1 :]
    return annotation


def sanitize_annotation(text: str) -> str:
    """Return a context hint as a usable annotation, or Any when it never was one."""
    body = PARENTHETICAL.sub(" ", collapse(text))
    cut = len(body)
    for separator in PROSE_CUTS:
        found = body.find(separator)
        if found >= 0:
            cut = min(cut, found)
    body = body[:cut].strip()
    for pattern, replacement in GENERIC_RULES:
        body = pattern.sub(replacement, body)
    body = " ".join(_optional(body).split()).strip(",;")
    if not body:
        return "Any"
    if re.search(r"\b(or|and|is|not|in|for)\b", body):
        return "Any"  # a hint written as an English clause, not as a type expression
    return body if _wellformed(body) else "Any"


def split_params(params: str) -> list[str]:
    """Split a parameter list on top-level commas so subscripts stay whole."""
    parts, depth, current = [], 0, ""
    for char in params:
        if char in "[(":
            depth += 1
        elif char in "])":
            depth -= 1
        if char == "," and depth <= 0:
            parts.append(current.strip())
            current = ""
            continue
        current += char
    if current.strip():
        parts.append(current.strip())
    return parts


def sanitize_params(params: str) -> tuple[str, list[str]]:
    """Sanitise a parameter list and return it beside the hints it now carries.

    Parameter names are deliberately not returned as hints: only the annotation after each
    colon is a type, and treating a name as a type is how a placeholder alias for 'files'
    would get invented.
    """
    parts, hints = [], []
    for chunk in split_params(params):
        if ":" in chunk:
            name, _, hint = chunk.partition(":")
            hint = sanitize_annotation(hint)
            hints.append(hint)
            chunk = name.strip() + ": " + hint
        parts.append(chunk)
    return ", ".join(parts), hints


def plan_imports(types: list[str]) -> tuple[list[str], list, list, bool]:
    """Resolve every name the module's final annotations use.

    Word boundaries, not bracket substrings, decide what counts as a name, so a type used
    inside ``list[X]`` is found and a word scraped out of prose is never invented into an
    alias. Names that come from typing, collections.abc or datetime are imported inside the
    TYPE_CHECKING block; a name that is really a module is imported at runtime.
    """
    roots: set[str] = set()
    bare: set[str] = set()
    for text in types:
        roots.update(match.group(1) for match in DOTTED.finditer(text))
        bare.update(WORD.findall(DOTTED.sub("\u0000", text)))
    runtime = {root for root in roots if root in MODULE_NAMES}
    module_datetime = "datetime" in roots and "datetime" in bare
    if module_datetime:
        bare.discard(
            "datetime"
        )  # the module form wins, so the class is qualified below
    checking: dict[str, set[str]] = {}
    aliases: set[str] = set()
    for name in bare - roots - BUILTIN_NAMES:
        if name in MODULE_NAMES and (name != "datetime" or module_datetime):
            runtime.add(name)  # a module named bare in an annotation is imported anyway
        elif name in DATETIME_NAMES:
            checking.setdefault("datetime", set()).add(name)
        elif name in ABC_NAMES:
            checking.setdefault("collections.abc", set()).add(name)
        elif name in TYPING_NAMES:
            checking.setdefault("typing", set()).add(name)
        else:
            aliases.add(name)
    if aliases:
        checking.setdefault("typing", set()).add("Any")
    ordered = [(module, checking[module]) for module in sorted(checking)]
    return sorted(runtime), ordered, sorted(aliases), module_datetime


def module_source(p: dict[str, Any], mod: str, doc: str) -> str:
    """Render one obligation module: stubs, their annotations and the imports they need."""
    entries = [e for e in p["api"] if e[0] == mod]
    names = sorted({e[2] for e in entries})
    bodies, types = [], []
    for _mod, kind, fn, params, ret, cite in entries:
        clean_params, param_types = sanitize_params(params)
        clean_ret = sanitize_annotation(ret)
        types += param_types + [clean_ret]
        bodies.append((kind, fn, clean_params, clean_ret, cite))
    runtime, checking, aliases, module_datetime = plan_imports(types)

    def final(text: str) -> str:
        if not text or not module_datetime:
            return text
        return BARE_DATETIME.sub("datetime.datetime", text)

    lines = [docstring(doc, MODULE_BODY), "", "from __future__ import annotations"]
    if runtime:
        lines += [""] + ["import " + name for name in runtime]
    if checking:
        lines += ["", "from typing import TYPE_CHECKING", "", "if TYPE_CHECKING:"]
        for module, members in checking:
            lines += import_block(module, members, "    ", 96)
        if aliases:
            lines.append("")
            lines += ["    " + alias + " = Any  " + PLACEHOLDER for alias in aliases]
    lines.append("")
    if names:
        lines.append("__all__ = [")
        lines += ['    "' + name + '",' for name in names]
        lines.append("]")
    else:
        lines.append("__all__: list[str] = []")
    for kind, fn, params, ret, cite in bodies:
        lines += [
            "",
            "",
            kind
            + " "
            + fn
            + "("
            + final(params)
            + ") "
            + ARROW
            + " "
            + final(ret)
            + ":",
        ]
        lines.append(
            docstring(
                "Pending behaviour defined by " + cite + ".",
                FUNC_TAIL.replace("{pair}", mod + "." + fn),
                "    ",
            )
        )
        lines.append(
            '    raise NotImplementedError("'
            + fn
            + "() is not implemented: "
            + cite
            + '")'
        )
    return "\n".join(lines) + "\n"


def init_source(p: dict[str, Any]) -> str:
    """Render the package __init__: sorted module list, sorted surface, sorted __all__."""
    mods = sorted({m for m, _d in p["mods"]})
    submodules = sorted(set(["apps"] + mods + (["cli"] if p.get("cli") else [])))
    lines = [
        docstring(p["title"], first_sentence(p["why"])[0]),
        "",
        "from __future__ import annotations",
        "",
        "from . import " + ", ".join(submodules),
    ]
    exposed: list[str] = []
    for mod in mods:
        surface = sorted(
            {e[2] for e in p["api"] if e[0] == mod and e[2] not in submodules}
        )
        surface = [name for name in surface if name not in exposed]
        if not surface:
            continue
        exposed += surface
        lines += import_block("." + mod, set(surface), "", 100)
    lines += ["", '__version__ = "0.1.0"', "", "__all__ = ["]
    for name in sorted(set(submodules + exposed) | {"__version__"}):
        lines.append('    "' + name + '",')
    lines.append("]")
    return "\n".join(lines) + "\n"


def cli_source(p: dict[str, Any]) -> str:
    """Render the CLI.

    The version is never imported at module scope: the package __init__ assigns it after
    it has imported this module, so a top-level import of it deadlocks the package import.
    """
    summary, body = CLI_DOC[0].replace("{name}", p["name"]), CLI_DOC[1]
    return (
        "\n".join(
            [
                docstring(summary, body),
                "",
                "from __future__ import annotations",
                "",
                "import argparse",
                "import sys",
                "",
                'USAGE = """\\',
                "Examples:",
                "  " + p["cli"] + '"""',
                "",
                "",
                "def build_parser():",
                "    return argparse.ArgumentParser(",
                '        prog="' + p["name"] + '",',
                '        description="' + collapse(p["desc"]) + '",',
                "        epilog=USAGE,",
                "        formatter_class=argparse.RawDescriptionHelpFormatter,",
                "    )",
                "",
                "",
                STUB_MAIN.replace("{DOC}", _main_doc()).replace("{name}", p["name"]),
            ]
        )
        + "\n"
    )


def _main_doc() -> str:
    """The CLI main() docstring: why a shell exits non-zero."""
    return docstring(
        "Parse arguments, then refuse to pretend the protocol works.",
        "Exiting non-zero is the correct behaviour for a shell. A CLI that printed a "
        "friendly banner and exited 0 would be indistinguishable from one that actually "
        "did something.",
        "    ",
    )


def render_module(p: dict[str, Any], mod: str, doc: str) -> str:
    """Keep the old call signature; the renderer is now module_source."""
    return module_source(p, mod, doc)


def render_init(p: dict[str, Any]) -> str:
    """Keep the old call signature; the renderer is now init_source."""
    return init_source(p)


def render_cli(p: dict[str, Any]) -> str:
    """Keep the old call signature; the renderer is now cli_source."""
    return cli_source(p)


def render_package(p: dict[str, Any]) -> dict[str, str]:
    """Render every managed Python file of one project."""
    pkg = p["pkg"]
    files = {}
    for mod, doc in p["mods"]:
        files[pkg + "/" + mod + ".py"] = module_source(p, mod, doc)
    files[pkg + "/__init__.py"] = init_source(p)
    files[pkg + "/apps/__init__.py"] = docstring(APPS_DOC[0], APPS_DOC[1]) + "\n"
    files[pkg + "/py.typed"] = ""
    if p.get("cli"):
        files[pkg + "/cli.py"] = cli_source(p)
        files[pkg + "/__main__.py"] = (
            docstring(MAIN_DOC.replace("{name}", p["name"])) + "\n"
        )
    files["conftest.py"] = docstring(CONFTEST_DOC[0], CONFTEST_DOC[1]) + "\n"
    return files
