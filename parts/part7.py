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
