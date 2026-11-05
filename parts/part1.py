"""sdk-forge: generate and refresh the RFC-protocol SDK shells under D:/code.

Every managed artefact is produced from the PROJECTS table, so configuration and
prose cannot drift between the eighteen projects. Rerunning rewrites managed
files in place; hand-written module bodies and extra tests are left alone.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import textwrap
from typing import Any

ROOT = pathlib.Path("D:/code")
HERE = pathlib.Path(__file__).resolve().parent
LICENSE_SRC = HERE / "templates" / "LICENSE-2.0.txt"

# PyPI evidence was collected on this date and every README says so: pymasque
# shipped 2026-11-04 and pydhcp 2026-10-21, so the landscape moved twice while
# this survey was being read. An undated "nothing exists" claim rots in a week.
SURVEY_DATE = "2026-11-05"
PYTHON_FLOORS = ("3.12", "3.13", "3.14")
ORG = "b1tninja"


DOC_WIDTH = 96  # generated docstring text is wrapped to this width, quotes included

# Prose is written for a reader and for a linter that flags look-alikes: U+2013 and the
# other dash-like code points become an ASCII hyphen before anything is written.
DASH_LIKE = ("\u2013", "\u2014", "\u2212", "\u2010", "\u2011")


def ascii_prose(text: str) -> str:
    """Replace dash look-alikes with ASCII hyphens so generated prose is plain ASCII."""
    for ch in DASH_LIKE:
        text = text.replace(ch, "-")
    return text.replace("\u00a0", " ")


def collapse(text: str) -> str:
    """Squeeze a prose blob to single-spaced sentences on one line."""
    return " ".join(ascii_prose(str(text)).split())


def first_sentence(text: str) -> tuple[str, str]:
    """Split prose into its leading sentence and the rest of the text.

    A period only ends the summary when an uppercase letter follows it, so 'sec. 14' and
    'e.g. one' inside a summary stay inside the summary.
    """
    body = collapse(text)
    best = -1
    for match in re.finditer(r"[.!?]", body):
        tail = body[match.end() :].lstrip()
        if tail[:1].isupper():
            best = match.end()
            break
    if best < 0:
        return body.rstrip(), ""
    return body[:best].rstrip(), body[best:].strip()


def sentence(summary: str) -> str:
    """Return a single summary sentence, terminated with a period."""
    head = first_sentence(summary)[0]
    return head if head.endswith((".", "!", "?", ":")) else head + "."


def wrap(text: str, width: int, indent: str = "", first: str | None = None) -> list[str]:
    """Wrap prose to width, keeping words whole and returning indented lines.

    `first` lets a caller prefix only the opening line, which is how a docstring puts its
    opening quotes in front of the summary and nowhere else.
    """
    if not text:
        return []
    return textwrap.wrap(
        text,
        width=max(20, width),
        initial_indent=indent if first is None else first,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


def docstring(summary: str, body: str = "", indent: str = "") -> str:
    """Render a docstring: one summary sentence, a blank line, then the wrapped body.

    The renderer, not the caller, owns the layout, so no project ships a docstring whose
    first line runs on into the body or whose lines overflow the wrap width.
    """
    quote = chr(34) * 3
    head = sentence(summary).replace(quote, chr(34))
    blocks = [block for block in (first_sentence(summary)[1], collapse(body)) if block]
    if not blocks:
        one = indent + quote + head + quote
        if len(one) <= DOC_WIDTH and not head.endswith(chr(34)):
            return one
    room = DOC_WIDTH - len(indent) - 3
    lines = wrap(head, room, indent, indent + quote)
    if blocks:
        lines.append("")
        for position, block in enumerate(blocks):
            if position:
                lines.append("")
            lines += wrap(block.replace(quote, chr(34)), room, indent)
    lines.append(indent + quote)
    return "\n".join(lines)


def write(path: pathlib.Path, text: str) -> None:
    """Write managed text as ASCII prose with LF endings and one trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = textwrap.dedent(ascii_prose(text)).strip("\n") + "\n"
    path.write_bytes(body.replace("\r\n", "\n").encode())


def table(header: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    out = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    out += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(out)


def spine_rows(docs: list[dict[str, str]]) -> str:
    return table(
        ("Document", "Status", "Published", "What it gives this project"),
        [
            (d.get("label") or "RFC " + d["n"], d["status"], d["date"], d["why"])
            for d in docs
        ],
    )


def prior_rows(art: list[dict[str, str]]) -> str:
    return table(
        ("Project", "Version", "Last release", "Why it is not this project"),
        [
            (a["name"], a.get("version", "-"), a.get("date", "-"), a["note"])
            for a in art
        ],
    )


def bullets(items: list[str]) -> str:
    return "\n".join("- " + i for i in items)
