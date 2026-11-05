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
