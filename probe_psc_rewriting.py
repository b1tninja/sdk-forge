"""The rule that decides whether a precert reconstructs, measured as a cross-tabulation.

RFC 6962 section 3.2 paragraph 9 defines the logged `TBSCertificate` as the precertificate's TBS "without the
signature and the poison extension" - and then adds two more transformations for the case where the precert
was not signed by the CA that will issue the final certificate, i.e. by a Precertificate Signing Certificate
(OID 1.3.6.1.4.1.11129.2.4.4): the issuer is changed to that of the issuing CA, and if an Authority Key
Identifier is present it is changed to match the final issuer too.

So "strip the poison and compare" should be exact for directly-signed precerts and inexact for PSC-signed
ones, and the PSC ones should be identifiable independently: the leaf's `issuer_key_hash` is the hash of the
*issuing CA's* SPKI, while `extra_data`'s chain starts with the PSC. If the two classifications line up on a
diagonal, the rule is established rather than guessed - and the practical consequence for an issuer graph is
severe, because attributing a precert to `chain[0]` would credit ~40% of issuance to throwaway CT-only
certificates that are not CAs at all.
"""

import base64
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "ctspy"), str(ROOT / "ctspy" / "tools"), str(ROOT / "asn1core")]

from asn1core import parse_certificate  # noqa: E402
from ctspy import entry  # noqa: E402
from fetch_evidence import POISON_OID_DER, get_json, strip_extension, tbs_of  # noqa: E402

ORIGINS = {
    "Argon2026h2 (merged)": "https://ct.googleapis.com/logs/us1/argon2026h2",
    "Xenon2026h2 (merged)": "https://ct.googleapis.com/logs/eu1/xenon2026h2",
    "Argon2027h1 (live)": "https://ct.googleapis.com/logs/us1/argon2027h1",
    "Wyvern2026h2 (DigiCert)": "https://wyvern.ct.digicert.com/2026h2",
    "Nimbus2026 (Cloudflare)": "https://ct.cloudflare.com/logs/nimbus2026",
}


def get_entries(origin: str, count: int, page: int = 32) -> list[dict]:
    out: list[dict] = []
    start = 0
    while len(out) < count:
        want = min(page, count - len(out))
        got = get_json(f"{origin}/ct/v1/get-entries?start={start}&end={start + want - 1}")["entries"]
        if not got:
            break
        out.extend(got)
        start += len(got)
    return out[:count]


def spki_hash(cert_der: bytes) -> bytes:
    return hashlib.sha256(parse_certificate(cert_der).subject_public_key_info).digest()


total = {"exact": 0, "rewritten": 0}
crosstab: dict[tuple[str, str], int] = {}
sample_pairs = []

for name, origin in ORIGINS.items():
    local = {"exact": 0, "rewritten": 0}
    for item in get_entries(origin, 160):
        leaf = entry.MerkleTreeLeaf.parse(base64.b64decode(item["leaf_input"]))
        signed = leaf.entry.entry
        if not isinstance(signed, entry.PrecertEntry):
            continue
        stored = entry.parse_extra_data(leaf, base64.b64decode(item["extra_data"]))
        logged = signed.tbs_certificate
        rebuilt = strip_extension(tbs_of(stored.certificate), POISON_OID_DER)
        exact = rebuilt == logged
        where = (
            "chain[0]" if stored.chain and spki_hash(stored.chain[0]) == signed.issuer_key_hash
            else "chain[1]" if len(stored.chain) > 1 and spki_hash(stored.chain[1]) == signed.issuer_key_hash
            else "nowhere"
        )
        kind = "exact" if exact else "rewritten"
        local[kind] += 1
        total[kind] += 1
        crosstab[(kind, where)] = crosstab.get((kind, where), 0) + 1
        if not exact and len(sample_pairs) < 2:
            sample_pairs.append((name, stored, signed, rebuilt))
    print(f"{name:26s} exact {local['exact']:3d}  rewritten {local['rewritten']:3d}")

print(f"\nall logs: exact {total['exact']}, rewritten {total['rewritten']}")
print("\nreconstruction result  x  where issuer_key_hash is found in the chain")
for (kind, where), count in sorted(crosstab.items()):
    print(f"  {kind:10s} {where:10s} {count:5d}")

for name, stored, signed, rebuilt in sample_pairs:
    precert = parse_certificate(stored.certificate)
    issuer = parse_certificate(stored.chain[0])
    print(f"\nexample rewritten precert ({name}):")
    print(f"  precert issuer : {precert.issuer}")
    print(f"  chain[0] subject: {issuer.subject}")
    print(f"  chain[0] is a PSC (CT EKU present): {any(e.oid == (1,3,6,1,4,1,11129,2,4,4) for e in issuer.extensions)}")
    print(f"  logged TBS {len(signed.tbs_certificate)}B vs poison-stripped {len(rebuilt)}B")
    print(f"  issuer_key_hash at chain[0]: {spki_hash(stored.chain[0]) == signed.issuer_key_hash}")
