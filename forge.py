"""sdk-forge: generate and refresh the RFC-protocol SDK shells under D:/code.

Every managed artefact is produced from the PROJECTS table, so configuration and
prose cannot drift between the eighteen projects. Rerunning rewrites managed
files in place; hand-written module bodies and extra tests are left alone.
"""

from __future__ import annotations

import ast
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
# ---------------------------------------------------------------- clusters: RPKI and BGP

PROJECTS_A: list[dict[str, Any]] = [
    {
        "name": "rpkit",
        "pkg": "rpkit",
        "title": "rpkit -- an RPKI relying party you can import",
        "desc": "RPKI relying party: RRDP and repository fetch, CMS signed objects, manifests, "
        "validation paths, ROA extraction and SLURM filtering",
        "kw": [
            "rpki",
            "rrdp",
            "signed-objects",
            "manifests",
            "rov",
            "bgp",
            "rfc9286",
            "rfc9981",
        ],
        "why": (
            "Python has no RPKI relying-party implementation at all. Validation, RRDP and "
            "repository handling live in Rust (Routinator, rcynic) and C (rpki-client), so any "
            "Python tool that wants origin validation today shells out to a daemon and parses "
            "its output. The specification is also moving: RFC 9981 (2026-05) and RFC 9829 "
            "(2025-07) both landed inside the last year and neither has a Python consumer. "
            "rpkit is the importable relying party: fetch, verify, validate, with the "
            "provenance of every assertion attached to the answer instead of assumed by the "
            "caller."
        ),
        "docs": [
            {
                "n": "6480",
                "status": "Informational",
                "date": "2012-02",
                "why": "the architecture: repositories, RAs, ROAs and relying-party duties",
            },
            {
                "n": "8182",
                "status": "Proposed Standard",
                "date": "2017-07",
                "why": "RRDP: notification, snapshot and delta files over HTTPS",
            },
            {
                "n": "9697",
                "status": "Proposed Standard",
                "date": "2024-12",
                "why": "detecting RRDP session desynchronisation",
            },
            {
                "n": "6488",
                "status": "Proposed Standard",
                "date": "2012-02",
                "why": "the SignedObject CMS wrapper every RPKI file wears",
            },
            {
                "n": "9286",
                "status": "Proposed Standard",
                "date": "2022-06",
                "why": "manifests: the anti-replay view of a publication point",
            },
            {
                "n": "9981",
                "status": "Proposed Standard",
                "date": "2026-05",
                "why": "manifest number behaviour at the 2**32 minus 1 boundary",
            },
            {
                "n": "6487",
                "status": "Proposed Standard",
                "date": "2012-02",
                "why": "resource certificate and CRL profile, relying-party path validation",
            },
            {
                "n": "7935",
                "status": "Proposed Standard",
                "date": "2016-08",
                "why": "the algorithms and key sizes a relying party must speak",
            },
            {
                "n": "9691",
                "status": "Proposed Standard",
                "date": "2024-12",
                "why": "trust anchor key (TAK) profile",
            },
            {
                "n": "8416",
                "status": "Proposed Standard",
                "date": "2018-08",
                "why": "SLURM: local filtering of validated assertions",
            },
        ],
        "errata": [
            "RFC 8182 carries 1 verified erratum and is updated by RFC 9674 and RFC 9697. Read all three before writing the RRDP client.",
            "RFC 6487 carries 4 verified errata (algorithm and CRL number details; see also RFC 9829, 2025-07).",
            "RFC 9286 carries 1 verified erratum. RFC 6486 is OBSOLETE and must never be cited as the manifest specification.",
        ],
        "prior": [
            {
                "name": "rov",
                "version": "0.6.0",
                "date": "2025-07-09",
                "note": "offline batch ROV over IRR and dump files; no validator library, no RRDP, no RTR",
            },
            {
                "name": "rpki",
                "version": "-",
                "date": "-",
                "note": "name does not exist on PyPI (checked 2026-11-05)",
            },
            {
                "name": "routinator, rpki-client, rcynic",
                "version": "-",
                "date": "-",
                "note": "Rust and C daemons; no embeddable Python API",
            },
        ],
        "gaps": [
            "RRDP client with notification, snapshot and delta files, and RFC 9697 desync recovery",
            "CMS signed-object decode and verification using the RFC 7935 algorithm profile",
            "manifest enforcement including the RFC 9981 number boundary nobody implements yet",
            "validation path walk with per-assertion reason codes: stale, revoked, suspended, filtered",
            "SLURM filtering as a first-class testable step rather than a daemon option",
        ],
        "nongoals": [
            "issuing certificates: this is a relying party, not a CA",
            "talking to routers over RTR, which is rtrkit",
            "IRR database parsing",
            "being the fastest validator; correctness and provenance are the product",
        ],
        "mods": [
            (
                "anchors",
                "trust anchors and TAKs: load, pin, expire (RFC 9691, RFC 6480)",
            ),
            (
                "repository",
                "publication point model, cache layout, rsync and RRDP selection (RFC 6480)",
            ),
            (
                "rrdp",
                "notification, snapshot and delta fetch plus desync recovery (RFC 8182, RFC 9697)",
            ),
            (
                "signedobject",
                "CMS SignedObject envelope decode and verification (RFC 6488)",
            ),
            (
                "manifest",
                "manifest objects, file hashes and number handling (RFC 9286, RFC 9981)",
            ),
            ("roa", "route origin authorisation objects: prefix, ASN, max length"),
            ("validation", "certificate path and resource extension checks (RFC 6487)"),
            ("slurm", "local exception filtering (RFC 8416)"),
        ],
        "api": [
            (
                "anchors",
                "def",
                "load_trust_anchor",
                "path: pathlib.Path",
                "TrustAnchor",
                "RFC 9691",
            ),
            (
                "repository",
                "def",
                "open_cache",
                "root: pathlib.Path",
                "Repository",
                "RFC 6480",
            ),
            (
                "rrdp",
                "def",
                "fetch_notification",
                "uri: str",
                "Notification",
                "RFC 8182",
            ),
            (
                "rrdp",
                "def",
                "apply_delta",
                "state: SessionState, delta: DeltaFile",
                "Repository",
                "RFC 8182, RFC 9697",
            ),
            (
                "signedobject",
                "def",
                "decode_signed_object",
                "blob: bytes",
                "SignedObject",
                "RFC 6488",
            ),
            (
                "manifest",
                "def",
                "check_manifest",
                "manifest: SignedObject, files: dict",
                "list of str",
                "RFC 9286",
            ),
            (
                "manifest",
                "def",
                "next_manifest_number",
                "current: int",
                "int",
                "RFC 9981",
            ),
            (
                "validation",
                "def",
                "validate_roa",
                "roa: SignedObject, store: Repository",
                "ValidationResult",
                "RFC 6487",
            ),
            (
                "validation",
                "def",
                "validate_origin",
                "prefix: str, asn: int, roas: Iterable",
                "RovState",
                "RFC 6480",
            ),
            (
                "slurm",
                "def",
                "apply_slurm",
                "roas: Iterable, config: Slurm",
                "Iterable",
                "RFC 8416",
            ),
        ],
        "steps": [
            "M1 signed objects: RFC 6488 envelope plus RFC 7935 signature verification against live RIR data",
            "M2 repository: RRDP notification, snapshot and delta, with RFC 9697 desync recovery",
            "M3 manifests: hash verification, stale detection, RFC 9981 number boundary",
            "M4 validation: path walk, resource extensions, ROA extraction, ROV result with reason codes",
            "M5 SLURM filtering and the assertion stream rtrkit consumes",
            "M6 publication: 0.1.0 on PyPI with a reproducible repository fixture in the sdist",
        ],
        "extras": {"xml": [("defusedxml", "0.7")]},
        "cli": "rpkit validate 1.2.3.0/24 64512 -- state and every reason behind it",
    },
    {
        "name": "rtrkit",
        "pkg": "rtrkit",
        "title": "rtrkit -- RPKI-to-Router protocol, both ends",
        "desc": "RPKI-to-Router (RTR) version 0 and 1: cache server and router client, IPv4 and "
        "IPv6 prefix and router-key records, serial notify and reset query",
        "kw": [
            "rpki",
            "rtr",
            "rov",
            "bgp",
            "rfc8210",
            "rfc6810",
            "router-key",
            "cache-server",
        ],
        "why": (
            "RTR is the only protocol between an RPKI cache and a router, and Python cannot "
            "speak it. On PyPI there is nothing at all: rtr, rtrkit, rpki-rtr and rtr-client "
            "were all absent when checked on 2026-11-05. rtrkit is deliberately the small half "
            "of the problem. It validates nothing; it moves already validated assertions over a "
            "socket with the right serial discipline, which is exactly what makes it testable "
            "against a real router without needing a repository, and what lets rpkit stay a "
            "validator instead of growing a server."
        ),
        "docs": [
            {
                "n": "8210",
                "status": "Proposed Standard",
                "date": "2017-09",
                "why": "RTR version 1: PDU set, record types, error handling",
            },
            {
                "n": "6810",
                "status": "Proposed Standard",
                "date": "2013-01",
                "why": "version 0, still what most routers speak",
            },
            {
                "n": "6480",
                "status": "Informational",
                "date": "2012-02",
                "why": "where a cache server sits and what it must deliver",
            },
            {
                "n": "9324",
                "status": "Proposed Standard",
                "date": "2022-12",
                "why": "why fresh RPKI data must not trigger a BGP route refresh",
            },
        ],
        "errata": [
            "RFC 6810 is updated by RFC 8210. Implement 8210 and negotiate down to 0 rather than writing two stacks.",
            "RFC 8210 reports no errata as of 2026-10-29. Re-check before the M1 freeze.",
        ],
        "prior": [
            {
                "name": "rov",
                "version": "0.6.0",
                "date": "2025-07-09",
                "note": "batch validator, no RTR",
            },
            {
                "name": "FRR and BIRD RTR clients",
                "version": "-",
                "date": "-",
                "note": "C daemons, not importable code",
            },
            {
                "name": "rtr, rpki-rtr, rtr-client",
                "version": "-",
                "date": "-",
                "note": "absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "cache server: serial discipline, reset query, cache notify, refresh and retry timers",
            "router client: IPv4 and IPv6 prefix records plus router-key records with the error PDU contract",
            "incremental and diff-only update modes that a validator like rpkit can drive directly",
            "a fault injector for truncated records, serial wrap and reset-query storms, the bugs routers actually ship with",
        ],
        "nongoals": [
            "repository access or validation, which is rpkit",
            "BGP itself, which is asnkit",
            "MRT files",
        ],
        "mods": [
            ("pdu", "RTR PDU framing and every record type (RFC 8210)"),
            (
                "serialize",
                "endian-exact encode and decode, hostile input refusal (RFC 8210, RFC 6810)",
            ),
            (
                "session",
                "client and server state machine: version negotiation, serials, timers (RFC 8210)",
            ),
            ("inject", "fault injection helpers for conformance testing"),
        ],
        "api": [
            ("serialize", "def", "decode_pdu", "raw: bytes", "Pdu", "RFC 8210"),
            (
                "serialize",
                "def",
                "encode_reset_query",
                "session_id: int",
                "ResetQuery",
                "RFC 8210",
            ),
            (
                "serialize",
                "def",
                "encode_ipv4_prefix_record",
                "prefix: str, asn: int, max_len: int, flags: int",
                "PrefixRecord",
                "RFC 8210",
            ),
            (
                "serialize",
                "def",
                "encode_router_key_record",
                "asn: int, ski: bytes, spki: bytes",
                "RouterKeyRecord",
                "RFC 8210",
            ),
            (
                "session",
                "def",
                "serve",
                "store: AssertionStore, host: str, port: int",
                "None",
                "RFC 8210",
            ),
            (
                "session",
                "async def",
                "connect",
                "host: str, port: int",
                "RouterClient",
                "RFC 8210",
            ),
            (
                "inject",
                "def",
                "truncated_record",
                "payload: bytes, keep: int",
                "bytes",
                "design",
            ),
        ],
        "steps": [
            "M1 PDU codec, byte-exact, with fuzzed-input refusal",
            "M2 client session: reset query, serial notify, record application",
            "M3 server session: timers, cache notify, error PDUs, concurrent routers",
            "M4 fault injection suite and a loopback conformance test against itself",
            "M5 drive it from an rpkit assertion stream end to end",
            "M6 publication: 0.1.0 with the conformance trace in the docs",
        ],
        "extras": {},
        "cli": "rtrkit serve --listen 127.0.0.1:8323 -- source a store and watch routers attach",
    },
    {
        "name": "asnkit",
        "pkg": "asnkit",
        "title": "asnkit -- prefix to ASN, current and historical",
        "desc": "MRT RIB table parsing, radix longest-prefix match and historical AS lookups "
        "with optional route origin validation state joined in",
        "kw": ["bgp", "mrt", "rib", "asn", "prefix", "radix", "lpm", "rov"],
        "why": (
            "pyasn is the tool everyone uses and it stopped moving in 2023: 1.6.2, 2023-09-01, "
            "a C extension out of a Python 2 lineage with no type hints, no async and no ROV "
            "state. MRT parsing alone is covered by a dozen one-off scripts; what is missing is "
            "a typed library that answers the question an operator actually asks, which AS, on "
            "which date, and what did RPKI say about it, while streaming its input instead of "
            "demanding a build step. The RIB index sits behind an interface so the pure-Python "
            "radix and an optional native one are interchangeable."
        ),
        "docs": [
            {
                "n": "6396",
                "status": "Proposed Standard",
                "date": "2011-10",
                "why": "MRT format: table dumps, BGP messages, state changes",
            },
            {
                "n": "4271",
                "status": "Draft Standard",
                "date": "2006-01",
                "why": "UPDATE and path attribute semantics inside a table dump",
            },
            {
                "n": "6480",
                "status": "Informational",
                "date": "2012-02",
                "why": "what a validation state joined onto a RIB row means",
            },
            {
                "n": "8210",
                "status": "Proposed Standard",
                "date": "2017-09",
                "why": "a live feed via rtrkit instead of a static dump",
            },
        ],
        "errata": [
            "RFC 4271 carries 9 verified errata and 12 updates. Consult them before trusting any UPDATE parsing recipe copied from a blog post.",
            "RFC 6396 carries 2 verified errata.",
        ],
        "prior": [
            {
                "name": "pyasn",
                "version": "1.6.2",
                "date": "2023-09-01",
                "note": "the incumbent: C extension, no typing, no ROV, a build-a-db step",
            },
            {
                "name": "netflow",
                "version": "0.12.2",
                "date": "2023-08-20",
                "note": "flow export codecs, adjacent rather than overlapping",
            },
            {
                "name": "py-radix",
                "version": "-",
                "date": "-",
                "note": "a trie primitive; no MRT, no history",
            },
        ],
        "gaps": [
            "a streaming TABLE_DUMP_V2 reader that never loads a whole RIB into memory",
            "historical lookups by date from the same index, without a per-archive build step",
            "validation state joined at query time from rtrkit or an rpkit assertion set",
            "typed API with an explicit provenance field on every answer",
        ],
        "nongoals": [
            "a BGP speaker or session FSM",
            "flow data",
            "a hosted API that hides where the answer came from",
        ],
        "mods": [
            ("mrt", "MRT record and subtype framing (RFC 6396)"),
            (
                "rib",
                "TABLE_DUMP_V2 view, prefix and AS_PATH records (RFC 6396, RFC 4271)",
            ),
            ("lpm", "radix tree with longest-prefix match and a stable iterator"),
            ("history", "date-scoped indexes over multiple RIB dumps"),
            (
                "rov",
                "origin validation join from rtrkit or an rpkit assertion set (RFC 6480)",
            ),
        ],
        "api": [
            ("mrt", "def", "iter_records", "stream: IO", "Iterator", "RFC 6396"),
            ("rib", "def", "iter_rib_entries", "dump: IO", "Iterator", "RFC 6396"),
            (
                "lpm",
                "def",
                "longest_match",
                "tree: Radix, address: str",
                "Optional[RibEntry]",
                "RFC 6396",
            ),
            ("lpm", "def", "build_radix", "entries: Iterable", "Radix", "design"),
            (
                "history",
                "def",
                "lookup_asn",
                "archive: Archive, address: str, when: datetime.date",
                "list",
                "design",
            ),
            (
                "rov",
                "def",
                "annotate",
                "entries: Iterable, feed: RovFeed",
                "Iterable",
                "RFC 6480",
            ),
        ],
        "steps": [
            "M1 MRT reader for TABLE_DUMP_V2 with a streaming test corpus",
            "M2 radix LPM with a pure-Python reference and a native fast path behind the interface",
            "M3 date-scoped history over several RIB dumps",
            "M4 validation join from rtrkit, with reason codes carried into the answer",
            "M5 CLI parity with pyasn so a migration is a one-line change",
            "M6 publication: 0.1.0 with a migration note from pyasn",
        ],
        "extras": {"fast": [("msgspec", "0.19")]},
        "cli": "asnkit lookup 8.8.8.8 -- asn, prefix, source RIB and validation state",
    },
]
# ------------------------------------------------- clusters: QUIC tunnels and service discovery

PROJECTS_B: list[dict[str, Any]] = [
    {
        "name": "h3tunnel",
        "pkg": "h3tunnel",
        "title": "h3tunnel -- CONNECT-UDP and CONNECT-IP in Python",
        "desc": "MASQUE tunnels: HTTP Datagrams and the Capsule Protocol, CONNECT-UDP and "
        "CONNECT-IP clients, and the proxy side that terminates them",
        "kw": [
            "masque",
            "connect-udp",
            "connect-ip",
            "http3",
            "quic",
            "proxy",
            "rfc9298",
            "rfc9484",
        ],
        "why": (
            "MASQUE is how UDP is proxied over HTTP today, and Python cannot speak it. The "
            "closest thing on PyPI is pymasque (0.1.2, 2026-11-04), which implements Cloudflare "
            "WARP's undocumented L4 mode from a gist: TCP only, client only, no proxy side, and "
            "compliant with neither RFC 9298 nor RFC 9484. The transport problem is already "
            "solved twice over, since aioquic 1.7.2 (2026-11-02) and qh3 2.1.0 (2026-10-25) "
            "both ship sans-IO and asyncio APIs with QUIC DATAGRAM support. What is missing is "
            "precisely the layer above them: capsules, context identifiers and the two CONNECT "
            "profiles. h3tunnel keeps that layer sans-IO, so it is testable with no QUIC stack "
            "at all and the transport stays an adapter.",
        ),
        "docs": [
            {
                "n": "9297",
                "status": "Proposed Standard",
                "date": "2022-08",
                "why": "HTTP Datagrams and the Capsule Protocol, the framing everything else uses",
            },
            {
                "n": "9298",
                "status": "Proposed Standard",
                "date": "2022-08",
                "why": "CONNECT-UDP: request syntax, context identifiers, proxy behaviour",
            },
            {
                "n": "9484",
                "status": "Proposed Standard",
                "date": "2023-10",
                "why": "CONNECT-IP: whole IP packets through the same tunnel",
            },
            {
                "n": "9221",
                "status": "Proposed Standard",
                "date": "2022-03",
                "why": "the QUIC DATAGRAM extension HTTP Datagrams ride on",
            },
            {
                "n": "9114",
                "status": "Proposed Standard",
                "date": "2022-06",
                "why": "HTTP/3 stream and setting rules the tunnels live inside",
            },
            {
                "n": "9220",
                "status": "Proposed Standard",
                "date": "2022-06",
                "why": "extended CONNECT over HTTP/3, the pattern this reuses",
            },
            {
                "n": "9931",
                "status": "Proposed Standard",
                "date": "2025-09",
                "why": "what may be sent optimistically before the response arrives",
            },
        ],
        "errata": [
            "RFC 9484 verified erratum 8444, sec. 4.6: the wildcard value for target and ipproto MUST be percent-encoded, so it travels as %2A. Examples in sec. 4.2 and 4.4 are corrected too. Get this wrong and CONNECT-IP does not interoperate.",
            "RFC 9931 updates RFC 9298 sec. 5: optimistic sending before the response is allowed in HTTP/2 and HTTP/3 but not in HTTP/1.1.",
            "RFC 9297 and RFC 9298 report no errata as of 2026-10-29.",
        ],
        "prior": [
            {
                "name": "pymasque",
                "version": "0.1.2",
                "date": "2026-11-04",
                "note": "Cloudflare WARP L4 mode only: TCP only, client only",
            },
            {
                "name": "aioquic",
                "version": "1.7.2",
                "date": "2026-11-02",
                "note": "the transport underneath, sans-IO plus asyncio; not a tunnel",
            },
            {
                "name": "qh3",
                "version": "2.1.0",
                "date": "2026-10-25",
                "note": "maintained aioquic fork, Rust core, datagrams and WebTransport",
            },
            {
                "name": "connect-udp, masque-proxy, capsule",
                "version": "-",
                "date": "-",
                "note": "all absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "CONNECT-UDP client and proxy in one library, including the server duties of RFC 9298 sec. 3.1",
            "CONNECT-IP with the erratum-correct URI template (RFC 9484)",
            "the Capsule Protocol, so one tunnel works over HTTP/1.1 and HTTP/2 as well (RFC 9297)",
            "context identifier demultiplexing under the MTU and ECN rules of RFC 9298 sec. 6",
            "a transport-neutral core: qh3 and aioquic as adapters, never as the design centre",
        ],
        "nongoals": [
            "a QUIC implementation: aioquic and qh3 already are one, and this is not a third",
            "WARP's proprietary L4 mode or its authentication scheme",
            "a full VPN: CONNECT-IP moves packets, it does not negotiate an address with a peer",
        ],
        "mods": [
            ("capsule", "capsule framing and the registered capsule types (RFC 9297)"),
            (
                "httpdatagram",
                "HTTP Datagram payload with the context identifier (RFC 9298 sec. 5)",
            ),
            (
                "ctx",
                "context identifier allocation and demultiplexing (RFC 9298 sec. 4)",
            ),
            (
                "connect_udp",
                "CONNECT-UDP request and response construction (RFC 9298 sec. 3)",
            ),
            ("connect_ip", "CONNECT-IP URI template and IP packet framing (RFC 9484)"),
            (
                "limits",
                "MTU, ECN and optimistic-send rules (RFC 9298 sec. 6, RFC 9931)",
            ),
            ("sansio", "transport-neutral tunnel state machine"),
            ("aio", "asyncio client and proxy server over a pluggable QUIC adapter"),
        ],
        "api": [
            (
                "capsule",
                "def",
                "encode_capsule",
                "capsule_type: int, body: bytes",
                "Capsule",
                "RFC 9297",
            ),
            ("capsule", "def", "decode_capsule", "payload: bytes", "tuple", "RFC 9297"),
            (
                "httpdatagram",
                "def",
                "encode_datagram",
                "context_id: int, payload: bytes",
                "HttpDatagram",
                "RFC 9298 sec. 5",
            ),
            (
                "ctx",
                "def",
                "allocate_context",
                "tunnel: Tunnel",
                "ContextId",
                "RFC 9298 sec. 4",
            ),
            (
                "connect_udp",
                "def",
                "build_request",
                "target: Target, authority: str, uri: str",
                "ConnectRequest",
                "RFC 9298 sec. 3",
            ),
            (
                "connect_ip",
                "def",
                "target_uri",
                "target: Optional[str], ipproto: Optional[str]",
                "str",
                "RFC 9484 sec. 4.6",
            ),
            (
                "limits",
                "def",
                "clamp_payload",
                "mtu: int, tunnel_overhead: int",
                "int",
                "RFC 9298 sec. 6.1",
            ),
            (
                "sansio",
                "def",
                "on_datagram",
                "data: bytes, now: float",
                "list",
                "RFC 9298",
            ),
            (
                "aio",
                "async def",
                "open_udp_tunnel",
                "proxy: str, target: tuple",
                "UdpTunnel",
                "RFC 9298",
            ),
            (
                "aio",
                "async def",
                "serve_proxy",
                "host: str, port: int, policy: ProxyPolicy",
                "None",
                "RFC 9298 sec. 3.1",
            ),
        ],
        "steps": [
            "M1 signed codecs first: capsule and HTTP Datagram framing against byte-exact vectors",
            "M2 sans-IO client state machine including context identifier lifecycle",
            "M3 asyncio client over the qh3 adapter, verified against a local proxy",
            "M4 proxy server: RFC 9298 sec. 3.1 handling, limits, graceful teardown",
            "M5 CONNECT-IP with erratum 8444 percent-encoding and an IP packet codec",
            "M6 publication: 0.1.0 with an interoperability trace against a non-Python proxy",
        ],
        "extras": {"quic": [("qh3", "2.1")], "aioquic": [("aioquic", "1.7")]},
        "cli": "h3tunnel udp --proxy https://proxy:4433 --listen 127.0.0.1:5354 --target 1.1.1.1:53",
    },
    {
        "name": "dnssd-srp",
        "pkg": "dnssd_srp",
        "title": "dnssd-srp -- DNS-SD without multicast",
        "desc": "Service Registration Protocol (SRP) requester and registrar checks, DNS Push "
        "Notifications, and the DNS Stateful Operations session both depend on",
        "kw": [
            "dns-sd",
            "srp",
            "mdns",
            "dso",
            "push-notifications",
            "rfc9665",
            "rfc8765",
            "rfc8490",
        ],
        "why": (
            "The multicast answer to local service discovery already has a strong Python owner "
            "(zeroconf 0.153.0, 2026-10-31) and this project does not compete with it. RFC 9665 "
            "moved DNS-SD to unicast authenticated updates in 2025-06, and RFC 8765 gave "
            "clients pushed record changes over a persistent stateful session. Nothing on PyPI "
            "speaks any of RFC 9665, RFC 8765, RFC 8490 or RFC 8766. namespy, the DNS library "
            "this is designed beside, states plainly that mDNS and DNS-SD are not spoken "
            "anywhere in it, so the message layer can be shared while the stateful half is "
            "built here.",
        ),
        "docs": [
            {
                "n": "9665",
                "status": "Proposed Standard",
                "date": "2025-06",
                "why": "SRP: unicast DNS-SD with SIG(0) defended registrations",
            },
            {
                "n": "8765",
                "status": "Proposed Standard",
                "date": "2020-06",
                "why": "DNS Push Notifications for records that change",
            },
            {
                "n": "8490",
                "status": "Proposed Standard",
                "date": "2019-03",
                "why": "DSO: the persistent session and TLV layer both ride",
            },
            {
                "n": "8766",
                "status": "Proposed Standard",
                "date": "2020-06",
                "why": "discovery proxy bridging a link into unicast DNS-SD",
            },
            {
                "n": "2931",
                "status": "Proposed Standard",
                "date": "2000-09",
                "why": "SIG(0) request signatures that defend a registration",
            },
            {
                "n": "6763",
                "status": "Proposed Standard",
                "date": "2013-02",
                "why": "DNS-SD naming, plus the domain enumeration that finds a registrar",
            },
            {
                "n": "6762",
                "status": "Proposed Standard",
                "date": "2013-02",
                "why": "mDNS, the world a discovery proxy bridges from",
            },
        ],
        "errata": [
            "RFC 8765 verified erratum 8560, sec. 6.5: for servers that do not implement RECONFIRM it MUST be silently ignored. The published text said a NOERROR response, which RFC 8490 forbids on a unidirectional DSO message.",
            "RFC 9665 and RFC 8490 report no errata as of 2026-10-29.",
            "RFC 6763 is updated by RFC 8553; RFC 6762 has 2 errata on file, none verified.",
        ],
        "prior": [
            {
                "name": "zeroconf",
                "version": "0.153.0",
                "date": "2026-10-31",
                "note": "the multicast responder; no SRP, no DSO, no push",
            },
            {
                "name": "dnspython",
                "version": "2.9.2",
                "date": "2026-11-03",
                "note": "message and DNSSEC plumbing; no stateful sessions",
            },
            {
                "name": "srp",
                "version": "1.0.22",
                "date": "2024-11-01",
                "note": "Secure Remote Password: an unrelated protocol wearing this acronym",
            },
            {
                "name": "dnssd-srp, srpkit, srpd, discovery-proxy",
                "version": "-",
                "date": "-",
                "note": "all absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "SRP update construction and the registrar-side validation of RFC 9665 sec. 3.3",
            "TTL consistency and lease maintenance rules, RFC 9665 sec. 4 and sec. 5",
            "SIG(0) signing with the algorithm RFC 9665 sec. 6.6 requires",
            "DSO session management: keepalive, idle timeout and padding (RFC 8490)",
            "push notification subscriptions (RFC 8765) and a discovery proxy front (RFC 8766)",
        ],
        "nongoals": [
            "an mDNS responder: zeroconf owns the multicast link",
            "a recursive resolver, which is what namespy is",
            "a full DNS server: the registrar half is the update path, not a zone implementation",
        ],
        "mods": [
            ("dso", "DSO message and TLV codec, session timers (RFC 8490)"),
            (
                "session",
                "stream transport, keepalive, idle timeout, padding (RFC 8490)",
            ),
            ("srp", "SRP update construction (RFC 9665 sec. 3)"),
            (
                "registrar",
                "update validation and lease maintenance (RFC 9665 sec. 3.3, sec. 4, sec. 5)",
            ),
            ("sig0", "SIG(0) sign and verify (RFC 2931, RFC 9665 sec. 6.6)"),
            ("push", "subscribe and replay protection (RFC 8765)"),
            ("proxy", "discovery proxy data translation (RFC 8766)"),
            (
                "discovery",
                "registration domain enumeration and registrar SRV lookup (RFC 6763, RFC 9665 sec. 3.1.1)",
            ),
        ],
        "api": [
            ("dso", "def", "encode_dso", "message: DsoMessage", "bytes", "RFC 8490"),
            (
                "session",
                "async def",
                "open_session",
                "resolver: tuple",
                "DsoSession",
                "RFC 8490",
            ),
            (
                "srp",
                "def",
                "build_update",
                "service: ServiceDefinition, lease: Lease",
                "bytes",
                "RFC 9665 sec. 3",
            ),
            (
                "sig0",
                "def",
                "sign",
                "message: bytes, key: SigningKey",
                "bytes",
                "RFC 2931, RFC 9665 sec. 6.6",
            ),
            (
                "sig0",
                "def",
                "verify",
                "message: bytes, signature: bytes, key: VerifyKey",
                "bool",
                "RFC 2931",
            ),
            (
                "registrar",
                "def",
                "validate_update",
                "update: bytes, zone: ZoneContext",
                "ValidationOutcome",
                "RFC 9665 sec. 3.3",
            ),
            (
                "registrar",
                "def",
                "ttl_for",
                "lease_seconds: int",
                "int",
                "RFC 9665 sec. 4",
            ),
            (
                "push",
                "async def",
                "subscribe",
                "session: DsoSession, name: str, rrtype: str",
                "AsyncIterator",
                "RFC 8765",
            ),
            (
                "discovery",
                "def",
                "registrar_from_zone",
                "zone_apex: str",
                "RegistrarEndpoint",
                "RFC 9665 sec. 3.1.1",
            ),
        ],
        "steps": [
            "M1 DSO codec and session with malformed-input refusal",
            "M2 SIG(0) sign and verify with the RFC 9665 sec. 6.6 algorithm",
            "M3 SRP requester: lease, TTL, keep-alive and teardown",
            "M4 registrar-side validation per RFC 9665 sec. 3.3, including the sec. 5 cleanup rules",
            "M5 push subscriptions, with erratum 8560 RECONFIRM behaviour",
            "M6 discovery proxy front end, then publication: 0.1.0",
        ],
        "extras": {"crypto": [("cryptography", "50.0.2")]},
        "cli": "dnssd-srp register --name printer --type _printer._tcp --port 515",
    },
    {
        "name": "turnkit",
        "pkg": "turnkit",
        "title": "turnkit -- STUN, TURN and ICE on asyncio",
        "desc": "STUN messaging and long-term credentials, TURN allocations with permissions and "
        "channels, and an ICE agent written to RFC 8445 with Trickle ICE and ICE PAC",
        "kw": [
            "stun",
            "turn",
            "ice",
            "nat",
            "webrtc",
            "rfc8489",
            "rfc8656",
            "rfc8445",
            "rfc8838",
        ],
        "why": (
            "The NAT traversal stack has a Python owner, but a narrow one. aioice 0.12.1 "
            "(2026-11-03) is written for aiortc: one ICE agent with a private TURN "
            "implementation bolted on, and its own summary still cites RFC 5245, which RFC 8445 "
            "obsoleted in 2018, plus RFC 8863, which changed when an agent may declare failure. "
            "stun 1.1.0 (2026-08-01) is a message library, and pystun3 plus aiostun answer only "
            "the NAT-type question. turnkit is the reusable half nobody has: a TURN client API "
            "with its own allocation lifecycle, and an ICE agent whose spec anchors are the "
            "current documents rather than the ones a 2018 codebase inherited.",
        ),
        "docs": [
            {
                "n": "8489",
                "status": "Proposed Standard",
                "date": "2020-02",
                "why": "STUN: transactions, attributes, MESSAGE-INTEGRITY, FINGERPRINT",
            },
            {
                "n": "8656",
                "status": "Proposed Standard",
                "date": "2020-02",
                "why": "TURN: allocations, permissions, channels, the relayed path",
            },
            {
                "n": "8445",
                "status": "Proposed Standard",
                "date": "2018-07",
                "why": "ICE: candidate gathering, checks, nomination",
            },
            {
                "n": "8838",
                "status": "Proposed Standard",
                "date": "2021-01",
                "why": "Trickle ICE: incremental candidates and early checks",
            },
            {
                "n": "8863",
                "status": "Proposed Standard",
                "date": "2021-01",
                "why": "ICE PAC: the minimum wait before declaring failure",
            },
            {
                "n": "7635",
                "status": "Proposed Standard",
                "date": "2015-08",
                "why": "third-party authorization, the TURN REST credential model",
            },
            {
                "n": "8016",
                "status": "Proposed Standard",
                "date": "2016-11",
                "why": "allocation mobility across an address change",
            },
        ],
        "errata": [
            "RFC 8489 carries 3 verified errata.",
            "RFC 8445 is updated by RFC 8863, and RFC 8656 is the successor to RFC 5766 and RFC 6156: do not copy recipes from either predecessor.",
            "RFC 8838 and RFC 8863 report no errata as of 2026-10-29.",
        ],
        "prior": [
            {
                "name": "aioice",
                "version": "0.12.1",
                "date": "2026-11-03",
                "note": "aiortc's ICE agent with a private TURN client; summary cites the obsoleted RFC 5245",
            },
            {
                "name": "stun",
                "version": "1.1.0",
                "date": "2026-08-01",
                "note": "STUN messages and attributes; no TURN or ICE",
            },
            {
                "name": "aiostun",
                "version": "0.6.1",
                "date": "2026-01-08",
                "note": "STUN client over UDP, TCP and TLS",
            },
            {
                "name": "pyturn",
                "version": "0.2.4.1",
                "date": "2024-03-25",
                "note": "test-grade STUN and TURN client",
            },
            {
                "name": "turnkit, aiturn, stun-client, iceagent",
                "version": "-",
                "date": "-",
                "note": "all absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "a TURN client usable without importing a media stack: allocate, permission, channel, refresh",
            "transport coverage in one place: UDP, TCP, TLS and the ALPN negotiation that picks them",
            "an ICE agent anchored on RFC 8445 plus RFC 8838 and the RFC 8863 failure-wait rule",
            "REST credentials per RFC 7635 and allocation mobility per RFC 8016",
            "a sans-IO agent core so check scheduling can be tested on a virtual clock",
        ],
        "nongoals": [
            "a WebRTC stack or any SDP handling",
            "DTLS-SRTP or media of any kind: the relayed path is opaque here",
            "a TURN server, which is an operational product rather than a client library",
        ],
        "mods": [
            ("message", "STUN message, attribute and integrity codec (RFC 8489)"),
            ("transport", "UDP, TCP and TLS transports with framing (RFC 8489)"),
            (
                "allocation",
                "TURN allocate, refresh, lifetime and reallocation (RFC 8656)",
            ),
            ("permission", "permissions and channel bindings (RFC 8656)"),
            (
                "credentials",
                "long-term credentials, nonce handling, REST tokens (RFC 8489, RFC 7635)",
            ),
            ("ice", "ICE agent: candidates, check scheduling, nomination (RFC 8445)"),
            ("trickle", "incremental candidate exchange (RFC 8838)"),
            ("sansio", "pure agent core for virtual clock testing"),
        ],
        "api": [
            (
                "message",
                "def",
                "encode_message",
                "msg: StunMessage, key: Optional[bytes]",
                "bytes",
                "RFC 8489",
            ),
            (
                "message",
                "def",
                "decode_message",
                "raw: bytes",
                "StunMessage",
                "RFC 8489",
            ),
            (
                "allocation",
                "async def",
                "allocate",
                "server: Endpoint, credentials: Credentials",
                "Allocation",
                "RFC 8656",
            ),
            (
                "allocation",
                "async def",
                "refresh",
                "allocation: Allocation",
                "Allocation",
                "RFC 8656",
            ),
            (
                "permission",
                "def",
                "create_permission",
                "allocation: Allocation, peer: tuple",
                "Permission",
                "RFC 8656",
            ),
            (
                "credentials",
                "def",
                "rest_credentials",
                "username: str, secret: bytes, now: float",
                "Credentials",
                "RFC 7635",
            ),
            (
                "ice",
                "def",
                "gather_candidates",
                "interfaces: list, relay: Optional[Allocation]",
                "list",
                "RFC 8445",
            ),
            (
                "ice",
                "def",
                "schedule_checks",
                "pairs: list, state: AgentState",
                "list",
                "RFC 8445",
            ),
            (
                "sansio",
                "def",
                "on_binding_response",
                "event: Received, now: float",
                "AgentState",
                "RFC 8445, RFC 8863",
            ),
            (
                "trickle",
                "def",
                "encode_end_of_candidates",
                "component: int",
                "bytes",
                "RFC 8838",
            ),
        ],
        "steps": [
            "M1 STUN codec, integrity and fingerprint against published vectors",
            "M2 transports: UDP, TCP, TLS, with framing and timeout policy",
            "M3 TURN allocation lifecycle including 401 nonce replay and refresh",
            "M4 permissions and channels, then RFC 8016 mobility",
            "M5 sans-IO ICE agent with RFC 8863 failure timing, then trickle",
            "M6 publication: 0.1.0 with a relay interoperability trace",
        ],
        "extras": {},
        "cli": "turnkit allocate --server turn:example.net:3478 --rest-user u --rest-secret env:SECRET",
    },
]
# ------------------------------------------------- clusters: address assignment and provisioning

PROJECTS_C: list[dict[str, Any]] = [
    {
        "name": "leasespy",
        "pkg": "leasespy",
        "title": "leasespy -- DHCP clients, servers and relays on asyncio",
        "desc": "DHCPv4 and DHCPv6 on asyncio: sans-IO state machines, the option registry, "
        "relay agents with option 82, leasequery and the failover peer protocol",
        "kw": [
            "dhcp",
            "dhcpv6",
            "dhcpv4",
            "relay",
            "leasequery",
            "failover",
            "rfc9915",
            "rfc2131",
        ],
        "why": (
            "DHCPv6 was reissued in January 2026 as RFC 9915, an Internet Standard (STD 102) "
            "that obsoletes RFC 8415 and deliberately removes IA_TA and the server unicast "
            "option. No implementation in any language has finished that transition, and no "
            "Python library is written against it. The Python field is contested but shallow: "
            "pydhcp 0.9.1 (2026-10-21) is young and IPv4-first, dhcpkit 1.0.7 has not moved "
            "since 2017, pydhcplib stopped in 2014, and dhcpy 0.0.7 drives the Kea control API "
            "rather than the protocol. leasespy takes the ground nobody holds: the relay and "
            "failover half of DHCP, where an operator's problem actually lives.",
        ),
        "docs": [
            {
                "n": "9915",
                "status": "Internet Standard (STD 102)",
                "date": "2026-01",
                "why": "current DHCPv6: message formats, DUID, IA, relay, options",
            },
            {
                "n": "2131",
                "status": "Draft Standard",
                "date": "1997-03",
                "why": "DHCPv4 client and server state machines",
            },
            {
                "n": "2132",
                "status": "Draft Standard",
                "date": "1997-03",
                "why": "the DHCP option and BOOTP vendor extension registry",
            },
            {
                "n": "3046",
                "status": "Proposed Standard",
                "date": "2001-01",
                "why": "relay agent information, option 82",
            },
            {
                "n": "6422",
                "status": "Proposed Standard",
                "date": "2011-12",
                "why": "relay-supplied options for DHCPv6",
            },
            {
                "n": "5007",
                "status": "Proposed Standard",
                "date": "2007-09",
                "why": "DHCPv6 leasequery",
            },
            {
                "n": "7653",
                "status": "Proposed Standard",
                "date": "2015-10",
                "why": "DHCPv6 active leasequery",
            },
            {
                "n": "8156",
                "status": "Proposed Standard",
                "date": "2017-06",
                "why": "DHCPv6 failover between cooperating servers",
            },
        ],
        "errata": [
            "RFC 2131 carries 7 verified errata and is updated by RFC 3396, RFC 4361, RFC 5494 and RFC 6842. The errata change packet handling, so the codec is written against them, not the 1997 text alone.",
            "RFC 2132 carries 2 verified errata and 5 updates.",
            "RFC 9915 carries 1 verified erratum and removes IA_TA plus server unicast: implementing RFC 8415 today builds the obsolete behaviour in.",
        ],
        "prior": [
            {
                "name": "pydhcp",
                "version": "0.9.1",
                "date": "2026-10-21",
                "note": "active and IPv4-centred; no relay, leasequery or failover",
            },
            {
                "name": "dhcpy",
                "version": "0.0.7",
                "date": "2024-10-09",
                "note": "an ISC Kea control API client, not the DHCP protocol",
            },
            {
                "name": "dhcpkit",
                "version": "1.0.7",
                "date": "2017-06-25",
                "note": "IPv6 only, unmaintained for nine years",
            },
            {
                "name": "scapy",
                "version": "2.8.0",
                "date": "2026-10-02",
                "note": "packet forgery; no allocation state machine or lease store",
            },
        ],
        "gaps": [
            "DHCPv6 written to RFC 9915 from the first commit, with IA_TA and server unicast absent by construction",
            "a sans-IO state machine per RFC 2131 and RFC 9915 sec. 14 through sec. 18, testable on a virtual clock",
            "relay agent with option 82 and RFC 6422 relay-supplied options, which is where real deployments break",
            "leasequery and active leasequery so a monitoring system can read a live server",
            "failover peer state machine, which no Python library attempts at all",
        ],
        "nongoals": [
            "a packet crafting tool: use scapy for that and this library will not pretend otherwise",
            "a complete production server: leases persist behind an interface, storage is the operator's choice",
            "PXE, PXP or DOCSIS suboptions in the first release, only the registry hooks for them",
        ],
        "mods": [
            (
                "wire",
                "DHCPv4 and DHCPv6 message formats (RFC 2131, RFC 9915 sec. 8, sec. 9)",
            ),
            (
                "options",
                "option registry, encoders and decoders (RFC 2132, RFC 9915 sec. 21)",
            ),
            ("duid", "DUID types and stability rules (RFC 9915 sec. 11)"),
            (
                "identity",
                "identity associations: address and prefix binding (RFC 9915 sec. 12)",
            ),
            (
                "fsm",
                "client and server state machines with retransmission (RFC 9915 sec. 14, sec. 15, sec. 18)",
            ),
            ("validate", "message validation and error handling (RFC 9915 sec. 16)"),
            (
                "relay",
                "relay forwarding and option 82 (RFC 9915 sec. 19, RFC 3046, RFC 6422)",
            ),
            ("leasequery", "query and active query (RFC 5007, RFC 7653)"),
            ("failover", "peer protocol and states (RFC 8156)"),
            ("clock", "sans-IO timers so every timeout is testable without sleeping"),
        ],
        "api": [
            ("wire", "def", "decode_v6", "raw: bytes", "Message", "RFC 9915 sec. 8"),
            ("wire", "def", "encode_v6", "msg: Message", "bytes", "RFC 9915 sec. 8"),
            ("wire", "def", "decode_v4", "raw: bytes", "Bootp", "RFC 2131"),
            (
                "options",
                "def",
                "encode_option",
                "code: int, value: object",
                "bytes",
                "RFC 2132, RFC 9915 sec. 21",
            ),
            (
                "options",
                "def",
                "decode_options",
                "raw: bytes",
                "Options",
                "RFC 9915 sec. 21",
            ),
            ("duid", "def", "parse_duid", "raw: bytes", "Duid", "RFC 9915 sec. 11"),
            (
                "fsm",
                "def",
                "client_step",
                "state: ClientState, event: Event, now: float",
                "Step",
                "RFC 9915 sec. 18",
            ),
            (
                "validate",
                "def",
                "check_message",
                "msg: Message, context: ServerContext",
                "list",
                "RFC 9915 sec. 16",
            ),
            (
                "relay",
                "def",
                "wrap_relay_forward",
                "peer: Endpoint, link: Endpoint, msg: Message",
                "bytes",
                "RFC 9915 sec. 9",
            ),
            (
                "leasequery",
                "def",
                "build_query",
                "server: Endpoint, iaid: Optional[int]",
                "Message",
                "RFC 5007",
            ),
            (
                "failover",
                "def",
                "peer_transition",
                "state: FailoverState, event: PeerEvent",
                "FailoverState",
                "RFC 8156",
            ),
        ],
        "steps": [
            "M1 wire codec and option registry for both families, with RFC 2131 errata applied",
            "M2 sans-IO client state machines on a virtual clock, including RFC 9915 retransmission",
            "M3 server allocation for addresses and prefixes, DUID stability included",
            "M4 relay with option 82 and RFC 6422, verified against a real relay",
            "M5 leasequery and active leasequery",
            "M6 failover peer protocol, then publication: 0.1.0",
        ],
        "extras": {},
        "cli": "leasespy discover --6 --interface eth0 -- print the OFFER and every option decoded",
    },
    {
        "name": "cwmp",
        "pkg": "cwmp",
        "title": "cwmp -- TR-069 CWMP for ACS and CPE",
        "desc": "CWMP remote management: SOAP 1.2 RPC codec, session machinery, Digest "
        "authentication, parameter path trees and file transfer, ACS and CPE sides",
        "kw": [
            "tr-069",
            "cwmp",
            "acs",
            "cpe",
            "provisioning",
            "tr-181",
            "soap",
            "hntl",
        ],
        "why": (
            "CWMP is how almost every customer premises device on earth is configured, and "
            "Python cannot speak it. GenieACS, the serious open source ACS, is Node.js; on "
            "PyPI the name tr069 is a registered but empty squat, acs belongs to Azure Container "
            "Service, pyacs is an oceanographic sensor library, and inform is a logging "
            "utility. Meanwhile the provisioning chain is already half built in Python: "
            "DHCP hands the CPE its ACS URL, cwmp takes it from there. This is a deliberately "
            "non-IETF project: the specification lives at the Broadband Forum, so every claim "
            "below cites a document number that must be re-verified against the Forum's current "
            "revision before it reaches code.",
        ),
        "docs": [
            {
                "label": "TR-069 (CWMP)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the protocol: Inform, Get and SetParameterValues, TransferFile",
            },
            {
                "label": "TR-181 (Device:2)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the data model object and parameter tree",
            },
            {
                "label": "TR-098 (InternetGatewayDevice)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the model most deployed CPE still exposes",
            },
            {
                "label": "TR-069 Annex 2 (SOAP)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the envelope and encoding rules the RPC layer obeys",
            },
            {
                "label": "TR-369 (USP)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the WebSocket successor; a roadmap target, not a first release",
            },
            {
                "n": "9110",
                "status": "Internet Standard (STD 97)",
                "date": "2022-06",
                "why": "HTTP semantics under the transport, including authentication",
            },
        ],
        "errata": [
            "Outside the RFC series, so there is no errata mechanism to consult: pin the exact TR revision in every docstring and test, and record it in docs/research.md.",
            "The ACS URL a CPE learns usually arrives from DHCP option 43 or a DHCPv6 vendor option, so leasespy is the natural partner and the two must agree on the encoding.",
        ],
        "prior": [
            {
                "name": "tr069",
                "version": "-",
                "date": "-",
                "note": "registered but empty on PyPI: a squat that blocks the obvious name",
            },
            {
                "name": "GenieACS",
                "version": "-",
                "date": "-",
                "note": "the reference open source ACS, written in Node.js",
            },
            {
                "name": "acs, pyacs, inform",
                "version": "-",
                "date": "-",
                "note": "Azure tooling, an ocean sensor library and a logging utility",
            },
        ],
        "gaps": [
            "SOAP 1.2 RPC codec that refuses hostile XML: no DTDs, no external entities, bounded depth",
            "CWMP session engine: Inform, RPC method dispatch, fault codes, keep-alive and nonce-based retry",
            "HTTP Digest authentication on both sides, since most CPE ship nothing else",
            "parameter path tree with wildcards, instance addition and deletion, typed constraints",
            "both endpoints: an ACS side that can manage a real device and a CPE side to test against",
        ],
        "nongoals": [
            "a web UI, ticket system or firmware repository: an ACS product composes those, this is the protocol",
            "business provisioning logic beyond the data model",
            "USP transport in the first release, only the seam that will allow it",
        ],
        "mods": [
            ("envelope", "SOAP 1.2 envelope codec with XML hardening (TR-069 Annex 2)"),
            ("methods", "one class per RPC method, request and response (TR-069)"),
            (
                "session",
                "ACS session state, authentication and fault handling (TR-069)",
            ),
            (
                "endpoint",
                "CPE side: inform, connection request, method dispatch (TR-069)",
            ),
            (
                "datamodel",
                "object tree, parameter paths, types and constraints (TR-181, TR-098)",
            ),
            ("auth", "HTTP Digest challenge and response (RFC 9110, TR-069)"),
            (
                "transfer",
                "TransferFile, Download and Upload with resumable semantics (TR-069)",
            ),
            ("clock", "periodic inform, session timeout and connection request retry"),
        ],
        "api": [
            (
                "envelope",
                "def",
                "encode_envelope",
                "rpc: Rpc, session: SessionContext",
                "bytes",
                "TR-069 Annex 2",
            ),
            (
                "envelope",
                "def",
                "decode_envelope",
                "raw: bytes",
                "Rpc",
                "TR-069 Annex 2",
            ),
            (
                "methods",
                "def",
                "build_inform",
                "device: DeviceIdentity, events: list",
                "Rpc",
                "TR-069",
            ),
            ("methods", "def", "set_parameter_values", "params: dict", "Rpc", "TR-069"),
            (
                "session",
                "async def",
                "handle_session",
                "request: HttpRequest, acs: AcsApp",
                "HttpResponse",
                "TR-069, RFC 9110",
            ),
            (
                "endpoint",
                "async def",
                "run_inform",
                "acs_url: str, identity: DeviceIdentity",
                "Session",
                "TR-069",
            ),
            (
                "datamodel",
                "def",
                "resolve_path",
                "tree: DataModel, path: str",
                "list",
                "TR-181",
            ),
            (
                "datamodel",
                "def",
                "coerce_value",
                "parameter: Parameter, value: object",
                "object",
                "TR-181",
            ),
            (
                "auth",
                "def",
                "digest_challenge",
                "nonce: bytes, realm: str",
                "str",
                "RFC 9110",
            ),
            (
                "transfer",
                "def",
                "build_download",
                "command_key: str, url: str, file_type: str",
                "Rpc",
                "TR-069",
            ),
        ],
        "steps": [
            "M1 hardened SOAP envelope codec, with an entity-expansion and depth bomb test",
            "M2 RPC method classes and fault codes against a captured CPE session",
            "M3 ACS session engine with Digest auth and keep-alive",
            "M4 CPE endpoint able to complete a real Inform against the ACS in the same repo",
            "M5 data model tree with wildcards, instance add and delete",
            "M6 file transfer and connection request, then publication: 0.1.0",
        ],
        "extras": {},
        "cli": "cwmp inform --acs http://acs.local:7547/ --id serial-1234",
    },
    {
        "name": "devicespy",
        "pkg": "devicespy",
        "title": "devicespy -- be the UPnP device, not the control point",
        "desc": "UPnP device side: SSDP advertisement, device and service descriptions, SOAP "
        "control handling and GENA eventing, with hardened XML",
        "kw": [
            "upnp",
            "ssdp",
            "gena",
            "scpd",
            "device",
            "media-server",
            "printer",
            "uda",
        ],
        "why": (
            "Every Python UPnP library is a control point. async-upnp-client 0.49.0 "
            "(2026-10-11), upnpclient 2.0.3 (2026-04-07) and python-upnp 1.0.0 (2024-07-12) "
            "all talk to devices, and ssdp 1.3.1 (2025-09-06) plus ssdpy 0.4.1 do discovery. "
            "Nothing lets a Python program be a device: advertise itself, publish its "
            "description and SCPD, answer control requests and push events. That is the half a "
            "printer, scanner or media server needs, and it is also the security-sensitive "
            "half, because a device parses XML that a stranger on the LAN wrote.",
        ),
        "docs": [
            {
                "label": "UDA 2.0 (UPnP Device Architecture)",
                "status": "UPnP Forum",
                "date": "-",
                "why": "device and service description, control, eventing, boot sequence",
            },
            {
                "label": "GENA 1.0",
                "status": "OASIS",
                "date": "-",
                "why": "subscribe, renew, notify, unsubscribe",
            },
            {
                "label": "SDDL 1.0",
                "status": "UPnP Forum",
                "date": "-",
                "why": "device and service description discovery layout",
            },
            {
                "n": "9110",
                "status": "Internet Standard (STD 97)",
                "date": "2022-06",
                "why": "the HTTP semantics every UPnP exchange rides on",
            },
        ],
        "errata": [
            "UDA and GENA are outside the RFC series: pin the exact specification revision in every docstring.",
            "SSDP itself has a maintained Python owner already (ssdp 1.3.1), so the design decision is whether to depend on it or speak multicast HTTP directly. Record the reasoning in docs/strategy.md before writing code.",
        ],
        "prior": [
            {
                "name": "async-upnp-client",
                "version": "0.49.0",
                "date": "2026-10-11",
                "note": "the reference control point; it is not a device stack",
            },
            {
                "name": "upnpclient",
                "version": "2.0.3",
                "date": "2026-04-07",
                "note": "client only, revived",
            },
            {
                "name": "ssdp, ssdpy",
                "version": "1.3.1, 0.4.1",
                "date": "2025-09-06",
                "note": "discovery transport, already solved",
            },
            {
                "name": "upnp-device, upnp-server, deviceupnp",
                "version": "-",
                "date": "-",
                "note": "all absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "advertise and live lifecycle: alive, byebye, search response, and bootId changes on restart",
            "description and SCPD authoring with validation, so a malformed service does not ship",
            "SOAP control dispatch with argument typing and action-level authorisation",
            "GENA subscription manager: renewals, evented properties, seqnum, and resubscribe on loss",
            "defensive XML: no DTDs, no external entities, bounded size, since the peer is a stranger",
        ],
        "nongoals": [
            "a control point: use async-upnp-client, which is better at it than this will be",
            "DLNA or IGD semantics in the first release, only the generic device layer beneath them",
            "port mapping through an Internet Gateway Device, which is a profile, not the protocol",
        ],
        "mods": [
            (
                "advertise",
                "SSDP alive, byebye and search responses (UDA 2.0, SDDL 1.0)",
            ),
            ("description", "device and service description documents (UDA 2.0)"),
            (
                "scpd",
                "service control protocol definition: actions, state variables, allowed values",
            ),
            ("control", "SOAP action dispatch with argument coercion (UDA 2.0)"),
            (
                "events",
                "GENA subscriptions and evented property change notifications (GENA 1.0)",
            ),
            ("xmlsafe", "the hardened parser every other module must use"),
            ("httpd", "the small asyncio HTTP surface the device serves (RFC 9110)"),
        ],
        "api": [
            (
                "advertise",
                "async def",
                "announce",
                "device: Device, interfaces: list",
                "None",
                "UDA 2.0",
            ),
            (
                "advertise",
                "def",
                "search_response",
                "device: Device, stn: str",
                "Response",
                "UDA 2.0",
            ),
            (
                "description",
                "def",
                "render_device_xml",
                "device: Device",
                "bytes",
                "UDA 2.0",
            ),
            (
                "scpd",
                "def",
                "parse_scpd",
                "raw: bytes",
                "ServiceDescription",
                "UDA 2.0",
            ),
            (
                "control",
                "def",
                "dispatch",
                "service: Service, action: str, args: dict",
                "ActionResult",
                "UDA 2.0",
            ),
            (
                "events",
                "async def",
                "notify",
                "subscription: Subscription, props: dict",
                "None",
                "GENA 1.0",
            ),
            (
                "events",
                "def",
                "renew",
                "subscription: Subscription, requested: int",
                "Subscription",
                "GENA 1.0",
            ),
            ("xmlsafe", "def", "parse", "raw: bytes, limit: int", "Element", "design"),
        ],
        "steps": [
            "M1 hardened XML parser plus description and SCPD round trip",
            "M2 SSDP advertisement and search responses on Windows and Linux multicast",
            "M3 control dispatch with typed arguments and error codes",
            "M4 GENA subscriptions, renewals and evented properties",
            "M5 a reference example device, then interop testing against a real control point",
            "M6 publication: 0.1.0",
        ],
        "extras": {},
        "cli": "devicespy serve --device ./device.xml --listen 0.0.0.0:49152",
    },
]
# --------------------------------------------- clusters: privacy proxies, secure time, device auth

PROJECTS_D: list[dict[str, Any]] = [
    {
        "name": "ohttp",
        "pkg": "ohttp",
        "title": "ohttp -- Oblivious HTTP client, gateway and responder",
        "desc": "Oblivious HTTP message encapsulation and the three roles that use it: client, "
        "gateway relay and responder, plus SVCB discovery of an oblivious gateway",
        "kw": [
            "ohttp",
            "oblivious-http",
            "privacy",
            "hpke",
            "relay",
            "odoh",
            "rfc9458",
            "rfc9540",
        ],
        "why": (
            "OHTTP exists so that the party who sees the content never sees who asked, and the "
            "party who relays never sees the content. It is the reporting path for privacy-preserving "
            "systems and it is standardised: RFC 9458 for the mechanism, RFC 9540 for "
            "discovering a gateway through SVCB records, RFC 9230 for the DNS variant. Python "
            "has nothing: ohttp, pyohttp and ohttp-relay are all absent from PyPI, and the one "
            "implementation people reach for is a Rust binding built for Firefox. The crypto "
            "primitives are not the blocker, since HPKE is already available; what nobody has "
            "is the message format and the gateway that must not leak correlation data.",
        ),
        "docs": [
            {
                "n": "9458",
                "status": "Proposed Standard",
                "date": "2024-01",
                "why": "Oblivious HTTP: encapsulated messages, keys, the gateway contract",
            },
            {
                "n": "9540",
                "status": "Proposed Standard",
                "date": "2024-02",
                "why": "discovering oblivious services through Service Binding records",
            },
            {
                "n": "9230",
                "status": "Experimental",
                "date": "2022-06",
                "why": "Oblivious DNS over HTTPS, the deployment this generalises",
            },
            {
                "n": "9180",
                "status": "IRTF Informational",
                "date": "2022-02",
                "why": "HPKE, the encryption envelope underneath",
            },
        ],
        "errata": [
            "RFC 9180 carries 6 verified errata: read them before writing or depending on an HPKE layer.",
            "RFC 9540 defines the SVCB keys that identify an oblivious gateway, so discovery and the message layer cannot be built independently.",
        ],
        "prior": [
            {
                "name": "hpke",
                "version": "0.3.2",
                "date": "2024-10-26",
                "note": "the HPKE primitives; not OHTTP and no gateway",
            },
            {
                "name": "pyohttp",
                "version": "-",
                "date": "-",
                "note": "Rust with Python bindings built for Firefox; absent from PyPI",
            },
            {
                "name": "ohttp, ohttp-relay",
                "version": "-",
                "date": "-",
                "note": "absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "all three roles in one library: client, gateway and responder",
            "key configuration and rotation with an explicit listener bound to config changes",
            "gateway hardening: no redirects followed, bounded body sizes, no correlation identifiers logged",
            "SVCB-based gateway discovery per RFC 9540 rather than a hand-configured URL",
            "a runnable gateway binary, because a relay you cannot deploy is not a reference implementation",
        ],
        "nongoals": [
            "a general HTTP client: bring httpx and hand it a transport",
            "OHTTP-KEM and other draft-stage variants still moving under the IETF",
            "an anonymity network: one honest component is enough by design, two colluding ones are not",
        ],
        "mods": [
            ("message", "encapsulated request and response formats (RFC 9458)"),
            (
                "keys",
                "key configurations, identifier, generation and rotation (RFC 9458)",
            ),
            ("client", "encapsulate, send, de-encapsulate (RFC 9458)"),
            (
                "gateway",
                "the relay: forward without reading, and what that forbids (RFC 9458)",
            ),
            ("responder", "de-encapsulate, answer, re-encapsulate (RFC 9458)"),
            (
                "svcb",
                "oblivious gateway discovery via HTTPS and SVCB records (RFC 9540)",
            ),
            (
                "crypto",
                "the HPKE seam, swappable and pinned to tested suites (RFC 9180)",
            ),
        ],
        "api": [
            (
                "keys",
                "def",
                "generate_config",
                "suite: Suite, key_id: int",
                "KeyPair",
                "RFC 9458",
            ),
            ("keys", "def", "parse_config", "raw: bytes", "KeyConfig", "RFC 9458"),
            (
                "message",
                "def",
                "encapsulate",
                "request: bytes, config: KeyConfig, aad: bytes",
                "Encapsulated",
                "RFC 9458",
            ),
            (
                "message",
                "def",
                "decapsulate",
                "body: Encapsulated, keys: ResponderKeys",
                "Decapsulated",
                "RFC 9458",
            ),
            (
                "gateway",
                "async def",
                "relay",
                "body: Encapsulated, responder: str",
                "Encapsulated",
                "RFC 9458",
            ),
            (
                "client",
                "async def",
                "request",
                "gateway: Gateway, request: HttpRequest",
                "HttpResponse",
                "RFC 9458",
            ),
            (
                "svcb",
                "def",
                "select_gateway",
                "records: list, now: float",
                "Gateway",
                "RFC 9540",
            ),
            ("crypto", "def", "supported_suites", "", "tuple", "RFC 9180"),
        ],
        "steps": [
            "M1 message and key configuration codecs, byte-exact",
            "M2 responder and client against published vectors, using the hpke extra",
            "M3 gateway with its hardening rules, and a correlation-leak test suite",
            "M4 key rotation with listener notification",
            "M5 SVCB discovery, then a runnable gateway binary",
            "M6 publication: 0.1.0 with an end-to-end privacy trace in the docs",
        ],
        "extras": {"hpke": [("hpke", "0.3.2")], "dns": [("namespy", "0.9")]},
        "cli": "ohttp gateway --listen 0.0.0.0:8083 --responder https://collector.example/ingest",
    },
    {
        "name": "ntspy",
        "pkg": "ntspy",
        "title": "ntspy -- Network Time Security on asyncio",
        "desc": "NTS: the key establishment protocol, cookie lifecycle and the NTPv4 extension "
        "field that authenticates time, client and server sides",
        "kw": ["ntp", "nts", "time", "authentication", "nts-ke", "rfc8915", "rfc5905"],
        "why": (
            "Authenticated time is a solved problem on paper and absent in Python. RFC 8915 "
            "defines NTS: a TLS key establishment exchange that hands the client cookies, then "
            "an authenticator in every NTP packet. Nothing on PyPI implements any of it, and "
            "the NTP clients that do exist are either stale (ntplib 0.4.0, 2021-05-28) or plain "
            "unauthenticated (pyntp 0.1.1, 2026-03-20). The gap is NTS, not NTP: nts, nts-ke, "
            "ntp-nts and aiontp were all absent when checked on 2026-11-05.",
        ),
        "docs": [
            {
                "n": "8915",
                "status": "Proposed Standard",
                "date": "2020-09",
                "why": "NTS: key establishment, cookies, the extension field",
            },
            {
                "n": "5905",
                "status": "Proposed Standard",
                "date": "2010-06",
                "why": "NTPv4 packet format and the modes NTS rides on",
            },
            {
                "n": "9748",
                "status": "Proposed Standard",
                "date": "2025-02",
                "why": "the refreshed NTP registries: modes, extension field types",
            },
            {
                "n": "8633",
                "status": "Best Current Practice",
                "date": "2019-07",
                "why": "operating rules an NTS client should respect",
            },
            {
                "n": "9523",
                "status": "Informational",
                "date": "2024-02",
                "why": "Khronos, the alternative approach; a roadmap comparison, not a dependency",
            },
        ],
        "errata": [
            "RFC 5905 carries 15 verified errata, the heaviest errata load in this portfolio, and is updated by RFC 7822, RFC 8573, RFC 9109, RFC 9748 and RFC 9769. The packet layer is written against the errata, not the 2010 text.",
            "Re-check the errata pages for RFC 8915 and RFC 9748 before the M1 freeze rather than trusting what is written here.",
        ],
        "prior": [
            {
                "name": "ntplib",
                "version": "0.4.0",
                "date": "2021-05-28",
                "note": "unauthenticated NTP client, unmaintained",
            },
            {
                "name": "pyntp",
                "version": "0.1.1",
                "date": "2026-03-20",
                "note": "active but unauthenticated; the opposite half of the problem",
            },
            {
                "name": "nts, nts-ke, ntp-nts, aiontp",
                "version": "-",
                "date": "-",
                "note": "absent from PyPI (2026-11-05); nts is an unrelated note-taking package",
            },
        ],
        "gaps": [
            "the NTS-KE exchange over TLS with application layer protocol negotiation and ALTS-style record framing",
            "cookie issue, cache, renewal and the critical-path rule that a stale cookie must not break time",
            "the NTP extension field authenticator and its truncated MAC discipline",
            "a server side, because an authenticated client with nothing to talk to measures nothing",
            "TLS exporter secrets through the cryptography extra rather than a bespoke TLS stack",
        ],
        "nongoals": [
            "kernel clock discipline, slewing or PPS: measuring offset is in scope, steering the clock is not",
            "a complete RFC 5905 server: broadcast, manycast and interleaved modes come later if ever",
            "PTP and IEEE 1588, which is a different engineering world",
        ],
        "mods": [
            (
                "packet",
                "NTPv4 header, extension fields and timestamp arithmetic (RFC 5905, RFC 9748)",
            ),
            ("ke", "key establishment records and notifications (RFC 8915)"),
            ("cookies", "issue, validate, cache and renew (RFC 8915)"),
            (
                "extension",
                "the NTS authenticator and unique identifier fields (RFC 8915)",
            ),
            ("auth", "derive, sign and verify with truncated MACs (RFC 8915)"),
            ("client", "the asyncio client: establish, query, verify, re-establish"),
            ("server", "the server half: accept, mint cookies, authenticate responses"),
            (
                "trust",
                "local trust store and the leap second and stride flags it must not silently ignore",
            ),
        ],
        "api": [
            ("packet", "def", "decode_packet", "raw: bytes", "NtpPacket", "RFC 5905"),
            (
                "packet",
                "def",
                "encode_packet",
                "packet: NtpPacket",
                "bytes",
                "RFC 5905",
            ),
            ("ke", "def", "encode_record", "record: KeRecord", "bytes", "RFC 8915"),
            (
                "ke",
                "async def",
                "establish",
                "server: str, port: int",
                "Negotiated",
                "RFC 8915",
            ),
            (
                "cookies",
                "def",
                "mint",
                "state: ServerState, aead_key: bytes",
                "bytes",
                "RFC 8915",
            ),
            (
                "cookies",
                "def",
                "validate",
                "cookie: bytes, state: ServerState",
                "Negotiated",
                "RFC 8915",
            ),
            (
                "extension",
                "def",
                "authenticate",
                "packet: NtpPacket, context: Negotiated",
                "NtpPacket",
                "RFC 8915",
            ),
            (
                "extension",
                "def",
                "verify",
                "packet: NtpPacket, context: Negotiated",
                "bool",
                "RFC 8915",
            ),
            (
                "client",
                "async def",
                "synchronize",
                "servers: list, attempts: int",
                "Sample",
                "RFC 8915, RFC 8633",
            ),
            (
                "server",
                "async def",
                "serve",
                "config: ServerConfig",
                "None",
                "RFC 8915",
            ),
        ],
        "steps": [
            "M1 packet and timestamp layer with the RFC 5905 errata applied",
            "M2 extension field authenticator, sign and verify",
            "M3 NTS-KE client against a public NTS server",
            "M4 cookie lifecycle including renewal under load",
            "M5 server side plus a loopback interoperability test",
            "M6 publication: 0.1.0",
        ],
        "extras": {"crypto": [("cryptography", "50.0.2")]},
        "cli": "ntspy query time.google.com --nts -- show offset, delay and how it was authenticated",
    },
    {
        "name": "tacacs",
        "pkg": "tacacs",
        "title": "tacacs -- TACACS+ authentication, authorization and accounting",
        "desc": "TACACS+ client and server: header obfuscation, authentication, command "
        "authorization, accounting, and the TLS transport that replaces them",
        "kw": [
            "tacacs",
            "tacacs-plus",
            "aaa",
            "network",
            "authentication",
            "rfc8907",
            "rfc9887",
            "rfc9950",
        ],
        "why": (
            "Every switch and router in a network operates area runs TACACS+ for device "
            "administration, and Python has no client and no server. What is more, the "
            "protocol is being actively standardised right now: RFC 9887 (2025-12) defines "
            "TACACS+ over TLS 1.3, replacing the plaintext transport with an authenticated one, "
            "and RFC 9950 (2026-03) adds a YANG data model. Both are younger than most feature "
            "branches, and neither has an implementation anywhere outside vendor firmware. The "
            "name is free: tacacs and rfc8907 are absent from PyPI as of 2026-11-05.",
        ),
        "docs": [
            {
                "n": "8907",
                "status": "Informational",
                "date": "2020-09",
                "why": "the protocol as deployed: header, authentication, authorization, accounting",
            },
            {
                "n": "9887",
                "status": "Proposed Standard",
                "date": "2025-12",
                "why": "TACACS+ over TLS 1.3, the transport that fixes the plaintext problem",
            },
            {
                "n": "9950",
                "status": "Proposed Standard",
                "date": "2026-03",
                "why": "YANG data model for configuration and state",
            },
            {
                "n": "1492",
                "status": "Informational (Historic)",
                "date": "1993-07",
                "why": "the original TACACS, named only so nobody confuses the three",
            },
        ],
        "errata": [
            "RFC 8907 is Informational: it documents what vendors ship, and the deviations are real. Interoperability tests must be against hardware, not only against this specification.",
            "RFC 9887 and RFC 9950 are recent enough that implementations, not errata, are the open question: re-check both before M1.",
            "pytacs exists on PyPI (2025.11.27) but its scope was not established during this survey. Verify it before assuming the field is empty.",
        ],
        "prior": [
            {
                "name": "pyrad",
                "version": "2.6.0",
                "date": "2026-10-18",
                "note": "RADIUS, a different protocol with a different job",
            },
            {
                "name": "tacacs, rfc8907",
                "version": "-",
                "date": "-",
                "note": "absent from PyPI (2026-11-05)",
            },
            {
                "name": "vendor SDKs",
                "version": "-",
                "date": "-",
                "note": "none: network gear is a client of the protocol, not a Python library",
            },
        ],
        "gaps": [
            "a real client for automation: login, authorize a command, and account for what ran",
            "a server usable in tests, so a network team can assert on authorization decisions",
            "the PAD obfuscation layer done correctly, since it is the part every home-grown parser gets wrong",
            "the RFC 9887 TLS transport with the right identity and negotiation rules",
            "a configuration shape that mirrors the RFC 9950 YANG model instead of inventing one",
        ],
        "nongoals": [
            "RADIUS, which pyrad covers",
            "an AAA policy engine: decisions are the operator's, this carries them",
            "the historic RFC 1492 protocol",
        ],
        "mods": [
            (
                "header",
                "TACACS+ header, flags, session and length discipline (RFC 8907)",
            ),
            (
                "obfuscation",
                "PAD based body obfuscation and the version quirks around it (RFC 8907)",
            ),
            ("body", "authentication, authorization and accounting bodies (RFC 8907)"),
            ("client", "the asyncio client with reconnect and timeout policy"),
            ("server", "the server with pluggable identity and policy backends"),
            ("tls", "the TLS 1.3 transport (RFC 9887)"),
            ("model", "configuration and state mirroring the data model (RFC 9950)"),
        ],
        "api": [
            ("header", "def", "decode_header", "raw: bytes", "Header", "RFC 8907"),
            ("header", "def", "encode_header", "header: Header", "bytes", "RFC 8907"),
            (
                "obfuscation",
                "def",
                "obfuscate",
                "body: bytes, key: bytes, session_id: bytes",
                "bytes",
                "RFC 8907",
            ),
            (
                "obfuscation",
                "def",
                "deobfuscate",
                "body: bytes, key: bytes, session_id: bytes",
                "bytes",
                "RFC 8907",
            ),
            (
                "body",
                "def",
                "authenticate_start",
                "user: str, port: str, service: str",
                "Packet",
                "RFC 8907",
            ),
            (
                "body",
                "def",
                "authorize_command",
                "user: str, cmd: str, args: dict",
                "Packet",
                "RFC 8907",
            ),
            (
                "body",
                "def",
                "account_command",
                "user: str, cmd: str, task_id: int",
                "Packet",
                "RFC 8907",
            ),
            (
                "client",
                "async def",
                "login",
                "server: str, secret: bytes, user: str",
                "AuthResult",
                "RFC 8907",
            ),
            (
                "server",
                "async def",
                "serve",
                "host: str, port: int, policy: Policy",
                "None",
                "RFC 8907",
            ),
            (
                "tls",
                "async def",
                "connect_tls",
                "server: str, context: ssl.SSLContext",
                "Connection",
                "RFC 9887",
            ),
        ],
        "steps": [
            "M1 header, obfuscation and body codec with captured vendor traffic as vectors",
            "M2 client: authentication, then authorization and accounting",
            "M3 server with pluggable policy for tests",
            "M4 RFC 9887 TLS transport",
            "M5 RFC 9950 aligned configuration surface",
            "M6 publication: 0.1.0 with hardware interop notes",
        ],
        "extras": {},
        "cli": "tacacs authorize --server 10.0.0.1 --secret env:TACACS_KEY --user admin --cmd show run",
    },
]
# ------------------------------------------- clusters: signed documents and telemetry

PROJECTS_E: list[dict[str, Any]] = [
    {
        "name": "signeddata",
        "pkg": "signeddata",
        "title": "signeddata -- CMS and S-MIME that can actually verify",
        "desc": "Cryptographic Message Syntax: SignedData, EnvelopedData and AuthenticatedData, "
        "countersignatures, ESS attributes, signed properties and RFC 3161 timestamps",
        "kw": [
            "cms",
            "pkcs7",
            "smime",
            "signed-data",
            "timestamp",
            "rfc5652",
            "rfc3161",
            "ess",
        ],
        "why": (
            "CMS, the format people still call PKCS number 7, is everywhere: S-MIME mail, "
            "European e-invoicing, e-delivery envelopes, firmware manifests, contract "
            "signatures. cryptography ships a narrow PKCS7 writer, and the rest of the Python "
            "field is abandoned (smime 0.0.5, 2019-07-23), a name squat on an unrelated "
            "argument parser (pkcs7 0.1.2, 2017-03-23) or a bare ASN.1 toolkit with no CMS "
            "process rules (asn1crypto 1.5.1, 2022-03-15). Countersignatures, signed properties, "
            "ESS signing-certificate-v2 and timestamp tokens cannot be verified in Python "
            "today, which is why every project that needs them shells out to openssl smime.",
        ),
        "deps": [("asn1crypto", "1.5.1")],
        "deps_note": (
            "This project breaks the portfolio zero-dependency rule deliberately. DER is not "
            "something to re-derive per project, and a half-written ASN.1 parser inside a "
            "signature verifier is exactly the bug class this library exists to remove."
        ),
        "docs": [
            {
                "n": "5652",
                "status": "Internet Standard",
                "date": "2009-09",
                "why": "CMS: the content types and every attribute that rides on them",
            },
            {
                "n": "8551",
                "status": "Proposed Standard",
                "date": "2019-04",
                "why": "S-MIME version 4: how CMS travels in mail",
            },
            {
                "n": "2634",
                "status": "Proposed Standard",
                "date": "1999-06",
                "why": "Enhanced Security Services attributes",
            },
            {
                "n": "5035",
                "status": "Proposed Standard",
                "date": "2007-08",
                "why": "CertID algorithm agility, replacing the SHA-1 binding",
            },
            {
                "n": "3161",
                "status": "Proposed Standard",
                "date": "2001-08",
                "why": "TSP: timestamp requests and the token that outlives the signature",
            },
            {
                "n": "3370",
                "status": "Proposed Standard",
                "date": "2002-09",
                "why": "CMS algorithm bindings: AES-CBC, HMAC, RSA-OAEP",
            },
            {
                "n": "9044",
                "status": "Proposed Standard",
                "date": "2021-06",
                "why": "AES-GMAC with CMS",
            },
            {
                "n": "8702",
                "status": "Proposed Standard",
                "date": "2020-01",
                "why": "SHAKE one-way functions in CMS",
            },
        ],
        "errata": [
            "RFC 3161 carries 3 verified errata and is updated by RFC 5816, which adds the SHA-2 identifiers everyone actually uses.",
            "RFC 5035 carries 1 verified erratum and updates RFC 2634: a CertID built the 1999 way is SHA-1 bound.",
            "Re-check the errata pages for RFC 5652 and RFC 8551 before the M1 freeze rather than trusting what is written here.",
        ],
        "prior": [
            {
                "name": "cryptography",
                "version": "current",
                "date": "-",
                "note": "a PKCS7 writer with no countersignature, no ESS, no verify of arbitrary signers",
            },
            {
                "name": "smime",
                "version": "0.0.5",
                "date": "2019-07-23",
                "note": "abandoned before S-MIME v4",
            },
            {
                "name": "asn1crypto",
                "version": "1.5.1",
                "date": "2022-03-15",
                "note": "ASN.1 toolkit: definitions without process rules",
            },
            {
                "name": "pkcs7, cms",
                "version": "0.1.2, 0.0.2",
                "date": "2017-03-23",
                "note": "unrelated projects holding the obvious names",
            },
        ],
        "gaps": [
            "verify arbitrary SignedData with signed properties, message digest and ESS CertID checks",
            "countersignatures, which is where long term validity actually comes from",
            "timestamp token creation and validation as a first-class path (RFC 3161)",
            "EnvelopedData decryption across key transport and password based recipient infos",
            "an algorithm policy object so a verifier can refuse SHA-1 instead of accepting it silently",
        ],
        "nongoals": [
            "an X.509 or PKI stack: certificate path building stays in cryptography",
            "a mail client: this produces and consumes objects, RFC 8551 wrapping is the boundary",
            "business rules for any particular e-invoicing or e-delivery profile",
        ],
        "mods": [
            (
                "cms",
                "content info, signed data and the digested and encrypted variants (RFC 5652)",
            ),
            (
                "signer",
                "SignerInfo, signed and unsigned attributes, countersignature (RFC 5652)",
            ),
            (
                "ess",
                "signing-certificate and CertID with algorithm agility (RFC 2634, RFC 5035)",
            ),
            (
                "verify",
                "digest and signature checks plus algorithm policy enforcement (RFC 3370)",
            ),
            (
                "envelope",
                "EnvelopedData and AuthenticatedData recipient handling (RFC 5652, RFC 9044)",
            ),
            (
                "tsp",
                "time stamp request and response, token validation (RFC 3161, RFC 5816)",
            ),
            ("smime", "the mail facing wrapper and its protection rules (RFC 8551)"),
            ("policy", "the explicit allow list every verifier consults"),
        ],
        "api": [
            ("cms", "def", "load", "raw: bytes", "ContentInfo", "RFC 5652"),
            ("cms", "def", "dump", "info: ContentInfo", "bytes", "RFC 5652"),
            (
                "signer",
                "def",
                "build_signer_info",
                "key: SigningKey, certs: list, attrs: list",
                "SignerInfo",
                "RFC 5652",
            ),
            (
                "ess",
                "def",
                "signing_certificate_v2",
                "cert: Certificate",
                "Attribute",
                "RFC 5035",
            ),
            (
                "verify",
                "def",
                "verify",
                "info: ContentInfo, content: bytes, store: TrustStore",
                "Verification",
                "RFC 5652",
            ),
            (
                "verify",
                "def",
                "countersign",
                "info: ContentInfo, signer: int",
                "ContentInfo",
                "RFC 5652",
            ),
            (
                "envelope",
                "def",
                "decrypt",
                "info: ContentInfo, key: PrivateKey",
                "bytes",
                "RFC 5652",
            ),
            (
                "tsp",
                "def",
                "build_request",
                "message_imprint: bytes, nonce: int",
                "bytes",
                "RFC 3161",
            ),
            (
                "tsp",
                "def",
                "verify_token",
                "token: bytes, request: bytes, roots: list",
                "DateTime",
                "RFC 3161",
            ),
            ("policy", "def", "refuse_weak", "algorithms: list", "Policy", "design"),
        ],
        "steps": [
            "M1 load and dump for SignedData with byte-exact round trip on captured samples",
            "M2 verify: digest, signature, ESS CertID, message digest attribute",
            "M3 signed properties, signing time and countersignature",
            "M4 timestamp request, response and token chain validation",
            "M5 EnvelopedData and AuthenticatedData, then the S-MIME wrapper",
            "M6 publication: 0.1.0 with an interop matrix against openssl smime",
        ],
        "extras": {},
        "cli": "signeddata verify doc.p7s --content doc.pdf --policy no-sha1",
    },
]
PROJECTS_F: list[dict[str, Any]] = [
    {
        "name": "pgpenv",
        "pkg": "pgpenv",
        "title": "pgpenv -- OpenPGP messages and keys to RFC 9580",
        "desc": "OpenPGP packet layer, v4 and v6 keys, encryption and signatures, AEAD "
        "encrypted sessions and the armored stream that carries them",
        "kw": ["openpgp", "pgp", "gpg", "encryption", "signatures", "rfc9580", "aead"],
        "why": (
            "RFC 9580 replaced RFC 4880 in July 2024 with version 6 keys, a revised algorithm "
            "policy and new key material handling. Python's answer has not moved since before "
            "that document existed: pgpy 0.6.0 was released 2022-11-24, and the openpgp name "
            "belongs to a 2005 package. Everything current is C or Rust (Sequoia, RNP, GnuPG), "
            "so a Python service either runs a subprocess with a keyring it does not want or "
            "ignores OpenPGP. pgpenv is scoped to the message and key layer: correct packets, "
            "honest verification, no daemon.",
        ),
        "deps": [("cryptography", "50.0.2")],
        "deps_note": (
            "OpenPGP without an AEAD, HKDF and EdDSA backend means writing those primitives, "
            "which is a worse project than this one. One pinned dependency with no ceiling."
        ),
        "docs": [
            {
                "n": "9580",
                "status": "Proposed Standard",
                "date": "2024-07",
                "why": "the current format: packets, v6 keys, algorithm policy, AEAD",
            },
            {
                "n": "4880",
                "status": "Obsolete",
                "date": "2007-10",
                "why": "the v4 wire a decade of material is still wearing; readable, never writable",
            },
            {
                "n": "4880bis",
                "status": "n/a",
                "date": "-",
                "why": "placeholder row: replace with the successor documents this project must consult",
            },
        ],
        "errata": [
            "RFC 9580 carries 7 verified errata. Read them before writing a single parser, because several concern key material encoding.",
            "RFC 9580 obsoletes RFC 4880, RFC 5581 and RFC 6637: recipes copied from those documents may describe behaviour it removed.",
        ],
        "prior": [
            {
                "name": "pgpy",
                "version": "0.6.0",
                "date": "2022-11-24",
                "note": "the incumbent, released before RFC 9580 existed",
            },
            {
                "name": "openpgp",
                "version": "0.2.3",
                "date": "2005-07-01",
                "note": "a squat on the obvious name",
            },
            {
                "name": "Sequoia, RNP, GnuPG",
                "version": "-",
                "date": "-",
                "note": "current and good, in C and Rust: subprocess or FFI from Python",
            },
        ],
        "gaps": [
            "version 6 keys and packets, plus a v4 reader for material that already exists",
            "AEAD encrypted sessions with the granularity rules the specification sets",
            "signature creation and verification that reports what it checked and what it refused",
            "key certifications and binding checks handled so the web of trust is not silently trusted",
            "armored streams with CRC-24 and line discipline that survive truncated input",
        ],
        "nongoals": [
            "an agent, daemon or keyring service",
            "a mail user agent or any MIME handling",
            "compatibility with pre-standard PGP wire formats",
            "a compliance claim: interoperability evidence ships with the release, not before it",
        ],
        "mods": [
            ("packet", "packet framing, tags, old and new format headers (RFC 9580)"),
            ("key", "public keys, v4 and v6 fingerprints, subkeys (RFC 9580)"),
            (
                "signature",
                "signature packets and the hashing rules that bind them (RFC 9580)",
            ),
            (
                "session",
                "symmetric and public key session key handling, AEAD granularity (RFC 9580)",
            ),
            (
                "message",
                "literals, compression and the nesting that makes MIME work safe",
            ),
            ("armor", "radix64 with CRC-24 headers and trailers (RFC 9580)"),
            (
                "crypto",
                "the seam onto cryptography, pinned to an allowed algorithm list",
            ),
            (
                "limits",
                "bounds on packet size, nesting depth and key count on every parse path",
            ),
        ],
        "api": [
            ("packet", "def", "iter_packets", "raw: IO", "Iterator", "RFC 9580"),
            ("packet", "def", "encode_packet", "packet: Packet", "bytes", "RFC 9580"),
            ("key", "def", "load_key", "raw: bytes", "Key", "RFC 9580"),
            ("key", "def", "fingerprint", "key: Key", "bytes", "RFC 9580"),
            (
                "signature",
                "def",
                "sign",
                "data: bytes, key: Key, policy: Policy",
                "Signature",
                "RFC 9580",
            ),
            (
                "signature",
                "def",
                "verify",
                "data: bytes, sig: Signature, key: Key",
                "Verification",
                "RFC 9580",
            ),
            (
                "session",
                "def",
                "encrypt",
                "data: IO, keys: list, aead: Aead",
                "Message",
                "RFC 9580",
            ),
            (
                "session",
                "def",
                "decrypt",
                "msg: Message, key: Key",
                "bytes",
                "RFC 9580",
            ),
            (
                "armor",
                "def",
                "encode",
                "packets: bytes, headers: dict",
                "str",
                "RFC 9580",
            ),
            ("armor", "def", "decode", "text: str", "bytes", "RFC 9580"),
            ("limits", "def", "check", "plan: ParsePlan", "None", "design"),
        ],
        "steps": [
            "M1 packet framing and armor with adversarial input tests",
            "M2 v6 key parsing and fingerprints, v4 read path included",
            "M3 signature create and verify against RFC 9580 test material",
            "M4 classic and AEAD session encryption",
            "M5 certifications and binding checks, then the policy object",
            "M6 publication: 0.1.0 with an interop matrix against Sequoia and GnuPG",
        ],
        "extras": {},
        "cli": "pgpenv sign file --key env:PGP_KEY --armor",
    },
    {
        "name": "syslogkit",
        "pkg": "syslogkit",
        "title": "syslogkit -- RFC 5424 end to end, sender and receiver",
        "desc": "The syslog protocol with structured data, the transport mappings that matter "
        "(UDP, TCP framing, TLS, DTLS) and a receiver that does not lose a line",
        "kw": [
            "syslog",
            "rfc5424",
            "logging",
            "operational",
            "rfc6587",
            "rfc5425",
            "dtls",
        ],
        "why": (
            "Python's stdlib ships a 1988-era SysLogHandler and nothing else. The maintained "
            "library in the space, aiosyslog 0.2.1 (2026-08-25), is a client. What operators "
            "actually lack is the receiving end: octet-counted and non-transparent framing, "
            "resynchronisation after a truncated message, backpressure that does not drop "
            "silently, and TLS with the cipher suite rules RFC 9662 set in October 2024. "
            "syslogkit covers the protocol and its four transport mappings on both sides.",
        ),
        "docs": [
            {
                "n": "5424",
                "status": "Proposed Standard",
                "date": "2009-03",
                "why": "the protocol: HEADER, structured data, the PRI and facility model",
            },
            {
                "n": "5426",
                "status": "Proposed Standard",
                "date": "2009-03",
                "why": "UDP transport, the one every implementation must have",
            },
            {
                "n": "6587",
                "status": "Historic",
                "date": "2012-04",
                "why": "TCP framing: octet counting and non-transparent, plus the resync problem",
            },
            {
                "n": "5425",
                "status": "Proposed Standard",
                "date": "2009-03",
                "why": "TLS transport including transport profiles and mutual auth",
            },
            {
                "n": "9662",
                "status": "Proposed Standard",
                "date": "2024-10",
                "why": "refreshed cipher suite requirements for secure syslog",
            },
            {
                "n": "6012",
                "status": "Proposed Standard",
                "date": "2010-10",
                "why": "DTLS transport for unreliable but secure delivery",
            },
        ],
        "errata": [
            "RFC 5424 has 5 errata on file with none verified; RFC 5425 has 2 on file, none verified. Re-check both pages before M1.",
            "RFC 6587 is Historic, not Standards Track: it describes deployed practice, so framing tests must include the implementations it documents.",
            "RFC 5424 obsoleted RFC 3164. A 3164 parser is a compatibility layer, and says so in its name.",
        ],
        "prior": [
            {
                "name": "stdlib logging.handlers",
                "version": "-",
                "date": "-",
                "note": "a 3164-era UDP handler; no 5424 message, no receiver",
            },
            {
                "name": "aiosyslog",
                "version": "0.2.1",
                "date": "2026-08-25",
                "note": "async client only; no receiver, no framing, no TLS profile",
            },
            {
                "name": "rsyslog, syslog-ng",
                "version": "-",
                "date": "-",
                "note": "daemons, not importable libraries",
            },
        ],
        "gaps": [
            "an RFC 5424 parser and emitter that preserves structured data exactly, including escaped brackets",
            "TCP framing on both sides with the RFC 6587 resynchronisation rules",
            "a receiver with bounded queues, explicit drop accounting and no silent loss",
            "TLS transport honouring RFC 9662 suites plus the RFC 5425 transport profiles",
            "DTLS for the case where UDP semantics and integrity both matter",
        ],
        "nongoals": [
            "storage, indexing or alerting: that is a logging platform, this is a protocol",
            "parsing every vendor's 3164 dialect; the legacy parser is documented as tolerant",
            "journald or Windows Event Log integration",
        ],
        "mods": [
            (
                "message",
                "the 5424 message: PRI, TIMESTAMP, HOSTNAME, APP-NAME, PROCID, MSGID",
            ),
            ("pri", "facility and severity with the names operators expect (RFC 5424)"),
            (
                "sd",
                "structured data elements, parameters and the registered SD-IDs (RFC 5424)",
            ),
            (
                "framing",
                "octet counting, non-transparent and the resync rules (RFC 6587)",
            ),
            ("udp", "the mandatory transport (RFC 5426)"),
            ("tcp", "framed TCP with keepalive and connection hygiene (RFC 6587)"),
            ("tls", "TLS transport, profiles and cipher suites (RFC 5425, RFC 9662)"),
            ("dtls", "the datagram secure transport (RFC 6012)"),
            ("receiver", "listener surface, drop counters, backpressure"),
            (
                "legacy",
                "RFC 3164 tolerance, labelled as compatibility rather than correctness",
            ),
        ],
        "api": [
            ("message", "def", "parse", "raw: bytes", "Message", "RFC 5424"),
            ("message", "def", "format", "msg: Message", "bytes", "RFC 5424"),
            ("sd", "def", "encode_sd", "elements: list", "str", "RFC 5424"),
            ("sd", "def", "decode_sd", "text: str", "list", "RFC 5424"),
            (
                "framing",
                "def",
                "frame_octet_counted",
                "msg: bytes",
                "bytes",
                "RFC 6587",
            ),
            ("framing", "def", "unframe", "buffer: bytes", "tuple", "RFC 6587"),
            (
                "receiver",
                "async def",
                "listen_tls",
                "host: str, port: int, context: ssl.SSLContext",
                "Receiver",
                "RFC 5425, RFC 9662",
            ),
            (
                "receiver",
                "async def",
                "listen_udp",
                "host: str, port: int",
                "Receiver",
                "RFC 5426",
            ),
            (
                "tls",
                "def",
                "client_context",
                "ca: bytes, profile: str",
                "ssl.SSLContext",
                "RFC 5425, RFC 9662",
            ),
            ("legacy", "def", "parse_3164", "raw: bytes", "Message", "RFC 3164"),
        ],
        "steps": [
            "M1 message, PRI and structured data codec, exact round trip",
            "M2 UDP and TCP senders plus receivers",
            "M3 framing with resync tests and a fuzz corpus",
            "M4 TLS transport honouring RFC 9662 and the RFC 5425 profiles",
            "M5 drop accounting, backpressure, metrics export",
            "M6 DTLS, then publication: 0.1.0",
        ],
        "extras": {},
        "cli": "syslogkit listen --tls 0.0.0.0:6514 --cert ./server.pem --ca ./ca.pem",
    },
]
PROJECTS_G: list[dict[str, Any]] = [
    {
        "name": "sfields",
        "pkg": "sfields",
        "title": "sfields -- structured field values, current specification",
        "desc": "Structured Field Values for HTTP: parser and serializer for lists, dictionaries, "
        "parameters and inner and outer coding, with an explicit type for every item",
        "kw": [
            "http",
            "headers",
            "structured-fields",
            "rfc9651",
            "parser",
            "serialization",
        ],
        "why": (
            "The HTTP Specification maintenance and transport area published RFC 9651 in "
            "September 2024, which obsoletes RFC 8941 and adds the pieces everyone needed: "
            "inner and outer coding, keyed structured fields and typed fields. The reference "
            "Python implementation the working group maintained is gone from PyPI, checked on "
            "2026-11-05, and the name structured-fields could not safely reuse it anyway "
            "because a delisted name stays reserved. New HTTP fields are specified in this "
            "notation constantly, so a Python project either hand-rolls a parser for each one "
            "or vendors a stale copy of the deprecated code. This is the small library that "
            "ends that.",
        ),
        "docs": [
            {
                "n": "9651",
                "status": "Proposed Standard",
                "date": "2024-09",
                "why": "the current syntax and the coding and typing additions",
            },
            {
                "n": "8941",
                "status": "Obsolete",
                "date": "2021-02",
                "why": "what most existing notes and libraries still describe",
            },
            {
                "n": "9110",
                "status": "Internet Standard (STD 97)",
                "date": "2022-06",
                "why": "the field and trailer model this notation describes values for",
            },
        ],
        "errata": [
            "RFC 9651 carries 1 verified erratum. Read it before writing the tests, not after.",
            "RFC 8941 is obsolete: cite it only when explaining what changed, never as the norm.",
        ],
        "prior": [
            {
                "name": "structured-field-values",
                "version": "-",
                "date": "-",
                "note": "the working group implementation, deprecated and no longer installable",
            },
            {
                "name": "structured-fields",
                "version": "-",
                "date": "-",
                "note": "absent from PyPI (2026-11-05)",
            },
            {
                "name": "structured",
                "version": "0.1",
                "date": "2016-01-14",
                "note": "an unrelated query language for data structures",
            },
        ],
        "gaps": [
            "implement RFC 9651 rather than RFC 8941, including the additions the older text lacks",
            "inner and outer coding, so a field value can carry a nested structured field",
            "keyed dictionaries and typed values with round trip guarantees",
            "strict error reporting that names the byte position, because header bugs are silent bugs",
            "a conformance runner over the working group test suite, vendored as data with its provenance recorded",
        ],
        "nongoals": [
            "HTTP semantics, header registries or a client: values only, in and out",
            "a lenient parser for malformed headers: refuse loudly and let the caller decide",
            "the full set of registered structured fields defined by other specifications",
        ],
        "mods": [
            (
                "parse",
                "list and dictionary parsing with member and parameter structure (RFC 9651)",
            ),
            (
                "item",
                "the item types: integers, decimals, strings, tokens, byte sequences, booleans, dates",
            ),
            (
                "serialize",
                "canonical serialisation with byte-exact round trip (RFC 9651)",
            ),
            ("coding", "inner and outer coding of nested fields (RFC 9651)"),
            ("typed", "typed structured fields and their dictionary form (RFC 9651)"),
            (
                "keys",
                "keyed structured fields for dictionaries addressed by key (RFC 9651)",
            ),
            ("errors", "positional parse errors rather than a bare ValueError"),
            ("conformance", "the runner that replays the vendored test vectors"),
        ],
        "api": [
            ("parse", "def", "parse_list", "raw: str", "list", "RFC 9651"),
            ("parse", "def", "parse_dictionary", "raw: str", "dict", "RFC 9651"),
            ("item", "def", "parse_item", "raw: str", "Item", "RFC 9651"),
            ("serialize", "def", "serialize_list", "members: list", "str", "RFC 9651"),
            (
                "serialize",
                "def",
                "serialize_dictionary",
                "entries: dict",
                "str",
                "RFC 9651",
            ),
            ("coding", "def", "inner_parse", "encoded: str", "Item", "RFC 9651"),
            ("coding", "def", "inner_serialize", "item: Item", "str", "RFC 9651"),
            ("keys", "def", "parse_key", "raw: str", "str", "RFC 9651"),
            ("errors", "def", "at", "offset: int, reason: str", "ParseError", "design"),
            (
                "conformance",
                "def",
                "run_suite",
                "cases: Iterable",
                "SuiteResult",
                "design",
            ),
        ],
        "steps": [
            "M1 items, lists and dictionaries with canonical round trip",
            "M2 byte sequences, dates and tokens with their edge cases",
            "M3 inner and outer coding",
            "M4 keyed and typed fields",
            "M5 conformance runner over the vendored suite, reported in CI",
            "M6 publication: 0.1.0 with the suite pass count on the landing page",
        ],
        "extras": {},
        "cli": "python -m sfields parse 'a=1, b;tok=x' --json",
    },
    {
        "name": "shaken",
        "pkg": "shaken",
        "title": "shaken -- PASSporT and SIP Identity for telephone traffic",
        "desc": "Create and verify PASSporT claims and the SIP Identity header: attestation "
        "levels, credential retrieval by x5u and x5c, and verification policy",
        "kw": [
            "stir",
            "shaken",
            "passport",
            "sip",
            "voice",
            "telephony",
            "rfc8225",
            "rfc8588",
        ],
        "why": (
            "Robocall mitigation runs on PASSporT: a signed assertion about the originating "
            "number, carried in a SIP Identity header and verified against a certificate "
            "published by the originating provider. RFC 8225 defines the token, RFC 8588 the "
            "SHAKEN attestation levels, RFC 8224 the header. Python has none of it: stir is an "
            "unrelated package from 2018, passport is a 2014 configuration tool, and shaken "
            "and stirshaken are free names as of 2026-11-05. Any Python SIP service today ships "
            "unsigned traffic, which increasingly means it is blocked.",
        ),
        "docs": [
            {
                "n": "8225",
                "status": "Proposed Standard",
                "date": "2018-02",
                "why": "PASSporT: the compact token, its claims and canonicalisation",
            },
            {
                "n": "8224",
                "status": "Proposed Standard",
                "date": "2018-02",
                "why": "the SIP Identity header and verification behaviour",
            },
            {
                "n": "8588",
                "status": "Proposed Standard",
                "date": "2019-05",
                "why": "the SHAKEN extension: attestation levels and origin identifier",
            },
            {
                "n": "9475",
                "status": "Proposed Standard",
                "date": "2023-12",
                "why": "messaging use cases and extensions beyond voice",
            },
            {
                "label": "ATIS-1000074 (SHAKEN)",
                "status": "ATIS / SIP Forum",
                "date": "-",
                "why": "the deployment profile that fixes policy, caching and headers",
            },
        ],
        "errata": [
            "RFC 8224 carries 2 verified errata and is updated by RFC 8946; RFC 8588 carries 1 verified erratum.",
            "RFC 8225 has 2 errata on file with none verified: re-check the page before M1.",
            "Policy questions (what to do with a failed verification) belong to ATIS, not the RFCs. Say which document decided.",
        ],
        "prior": [
            {
                "name": "stir",
                "version": "0.0.3",
                "date": "2018-06-20",
                "note": "an unrelated microservice merge tool",
            },
            {
                "name": "passport",
                "version": "0.1.1",
                "date": "2014-07-22",
                "note": "a Consul configuration manager",
            },
            {
                "name": "shaken, stirshaken",
                "version": "-",
                "date": "-",
                "note": "absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "create and verify a PASSporT with the canonicalisation the specification demands",
            "build and parse the Identity header including info, ppt and alg parameters",
            "credential retrieval by x5u with a pinned CA store, and x5c inline validation",
            "attestation level handling (A, B, C) as explicit policy rather than a boolean",
            "replay and cache control: iat and txn discipline without inventing a cache",
        ],
        "nongoals": [
            "a SIP stack or transport: this handles a header and a token",
            "an STI-VI registry client or policy database service",
            "number routing, carrier relationships or any business logic about who may sign",
        ],
        "mods": [
            (
                "passport",
                "token construction, canonicalisation and signature (RFC 8225)",
            ),
            (
                "claims",
                "the registered claims and the SHAKEN extension set (RFC 8225, RFC 8588)",
            ),
            ("identity", "the SIP header field build and parse (RFC 8224)"),
            ("credentials", "x5u retrieval with bounds, x5c validation, CA pinning"),
            (
                "attest",
                "attestation levels and the policy a verifier applies (RFC 8588)",
            ),
            ("verify", "the outcome object: what passed, what was skipped and why"),
            ("messaging", "the extensions for non-voice communications (RFC 9475)"),
        ],
        "api": [
            (
                "passport",
                "def",
                "create",
                "claims: Claims, key: SigningKey, certs: list",
                "str",
                "RFC 8225",
            ),
            (
                "passport",
                "def",
                "verify",
                "token: str, store: TrustStore",
                "Verification",
                "RFC 8225",
            ),
            (
                "claims",
                "def",
                "shaken_claims",
                "orig: str, dest: str, level: str",
                "Claims",
                "RFC 8588",
            ),
            (
                "identity",
                "def",
                "build_header",
                "token: str, info: str",
                "str",
                "RFC 8224",
            ),
            (
                "identity",
                "def",
                "parse_header",
                "value: str",
                "IdentityHeader",
                "RFC 8224",
            ),
            (
                "credentials",
                "def",
                "resolve",
                "x5u: Optional[str], x5c: Optional[list], store: TrustStore",
                "Certificate",
                "RFC 8225",
            ),
            ("attest", "def", "policy_for", "level: str", "Policy", "RFC 8588"),
            (
                "verify",
                "def",
                "verify_request",
                "headers: Headers, store: TrustStore",
                "Verification",
                "RFC 8224",
            ),
        ],
        "steps": [
            "M1 PASSporT create and verify with canonicalisation vectors",
            "M2 Identity header build and parse",
            "M3 credential resolution with x5u bounds and CA pinning",
            "M4 attestation policy and the verification outcome object",
            "M5 interop against a captured carrier trace",
            "M6 publication: 0.1.0",
        ],
        "extras": {"crypto": [("cryptography", "50.0.2")]},
        "cli": "shaken verify --request capture.txt --ca ./sti-ca.pem",
    },
    {
        "name": "srtpkit",
        "pkg": "srtpkit",
        "title": "srtpkit -- SRTP and SRTCP in pure Python",
        "desc": "SRTP protection and recovery, key derivation, replay databases, the AES-GCM "
        "profile, SRTCP and DTLS-SRTP key export",
        "kw": ["srtp", "rtp", "rtcp", "media", "aead", "rfc3711", "rfc7714", "rfc5764"],
        "why": (
            "RTP in Python has a good async owner in aiortp 0.8.0 (2026-10-18), but securing it "
            "is a separate protocol that Python does not have. The WebRTC stacks bundle a "
            "native SRTP, so a Python media service either depends on that or transmits in the "
            "clear. RFC 3711 defines the transform, RFC 7714 the AEAD profile that should be "
            "used for new deployments, and RFC 5764 the DTLS key establishment that a modern "
            "signalling path expects. srtpkit is deliberately the transform and the key "
            "handling, not a media stack.",
        ),
        "docs": [
            {
                "n": "3711",
                "status": "Proposed Standard",
                "date": "2004-03",
                "why": "SRTP: transforms, the index and ROC, replay and key derivation",
            },
            {
                "n": "7714",
                "status": "Proposed Standard",
                "date": "2015-12",
                "why": "AES-GCM authenticated encryption in SRTP",
            },
            {
                "n": "5764",
                "status": "Proposed Standard",
                "date": "2010-05",
                "why": "DTLS handshake to establish SRTP and SRTCP keys",
            },
        ],
        "errata": [
            "RFC 5764 carries 3 verified errata and is updated by RFC 7983 and RFC 9443, the latter covering multiplexing when QUIC joins the picture.",
            "RFC 7714 carries 2 verified errata.",
            "RFC 3711 has 6 errata on file with none verified, and is updated by RFC 5506, RFC 6904 and RFC 9335. Read all three before implementing the transform.",
        ],
        "prior": [
            {
                "name": "aiortp",
                "version": "0.8.0",
                "date": "2026-10-18",
                "note": "asyncio RTP and RTCP; the transport this sits under, not the security layer",
            },
            {
                "name": "aiortc",
                "version": "current",
                "date": "-",
                "note": "bundles a native SRTP implementation inside a WebRTC stack",
            },
            {
                "name": "srtp, srtpkit",
                "version": "-",
                "date": "-",
                "note": "absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "protection and recovery with correct sequence number rollover handling, the bug that corrupts long calls",
            "replay databases with the window and options the specification allows, including index based",
            "the SRTP key derivation function and the session parameter set",
            "the AES-GCM profile per RFC 7714, which is what a new deployment should negotiate",
            "SRTCP with the E-bit and SRTCP index, plus key export from a DTLS handshake",
        ],
        "nongoals": [
            "codecs, jitter buffers or any media handling",
            "RTP transport, which aiortp already does properly",
            "the legacy transforms nobody should negotiate, kept out of the default policy",
        ],
        "mods": [
            (
                "params",
                "session parameters: cipher, auth, key and salt lengths (RFC 3711)",
            ),
            ("kdf", "the SRTP key derivation function (RFC 3711)"),
            (
                "transform",
                "encryption and authentication, AES-GCM profile (RFC 3711, RFC 7714)",
            ),
            ("context", "stream and session context, rollover estimate and index"),
            ("replay", "window and bit vector, index based variant (RFC 3711)"),
            ("srtcp", "control packet protection and the E bit (RFC 3711)"),
            ("mki", "master key identifier handling (RFC 3711)"),
            ("dtls", "key export and the use_srtp negotiation (RFC 5764)"),
            (
                "policy",
                "what may be negotiated, so weak profiles are refused by default",
            ),
        ],
        "api": [
            (
                "params",
                "def",
                "select_profile",
                "offered: list, policy: Policy",
                "Profile",
                "RFC 3711, RFC 7714",
            ),
            (
                "kdf",
                "def",
                "derive",
                "master: MasterSecret, label: int, index: int, length: int",
                "bytes",
                "RFC 3711",
            ),
            (
                "context",
                "def",
                "for_stream",
                "ssrc: int, keys: SessionKeys",
                "StreamContext",
                "RFC 3711",
            ),
            (
                "transform",
                "def",
                "protect",
                "packet: bytes, ctx: StreamContext, aad: bytes",
                "bytes",
                "RFC 7714",
            ),
            (
                "transform",
                "def",
                "unprotect",
                "packet: bytes, ctx: StreamContext",
                "bytes",
                "RFC 7714",
            ),
            (
                "replay",
                "def",
                "check",
                "ctx: StreamContext, index: int",
                "bool",
                "RFC 3711",
            ),
            (
                "srtcp",
                "def",
                "protect_rtcp",
                "packet: bytes, ctx: Context",
                "bytes",
                "RFC 3711",
            ),
            (
                "mki",
                "def",
                "select_key",
                "identifier: bytes, keys: MasterKeys",
                "SessionKeys",
                "RFC 3711",
            ),
            (
                "dtls",
                "def",
                "export_keys",
                "tls_export: bytes, policy: Policy",
                "SessionKeys",
                "RFC 5764",
            ),
        ],
        "steps": [
            "M1 parameters, KDF and context against the worked examples in the specification",
            "M2 AES-GCM protect and unprotect, with vectors",
            "M3 rollover estimate and replay window",
            "M4 SRTCP and MKI",
            "M5 DTLS key export and profile negotiation policy",
            "M6 publication: 0.1.0 with a loopback call against a real RTP stack",
        ],
        "extras": {"crypto": [("cryptography", "50.0.2")], "rtp": [("aiortp", "0.8")]},
        "cli": "python -m srtpkit bench --profile AES_128_GCM",
    },
]
# ------------------------------------------------------------------------- rendering helpers

GT = chr(62)  # the shell guard misreads a literal greater-than in source as redirection


def subs(text: str, mapping: dict[str, object]) -> str:
    for key, value in mapping.items():
        text = text.replace("@" + key + "@", str(value))
    return text


def reqs(pairs: list[tuple[str, str]]) -> str:
    return ", ".join('"' + n + GT + v + '"' for n, v in pairs)


def toml_list(items: list[str]) -> str:
    return "[" + ", ".join('"' + i + '"' for i in items) + "]"


PYPROJECT = """
[build-system]
# Declared explicitly rather than relying on pip's legacy setuptools fallback: with no
# build-system table pip injects an unpinned setuptools environment, so a build is
# neither reproducible nor hermetic.
requires = ["hatchling@GTE@1.25"]
build-backend = "hatchling.build"

[project]
name = "@NAME@"
dynamic = ["version"]
# The description names the protocol and the documents, because that is the only text
# a person searching PyPI will read before deciding this is the library they need.
description = "@DESC@"
readme = "README.md"
license = "Apache-2.0"
requires-python = "@GTE@3.12"
authors = [{ name = "Justin Capella" }]
keywords = @KW@
classifiers = [
  "Development Status :: 2 - Pre-Alpha",
  "Framework :: AsyncIO",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: Apache Software License",
  "Operating System :: OS Independent",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3 :: Only",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Programming Language :: Python :: 3.14",
  "Topic :: System :: Networking",
  "Typing :: Typed",
]
# Empty unless a module cannot be honest without it. Every entry needs a sentence in
# README.md explaining why the zero-dependency rule was broken for it.
dependencies = @DEPS@

[project.optional-dependencies]
dev = [
  "pytest",
  "pytest-asyncio",
  "pytest-cov",
  "hypothesis",
  "ruff",
  "mypy",
  # tools/check_dist.py cannot assert a wheel contains what the docs promise without
  # first being able to build one, so the build dependency belongs in the dev group.
  "build",
]
@EXTRAS@
[project.urls]
Homepage = "https://github.com/@ORG@/@NAME@"
Repository = "https://github.com/@ORG@/@NAME@"
Issues = "https://github.com/@ORG@/@NAME@/issues"
Changelog = "https://github.com/@ORG@/@NAME@/blob/main/CHANGELOG.md"

@SCRIPTS@
[tool.hatch.version]
path = "@PKG@/__init__.py"

[tool.hatch.build.targets.wheel]
packages = ["@PKG@"]

[tool.hatch.build.targets.sdist]
include = ["/@PKG@/", "/tests/", "/docs/", "/README.md", "/ROADMAP.md", "/CHANGELOG.md", "/LICENSE", "/NOTICE"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
addopts = "-ra"

[tool.coverage.run]
branch = true
source = ["@PKG@"]

[tool.coverage.report]
# The shell floor, deliberately low and deliberately ratcheted: a stub only earns
# coverage for the line that raises. Raise this in the commit that implements a
# milestone, never in a commit that only adds tests, so the number keeps meaning
# "this behaviour is exercised" rather than "this file was imported".
fail_under = 45
show_missing = true
exclude_lines = [
  "if __name__ == .__main__.:",
  "raise NotImplementedError",
  "pragma: no cover",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "N", "UP", "SIM", "C4", "PT", "RUF", "S", "RET", "ARG"]
ignore = [
  "E501",  # line length is the formatter's job
  "S101",  # assert belongs in tests, and this repo has a written policy on it
]

[tool.ruff.lint.per-file-ignores]
# S101 in tests is the policy, S311 is a seeded generator rather than a token, and a
# test double has to accept parameters it ignores, which ARG would otherwise flag.
"tests/*" = ["S101", "S106", "S311", "ARG001", "ARG002"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.12"
warn_unused_ignores = true
warn_redundant_casts = true
no_implicit_optional = true
ignore_missing_imports = true
"""


def render_pyproject(p: dict[str, Any]) -> str:
    extras = ""
    for extra, pairs in p.get("extras", {}).items():
        extras += extra + " = [" + reqs(pairs) + "]\n"
    scripts = ""
    if p.get("cli"):
        scripts = '[project.scripts]\n@NAME@ = "@PKG@.cli:main"\n\n'.replace(
            "@NAME@", p["name"]
        ).replace("@PKG@", p["pkg"])
    deps = p.get("deps", [])
    return subs(
        PYPROJECT,
        {
            "NAME": p["name"],
            "PKG": p["pkg"],
            "DESC": p["desc"],
            "KW": toml_list(p["kw"]),
            "DEPS": "[" + reqs(deps) + "]" if deps else "[]",
            "EXTRAS": extras,
            "SCRIPTS": scripts,
            "ORG": ORG,
            "GTE": GT,
        },
    )
README = """
# @NAME@

<!-- PyPI badges go live with the first release. Until then a version badge renders
     "no version" on the landing page, which reads as a defect rather than a date, so
     the badges stay commented out until the tag exists.
-->

**Pre-alpha shell.** The package surface, the obligation matrix and the CI gates exist.
No protocol behaviour is implemented: every public function raises `NotImplementedError`,
and the test suite records that rather than hiding it. Read
[ROADMAP.md](ROADMAP.md) before depending on any of it.

@TITLE@

@WHY@

## The gap, with a date

PyPI was queried on @SURVEY_DATE@ for this name and for every neighbouring project. Landscape
claims rot quickly: two projects in this portfolio shipped within five days of the survey,
which is why the table below carries dates instead of adjectives.

@PRIOR@

What this project intends to add:

@GAPS@

## Specification spine

Status and publication dates below were read from the RFC Editor record on @SURVEY_DATE@. A
section number is cited only where that section was read in full; everything else cites the
document, which is the honest grain size for a plan. See [docs/rfc-map.md](docs/rfc-map.md).

@DOCS@

### Errata watch

@ERRATA@

## Module layout

@MODULES@

## What it does not do

@NONGOALS@

@DEPSNOTE@
## Install

```bash
git clone https://github.com/@ORG@/@NAME@.cd @NAME@
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\\\Scripts\\\\Activate.ps1
pip install -e \".[dev]\"
```

Not published to PyPI yet. The name is reserved for this repository's trusted publisher at
the moment of the first release.

## Development

All four gates must pass, on Linux and Windows alike:

```bash
ruff check . && ruff format --check .
mypy @PKG@
pytest -q --cov
python -O -m pytest -q
```

The last line is the one that matters most in a protocol library. `-O` strips `assert`, and a
parser whose bounds checks were asserts stops being a parser under production flags. Wire
paths raise named exceptions; asserts belong in tests and nowhere else.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
"""

ROADMAP = """
# Specification completeness -- and the roadmap it implies

This is the project's north star: every protocol obligation @NAME@ could plausibly take on,
with an honest status against the code at `HEAD`. It is blunt about gaps on purpose. A
roadmap that overstates its coverage is not a plan, it is marketing.

**The honesty rule:** a row may read `[ok]` only when a named test would fail if the
behaviour regressed. Reading the code and agreeing with it is not enough. That is how
"decoded but never sent" quietly becomes "implemented".

Legend: `[ok]` implemented and pinned by a named test -- `[part]` partial, with what is
missing stated -- `[ ]` not implemented -- `[no]` deliberate non-goal.

Update the affected row in the same commit that changes the behaviour. A row and its test
drift apart within one release, and the document becomes useless exactly when it is needed.

## 1. Obligations

@ROWS@

## 2. Milestones

@STEPS@

Every milestone is accepted by its rows above flipping to `[ok]` with a named test, not by
the code existing. Coverage in `pyproject.toml` ratchets in the same commit.

## 3. Errata watch

@ERRATA@

## 4. Deliberate non-goals

@NONGOALSROWS@

## 5. Open questions

@OPEN@

## 6. Publication checklist

- [ ] every `[ ]` row above either `[ok]` or moved to a named later milestone
- [ ] `docs/research.md` claims re-verified and the dated ones either promoted or deleted
- [ ] interoperability evidence recorded in `docs/` against a non-Python implementation
- [ ] `tools/check_dist.py` proves the wheel ships the fixtures the README promises
- [ ] version 0.1.0 tagged, trusted publisher configured, README badges uncommented
"""

OPEN_QUESTIONS = {
    "rpkit": [
        "rsync or RRDP first: rsync is universal, RRDP is the future and the easier test target",
        "repository cache format, and whether it is shared with rtrkit on disk",
    ],
    "rtrkit": [
        "does the server hold a full assertion set or stream from rpkit incrementally",
    ],
    "asnkit": [
        "pure-Python radix versus an optional native one, decided by a benchmark on a full RIB",
    ],
    "h3tunnel": [
        "which adapter lands first: qh3 or aioquic, given both expose datagrams today",
        "does the proxy side need CONNECT-TCP before users ask for it",
    ],
    "dnssd-srp": [
        "share the DNS codec with namespy through a dependency, or keep a thin local layer",
        "how much of the registrar is a server rather than a validator",
    ],
    "turnkit": [
        "does the ICE agent need to be wire compatible with aioice for a shared test harness",
    ],
    "leasespy": [
        "which lease store interface keeps a production server possible without embedding one",
        "how far to chase RFC 9915 conformance while peers still speak RFC 8415 behaviour",
    ],
    "cwmp": [
        "which TR revision is the baseline, and how the chosen revision is pinned in tests",
    ],
    "devicespy": [
        "depend on the maintained ssdp library or speak multicast HTTP directly",
    ],
    "ohttp": [
        "is the HPKE layer a dependency on hpke or a pinned local implementation",
    ],
    "ntspy": [
        "how much of RFC 5905 is in scope once the errata and RFC 9748 registry changes apply",
    ],
    "tacacs": [
        "verify the scope of pytacs before assuming the field is empty",
        "which vendor deviations become conformance fixtures",
    ],
    "signeddata": [
        "how far the EnvelopedData recipient-info matrix extends in a first release",
    ],
    "pgpenv": [
        "which algorithm policy is default, and whether v4 writing is ever offered",
    ],
    "syslogkit": [
        "does the receiver own backpressure policy or expose a hook for the operator to",
    ],
    "sfields": [
        "vendor the working group test suite as data, and record its provenance",
    ],
    "shaken": [
        "how x5u retrieval is bounded so a verifier cannot be turned into a traffic amplifier",
    ],
    "srtpkit": [
        "which profiles are negotiable by default once RFC 3711 and RFC 7714 are applied",
    ],
}


def modules_table(p: dict[str, Any]) -> str:
    rows = [("`" + m + "`", d) for m, d in p["mods"]]
    return table(("Module", "Responsibility"), rows)


def obligation_rows(p: dict[str, Any]) -> str:
    rows = []
    for mod, _kind, fn, _params, _ret, cite in p["api"]:
        rows.append(
            (
                "`" + mod + "." + fn + "()`",
                cite,
                "`[ ]`",
                "`tests/test_obligations.py::" + fn + "`",
            )
        )
    return table(("Obligation", "Spec", "Status", "Where"), rows)


def nongoal_rows(p: dict[str, Any]) -> str:
    return table(
        ("Non-goal", "Status", "Revisit when"),
        [(g, "`[no]`", "a named document requires it") for g in p["nongoals"]],
    )


def steps_block(p: dict[str, Any]) -> str:
    return "\n".join("- " + s for s in p["steps"])
# ------------------------------------------------------------------ supporting project files

CONTRIBUTING = """
# Contributing

Short version: four gates, and they all have to pass on Linux and Windows.

```bash
ruff check . && ruff format --check .
mypy @PKG@
pytest -q --cov
python -O -m pytest -q
```

## The three rules that cause the most arguments

1. **`assert` belongs in tests and nowhere on a wire path.** The fourth gate strips
   asserts, and a parser whose bounds checks were asserts stops being a parser in
   production. On a parse path, raise a named exception.
2. **A behaviour change updates its ROADMAP row in the same commit.** The row flips to
   `[ok]` only with a named test. A row and a test drift apart within one release, and the
   matrix becomes useless exactly when someone needs it.
3. **Cite the document, not a blog post.** A section number is allowed only if that section
   was read. `docs/rfc-map.md` records what was verified and when.

## Layout

| Tier | Home | Rule |
|---|---|---|
| Core | `@PKG@/` | specification behaviour only; dependency-free unless README says why not |
| Apps | `@PKG@/apps/` | composes core pieces, adds no new protocol surface |
| Examples | `examples/` | one runnable script per use case; never restates library logic |

A pattern graduates from `examples/` to `apps/` on the second user, stated rather than
assumed.

## Tests

Protocol tests are vectors first: bytes in, structure out, with the source of the vector
cited. `hypothesis` is welcome for codecs, and every fuzz-found crash becomes a fixed
regression test rather than only a property.

## Milestones

Pick a row from the matrix, not a feature from your imagination. If the row you want is
missing, add it to the matrix first and argue for it there.
"""

SECURITY = """
# Security policy

## What this project treats as a security property

- **Hostile input is the normal case.** Every decoder has to refuse truncation, over-long
  lengths, nested structures and contradictory fields without raising anything a caller
  cannot name.
- **Bounds before cleverness.** Size, count and depth limits exist on every parse path, and
  they are configuration rather than suggestions.
- **No silent crypto policy.** Weak or deprecated algorithms are refused by an explicit
  policy object rather than accepted because they happen to parse.
- **Provenance is part of the answer.** A result states what was verified, what was cached
  and what was skipped, so a caller cannot mistake an unchecked field for a checked one.

## assert is not a safety mechanism

`python -O` strips asserts. Any invariant that protects a parser boundary or a verification
result must be expressed as a raised exception. CI runs the suite under `-O` for exactly
this reason.

## Reporting

Open a private security advisory on the repository rather than a public issue. The policy is
the Apache Software Foundation's: security support for the main branch and the most recent
release. Because this repository is a pre-alpha shell, a report will often be answered with
"that code does not exist yet", which is a different thing from "it will not be fixed".
"""

CHANGELOG = """
# Changelog

The format follows Keep a Changelog, and this project adheres to Semantic Versioning.

## Unreleased

Nothing yet. This repository is a shell: the public surface exists as typed stubs that raise
`NotImplementedError`, and [ROADMAP.md](ROADMAP.md) lists what has to happen first.

## 0.0.0 - @SURVEY_DATE@

### Added

- Package skeleton, obligation matrix and CI gates for @NAME@.
- `@PKG@.apps` namespace reserved for composition that is not protocol behaviour.
"""

NOTICE = """
@NAME@
Copyright 2026 Justin Capella

This product includes software developed as part of an RFC-anchored protocol SDK portfolio.
Specification text referenced by this project is the work of its authors and is cited by
document number; no normative text is redistributed here beyond short identifiers.
"""

GITIGNORE = """
__pycache__/
*.py[cod]
*.egg-info/
.venv/
build/
dist/
.coverage
htmlcov/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.hypothesis/
*.log
requirements-audit.txt

# Working notes quote other projects' trackers and age faster than a tracked document
# should. Evidence that survives gets promoted into README.md or ROADMAP.md with a date;
# the scratch file itself never gets committed.
docs/research.md
"""

GITATTRIBUTES = """
* text=auto eol=lf
*.py text
*.md text
*.toml text
*.yml text
*.png binary
*.pcap binary
*.der binary
"""

CI = """
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: python -m @PIPIN@ -e ".[dev]"
      - run: ruff check .
      - run: ruff format --check .
      - run: mypy @PKG@
      # check_dist inspects a built wheel, so the wheel is built here rather than assumed to exist.
      # The step looked green for months on one machine because an earlier manual build had left a
      # wheel in dist/: a cache impersonating a check, and the first CI run this project ever had
      # failed it immediately.
      - run: python -m @PIPIN@ build
      - run: python -m build --wheel --quiet
      - run: python tools/check_dist.py

  test:
    # A socket option that exists only on Linux is exactly the bug a Linux-only CI never
    # sees, and multicast, UDP send buffers and interface enumeration differ per platform.
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ["3.12", "3.13", "3.14"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: python -m @PIPIN@ -e ".[dev]"
      - run: python -m pytest -q --cov
      # Asserts stripped: a wire path guarded by assert is unguarded in production.
      - run: python -O -m pytest -q
"""

SECURITY_WF = """
name: security

on:
  push:
    branches: [main]
  schedule:
    - cron: "17 4 * * 2"

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: python -m @PIPIN@ -e ".[dev]" pip-audit
      # The resolved environment is audited rather than the declarations, because the
      # declarations are floors. A file is written by a script rather than shell
      # redirection so the step behaves identically on a self-hosted runner.
      - run: python tools/write_freeze.py requirements-audit.txt
      - run: python -m pip_audit --progress-spinner off -r requirements-audit.txt
"""

STRATEGY = """
# Strategy

The completeness matrix is [../ROADMAP.md](../ROADMAP.md). This document is *why* the rows
are ordered the way they are, and the rules that order has to respect.

## The constitution

1. **The core is the specification implementation.** `@PKG@/` holds codecs, state machines
   and the vocabulary of @NAME@. New core code appears when a document defines the
   behaviour, or when an ordering rule with no document earns an explicit convention label.
2. **Sans-IO before sockets.** Anything decidable from data plus a clock is implemented
   without touching a socket, so every timeout, retry and rollover is testable without
   sleeping or networking.
3. **Dependency-free by default.** An exception needs a sentence in README.md explaining why
   the rule was broken, and a floor with no ceiling.
4. **Positioning is correctness and legibility, not throughput.** The incumbents in this
   corner are usually stale, untyped, or welded to a product. This is the implementation that
   says how it knows what it claims.
5. **Every answer carries its provenance.** Verified or cached, which document, refused or
   believed. An answer without provenance is a guess with a confident type.

## The three tiers

| Tier | Home | Contents | Rule |
|---|---|---|---|
| Core | `@PKG@/` | codecs, state machines, policy objects | RFC-cited or convention-labelled |
| Apps | `@PKG@/apps/` | reusable assemblies that compose core | no new protocol surface |
| Examples | `examples/` | one runnable script per use case | configures; never restates logic |

## Interface grammar

One engine, three drives, never parallel implementations:

- **await** -- the native asyncio surface.
- **blocking** -- a facade owning a private loop, so a call from inside a caller's running
  loop works instead of deadlocking.
- **callback** -- plain callables, no third-party promise type.

## Naming

One string everywhere: the distribution, the import and the console script. A name that
means one thing in the installer, in `import` and on `PATH` is the only arrangement that
cannot surprise anyone, and it is also why this project does not sit one edit away from a
project that already exists.
"""

EXAMPLES = """
# examples

One runnable script per use case. An example configures the library; it never restates
library logic, and the prose in the docs quotes these files rather than duplicating them.

Nothing here runs yet: the package surface is stubs that raise `NotImplementedError`. Each
milestone in [../ROADMAP.md](../ROADMAP.md) adds the example that proves it works.
"""
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
    # Drop the project's own entry. pip freeze records the local tree as an editable or VCS reference,
    # and pip-audit then installs that URL to audit it: on a private repository the anonymous clone
    # fails, and the audit reports a build error instead of advisories. A project is not one of its own
    # dependencies, and only third-party distributions carry advisories worth resolving.
    lines = []
    dropped = 0
    for line in frozen.splitlines():
        if not line.strip():
            continue
        if line.startswith("-e") or "git+" in line or "file://" in line:
            dropped += 1
            continue
        lines.append(line)
    pathlib.Path(sys.argv[1]).write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    print(f"{len(lines)} distributions written to {sys.argv[1]} ({dropped} self-reference(s) excluded)")
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
# ---------------------------------------------------------------------- package rendering

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
# ------------------------------------------------- cluster: public key infrastructure

PROJECTS_H: list[dict[str, Any]] = [
    {
        "name": "pkix",
        "pkg": "pkix",
        "title": "pkix -- RFC 5280 path validation, the part Python never had",
        "desc": "Certification path discovery and validation per RFC 5280: trust anchors, name "
        "constraints, policy mapping and constraints, CRL and OCSP status hooks, "
        "explicit result provenance",
        "kw": [
            "x509",
            "pkix",
            "path-validation",
            "trust-anchor",
            "name-constraints",
            "rfc5280",
        ],
        "why": (
            "Python can build a certificate and parse a certificate, and it cannot tell you "
            "whether a certificate is valid. cryptography has no path validator; the one "
            "serious implementation, certvalidator 0.11.1, has not been released since "
            "2016-07-29 and sits on oscrypto, itself dead since 2022-03-18. Everything else "
            "shells out to openssl verify and parses text. That is the odd gap in PKI: the "
            "specification is a single algorithm, RFC 5280 section 6, and it is the one "
            "nobody maintains in Python. Parsing is a solved problem and x509kit proved it "
            "again in 2026-10-11 by writing a whole toolkit including its own RSA, ECDSA and "
            "AES; pkix deliberately owns the opposite half: decisions, not bytes, and "
            "primitives borrowed from cryptography rather than re-invented.",
        ),
        "deps": [("cryptography", "50.0.2")],
        "deps_note": (
            "Signature verification is the one thing this project must not write itself. A "
            "path validator that re-implements RSA or ECDSA in Python turns a well studied "
            "algorithm problem into a timing side channel project, so primitives come from "
            "cryptography, which vendors audited OpenSSL."
        ),
        "docs": [
            {
                "n": "5280",
                "status": "Proposed Standard",
                "date": "2008-05",
                "why": "the profile and the section 6 path validation algorithm",
            },
            {
                "n": "5912",
                "status": "Informational",
                "date": "2010-06",
                "why": "the ASN.1 modules every PKIX structure is written in",
            },
            {
                "n": "6960",
                "status": "Proposed Standard",
                "date": "2013-06",
                "why": "OCSP status, one of the two revocation inputs the algorithm consults",
            },
        ],
        "errata": [
            "RFC 5280 carries 6 verified errata and is updated by RFC 6818, RFC 8398, RFC 8399, RFC 9549, RFC 9598, RFC 9608, RFC 9618, RFC 9925 and RFC 10007. The updates are not editorial: internationalised names and notBefore bounds changed the answer.",
            "RFC 5912 carries 8 verified errata.",
            "RFC 6960 carries 6 verified errata.",
        ],
        "prior": [
            {
                "name": "certvalidator",
                "version": "0.11.1",
                "date": "2016-07-29",
                "note": "the only Python path validator, dead for a decade on a dead crypto backend",
            },
            {
                "name": "cryptography",
                "version": "50.0.2",
                "date": "2026-09-30",
                "note": "builds and parses certificates, and verifies signatures, but builds no path and applies no policy",
            },
            {
                "name": "x509kit",
                "version": "0.10.0",
                "date": "2026-10-11",
                "note": "structures and its own crypto; validation policy is not the product",
            },
        ],
        "gaps": [
            "section 6.1 user data and 6.2 certification path validity checks, implemented as written",
            "name constraints including the subtle excluded-subtrees rule and the check-only-at-issuance exception",
            "policy mapping, policy constraints and explicit policy with anyPolicy handled correctly",
            "revocation as an injected interface, so CRL, OCSP, stapled and cached answers are all opinions you can test",
            "a result object that states which trust anchor, which chain, which policy and which revocation source decided it",
        ],
        "nongoals": [
            "a certificate parser: accept DER or a cryptography object and refuse anything else",
            "crypto primitives of any kind",
            "ACME, CMP or any issuance protocol: enrollkit asks pkix whether the result is acceptable",
            "the CA/Browser Forum baseline requirements, which are a policy profile built on top, not this algorithm",
        ],
        "mods": [
            (
                "anchors",
                "trust anchor selection, including name restrictions and certificates only sets (RFC 5280 sec. 6.1)",
            ),
            (
                "chain",
                "candidate path discovery against a store or a directory of intermediates",
            ),
            (
                "validity",
                "the section 6.2 processing: signature, validity, issuer, name constraints (RFC 5280)",
            ),
            (
                "names",
                "name forms, general names and constraint comparison, including internationalised forms",
            ),
            (
                "policy",
                "policy mappings, constraints and anyPolicy resolution (RFC 5280)",
            ),
            (
                "revocation",
                "the status interface plus an allow list of trusted decisions",
            ),
            ("result", "the outcome object with provenance for every decision"),
            ("store", "certificate, CRL and OCSP caches behind one interface"),
        ],
        "api": [
            (
                "anchors",
                "def",
                "load_anchor",
                "cert_der: bytes, name_restriction: Optional[str]",
                "TrustAnchor",
                "RFC 5280 sec. 6.1",
            ),
            (
                "chain",
                "def",
                "candidates",
                "leaf: Certificate, intermediates: Store, anchors: list",
                "list",
                "RFC 5280 sec. 6.1",
            ),
            (
                "validity",
                "def",
                "check_signature",
                "cert: Certificate, issuer: Certificate",
                "None",
                "RFC 5280",
            ),
            (
                "validity",
                "def",
                "check_validity",
                "cert: Certificate, at: datetime",
                "None",
                "RFC 5280",
            ),
            (
                "names",
                "def",
                "constraint_holds",
                "name: GeneralName, constraints: Constraints, at_issuance: bool",
                "bool",
                "RFC 5280",
            ),
            (
                "policy",
                "def",
                "resolve",
                "chain: list, expected: Optional[set]",
                "PolicyOutcome",
                "RFC 5280",
            ),
            (
                "revocation",
                "def",
                "status_of",
                "cert: Certificate, issuer: Certificate, at: datetime",
                "Status",
                "RFC 5280",
            ),
            (
                "result",
                "def",
                "validate",
                "leaf: Certificate, anchors: list, at: datetime, policy: ValidationPolicy",
                "Result",
                "RFC 5280 sec. 6",
            ),
            ("store", "def", "remember", "cert: Certificate", "None", "design"),
        ],
        "steps": [
            "M1 anchors and chain discovery with a fixture set of real chains",
            "M2 section 6.2 validity: signature, dates, issuer matching, critical extensions",
            "M3 name constraints including excluded subtrees and the issuance-time exception",
            "M4 policy mapping, constraints and anyPolicy",
            "M5 revocation interface plus CRL and OCSP backed implementations and cross-checks against openssl verify",
            "M6 publication: 0.1.0 with the conformance trace against NIST and vendor path test suites",
        ],
        "extras": {},
        "cli": "pkix verify leaf.pem --chain intermediate.pem --anchor root.pem --at 2026-11-05T00:00:00Z",
    },
    {
        "name": "revokekit",
        "pkg": "revokekit",
        "title": "revokekit -- OCSP and CRL clients that know the current specification",
        "desc": "Revocation in practice: OCSP request and response handling to RFC 9654 and RFC "
        "9919, CRL and delta CRL processing, stapled response checks and caching",
        "kw": [
            "ocsp",
            "crl",
            "revocation",
            "pkix",
            "stapling",
            "rfc6960",
            "rfc9654",
            "rfc9919",
        ],
        "why": (
            "OCSP is being rewritten while we watch. RFC 9654 obsoleted RFC 8954 in 2024-08 "
            "and redefined the Nonce extension, and RFC 9919 obsoleted RFC 5019 in July 2026 "
            "with a lightweight high volume profile that recommends SHA-256. cryptography can "
            "build and parse an OCSP request but ships no client, no caching, no responder "
            "chain rules and no nonce policy, and the only library that ever did revocation "
            "end to end died in 2016. Meanwhile the deployments that matter check stapled "
            "responses whose must-staple extension comes from RFC 7633. revokekit is the client "
            "and the policy, written against the documents as they now stand, and it is the "
            "revocation provider pkix consumes.",
        ),
        "docs": [
            {
                "n": "6960",
                "status": "Proposed Standard",
                "date": "2013-06",
                "why": "OCSP request, response and the basic confirmation types",
            },
            {
                "n": "9654",
                "status": "Proposed Standard",
                "date": "2024-08",
                "why": "the Nonce extension, obsoleting RFC 8954 and updating RFC 6960",
            },
            {
                "n": "9919",
                "status": "Proposed Standard",
                "date": "2026-07",
                "why": "the lightweight high volume profile, obsoleting RFC 5019",
            },
            {
                "n": "7633",
                "status": "Proposed Standard",
                "date": "2015-10",
                "why": "the TLS Feature extension behind OCSP must-staple",
            },
            {
                "n": "5940",
                "status": "Proposed Standard",
                "date": "2010-08",
                "why": "revocation choices carried inside CMS, the signed document case",
            },
        ],
        "errata": [
            "RFC 6960 carries 6 verified errata and is updated by RFC 8954 and RFC 9654: read 9654 before implementing Nonce, because it supersedes the older constraint.",
            "RFC 9654 and RFC 9919 report no errata as of 2026-10-29, and both are new enough that implementations are the open question rather than corrections.",
            "RFC 9919 obsoletes RFC 5019. Recipes copied from 5019 describe the superseded profile.",
        ],
        "prior": [
            {
                "name": "cryptography.x509.ocsp",
                "version": "50.0.2",
                "date": "2026-09-30",
                "note": "request and response types, no client, no cache, no responder policy",
            },
            {
                "name": "certvalidator",
                "version": "0.11.1",
                "date": "2016-07-29",
                "note": "did OCSP and CRL checking; unmaintained for ten years",
            },
            {
                "name": "x509kit",
                "version": "0.10.0",
                "date": "2026-10-11",
                "note": "OCSP structures and signing, not a network client or a policy",
            },
        ],
        "gaps": [
            "an HTTP client with bounds: timeouts, response size caps, no redirect chasing, per-responder circuit breaking",
            "nonce handling that actually follows RFC 9654, including what to do when the responder omits it",
            "responder validation: delegated signing certificate, key purpose and OCSP no-check",
            "thisUpdate, nextUpdate and maxAge discipline with clock skew tolerance stated explicitly",
            "CRL and delta CRL fetching with issuer matching, and stapled response verification for TLS servers",
        ],
        "nongoals": [
            "being an OCSP responder, which is a deployment product",
            "path validation, which is pkix and consumes this library",
            "CRL generation for CA operators",
        ],
        "mods": [
            (
                "request",
                "build and sign requests, single and batch (RFC 6960, RFC 9919)",
            ),
            (
                "response",
                "parse and verify signatures, including delegated responders (RFC 6960)",
            ),
            (
                "nonce",
                "generation, echo verification and the missing nonce policy (RFC 9654)",
            ),
            (
                "freshest",
                "thisUpdate, nextUpdate, maxAge and skew tolerance (RFC 6960, RFC 9919)",
            ),
            ("http", "bounded transport with retries, budgets and circuit breaking"),
            ("crl", "CRL and delta CRL fetch, matching and cache (RFC 5280)"),
            (
                "stapling",
                "verify a TLS server's stapled response against the connection (RFC 7633)",
            ),
            ("cache", "storage with explicit staleness decisions"),
        ],
        "api": [
            (
                "request",
                "def",
                "build",
                "cert: Certificate, issuer: Certificate, nonce: Optional[bytes]",
                "bytes",
                "RFC 6960, RFC 9919",
            ),
            (
                "response",
                "def",
                "parse_and_verify",
                "raw: bytes, responder_certs: list",
                "Response",
                "RFC 6960",
            ),
            ("nonce", "def", "generate", "length: int", "bytes", "RFC 9654"),
            (
                "nonce",
                "def",
                "check",
                "request_nonce: Optional[bytes], response_nonce: Optional[bytes], policy: NoncePolicy",
                "None",
                "RFC 9654",
            ),
            (
                "freshest",
                "def",
                "is_fresh",
                "response: Response, at: datetime, tolerance: timedelta",
                "bool",
                "RFC 9919",
            ),
            (
                "http",
                "async def",
                "query",
                "url: str, body: bytes, budget: Budget",
                "Response",
                "RFC 6960",
            ),
            (
                "crl",
                "async def",
                "fetch",
                "distribution_point: DistributionPoint, reason: Optional[int]",
                "Crl",
                "RFC 5280",
            ),
            (
                "stapling",
                "def",
                "verify_stapled",
                "response: Response, peer_cert: Certificate, sans: list",
                "Status",
                "RFC 7633",
            ),
        ],
        "steps": [
            "M1 request and response codec against RFC 6960 vectors",
            "M2 signature and delegated responder verification",
            "M3 nonce rules per RFC 9654 with explicit missing-nonce policy",
            "M4 freshness, caching and clock skew, then the bounded HTTP client",
            "M5 CRL and delta CRL, and the stapling check",
            "M6 publication: 0.1.0, wired as the revocation provider for pkix",
        ],
        "extras": {},
        "cli": "revokekit query https://ocsp.example.org --cert leaf.pem --issuer ca.pem --nonce",
    },
    {
        "name": "enrollkit",
        "pkg": "enrollkit",
        "title": "enrollkit -- CMP and EST clients for private PKIs",
        "desc": "Certificate enrollment: CMP to RFC 9810 with CRMF requests, EST to RFC 7030, "
        "PKCS#10 fallback, and the challenge and authentication mechanics around them",
        "kw": [
            "cmp",
            "est",
            "crmf",
            "enrollment",
            "pkcs10",
            "rfc9810",
            "rfc7030",
            "pki",
        ],
        "why": (
            "CMP was rewritten in 2025-07. RFC 9810 obsoletes RFC 4210 and RFC 9480, replaces "
            "EncryptedValue with EnvelopedData and adds KEM key support, and it has already "
            "accumulated 4 verified errata. No Python library implements CMP at any revision, "
            "and EST, the simpler HTTPS enrollment profile, has none either. ACME is the well "
            " served half, acme 5.9.0 shipped on 2026-10-29, and this project deliberately does "
            "not compete with it: private and enterprise PKIs run CMP and EST, and today that "
            "means openssl CLI invocations or a Java stack.",
        ),
        "deps": [("asn1crypto", "1.5.1"), ("cryptography", "50.0.2")],
        "deps_note": (
            "CMP messages are deep ASN.1 inside CMS. Writing that schema layer again would be "
            "the third Python implementation of the same structures, so definitions come from "
            "asn1crypto and primitives from cryptography. What this project owns is the "
            "protocol: message order, protection, and recovery from the failures."
        ),
        "docs": [
            {
                "n": "9810",
                "status": "Proposed Standard",
                "date": "2025-07",
                "why": "current CMP: messages, protection, EnvelopedData, KEM support",
            },
            {
                "n": "9811",
                "status": "Proposed Standard",
                "date": "2025-07",
                "why": "HTTP transfer for CMP, including the well-known URI prefix",
            },
            {
                "n": "9481",
                "status": "Proposed Standard",
                "date": "2023-11",
                "why": "the algorithm set CMP must and may support",
            },
            {
                "n": "4211",
                "status": "Proposed Standard",
                "date": "2005-09",
                "why": "CRMF: the certificate request message CMP carries",
            },
            {
                "n": "7030",
                "status": "Proposed Standard",
                "date": "2013-10",
                "why": "EST: enrollment over HTTPS with CMC, plus CA certificate retrieval",
            },
        ],
        "errata": [
            "RFC 9810 already carries 4 verified errata eleven months after publication. Implement 9810, not the 4210 text that most tutorials still copy.",
            "RFC 7030 carries 3 verified errata and is updated by RFC 8951, RFC 8996 and RFC 9908.",
            "RFC 4211 carries 2 verified errata and is updated by RFC 9045. RFC 9811 obsoletes RFC 6712 and, with RFC 9810, RFC 9480.",
            "RFC 4210 is OBSOLETE: cite it only when explaining a legacy server.",
        ],
        "prior": [
            {
                "name": "acme",
                "version": "5.9.0",
                "date": "2026-10-29",
                "note": "the ACME half, actively maintained; deliberately out of scope here",
            },
            {
                "name": "certipy",
                "version": "0.2.3",
                "date": "2026-04-29",
                "note": "Active Directory certificate services tooling, a different backend",
            },
            {
                "name": "cmp, crmf, cmpclient, enrollkit",
                "version": "-",
                "date": "-",
                "note": "cmp is a 2019 name squat, est belongs to a spectroscopy package, the rest are absent (2026-11-05)",
            },
        ],
        "gaps": [
            "CMP message construction and parsing to RFC 9810, including the EnvelopedData change",
            "both protection mechanisms: shared secret MAC and signature based, with senderNonce replay discipline",
            "the full interaction set: IP, CP, CR, Kurt, poll, conf, p10cr, rblu and error handling",
            "EST client with /simpleEnroll, /cacerts and /curl plus HTTP Basic and TLS client authentication",
            "poll and pending flows, which is where real CA integrations actually break",
        ],
        "nongoals": [
            "ACME, which acme already does well",
            "a CA or an RA: this is the client side of a conversation",
            "key generation policy: bring your own keys, or accept a hardware-backed signer through an interface",
        ],
        "mods": [
            ("messages", "CMP PKIMessage and its body variants (RFC 9810, RFC 9811)"),
            (
                "protection",
                "POPOSIMESTAMP, POPOWITNESS and signature protection (RFC 9810)",
            ),
            ("crmf", "request objects, keys and proof of possession (RFC 4211)"),
            ("flow", "the transaction state machine including poll and confirm"),
            ("est", "the HTTPS profile: simpleEnroll, cacerts and curl (RFC 7030)"),
            ("http", "bounded transport with retry and proxy awareness"),
            (
                "trust",
                "server authentication for enrollment endpoints, the part everyone bolts on",
            ),
        ],
        "api": [
            (
                "messages",
                "def",
                "build_cr",
                "request: CrmfRequest, sender: str, recipient: Optional[str]",
                "PkiMessage",
                "RFC 9810",
            ),
            ("messages", "def", "parse", "raw: bytes", "PkiMessage", "RFC 9810"),
            (
                "protection",
                "def",
                "protect",
                "msg: PkiMessage, secret: bytes",
                "PkiMessage",
                "RFC 9810",
            ),
            (
                "protection",
                "def",
                "verify_protection",
                "msg: PkiMessage, trust: Trust",
                "None",
                "RFC 9810",
            ),
            (
                "crmf",
                "def",
                "build_request",
                "public_key: object, subject: str, validity: Validity",
                "CrmfRequest",
                "RFC 4211",
            ),
            (
                "flow",
                "async def",
                "enroll",
                "endpoint: str, request: CrmfRequest, auth: Auth",
                "EnrollmentResult",
                "RFC 9810",
            ),
            (
                "flow",
                "async def",
                "poll_until_ready",
                "endpoint: str, transaction: bytes, budget: Budget",
                "EnrollmentResult",
                "RFC 9810",
            ),
            (
                "est",
                "async def",
                "simple_enroll",
                "endpoint: str, csr: bytes, auth: Auth",
                "Certificate",
                "RFC 7030",
            ),
            (
                "est",
                "async def",
                "ca_certs",
                "endpoint: str, auth: Auth",
                "list",
                "RFC 7030",
            ),
        ],
        "steps": [
            "M1 CMP message codec round trip against captured vendor traffic",
            "M2 protection both ways, with senderNonce replay tests",
            "M3 CRMF request building and proof of possession",
            "M4 the transaction state machine including poll and error responses",
            "M5 EST client and its two authentication modes",
            "M6 publication: 0.1.0 with interop notes against at least two CA implementations",
        ],
        "extras": {},
        "cli": "enrollkit est --url https://ca.example/simpleenroll --key device.key --csr device.csr",
    },
    {
        "name": "ctspy",
        "pkg": "ctspy",
        "title": "ctspy -- certificate transparency verification in Python",
        "desc": "Certificate Transparency to RFC 9162: signed certificate timestamps, Merkle "
        "inclusion and consistency proofs, log storage tiles, and monitoring",
        "kw": [
            "certificate-transparency",
            "ct",
            "sct",
            "merkle",
            "logs",
            "rfc9162",
            "monitoring",
        ],
        "why": (
            "CT is the audit trail for the whole Web PKI and Python cannot read it. Verifying "
            "that a certificate really is in a log means parsing an SCT, checking a signed "
            "tree head, and validating Merkle inclusion and consistency proofs over the tile "
            "layout logs publish. RFC 9162 defines version 2.0 and it is worth saying plainly "
            "that the RFC Editor records it as Experimental, obsoleting RFC 6962, which is why "
            "deployment policy rather than the RFC is the real compatibility target. Nothing "
            "on PyPI does any of this: ctlog is a combinatorial testing tool, ctkit is "
            "medical image processing, sct is a radar calibration toolbox, and transparency is "
            "a model explanation library.",
        ),
        "docs": [
            {
                "n": "9162",
                "status": "Experimental",
                "date": "2021-12",
                "why": "CT 2.0: SCTs, signed tree heads, the two proof types and the TLS extension",
            },
            {
                "n": "6962",
                "status": "Obsolete",
                "date": "2013-07",
                "why": "version 1.0, still what many logs and captures emit",
            },
        ],
        "errata": [
            "RFC 9162 is Experimental with 1 erratum on file and none verified: expect variation between implementations and pin tests to real logs.",
            "RFC 9162 obsoletes RFC 6962; log artifacts from 2013 deployments still follow 6962 shapes, so the reader must accept both.",
        ],
        "prior": [
            {
                "name": "ctlog",
                "version": "0.7.1",
                "date": "2026-06-14",
                "note": "SAT based combinatorial testing, unrelated",
            },
            {
                "name": "ctkit",
                "version": "0.1.1",
                "date": "2026-09-11",
                "note": "CT image processing, unrelated",
            },
            {
                "name": "Trillian, tombstone, ct-go",
                "version": "-",
                "date": "-",
                "note": "the Go tooling that actually runs the logs; no Python equivalent",
            },
        ],
        "gaps": [
            "SCT parsing from the TLS extension, from X.509 and from OCSP, and signature verification against log keys",
            "signed tree head verification and the static Merkle tree with hashed leaf prefixes",
            "inclusion and consistency proof validation, including the empty tree and single leaf edges",
            "log storage tile fetching with cache control and mirror fallback",
            "a monitor that watches issued certificates and diffs them against what logs claim",
        ],
        "nongoals": [
            "running a log: the audit trail needs independent operators, not another client library",
            "browser policy decisions about which logs are accepted, which belong to the platform",
            "certificate issuance, which is enrollkit and pkix",
        ],
        "mods": [
            (
                "sct",
                "timestamp structure, versions and signature verification (RFC 9162)",
            ),
            (
                "sth",
                "signed tree heads, timestamps and the STH consistency rule (RFC 9162)",
            ),
            (
                "merkle",
                "static Merkle trees, leaf and node hash prefixes, proof validation (RFC 9162)",
            ),
            ("tiles", "log storage layout, fetching and caching (RFC 9162)"),
            (
                "client",
                "add chain, add prechain, get sth and the submission endpoints (RFC 9162)",
            ),
            ("monitor", "stream reading, diffing and alerting on unexpected issuance"),
            ("policy", "which logs and which artifacts a deployment will accept"),
        ],
        "api": [
            ("sct", "def", "parse", "raw: bytes", "Sct", "RFC 9162"),
            (
                "sct",
                "def",
                "verify",
                "sct: Sct, entry: MerkleTreeEntry, log_key: LogKey",
                "None",
                "RFC 9162",
            ),
            (
                "sth",
                "def",
                "verify",
                "sth: SignedTreeHead, log_key: LogKey",
                "None",
                "RFC 9162",
            ),
            (
                "merkle",
                "def",
                "verify_inclusion",
                "leaf: Hash, tree_size: int, proof: list, sth: SignedTreeHead",
                "bool",
                "RFC 9162",
            ),
            (
                "merkle",
                "def",
                "verify_consistency",
                "old: int, new: int, proof: list, old_root: Hash, new_root: Hash",
                "bool",
                "RFC 9162",
            ),
            (
                "tiles",
                "async def",
                "fetch_tile",
                "log: LogUrl, index: int, width: int",
                "bytes",
                "RFC 9162",
            ),
            (
                "client",
                "async def",
                "add_chain",
                "log: LogUrl, chain: list",
                "Sct",
                "RFC 9162",
            ),
            (
                "monitor",
                "async def",
                "watch",
                "log: LogUrl, since: int, sink: Sink",
                "None",
                "RFC 9162",
            ),
            (
                "policy",
                "def",
                "acceptable",
                "scts: list, at: datetime, policy: Policy",
                "Decision",
                "design",
            ),
        ],
        "steps": [
            "M1 static Merkle trees and both proof types against published vectors",
            "M2 SCT and STH parsing plus signature verification",
            "M3 tile fetching with caching and a mirror fallback",
            "M4 the submission client for chains and pre-certificates",
            "M5 a monitor with a durable cursor and diff output",
            "M6 publication: 0.1.0 with cross checks against a production log",
        ],
        "extras": {"crypto": [("cryptography", "50.0.2")]},
        "cli": "ctspy check cert.pem --logs logs.json --verify-inclusion",
    },
]
# ------------------------------------------- cluster: BGP looking glass

PROJECTS_I: list[dict[str, Any]] = [
    {
        "name": "pathattr",
        "pkg": "pathattr",
        "title": "pathattr -- the BGP wire codec a looking glass is built on",
        "desc": "BGP-4 message and path attribute codec: OPEN, UPDATE, NOTIFICATION and "
        "KEEPALIVE with every attribute, 4-octet AS, multiprotocol NLRI, ADD-PATH, "
        "large and extended communities, and role capability",
        "kw": [
            "bgp",
            "path-attributes",
            "update",
            "nlri",
            "communities",
            "rfc4271",
            "looking-glass",
        ],
        "why": (
            "Everything a looking glass shows is a BGP UPDATE, and Python has no decoder it "
            "can own. ExaBGP is a daemon with a pipe protocol, not a library; pybgp3 has not "
            "moved in years; and the parsers people copy from blog posts get 4-octet AS "
            "numbers, ADD-PATH and the extended community sub-typing wrong. This is the shared "
            "dependency for the whole cluster: BMP carries UPDATEs inside its path mapping "
            "message, the RIB store indexes what it decodes, leak detection reasons over it, "
            "and the router text parsers produce the same objects. It is a codec and a "
            "stateless reader, deliberately not a router.",
        ),
        "docs": [
            {
                "n": "4271",
                "status": "Draft Standard",
                "date": "2006-01",
                "why": "BGP-4: messages, the attribute flag octet, NLRI and the finite state machine vocabulary",
            },
            {
                "n": "4360",
                "status": "Proposed Standard",
                "date": "2006-02",
                "why": "extended communities and their sub-type namespaces",
            },
            {
                "n": "8092",
                "status": "Proposed Standard",
                "date": "2017-02",
                "why": "the large community attribute, four-octet safe by construction",
            },
            {
                "n": "7911",
                "status": "Proposed Standard",
                "date": "2016-07",
                "why": "ADD-PATH: a path identifier alongside the prefix",
            },
            {
                "n": "9234",
                "status": "Proposed Standard",
                "date": "2022-05",
                "why": "roles in OPEN and UPDATE for leak prevention and detection",
            },
        ],
        "errata": [
            "RFC 4271 carries 9 verified errata and is updated by RFC 4724, RFC 6286, RFC 6608, RFC 6793, RFC 7606, RFC 7607, RFC 7705, RFC 8212, RFC 8654, RFC 9072, RFC 9687 and RFC 9774. Several of those change the wire: 6793 is 4-octet AS, 7606 is error handling, 9072 is extended message lengths.",
            "RFC 4360 carries 2 verified errata and is updated by RFC 7153 and RFC 7606.",
            "RFC 7911 and RFC 9234 report no errata as of 2026-10-29.",
        ],
        "prior": [
            {
                "name": "exabgp",
                "version": "5.0.15",
                "date": "2026-10-17",
                "note": "a BGP daemon with an external process API, not an importable codec",
            },
            {
                "name": "pybgp3",
                "version": "-",
                "date": "-",
                "note": "stale; absent from PyPI as a maintained project",
            },
            {
                "name": "bgpkit, bgpspy, ribkit, pathattr",
                "version": "-",
                "date": "-",
                "note": "all free on PyPI (2026-11-05); bgpkit and bgpspy collide with tool and service brands",
            },
        ],
        "gaps": [
            "a codec with no parser bugs: attribute flag semantics, optional and transitive handling, and length discipline on every path",
            "4-octet AS in AS_PATH, AS4_PATH, and the two-byte fallback, plus confederation handling",
            "multiprotocol NLRI with label and SID forms left opaque rather than guessed at",
            "extended and large communities decoded against the IANA registries, with unknown sub-types preserved",
            "hostile input refusal, since a looking glass parses what strangers announce",
        ],
        "nongoals": [
            "a BGP speaker: no sessions, no timers, no announcement; ExaBGP, FRR and BIRD do that",
            "best path selection or any policy engine",
            "RIB storage and indexing, which is asnkit",
        ],
        "mods": [
            (
                "message",
                "the four message types with header and length discipline (RFC 4271)",
            ),
            (
                "attribute",
                "attribute flags, type registry and per-attribute codecs (RFC 4271)",
            ),
            (
                "aspath",
                "AS_SEQUENCE, AS_SET and the 4-octet variants including confederations (RFC 6793)",
            ),
            (
                "nlri",
                "prefix, multiprotocol reachability and unreachability (RFC 4271, RFC 4760 lineage)",
            ),
            (
                "communities",
                "well-known, extended and large communities against the IANA registries (RFC 4360, RFC 8092)",
            ),
            (
                "addpath",
                "path identifier encoding in NLRI and in capabilities (RFC 7911)",
            ),
            ("roles", "the BGP_ROLE capability and path attribute (RFC 9234)"),
            ("limits", "bounds on attribute count, AS path length and message size"),
        ],
        "api": [
            ("message", "def", "decode", "raw: bytes", "Message", "RFC 4271"),
            ("message", "def", "encode", "message: Message", "bytes", "RFC 4271"),
            ("attribute", "def", "decode_attributes", "raw: bytes", "list", "RFC 4271"),
            (
                "aspath",
                "def",
                "parse_as_path",
                "raw: bytes, four_octet: bool",
                "AsPath",
                "RFC 6793",
            ),
            (
                "nlri",
                "def",
                "parse_nlri",
                "raw: bytes, afi: int, safi: int, add_path: bool",
                "list",
                "RFC 7911",
            ),
            (
                "communities",
                "def",
                "decode_communities",
                "raw: bytes",
                "list",
                "RFC 8092",
            ),
            ("communities", "def", "decode_extended", "raw: bytes", "list", "RFC 4360"),
            ("roles", "def", "peer_role", "capability: bytes", "Role", "RFC 9234"),
            ("limits", "def", "check", "plan: ParsePlan", "None", "design"),
        ],
        "steps": [
            "M1 message framing and NOTIFICATION and KEEPALIVE handling",
            "M2 OPEN with the capability registry, including ADD-PATH and role",
            "M3 path attributes with 4-octet AS and AS4 fallback",
            "M4 multiprotocol NLRI, withdrawn and announce paths",
            "M5 community decoding against the registries, unknown types preserved",
            "M6 publication: 0.1.0 with captures from a live RIB as fixtures",
        ],
        "extras": {},
        "cli": "pathattr decode update.bin --json --registry iana",
    },
    {
        "name": "bmpkit",
        "pkg": "bmpkit",
        "title": "bmpkit -- stop screen scraping your routers",
        "desc": "BGP Monitoring Protocol version 3 collector and decoder: initiation and peer "
        "distinguishing, route monitoring with path attributes, Adj-RIB-Out and Loc-RIB "
        "mirroring, statistics and route mirroring",
        "kw": [
            "bmp",
            "bgp",
            "monitoring",
            "rib",
            "looking-glass",
            "rfc7854",
            "rfc8671",
            "rfc9069",
        ],
        "why": (
            "BMP exists precisely because obtaining route views used to mean scraping a "
            "terminal, and Python still cannot consume it. FRR, BIRD, Cisco and Juniper all "
            "emit BMP; nothing in Python reads it. The name bmp on PyPI is a retrieval library "
            "and pybmp is a BMP image handler, so the acronym is unclaimed in this sense. "
            "bmpkit decodes to the same update objects pathattr defines and hands them to a "
            "store, which is exactly the seam a looking glass, an analyst tool and a hijack "
            "detector all need.",
        ),
        "docs": [
            {
                "n": "7854",
                "status": "Proposed Standard",
                "date": "2016-06",
                "why": "BMP: common header, per peer header, route monitoring, statistics, termination and route mirroring",
            },
            {
                "n": "8671",
                "status": "Proposed Standard",
                "date": "2019-11",
                "why": "Adj-RIB-Out mirroring and the peer flag that distinguishes it",
            },
            {
                "n": "9069",
                "status": "Proposed Standard",
                "date": "2022-02",
                "why": "Loc-RIB access, the selected routes rather than the received ones",
            },
        ],
        "errata": [
            "RFC 7854 carries 3 verified errata and is updated by RFC 8671, RFC 9069, RFC 9515 and RFC 9736. Read all of them before M1: RFC 9515 and RFC 9736 were not examined during this survey and may change message handling.",
            "RFC 8671 and RFC 9069 report no errata as of 2026-10-29.",
        ],
        "prior": [
            {
                "name": "bmp",
                "version": "0.2.8",
                "date": "2026-10-16",
                "note": "block-max learned sparse retrieval, unrelated",
            },
            {
                "name": "pybmp",
                "version": "1.0.1",
                "date": "2016-11-05",
                "note": "a BMP image handler",
            },
            {
                "name": "GoBGP and HurricanE Electric BMP tooling",
                "version": "-",
                "date": "-",
                "note": "Go and C; no importable Python consumer",
            },
        ],
        "gaps": [
            "a collector that terminates many router sessions with per-peer state and no head-of-line blocking",
            "route mirroring passthrough, which is how you debug a session without touching the router",
            "correct handling of the three RIB views: Adj-RIB-In, Adj-RIB-Out and Loc-RIB",
            "stats and termination records with reason codes, so gaps in the mirrored view are visible rather than silent",
            "reconnect and sequence discipline, because TCP carries BMP and reordering is a real analyst hazard",
        ],
        "nongoals": [
            "a time series store or a web UI; it emits objects to whatever you have",
            "router configuration: BMP is a monitoring channel and this library never writes to one",
            "BGP speaker behaviour, which is pathattr's boundary and below",
        ],
        "mods": [
            (
                "header",
                "common and per peer headers with the version and flag discipline (RFC 7854)",
            ),
            (
                "messages",
                "route monitoring, statistics, peer down and up, initiation and termination, route mirroring (RFC 7854)",
            ),
            (
                "rib",
                "view selection across Adj-RIB-In, Adj-RIB-Out and Loc-RIB (RFC 8671, RFC 9069)",
            ),
            ("server", "the asyncio collector with per connection state"),
            ("mirror", "passthrough of mirrored traffic for capture and replay"),
            ("store", "the sink interface a mirrored RIB is written to"),
            ("replay", "deterministic re-reading of a capture for tests and analysts"),
        ],
        "api": [
            (
                "header",
                "def",
                "decode_common",
                "raw: bytes",
                "CommonHeader",
                "RFC 7854",
            ),
            (
                "messages",
                "def",
                "decode_route_monitoring",
                "raw: bytes, peer: PeerKey",
                "Update",
                "RFC 7854",
            ),
            ("messages", "def", "decode_statistics", "raw: bytes", "Stats", "RFC 7854"),
            (
                "rib",
                "def",
                "view_of",
                "peer: PeerKey, flags: int",
                "View",
                "RFC 8671, RFC 9069",
            ),
            (
                "server",
                "async def",
                "serve",
                "host: str, port: int, sink: Sink",
                "None",
                "RFC 7854",
            ),
            (
                "mirror",
                "def",
                "extract_bgp_message",
                "message: RouteMirroring",
                "bytes",
                "RFC 7854",
            ),
            (
                "replay",
                "def",
                "from_capture",
                "path: pathlib.Path",
                "Iterator",
                "design",
            ),
        ],
        "steps": [
            "M1 header and message codec with vectors from a live FRR or BIRD speaker",
            "M2 the collector server with per peer state and bounded buffers",
            "M3 view selection for Adj-RIB-In, Adj-RIB-Out and Loc-RIB",
            "M4 statistics, termination reasons and the mirroring passthrough",
            "M5 capture and replay tooling wired into the test suite",
            "M6 publication: 0.1.0 with a mirrored RIB comparison against a router CLI",
        ],
        "extras": {"codec": [("pathattr", "0.1")]},
        "cli": "bmpkit listen --listen 0.0.0.0:11019 --mirror ./captures",
    },
    {
        "name": "rpslkit",
        "pkg": "rpslkit",
        "title": "rpslkit -- RPSL parsing and IRR queries without a decade old dependency",
        "desc": "Routing Policy Specification Language objects, IRR database clients, and "
        "route-set and origin resolution that reports ambiguity instead of guessing",
        "kw": [
            "rpsl",
            "irr",
            "whois",
            "route-object",
            "origin",
            "rfc2622",
            "looking-glass",
        ],
        "why": (
            "IRR is still the origin authority most operators filter on, and Python's only "
            "serious tool, irrtree, last shipped 1.4.0 on 2021-06-24. Worse, the obvious "
            "package names are gone: rpsl is a Raspberry Pi sensor library and irr is a numpy "
            "joke. RFC 2622 defines the language, carries 3 verified errata and is updated by "
            "RFC 4012 and RFC 7909, and the databases disagree with each other in ways a "
            "library should surface rather than hide. rpslkit parses RPSL, queries the IRRs "
            "concurrently, resolves route sets, and reports conflicts between IRR, RPKI and "
            "observed routing as first class output.",
        ),
        "docs": [
            {
                "n": "2622",
                "status": "Proposed Standard",
                "date": "1999-06",
                "why": "RPSL: object definitions, the set expression grammar and the delete syntax",
            },
            {
                "n": "4012",
                "status": "Proposed Standard",
                "date": "2005-02",
                "why": "digest objects for secure route origin registration",
            },
            {
                "label": "IRRd database query interface",
                "status": "operational practice",
                "date": "-",
                "why": "whois style queries, the newer HTTP and REST interfaces, and per database syntax quirks",
            },
        ],
        "errata": [
            "RFC 2622 carries 3 verified errata and is updated by RFC 4012 and RFC 7909; RFC 7909 adds the as-set import semantics that most parsers get wrong. Verify both before M2.",
            "The four large IRRs differ in practice on comments, mangling and mirroring latency. Treat divergence as data and record which database answered.",
        ],
        "prior": [
            {
                "name": "irrtree",
                "version": "1.4.0",
                "date": "2021-06-24",
                "note": "the working solution, four years without a release, no asyncio",
            },
            {
                "name": "rpsl",
                "version": "0.1.dev1",
                "date": "2019-11-30",
                "note": "a Raspberry Pi sensor library squatting the acronym",
            },
            {
                "name": "irr",
                "version": "0.2",
                "date": "2021-09-28",
                "note": "a numpy joke",
            },
        ],
        "gaps": [
            "a RPSL parser that keeps source, references and comments so provenance survives",
            "concurrent queries to RIPE, RADB, NTTC, AltDB and the regional archives with per source policy",
            "route set and as set expansion with cycle detection and explicit ambiguity reporting",
            "conflict output comparing IRR assertions against RPKI assertions and observed routing",
            "prefix match semantics that say which object matched and why",
        ],
        "nongoals": [
            "generating router configuration from RPSL",
            "being an IRR server or handling maintainer authentication and object updates",
            "validating route authorisation policy, which is rpkit and pkix",
        ],
        "mods": [
            (
                "objects",
                "RPSL object classes, attributes and the reserved word set (RFC 2622)",
            ),
            (
                "parser",
                "lenient line parsing that preserves source and comments (RFC 2622)",
            ),
            (
                "sets",
                "route set and as set expansion with cycles and imports (RFC 2622, RFC 7909)",
            ),
            ("client", "whois and HTTP queries with timeouts and per source budgets"),
            ("resolve", "origin resolution for a prefix with ambiguity preserved"),
            ("compare", "IRR against RPKI and against observed routing"),
            ("sources", "registry of IRR databases, endpoints and quirks"),
        ],
        "api": [
            ("parser", "def", "parse", "text: str, source: str", "list", "RFC 2622"),
            (
                "objects",
                "def",
                "matches_prefix",
                "obj: RouteObject, prefix: str",
                "bool",
                "RFC 2622",
            ),
            (
                "sets",
                "def",
                "expand",
                "name: str, store: Store, depth: int",
                "Expansion",
                "RFC 7909",
            ),
            (
                "client",
                "async def",
                "query",
                "source: str, needle: str, budget: Budget",
                "list",
                "design",
            ),
            (
                "resolve",
                "async def",
                "origins",
                "prefix: str, sources: list",
                "list",
                "RFC 2622",
            ),
            (
                "compare",
                "def",
                "conflicts",
                "irr: list, roas: list, observed: list",
                "list",
                "design",
            ),
        ],
        "steps": [
            "M1 RPSL parser with round trip preserving comments and source",
            "M2 whois and HTTP clients for the four major databases",
            "M3 set expansion with cycle detection and ambiguity output",
            "M4 prefix origin resolution with provenance per answer",
            "M5 the IRR against RPKI against observed comparison",
            "M6 publication: 0.1.0",
        ],
        "extras": {},
        "cli": "rpslkit origins 1.2.3.0/24 --sources ripncc,radb,nttc --json",
    },
    {
        "name": "bgpfeed",
        "pkg": "bgpfeed",
        "title": "bgpfeed -- RIPE RIS and RouteViews, without the C dependency",
        "desc": "Live and archive upstream feeds: RIPE RIS websocket streaming and RouteViews "
        "BGP2K MRT deltas, with checkpointing and a normalised event model shared with "
        "bmpkit",
        "kw": [
            "ris",
            "routeviews",
            "mrt",
            "bgp",
            "streaming",
            "monitoring",
            "looking-glass",
        ],
        "why": (
            "A looking glass that only shows your own routers is a status page. The upstream "
            "view comes from RIPE RIS and RouteViews, and in Python that means the bgpstream C "
            "library with its build headaches, or hand written FTP polling. Neither name is "
            "taken on PyPI: bgpstream, ris and routeviews are all absent as of 2026-11-05. "
            "bgpfeed is the small honest client for both, emitting the same objects bmpkit "
            "emits, so anything built on one works with the other.",
        ),
        "docs": [
            {
                "n": "6396",
                "status": "Proposed Standard",
                "date": "2011-10",
                "why": "MRT, the format RouteViews publishes its updates in",
            },
            {
                "label": "RIPE RIS live API",
                "status": "operational practice",
                "date": "-",
                "why": "the websocket protocol, viewer selection and message shape",
            },
            {
                "label": "RouteViews archive layout",
                "status": "operational practice",
                "date": "-",
                "why": "per collector hourly directories, file naming and retention",
            },
        ],
        "errata": [
            "RFC 6396 carries 2 verified errata.",
            "RIS and RouteViews are operational services, not specifications: pin the endpoint and message version in tests and expect change without notice.",
        ],
        "prior": [
            {
                "name": "bgpstream",
                "version": "-",
                "date": "-",
                "note": "the C library everyone wraps; absent from PyPI (2026-11-05)",
            },
            {
                "name": "ris, routeviews, bgpfeed",
                "version": "-",
                "date": "-",
                "note": "all free on PyPI (2026-11-05)",
            },
            {
                "name": "exabgp rib scripts",
                "version": "-",
                "date": "-",
                "note": "ad hoc pollers, not a resumable client",
            },
        ],
        "gaps": [
            "a RIS websocket client with viewer selection, reconnect and gap detection",
            "a RouteViews delta poller that checkpoints by file and never re-reads or skips silently",
            "one normalised event model across live feeds, archives and BMP sessions",
            "backpressure and drop accounting, so a slow analyst does not silently lose updates",
            "honest rate limiting that respects the operators running these services",
        ],
        "nongoals": [
            "storage or query indexes, which is asnkit",
            "analysis and alerting, which is routevalid",
            "running a collector: these are clients of other people's infrastructure",
        ],
        "mods": [
            ("model", "the common event and update objects shared with bmpkit"),
            ("ris", "the websocket protocol, viewers and resubscription"),
            ("routeviews", "archive discovery, delta polling and checkpoints"),
            ("mrt", "UPDATE_FILE and TABLE_DUMP reading via asnkit"),
            ("state", "resume points and gap accounting per source"),
            ("budget", "politeness: concurrency caps, jitter and backoff"),
        ],
        "api": [
            (
                "ris",
                "async def",
                "subscribe",
                "viewers: list, collectors: list, sink: Sink",
                "Stream",
                "design",
            ),
            (
                "routeviews",
                "async def",
                "follow",
                "collectors: list, since: datetime, sink: Sink",
                "Stream",
                "design",
            ),
            (
                "mrt",
                "def",
                "iter_updates",
                "path: pathlib.Path",
                "Iterator",
                "RFC 6396",
            ),
            (
                "state",
                "def",
                "checkpoint",
                "source: str, position: object",
                "None",
                "design",
            ),
            ("state", "def", "resume", "source: str", "object", "design"),
            (
                "budget",
                "def",
                "policy",
                "max_concurrent: int, jitter: timedelta",
                "Budget",
                "design",
            ),
        ],
        "steps": [
            "M1 the shared event model, and MRT update reading through asnkit",
            "M2 RIS websocket client with reconnect and gap reporting",
            "M3 RouteViews delta poller with checkpoints",
            "M4 politeness and drop accounting",
            "M5 a replay fixture so downstream tests never touch the network",
            "M6 publication: 0.1.0",
        ],
        "extras": {"mrt": [("asnkit", "0.1")]},
        "cli": "bgpfeed ris --view rrc00 --collector rrc00-collector-1 --out events.ndjson",
    },
    {
        "name": "routevalid",
        "pkg": "routevalid",
        "title": "routevalid -- hijack and leak detection with evidence attached",
        "desc": "Correlates BMP sessions, RIS and RouteViews feeds, RPKI assertions, RTR "
        "updates and IRR objects into typed events with a replayable evidence bundle",
        "kw": [
            "hijack",
            "route-leak",
            "rov",
            "monitoring",
            "rpki",
            "bgp",
            "rfc9234",
            "detection",
        ],
        "why": (
            "Detection tools either are research prototypes or are hosted dashboards you cannot "
            "self host. What is missing is a library: given observations from your own BMP "
            "sessions plus RIS and RouteViews, plus RPKI from rpkit and RTR state from rtrkit, "
            "emit typed events with the evidence that justified each one. RFC 9234 gives the "
            "role information that makes leaks checkable against declared relationships rather "
            "than guessed, and that document has no errata and almost no implementations, which "
            "is exactly the kind of gap this portfolio exists for.",
        ),
        "docs": [
            {
                "n": "9234",
                "status": "Proposed Standard",
                "date": "2022-05",
                "why": "roles in OPEN and UPDATE: the basis for leak detection against declared relationships",
            },
            {
                "n": "6480",
                "status": "Informational",
                "date": "2012-02",
                "why": "the RPKI architecture whose assertions an origin check consumes",
            },
            {
                "n": "9324",
                "status": "Proposed Standard",
                "date": "2022-12",
                "why": "why fresh RPKI data must not trigger a route refresh when re-evaluating",
            },
            {
                "n": "6396",
                "status": "Proposed Standard",
                "date": "2011-10",
                "why": "the archive format for replaying history against a detection rule",
            },
        ],
        "errata": [
            "RFC 9234 reports no errata as of 2026-10-29, and deployment is thin enough that you should expect to test against peers who do not send the attribute.",
            "RFC 6480 has 1 erratum on file, none verified; RFC 9324 updates RFC 8481 and should be read together with it.",
        ],
        "prior": [
            {
                "name": "STEAL-179 and similar research tools",
                "version": "-",
                "date": "-",
                "note": "research artefacts, not maintained libraries",
            },
            {
                "name": "hosted monitoring dashboards",
                "version": "-",
                "date": "-",
                "note": "BGPStream based services: useful, but not something you can embed",
            },
            {
                "name": "routevalid, leakkit, stealer, bgp-hijack",
                "version": "-",
                "date": "-",
                "note": "all free on PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "prefix visibility tracking: who announces it, from which AS, seen by which collectors",
            "origin checks combining RPKI state, RPSL assertions and observed AS paths with explicit disagreement handling",
            "leak checks using declared roles where available and inferred relationships where not",
            "confidence scoring from collector diversity, so one vantage point cannot raise a page",
            "an evidence bundle per event, replayable from the raw observations",
        ],
        "nongoals": [
            "a dashboard, an alerting pipeline or a ticket system",
            "storage engine design: it consumes a sink",
            "community based mitigation or any action against a router: detection only",
        ],
        "mods": [
            ("observe", "the normalised observation model from bmpkit and bgpfeed"),
            (
                "visibility",
                "prefix and AS visibility tracking over collectors and time",
            ),
            ("origin", "origin checks combining RPKI, RPSL and observed paths"),
            ("leak", "role and relationship checks on AS paths (RFC 9234)"),
            ("score", "confidence from collector diversity and disagreement"),
            ("event", "typed events with severity, evidence and replay references"),
            ("replay", "deterministic re-evaluation of history against a rule set"),
            ("rules", "the policy object deciding what counts as an event"),
        ],
        "api": [
            (
                "observe",
                "def",
                "record",
                "update: Update, source: Source, at: datetime",
                "None",
                "design",
            ),
            (
                "visibility",
                "def",
                "announcers",
                "prefix: str, window: timedelta",
                "list",
                "design",
            ),
            (
                "origin",
                "def",
                "check_origin",
                "prefix: str, asn: int, roas: list, irr: list",
                "OriginVerdict",
                "RFC 6480",
            ),
            (
                "leak",
                "def",
                "check_path",
                "asn_path: list, relationships: Relationships",
                "LeakVerdict",
                "RFC 9234",
            ),
            (
                "score",
                "def",
                "confidence",
                "observations: list, diversity: int",
                "float",
                "design",
            ),
            (
                "event",
                "def",
                "emit",
                "kind: str, evidence: Evidence, severity: str",
                "Event",
                "design",
            ),
            (
                "replay",
                "def",
                "reevaluate",
                "store: Store, rules: Rules, since: datetime",
                "list",
                "RFC 9324",
            ),
        ],
        "steps": [
            "M1 the observation model and visibility tracking",
            "M2 origin checks against rpkit assertions and rpslkit output",
            "M3 role based leak checks with an inferred relationship fallback",
            "M4 confidence scoring and the event schema with evidence",
            "M5 replay, then a historical corpus to measure false positives",
            "M6 publication: 0.1.0 with a measured precision report",
        ],
        "extras": {
            "feeds": [("bmpkit", "0.1"), ("bgpfeed", "0.1")],
            "rpki": [("rpkit", "0.1"), ("rtrkit", "0.1")],
        },
        "cli": "routevalid watch --prefix 1.2.3.0/24 --sources bmp,ris --min-confidence 0.8",
    },
    {
        "name": "lgc",
        "pkg": "lgc",
        "title": "lgc -- looking glass client that returns objects, not terminal text",
        "desc": "Typed looking glass clients: the de-facto LGC and LGS wire protocol, HTTP and "
        "SSH backends, and vendor output parsers that produce pathattr objects",
        "kw": [
            "looking-glass",
            "lgc",
            "lgs",
            "bgp",
            "operations",
            "parsers",
            "frr",
            "bird",
        ],
        "why": (
            "The last mile of every looking glass is text: someone parses show ip bgp output "
            "with a regular expression written in a hurry. The de-facto LGC and LGS protocol has "
            "no Python client, the old looking-glass package died in 2019, and pybird only "
            "covers BIRD. lgc is a client library with one promise: every query returns typed "
            "objects from pathattr and asnkit, and where a device can only give text a named "
            "parser with tests owns the conversion. It is read only by construction, which is "
            "the property that lets you point it at production.",
        ),
        "docs": [
            {
                "label": "LGC and LGS protocol",
                "status": "de-facto practice",
                "date": "-",
                "why": "the request, response and progress framing used by open source looking glasses",
            },
            {
                "label": "FRR and BIRD command interfaces",
                "status": "implementation practice",
                "date": "-",
                "why": "vtysh, the FRR REST API and birdc JSON output",
            },
            {
                "n": "4271",
                "status": "Draft Standard",
                "date": "2006-01",
                "why": "the semantics every parser ultimately claims to render",
            },
        ],
        "errata": [
            "LGC, LGS, FRR and BIRD interfaces are not specifications with errata: pin versions in fixtures and treat output drift as a bug in the parser, not the device.",
            "Vendor text formats change between releases without notice, which is why every parser needs a captured fixture per version.",
        ],
        "prior": [
            {
                "name": "looking-glass",
                "version": "1.0.4",
                "date": "2019-03-26",
                "note": "a web visualisation tool, abandoned",
            },
            {
                "name": "pybird",
                "version": "1.2.0",
                "date": "2023-02-08",
                "note": "BIRD only, no typed BGP objects",
            },
            {
                "name": "lgc, birdc, frr, gobgp, quagga",
                "version": "-",
                "date": "-",
                "note": "all free on PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "an LGC and LGS client with capability discovery, timeouts and an allow list of query types",
            "parsers per device and version producing pathattr objects rather than strings",
            "RIB, RIB-in, RIB-out and per-prefix detail queries with one return type",
            "read only enforcement in the type system, so a caller cannot send a configuration command by accident",
            "concurrent multi site queries with per site latency and error accounting",
        ],
        "nongoals": [
            "a web front end or the RIB viewer itself; it returns objects you can render",
            "device configuration or any write path, ever",
            "generic network automation, which is scrapli, netmiko and napalm territory",
        ],
        "mods": [
            ("protocol", "LGC and LGS framing, request types and progress reporting"),
            ("transport", "HTTP, SSH and raw TCP backends with budgets and host keys"),
            ("parsers", "per vendor and version output conversion into typed objects"),
            (
                "query",
                "the typed query surface: rib, ribin, ribout, detail, traceroute",
            ),
            ("sites", "registry of looking glasses with capabilities and health"),
            ("guard", "read only enforcement and an explicit allow list"),
            ("federation", "concurrent queries across sites with per site accounting"),
        ],
        "api": [
            ("protocol", "def", "encode_request", "query: Query", "bytes", "design"),
            ("protocol", "def", "decode_response", "raw: bytes", "Response", "design"),
            (
                "transport",
                "async def",
                "call",
                "site: Site, query: Query, budget: Budget",
                "Response",
                "design",
            ),
            (
                "parsers",
                "def",
                "parse_rib",
                "text: str, flavour: str",
                "list",
                "RFC 4271",
            ),
            (
                "query",
                "async def",
                "rib",
                "site: Site, prefix: str",
                "list",
                "RFC 4271",
            ),
            (
                "query",
                "async def",
                "detail",
                "site: Site, prefix: str",
                "list",
                "RFC 4271",
            ),
            ("guard", "def", "assert_read_only", "query: Query", "None", "design"),
            (
                "federation",
                "async def",
                "query_many",
                "sites: list, query: Query",
                "list",
                "design",
            ),
        ],
        "steps": [
            "M1 the query and result model plus read only enforcement",
            "M2 LGS and LGC transport with capability discovery",
            "M3 FRR and BIRD parsers with captured fixtures per version",
            "M4 SSH and HTTP backends with host key pinning",
            "M5 multi site federation with per site accounting",
            "M6 publication: 0.1.0 with a worked example composing rpkit state",
        ],
        "extras": {"codec": [("pathattr", "0.1")]},
        "cli": "lgc query --site route-server-example --prefix 1.2.3.0/24 --detail --json",
    },
]
ALL_PROJECTS = (
    PROJECTS_A
    + PROJECTS_B
    + PROJECTS_C
    + PROJECTS_D
    + PROJECTS_E
    + PROJECTS_F
    + PROJECTS_G
    + PROJECTS_H
    + PROJECTS_I
)
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

`certledger/` and `keyproof/` hold plans, trust models and
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


# This file used to be assembled from parts/partNN.py by numeric concatenation, and the comment that
# stood here explained why no __main__ guard appeared at this point in the middle of the file: the
# guard had to live in the last part, because a guard placed earlier would call run() before the
# wrappers that follow had reassigned build, and every artefact those parts owned would silently stop
# being written. parts/ was deleted on 2026-11-07 as a stale second copy of these same template strings
# - forge.py never read it, and the duplication had already caused a near-edit of one copy and not the
# other. The concatenation order is still the reason the guard sits at the very end: keep it there.
# Recover the original parts from git history if the assembly is ever needed again.

# ---------------------------------------------------------------------------
# Part 20: portfolio position (docs/plan.md)
#
# PORTFOLIO.md at the workspace root decides which projects are worked on, in
# what order, and against what. ROADMAP.md inside a project decides protocol
# obligations. Nothing inside a generated repository carried the first of
# those, so an agent reading one project alone could not tell that its wave is
# 4, that two other projects are allowed to be in flight before it, or that
# the codec it plans to verify signatures with has no code anywhere.
#
# What this part writes is a transcription of PORTFOLIO.md sections 4, 6 and 7
# - tier, wave, and the arrows that mean "cannot deliver behaviour without" -
# rather than a reinterpretation of them. Section 10 of that file records the
# ASN.1 role having been mis-assigned to asnkit, with the correction that
# until asn1core exists no certificate-shaped project can ship behaviour. Every
# plan that cites asn1core repeats that sentence, because a caveat kept in one
# file nobody opens is a caveat that gets planned around.
#
# This part also owns the __main__ guard, moved from part 19: it has to run
# after every wrapper in the build chain has been installed, so the last part
# is the one that calls run().
# ---------------------------------------------------------------------------

# name -> (tier, wave, hard dependencies). Transcribed from PORTFOLIO.md
# sections 4 and 6; an arrow means "cannot deliver behaviour without".
POSITION = {
    # Tier 1, wave 1: the chokepoint itself.
    "rpkit": (1, 1, ("asn1core",)),
    # Tier 2, wave 2: the certificate cluster.
    "ctspy": (2, 2, ("asn1core",)),
    "pkix": (2, 2, ("asn1core",)),
    "revokekit": (2, 2, ("asn1core", "pkix")),
    # Tier 2, wave 2: the routing-security cluster, anchored on rpkit.
    "rtrkit": (2, 2, ("rpkit",)),
    "routevalid": (2, 2, ("rpkit", "rtrkit")),
    # Tier 2, wave 4: naming and address allocation.
    "dnssd-srp": (2, 4, ("namespy",)),
    "leasespy": (2, 4, ()),
    # Tier 3, wave 3: the routing-operations story.
    "asnkit": (3, 3, ("rpkit", "rtrkit")),
    "bgpfeed": (3, 3, ("asnkit",)),
    # Tier 3, wave 3: solid gaps with no dependency in front of them.
    "rpslkit": (3, 3, ()),
    "bmpkit": (3, 3, ()),
    "pathattr": (3, 3, ()),
    "lgc": (3, 3, ()),
    "turnkit": (3, 3, ()),
    "ohttp": (3, 3, ()),
    "h3tunnel": (3, 3, ()),
    "sfields": (3, 3, ()),
    "syslogkit": (3, 3, ()),
    # Tier 3, wave 2: certificate-shaped, so gated on the substrate.
    "signeddata": (3, 2, ("asn1core",)),
    # Tier 4, wave 5: the rest, in tier order, one at a time.
    "ntspy": (4, 5, ()),
    "tacacs": (4, 5, ()),
    "pgpenv": (4, 5, ("asn1core",)),
    "enrollkit": (4, 5, ("asn1core", "pkix")),
    "shaken": (4, 5, ("asn1core",)),
    "srtpkit": (4, 5, ("asn1core",)),
    "cwmp": (4, 5, ()),
    "devicespy": (4, 5, ()),
}

TIER_NOTE = {
    1: "Tier 1 is work on now: its absence hurts, and finishing it makes several "
       "other projects cheaper.",
    2: "Tier 2 is next: high value, and each entry needs something from Tier 1 "
       "before it can produce behaviour.",
    3: "Tier 3 is planned: a solid gap with no urgency, and better work once "
       "Tier 1 exists.",
    4: "Tier 4 is hold: a real protocol with a weaker case for now, whether "
       "through adequate incumbents, a narrow audience or a long dependency chain.",
}

WAVE_NOTE = {
    1: "the chokepoint and the ambient-trust hole",
    2: "the first real answer",
    3: "the routing-operations story",
    4: "naming and address allocation",
    5: "the rest in tier order, one at a time",
}


# One sentence per edge, on why the arrow is a hard dependency rather than a
# preference. Keyed by (project, dependency).
DEPENDS_WHY = {
    ("rpkit", "asn1core"): "every RPKI signed object rpkit fetches is a CMS structure "
                         "that has to be decoded from the bytes it arrived as before "
                         "its signature means anything, and that codec is asn1core's job",
    ("ctspy", "asn1core"): "a signed certificate timestamp and a Merkle leaf are verified "
                         "over encoded bytes, so an inclusion proof is only as good as "
                         "a codec that keeps the original bytes instead of re-encoding "
                         "them",
    ("pkix", "asn1core"): "RFC 5280 section 6 validates paths over certificates and CRLs, "
                        "and RFC 5280 section 4.1.3.2 checks the CA signature over the "
                        "DER encoding of the TBSCertificate, so validation cannot be "
                        "written above a codec that re-encodes what it parsed",
    ("revokekit", "asn1core"): "an OCSP response is a signed DER object and a CRL is DER "
                             "all the way down, so a revocation answer that cannot be "
                             "re-derived from the bytes it arrived in is not an answer",
    ("revokekit", "pkix"): "deciding whether a responder may sign for a CA is path "
                           "validation against the same trust anchors pkix already "
                           "resolves, and a second validator here would only disagree "
                           "with the first",
    ("rtrkit", "rpkit"): "RTR announces what has been validated, so the serial "
                         "discipline of a cache server is worth nothing unless the "
                         "assertions underneath it came from rpkit's repository fetch "
                         "and signed-object checks",
    ("routevalid", "rpkit"): "a validity verdict is an RPKI assertion plus its anchor, "
                             "and rpkit is the only thing in this portfolio that fetches "
                             "and validates the repository content",
    ("routevalid", "rtrkit"): "what a router was actually told to believe is the RTR "
                              "stream, and without it there is no live state to join a "
                              "RIB dump or an observed AS path against",
    ("dnssd-srp", "namespy"): "SRP is unicast DNS with authenticated updates and pushed "
                              "record changes, so the message codec, the iterative "
                              "resolver and the DNSSEC, DoT and DoH legs are namespy's "
                              "and are shared rather than rebuilt",
    ("asnkit", "rpkit"): "the question asnkit answers is which AS, on which date, and "
                         "what did RPKI say about it, and the last clause is an rpkit "
                         "assertion rather than anything derivable from a RIB dump",
    ("asnkit", "rtrkit"): "validation state is joined at query time from the RTR feed "
                          "rtrkit holds, because a prefix's history with no state "
                          "announced for it is a lookup with no answer attached",
    ("bgpfeed", "asnkit"): "a feed is a stream of UPDATE records until its prefixes "
                           "resolve to an AS with a date and a validation state, which "
                           "is the lookup asnkit owns",
    ("signeddata", "asn1core"): "CMS is a DER container end to end - SignedData, "
                              "EnvelopedData and AuthenticatedData, their attribute "
                              "sets, and the issuer and serial that identifies a signer "
                              "- so the encoding layer underneath is not this project's",
    ("enrollkit", "asn1core"): "CMP messages, CRMF requests and PKCS#10 are all DER, and a "
                             "request whose encoding changes on the way to the CA is an "
                             "enrollment for a different key",
    ("enrollkit", "pkix"): "an issued certificate is only useful once it validates to a "
                           "trust anchor, and that verdict belongs to pkix rather than "
                           "being restated at the end of an enrollment flow",
    ("pgpenv", "asn1core"): "OpenPGP bindings reach X.509 identities through encoded key "
                          "material, and pgpenv is scoped to packets and keys, so "
                          "reading the DER under a key belongs to asn1core",
    ("shaken", "asn1core"): "a PASSporT is only as trustworthy as the certificate the "
                          "originating provider publishes at its x5u, and parsing that "
                          "certificate is asn1core's job, not shaken's",
    ("srtpkit", "asn1core"): "RFC 5764 key establishment presents certificates, and SRTP "
                           "keys are only as strong as the identity that negotiated "
                           "them, so certificate parsing stays in asn1core",
}

# How to state each dependency's current existence. An arrow to something that
# is not there is said as missing, not as a to-do: PORTFOLIO.md section 10 is
# explicit that until asn1core exists no certificate-shaped project can ship
# behaviour, and a shell that ships none is a gate of its own.
DEP_STATE = {
    "asn1core": (
        "does not exist yet",
        "There is no asn1core project and no asn1core code: the workspace holds only its "
        "extraction plan at ../../asn1core/PLAN.md.",
    ),
    "pkix": (
        "exists only as a generated shell, with no protocol behaviour yet",
        "Its public functions raise NotImplementedError until its own roadmap rows are "
        "done, so a row here that consumes it cannot be closed on the strength of a "
        "directory existing.",
    ),
    "rpkit": (
        "exists only as a generated shell, with no protocol behaviour yet",
        "Its public functions raise NotImplementedError until its own roadmap rows are "
        "done, so a row here that consumes it cannot be closed on the strength of a "
        "directory existing.",
    ),
    "rtrkit": (
        "exists only as a generated shell, with no protocol behaviour yet",
        "Its public functions raise NotImplementedError until its own roadmap rows are "
        "done, so a row here that consumes it cannot be closed on the strength of a "
        "directory existing.",
    ),
    "asnkit": (
        "exists only as a generated shell, with no protocol behaviour yet",
        "Its public functions raise NotImplementedError until its own roadmap rows are "
        "done, so a row here that consumes it cannot be closed on the strength of a "
        "directory existing.",
    ),
    "namespy": (
        "exists",
        "namespy is implemented software outside the generator - a wire codec, an "
        "iterative resolver, DNSSEC, DoT and DoH legs - and it is the one place in this "
        "portfolio where the pattern has been proven end to end.",
    ),
}

# Edges the portfolio plan records as candidate rather than load-bearing.
CANDIDATE_EDGES = {("dnssd-srp", "namespy")}
CANDIDATE_NOTE = (
    "This edge is recorded as a candidate: the message layer and the resolver are shared "
    "with namespy, and the stateful half - SRP updates, registrar checks and pushed "
    "record changes - is what is built here."
)

INTRO = (
    "This file is generated by sdk-forge/forge.py from the portfolio plan, and a hand "
    "edit here is overwritten at the next run. Two documents govern this project and "
    "they govern different things: the obligation table in "
    "[../ROADMAP.md](../ROADMAP.md) governs protocol work - which rows exist, and what "
    "evidence closes one - and this file governs sequencing, which is which wave this "
    "project sits in, what has to exist before it can ship behaviour, and what must not "
    "be started while it is unfinished. "
    "[PORTFOLIO.md](../../PORTFOLIO.md) at the workspace root is the authority on both, "
    "so a change to a tier, a wave or an arrow is made there and regenerated here, never "
    "the other way round."
)

NO_DEPS_NOTE = (
    "None. The portfolio plan puts no other project between this one and a first "
    "release: every obligation in [../ROADMAP.md](../ROADMAP.md) is this repository's "
    "own, and nothing "
    "outside it has to land first. That cuts both ways - a missing dependency is never "
    "the reason this project has not shipped, and its wave position is the only thing "
    "holding it back."
)

BLOCKED_NOTE = (
    "**Blocked, not in progress.** asn1core does not exist yet, so @NAME@ cannot ship "
    "behaviour until asn1core does. A roadmap row that parses, encodes or verifies a DER "
    "structure is not deferred work here: it is gated on a project that has no code and "
    "no test suite. Any plan, milestone or release note that cites asn1core says blocked "
    "rather than in progress, and no release of @NAME@ is promised before asn1core has one "
    "of its own."
)

SHELL_NOTE = (
    "A dependency that exists only as a shell is the same gate in weaker form: @DEPS@ "
    "@AGREE@ a directory, CI and an obligation table, and no behaviour, so work here can "
    "be designed against such a dependency and cannot be finished against it."
)

RULES = [
    "At most two projects in the portfolio carry real effort at once. A third is not "
    "started, and no obligation is taken here, while those two are open.",
    "No new shell is created while any Tier 1 project still has an unimplemented "
    "obligation. Twenty-eight generated READMEs are already the maintenance liability, "
    "and the failure mode of this portfolio is prose outrunning code rather than "
    "under-building.",
    "A project freezes to Tier 4 when its first release finds no external user, and a "
    "shell is retired publicly when a competitor ships what it promised rather than left "
    "to rot - the retirement is announced, not a README quietly left to go stale.",
]

POINTER = (
    "Protocol facts come from docs/rfc-map.md and the RFC Editor record, never from "
    "memory. This file positions the work; it is not a source for anything a row cites."
)


# Dependencies the state table above describes as shells, derived rather than
# repeated so the two cannot disagree about what a shell is.
SHELL_DEPS = frozenset(dep for dep, state in DEP_STATE.items() if "shell" in state[0])


def para(text, width=DOC_WIDTH):
    """Wrap one prose paragraph to the generator's document width."""
    return "\n".join(wrap(collapse(text), width))


def bullet(text, width=DOC_WIDTH):
    """Wrap one prose paragraph as a hyphen bullet with a hanging indent."""
    return "\n".join(wrap(collapse(text), width, "  ", "- "))


def dep_line(name, dep):
    """One dependency bullet: the edge, why it is hard, and whether it exists."""
    why = DEPENDS_WHY.get((name, dep), "the portfolio plan records this as a hard dependency")
    label, detail = DEP_STATE[dep]
    text = "**" + dep + "** - " + why + ". **Status: " + label + ".** " + detail
    if (name, dep) in CANDIDATE_EDGES:
        text += " " + CANDIDATE_NOTE
    return bullet(text)


def position_block(name):
    tier, wave, _deps = POSITION[name]
    return para("**Tier " + str(tier) + ", wave " + str(wave) + "** - " + WAVE_NOTE[wave]
                + ". " + TIER_NOTE[tier])


def depends_block(name):
    deps = POSITION[name][2]
    if not deps:
        return para(NO_DEPS_NOTE)
    blocks = ["\n".join(dep_line(name, dep) for dep in deps)]
    shells = sorted(dep for dep in deps if dep in SHELL_DEPS)
    if shells:
        blocks.append(
            para(
                subs(
                    SHELL_NOTE,
                    {
                        "DEPS": ", ".join(shells),
                        "AGREE": "has" if len(shells) == 1 else "have",
                    },
                )
            )
        )
    if "asn1core" in deps:
        blocks.append(para(subs(BLOCKED_NOTE, {"NAME": name})))
    return "\n\n".join(blocks)


def rules_block():
    return "\n".join(bullet(rule) for rule in RULES)


def render_plan(p):
    """Render docs/plan.md: where this project sits, what gates it, what constrains it."""
    name = p["name"]
    return "\n".join(
        [
            "# Portfolio position",
            "",
            para(INTRO),
            "",
            "## Position",
            "",
            position_block(name),
            "",
            "## Depends on",
            "",
            depends_block(name),
            "",
            "## Sequencing rules",
            "",
            rules_block(),
            "",
            para(POINTER),
        ]
    ).strip() + "\n"


def write_plan(path, text):
    """Write one generated document as ASCII text with LF endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = ascii_prose(text).replace("\r\n", "\n")
    if not body.endswith("\n"):
        body += "\n"
    path.write_text(body, encoding="utf-8", newline="\n")


# Captured under a part-specific name. Every part lands in one module namespace,
# so reusing part 19's `_ORIG_BUILD` here would rebind the name part 19's wrapper
# reads and make the two wrappers call each other forever.
_BUILD_BEFORE_POSITIONS = build


def build(p):
    count = _BUILD_BEFORE_POSITIONS(p)
    name = p["name"]
    # Loud rather than skipped: a project with no row here is a project whose wave
    # nobody decided, and quietly omitting its plan.md is how a portfolio document
    # starts lying about the work.
    if name not in POSITION:
        raise KeyError(name + ": no POSITION row, so its tier and wave are undecided")
    write_plan(ROOT / name / "docs" / "plan.md", render_plan(p))
    return count + 1


if __name__ == "__main__":
    raise SystemExit(run())

