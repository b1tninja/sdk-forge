"""Build the multi-valued-RDN fixture the survey showed the trust store does not contain.

`probe_name_survey.py` looked at 150 names in 75 shipped root certificates and found 577
relative distinguished names, **every one of them single-valued**, and **no PrintableString at
all** - 520 of the values are TeletexString. `VECTORS.md` asks for a certificate with multi-valued
RDNs and mixed PrintableString and UTF8String, so the store cannot supply it and it has to be
made. It is a generated document and is labelled as one everywhere it is referenced; it is not
evidence about what CAs issue, only about how the parser handles a shape that is legal and that
path validation depends on.

Signing is done here, in a scratch probe, on purpose: `asn1core` is scoped to encoding and
canonicalisation and does not do cryptography, so the key pair and the signature belong to the
fixture generator rather than to the library.

Run: `python probe_name_fixture.py` from D:\\code\\sdk-forge.
"""

from __future__ import annotations

import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

FIXTURE = "D:/code/asn1core/tests/fixtures/multivalue-rdn.der"

# One RDN deliberately carries two attributes, and another carries a value with interior double
# spaces and non-ASCII characters, which is what §7.1's string preparation has to normalise.
rdn_multi = x509.RelativeDistinguishedName(
    [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),  # C is PrintableString
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Example  Université  S.A."),  # UTF8String
    ]
)
name = x509.Name(
    [
        rdn_multi,
        x509.RelativeDistinguishedName(
            [x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Test Services")]
        ),
        x509.RelativeDistinguishedName(
            [x509.NameAttribute(NameOID.LOCALITY_NAME, "  Paris  ")]  # padded
        ),
        x509.RelativeDistinguishedName(
            [x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Île-de-France")]
        ),
        x509.RelativeDistinguishedName(
            [x509.NameAttribute(NameOID.COMMON_NAME, "Multi Valued Root CA #1")]
        ),
        x509.RelativeDistinguishedName(
            [x509.NameAttribute(NameOID.DOMAIN_COMPONENT, "example")]
        ),
        x509.RelativeDistinguishedName(
            [x509.NameAttribute(NameOID.EMAIL_ADDRESS, "pki@example.test")]
        ),
    ]
)

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
# Serial and dates are fixed so the document is stable apart from the key, which is generated
# fresh each run. That means the fixture's own digest is deliberately not pinned anywhere: pinning
# it would fail the next time the file is regenerated. What is pinned in the tests is the name -
# its structure, its attribute types and its rendering - because none of that depends on the key.
builder = (
    x509.CertificateBuilder()
    .subject_name(name)
    .issuer_name(name)
    .public_key(key.public_key())
    .serial_number(42)
    .not_valid_before(datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc))
    .not_valid_after(datetime.datetime(2034, 1, 1, tzinfo=datetime.timezone.utc))
)
der = builder.sign(key, hashes.SHA256()).public_bytes(Encoding.DER)
with open(FIXTURE, "wb") as handle:
    handle.write(der)

import hashlib  # noqa: E402  (after the write so a failure leaves no half-written fixture)

print(f"wrote {FIXTURE}")
print(f"  bytes  {len(der)}")
print(f"  sha256 {hashlib.sha256(der).hexdigest()}")
print(f"  cryptography rfc4514 subject: {name.rfc4514_string()}")
for rdn in name.rdns:
    print(f"  rdn arity {len(rdn)}: {[a.oid.dotted_string for a in rdn]}")
