"""Do two logs' verified prefixes actually contain the same certificates? `cl.dedupe` depends on it.

The row says entries are not certificates because one certificate is logged in several logs. That is true as
a statement about submissions and unproven as a statement about data a monitor can reach: a corpus is only
verifiable if it is a *prefix* (its Merkle Tree Hash can be tied to a signed tree head by a consistency
proof), so the duplicates have to occur inside prefixes, and prefixes are old entries - the beginning of each
log, which for static-merge logs is content merged from specific expiring logs rather than whatever the Web
was issuing that week.

So measure before designing the store. For each operational log, take a prefix and record the identity of
every certificate in it - SHA-256 over the logged TBSCertificate with the SCT-list extension removed, which
is the transformation RFC 6962 section 3.2 paragraph 9 itself identifies as the difference between a
precertificate's TBS and the final certificate's. Then intersect every pair of logs, same operator and
across operators.
"""

import base64
import hashlib
import itertools
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "ctspy"), str(ROOT / "ctspy" / "tools"), str(ROOT / "asn1core")]

from asn1core import parse_certificate  # noqa: E402
from ctspy import entry  # noqa: E402
from fetch_evidence import get_json  # noqa: E402

SWEEP = json.loads(
    (ROOT / "ctspy" / "tests" / "fixtures" / "log-list-sweep.json").read_text(encoding="utf-8")
)
PREFIX = 256
SCT_OID_DER = bytes.fromhex("060a2b06010401d679020402")  # 1.3.6.1.4.1.11129.2.4.2


def certificate_id(tbs: bytes) -> bytes:
    """PLAN's identity: SHA-256 over the logged TBSCertificate as the log stored it.

    For a precert entry that is the TBS in the leaf, which carries no SCT extension, so the same precertificate
    submitted to two logs yields the same identity in both - which is exactly the collision `cl.dedupe` exists
    to find.
    """
    return hashlib.sha256(tbs).digest()


def prefix(origin: str) -> dict[bytes, int]:
    out: dict[bytes, int] = {}
    start = 0
    while start < PREFIX:
        want = min(32, PREFIX - start)
        body = get_json(f"{origin}/ct/v1/get-entries?start={start}&end={start + want - 1}")
        entries = body["entries"]
        if not entries:
            break
        for offset, item in enumerate(entries):
            leaf = entry.MerkleTreeLeaf.parse(base64.b64decode(item["leaf_input"]))
            signed = leaf.entry.entry
            tbs = (
                signed.tbs_certificate
                if isinstance(signed, entry.PrecertEntry)
                else parse_certificate(signed.certificate).tbs_certificate
            )
            out[certificate_id(tbs)] = start + offset
        start += len(entries)
    return out


corpora: dict[str, dict[bytes, int]] = {}
for record in SWEEP["logs"]:
    name, origin = record["description"], record["url"]
    try:
        corpora[name] = prefix(origin)
    except Exception as exc:  # noqa: BLE001
        print(f"{name}: {type(exc).__name__}")
        continue
    print(f"{name:34s} {len(corpora[name]):4d} distinct certificates in the prefix")

print("\n=== pairwise overlap, by certificate identity ===")
best = []
for left, right in itertools.combinations(sorted(corpora), 2):
    shared = set(corpora[left]) & set(corpora[right])
    if shared:
        best.append((len(shared), left, right))
for count, left, right in sorted(best, reverse=True)[:15]:
    print(f"  {count:4d}  {left} / {right}")
if not best:
    print("  no pair of prefixes shares a certificate at this prefix length")
