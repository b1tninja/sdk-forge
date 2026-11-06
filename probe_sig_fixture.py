"""Generate the two remaining end-to-end fixtures `VECTORS.md` asks for.

Fixture 2 - an ECDSA certificate whose `r` carries a leading zero byte and whose `s` does not. This
is the classic hand-written-INTEGER trap: a codec that "canonicalises" away the 0x00 padding turns
a valid signature into a corrupt one, silently, at exactly the layer that should not be touching it.

Fixture 3 - a CRL with one revoked entry whose reasonCode is keyCompromise, which exercises the
shapes a certificate does not: `nextUpdate` absent, `crlEntryExtensions` carried as `[0]`,
`crlReason` as ENUMERATED, and the default-valued `unmapped(0)` case where an absent reason code
means something specific.

**Not byte-reproducible, and that is recorded rather than glossed over.** The signing key is
derived from a fixed scalar and the serial numbers and dates are fixed, but the ECDSA nonces in
this build are not RFC 6979 deterministic - measured, not assumed: the first run found a padded `r`
at serial 1 and the next found one at serial 5. So regeneration produces a different document with
the same shape, and the fixtures' digests are therefore documented in `VECTORS.md` as "as
committed" rather than asserted in tests, which check structure instead. The private scalar stays
here in a scratch probe and never enters the library repository: the fixtures are public documents,
and the key is a throwaway used only to make them.
"""

from __future__ import annotations

import datetime
import hashlib

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID, ObjectIdentifier

FIXTURES = "D:/code/asn1core/tests/fixtures"
CURVE = ec.SECP256R1()
# An arbitrary fixed scalar. Not a secret, and not used for anything but signing these fixtures.
SCALAR = 0x0C0FFE0D00D10E55151A2B3C4D5E6F708192A3B4C5D6E7F8091A2B3C4D5E6F70
key = ec.derive_private_key(SCALAR, CURVE)
name = x509.Name(
    [
        x509.NameAttribute(NameOID.COMMON_NAME, "Padded r Test CA"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "asn1core fixtures"),
    ]
)
EPOCH = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)


def der_integers(signature: bytes) -> tuple[bytes, bytes]:
    """Pull the two INTEGER content octets out of a DER ECDSA-Sig-Value without a parser."""
    inner = signature[2:]  # skip SEQUENCE tag+length
    r_len = inner[1]
    r = inner[2 : 2 + r_len]
    rest = inner[2 + r_len :]
    s_len = rest[1]
    return r, rest[2 : 2 + s_len]


def build_ecdsa_cert() -> bytes:
    serial = 0
    while True:
        serial += 1
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(serial)
            .not_valid_before(EPOCH)
            .not_valid_after(EPOCH + datetime.timedelta(days=3650))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(key, hashes.SHA256())
        )
        r, s = der_integers(cert.signature)
        if len(r) == 33 and r[0] == 0x00 and len(s) == 32 and s[0] != 0x00:
            print(f"  ecdsa fixture: serial={serial} r={len(r)} bytes (padded), s={len(s)} bytes")
            return cert.public_bytes(Encoding.DER)
        if serial > 5000:  # pragma: no cover - would mean the shape is unreachable
            raise SystemExit("no padded-r signature found in 5000 attempts")


def build_crl() -> bytes:
    entry = (
        x509.RevokedCertificateBuilder()
        .serial_number(101)
        .revocation_date(EPOCH)
        .add_extension(x509.CRLReason(x509.ReasonFlags.key_compromise), critical=False)
        .build()
    )
    plain = (
        x509.RevokedCertificateBuilder()
        .serial_number(102)
        .revocation_date(EPOCH + datetime.timedelta(days=1))
        .build()
    )
    crl = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(name)
        .last_update(EPOCH)
        .next_update(EPOCH + datetime.timedelta(days=365))
        .add_revoked_certificate(entry)
        .add_revoked_certificate(plain)
        .add_extension(x509.CRLNumber(7), critical=False)
        .sign(key, hashes.SHA256())
    )
    print(f"  crl fixture: {len(crl.public_bytes(Encoding.DER))} bytes, 2 revoked entries")
    return crl.public_bytes(Encoding.DER)


for filename, der in (
    ("ecdsa-padded-r.der", build_ecdsa_cert()),
    ("crl-keycompromise.der", build_crl()),
):
    path = f"{FIXTURES}/{filename}"
    with open(path, "wb") as handle:
        handle.write(der)
    print(f"wrote {path}")
    print(f"  bytes  {len(der)}")
    print(f"  sha256 {hashlib.sha256(der).hexdigest()}")
    print(f"  head   {der[:8].hex()}")

print("\nsanity: reasonCode is 2.5.29.21, BasicConstraints is", ObjectIdentifier("2.5.29.19").dotted_string)
print("reruns produce different signatures: the nonces here are not RFC 6979 deterministic")
