"""What the two vendored fixtures say about time, from both parsers.

Feeds the frozen expectations in asn1core's `tests/test_time_corpus.py`. The dates come from
`cryptography` and the bytes come from asn1core's own node walk, printed side by side so the test
can pin a tag, a length, a spelling and a `datetime` without any of it being derived from the code
under test.
"""

from __future__ import annotations

import sys

from cryptography import x509

sys.path.insert(0, "D:/code/asn1core")

from asn1core import certificate_parts, decode  # noqa: E402

for name in ("root-ecdsa.der", "root-rsa.der"):
    der = open(f"D:/code/asn1core/tests/fixtures/{name}", "rb").read()
    cert = x509.load_der_x509_certificate(der)
    parts = certificate_parts(der)
    tbs, _ = decode(parts.tbs_certificate, der=True)
    # The validity is the only SEQUENCE whose two children are both time tags. Matching on
    # "a SEQUENCE with two children" would land on the AlgorithmIdentifier first.
    validity = next(
        (
            c
            for c in tbs.children
            if c.tag.number == 16 and len(c.children) == 2 and all(
                k.tag.number in (23, 24) for k in c.children
            )
        ),
        None,
    )
    print(name)
    print(f"  cryptography notBefore={cert.not_valid_before_utc!r}")
    print(f"  cryptography notAfter ={cert.not_valid_after_utc!r}")
    if validity is None:
        print("  no validity candidate found")
        continue
    for child in validity.children:
        tag = "UTCTime" if child.tag.number == 23 else "GeneralizedTime"
        print(f"  asn1core  {tag:<15} len={len(child.payload or b'')} ascii={child.payload!r}")
