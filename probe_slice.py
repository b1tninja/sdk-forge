"""Throwaway: why does a signature over asn1core's tbs slice fail to verify?"""

import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

import asn1core

key = ec.generate_private_key(ec.SECP256R1())
name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "probe")])
now = datetime.datetime.now(datetime.UTC)
cert = (
    x509.CertificateBuilder()
    .subject_name(name)
    .issuer_name(name)
    .public_key(key.public_key())
    .serial_number(1)
    .not_valid_before(now - datetime.timedelta(days=1))
    .not_valid_after(now + datetime.timedelta(days=1))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(key, hashes.SHA256())
)
der = cert.public_bytes(serialization.Encoding.DER)
parts = asn1core.certificate_parts(der)
print("lengths: der", len(der), "tbs", len(parts.tbs_certificate), "sig", len(parts.signature_value))
print("sig equals cryptography:", parts.signature_value == cert.signature)
print("tbs head:", parts.tbs_certificate[:8].hex())
print("der head:", der[:8].hex())
print("tbs offset in der:", der.find(parts.tbs_certificate), "len", len(parts.tbs_certificate))
print("sig offset in der:", der.find(parts.signature_value), "len", len(parts.signature_value))
print("hash alg:", cert.signature_hash_algorithm, "sig alg oid:", cert.signature_algorithm_oid.dotted_string)
print("pubkey type:", type(cert.public_key()).__name__)
try:
    cert.public_key().verify(
        parts.tbs_certificate, cert.signature, ec.ECDSA(cert.signature_hash_algorithm)
    )
    print("verify over asn1core slice: OK")
except Exception as exc:
    print("verify failed:", type(exc).__name__, exc)

hand = der[der.find(parts.tbs_certificate) : der.find(parts.tbs_certificate) + 203]
print("hand slice equals asn1core slice:", hand == parts.tbs_certificate)
fresh = key.sign(parts.tbs_certificate, ec.ECDSA(hashes.SHA256()))
try:
    key.public_key().verify(fresh, parts.tbs_certificate, ec.ECDSA(hashes.SHA256()))
    print("plumbing OK")
except Exception as exc:
    print("plumbing failed:", type(exc).__name__, exc)
try:
    key.public_key().verify(cert.signature, parts.tbs_certificate, ec.ECDSA(hashes.SHA256()))
    print("verify with explicit SHA256: OK")
except Exception as exc:
    print("explicit SHA256 failed:", type(exc).__name__, exc)

