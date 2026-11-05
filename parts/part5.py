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
