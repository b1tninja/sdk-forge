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
