"""Smoke: parse the two new fixtures and the trust-store certs with asn1core.cert / asn1core.crl."""

import pathlib

from asn1core.cert import parse_certificate
from asn1core.crl import parse_crl

FIX = pathlib.Path("D:/code/asn1core/tests/fixtures")

for name in ("root-rsa.der", "root-ecdsa.der", "multivalue-rdn.der", "ecdsa-padded-r.der"):
    der = (FIX / name).read_bytes()
    cert = parse_certificate(der)
    print(
        f"{name}: v{cert.version + 1} serial={cert.serial} self={cert.self_issued} "
        f"exts={len(cert.extensions)} critical={[e.dotted_oid for e in cert.critical_extensions]} "
        f"unrec={cert.unrecognised_critical[0].dotted_oid if cert.unrecognised_critical else '-'} "
        f"sigalg={'.'.join(map(str, cert.signature_algorithm))} "
        f"notBefore={cert.validity.not_before:%Y-%m-%d} notAfter={cert.validity.not_after:%Y-%m-%d}"
    )

crl = parse_crl((FIX / "crl-keycompromise.der").read_bytes())
nxt = "absent" if crl.next_update is None else f"{crl.next_update:%Y-%m-%d}"
print(
    f"\nCRL v{crl.version} (1 == v2) entries={len(crl.revoked)} "
    f"serials={crl.revoked_serials} this={crl.this_update:%Y-%m-%d} "
    f"next={nxt} list_exts={[e.dotted_oid for e in crl.extensions]}"
)
for entry in crl.revoked:
    print(
        f"  serial={entry.serial} date={entry.revocation_date:%Y-%m-%dT%H:%M:%SZ} "
        f"reason={entry.reason} name={entry.reason_name} compromised={entry.compromised} "
        f"entry_exts={len(entry.extensions)}"
    )
print("  tbs inside raw:", crl.tbs_cert_list in crl.raw, "sig len", len(crl.signature_value))

# The padded-r fixture is the point of the exercise: the leading zero on r must survive our codec.
from asn1core.node import decode

der = (FIX / "ecdsa-padded-r.der").read_bytes()
cert = parse_certificate(der)
seq, end = decode(cert.signature_value, der=True)
r, s = seq.children
print(
    f"\nECDSA-Sig-Value: r {len(r.payload)} bytes leading={r.payload[0]:02x}, "
    f"s {len(s.payload)} bytes leading={s.payload[0]:02x}, consumed={end}/{len(cert.signature_value)}"
)
print("signature bytes reproduced from the parsed tree:", seq.raw == cert.signature_value)
