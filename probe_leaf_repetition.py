"""Two questions the layout survey leaves open, both answerable with one request per log.

1. For an x509 entry, is the first certificate in `extra_data`'s vector the leaf certificate again, or the
   first issuer? RFC 6962 section 4.6 says `extra_data` "is the certificate_chain", which implies the leaf is
   absent - but Trillian's storage keeps a full chain, and a monitor that assumed one or the other builds its
   issuer graph on the wrong node. The leaf's DER is authenticated in `leaf_input`, so comparing the two is
   exact rather than inferential.

2. The static-merge blocker in ROADMAP section 5 says that at Argon2026h2 indices 0-9 the logged
   `TBSCertificate` and "the stored precert" differ by 11 bytes from byte 4 onward. That comparison assumed
   those entries were precert entries. If any of them is an x509 entry, the comparison was between a real
   TBSCertificate and a slice of chain, and the anomaly is an artefact of the reader rather than of the log.
"""

import base64
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ctspy"))

from ctspy import entry  # noqa: E402


def get(url: str) -> dict:
    import json

    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
        return json.loads(response.read())


ARGON = "https://ct.googleapis.com/logs/us1/argon2026h2"
XENON = "https://ct.googleapis.com/logs/eu1/xenon2026h2"
WYVERN = "https://wyvern.ct.digicert.com/2026h2"

print("=== is the leaf certificate repeated in extra_data? ===")
for name, origin in (("Argon2026h2", ARGON), ("Xenon2026h2", XENON), ("Wyvern2026h2", WYVERN)):
    try:
        entries = get(f"{origin}/ct/v1/get-entries?start=0&end=31")["entries"]
    except Exception as exc:  # noqa: BLE001
        print(f"  {name}: {type(exc).__name__}")
        continue
    kinds: dict[str, list[str]] = {}
    for item in entries:
        leaf = entry.MerkleTreeLeaf.parse(base64.b64decode(item["leaf_input"]))
        signed = leaf.entry.entry
        extra = base64.b64decode(item["extra_data"])
        try:
            stored = entry.parse_extra_data(leaf, extra)
        except Exception as exc:  # noqa: BLE001
            kinds.setdefault("refused", []).append(str(exc)[:50])
            continue
        if isinstance(signed, entry.X509Entry):
            same = "leaf-repeated" if stored.chain and stored.chain[0] == signed.certificate else "leaf-absent"
            kinds.setdefault(same, []).append(f"{len(stored.chain)} items")
        else:
            repeated = "pre-repeated" if signed.tbs_certificate in stored.certificate else "pre-not-substring"
            kinds.setdefault(repeated, []).append(f"{len(stored.chain)} items")
    print(f"  {name}: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(kinds.items())))

print("\n=== the static-merge entries at Argon2026h2 indices 0-9 ===")
for item in get(f"{ARGON}/ct/v1/get-entries?start=0&end=9")["entries"]:
    leaf = entry.MerkleTreeLeaf.parse(base64.b64decode(item["leaf_input"]))
    signed = leaf.entry.entry
    kind = "precert" if isinstance(signed, entry.PrecertEntry) else "x509  "
    stored = entry.parse_extra_data(leaf, base64.b64decode(item["extra_data"]))
    print(
        f"  {kind} chain={len(stored.chain)} cert_from={'leaf' if stored.authenticated else 'extra_data'} "
        f"cert_len={len(stored.certificate)}"
    )
