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
