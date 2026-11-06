"""Does the precert reconstruction rule hold on static-merge entries once only precerts are compared?

ROADMAP section 5 says that at Argon2026h2 indices 0-9 the logged `TBSCertificate` and the stored precert's
differ by 11 bytes and diverge from byte 4 onward, while recent entries reconstruct byte for byte, and it
records that as an unexplained property of merged entries. The measurement looped over *entries*, and it is
now known that an x509 entry's `extra_data` contains no precertificate at all - it is the issuer chain, and
three of those ten entries are x509 entries. So the anomaly may be a comparison between a logged
TBSCertificate and an issuer's TBSCertificate: two real documents of similar length that diverge immediately,
which is exactly the signature described.

The test is to apply the reconstruction rule - remove the poison extension from the stored precert's TBS,
compare with the leaf's `TBSCertificate` - to precert entries only, over a longer merge prefix, and see
whether anything is left to explain.
"""

import base64
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "ctspy"), str(ROOT / "ctspy" / "tools"), str(ROOT / "asn1core")]

from asn1core import certificate_parts  # noqa: E402
from ctspy import entry  # noqa: E402
from fetch_evidence import POISON_OID_DER, get_json, strip_extension, tbs_of  # noqa: E402

ORIGINS = {
    "Argon2026h2 merge prefix": "https://ct.googleapis.com/logs/us1/argon2026h2",
    "Xenon2026h2 merge prefix": "https://ct.googleapis.com/logs/eu1/xenon2026h2",
    "Argon2027h1 live entries": "https://ct.googleapis.com/logs/us1/argon2027h1",
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


for name, origin in ORIGINS.items():
    exact = mismatched = x509 = refused = 0
    first_diff = None
    for item in get_entries(origin, 128):
        leaf = entry.MerkleTreeLeaf.parse(base64.b64decode(item["leaf_input"]))
        signed = leaf.entry.entry
        extra = base64.b64decode(item["extra_data"])
        try:
            stored = entry.parse_extra_data(leaf, extra)
        except Exception:  # noqa: BLE001
            refused += 1
            continue
        if not isinstance(signed, entry.PrecertEntry):
            x509 += 1
            continue
        logged = signed.tbs_certificate
        rebuilt = strip_extension(tbs_of(stored.certificate), POISON_OID_DER)
        if rebuilt == logged:
            exact += 1
            continue
        mismatched += 1
        if first_diff is None:
            at = next((i for i, (a, b) in enumerate(zip(rebuilt, logged)) if a != b), None)
            first_diff = (len(rebuilt), len(logged), at)
    print(
        f"\n{name}: {exact} precerts reconstruct byte for byte, {mismatched} do not, "
        f"{x509} were x509 entries, {refused} refused"
    )
    if first_diff:
        print(f"  first mismatch: rebuilt {first_diff[0]}B vs logged {first_diff[1]}B, diverging at byte {first_diff[2]}")
        for i, item in enumerate(get_entries(origin, 128)):
            leaf = entry.MerkleTreeLeaf.parse(base64.b64decode(item["leaf_input"]))
            signed = leaf.entry.entry
            if not isinstance(signed, entry.PrecertEntry):
                continue
            stored = entry.parse_extra_data(leaf, base64.b64decode(item["extra_data"]))
            rebuilt = strip_extension(tbs_of(stored.certificate), POISON_OID_DER)
            if rebuilt != signed.tbs_certificate:
                print(f"  entry index {i}: issuer {signed.issuer_key_hash.hex()[:16]}...")
                break
