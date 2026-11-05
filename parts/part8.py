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
