"""What is the real layout of `extra_data` for a precert entry, per implementation?

`parse_extra_data` in ctspy's evidence tool reads `ASN.1Cert` then `ASN.1Cert<1..2^24-1>`, which matches
Google exactly: hashing the SPKI of the first chain certificate reproduced the log's own `issuer_key_hash`
thirteen times out of thirteen. The same reader then failed on roughly a third of Cloudflare, DigiCert and
Sectigo entries with "N bytes follow the certificate", and the refused slices began with another 3-byte
length rather than with a DER SEQUENCE.

Either those logs encode `extra_data` differently - which would be a deployment finding worth writing down,
because a monitor would silently mis-store a third of the fleet's CA certificates - or the reader is wrong
and Google happened to work for a reason I have not identified. The leaf gives me ground truth to settle it:
`leaf_input` contains the exact `TBSCertificate` the log hashed, so finding those bytes inside
`extra_data` shows where the certificate actually begins, and the four bytes before it show what prefixes
it.
"""

import base64
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "ctspy"), str(ROOT / "ctspy" / "tools"), str(ROOT / "asn1core")]

from ctspy.entry import MerkleTreeLeaf  # noqa: E402
from fetch_evidence import get_json  # noqa: E402

SWEEP = json.loads(
    (ROOT / "ctspy" / "tests" / "fixtures" / "log-list-sweep.json").read_text(encoding="utf-8")
)
BY_NAME = {record["description"]: record["url"] for record in SWEEP["logs"]}
ORIGINS = {
    name: BY_NAME[name]
    for name in (
        "Google Argon2026h2",
        "Cloudflare Nimbus2026",
        "DigiCert Wyvern2026h2",
        "Sectigo Mammoth2026h2",
    )
    if name in BY_NAME
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
    print(f"\n{name}  ({origin})")
    reported = 0
    for index, raw in enumerate(get_entries(origin, 16)):
        leaf = MerkleTreeLeaf.parse(base64.b64decode(raw["leaf_input"]))
        if getattr(leaf.entry.entry, "tbs_certificate", None) is None:
            continue
        tbs = leaf.entry.entry.tbs_certificate
        extra = base64.b64decode(raw["extra_data"])
        at = extra.find(tbs)
        if at < 0:
            print(f"  entry {index}: TBS not found in extra_data ({len(extra)} bytes)")
            continue
        # The TBS is the first child of the certificate's outer SEQUENCE, so the SEQUENCE header is
        # the four bytes before it in the ordinary case.
        head = extra[max(0, at - 8) : at]
        print(
            f"  entry {index}: extra {len(extra):5d}B, tbs at {at:5d}, "
            f"issuer_hash {leaf.entry.entry.issuer_key_hash.hex()[:12]}..., bytes before: {head.hex()}"
        )
        reported += 1
        if reported >= 4:
            break
