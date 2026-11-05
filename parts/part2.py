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
