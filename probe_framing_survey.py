"""Hypothesis: `extra_data` carries an extra opaque layer for x509 entries and not for precert entries.

The per-entry dumps show it. A precert entry begins `0002f8 3082 02f4` - a 3-byte length and then a DER
SEQUENCE, which is the bare `PreCertChainEntry`. An x509 entry begins `000ba3 0005cc 3082...` - a length
covering everything after it, then the certificate's own length, then the SEQUENCE. DigiCert's x509 entries
are 631 bytes and end immediately after the certificate, so the trailing chain vector is sometimes absent
as well.

If that is what the fleet does, a reader that assumes one framing mis-reads part of every log, which for a
monitor is not a cosmetic bug - it is CA certificates that never make it into the store. So: test both
framings against every operational log, by entry type, and count. This checks byte arithmetic rather than
what a parser happens to accept, so a "fit" means the lengths account for every byte with nothing left over.
"""

import base64
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "ctspy"), str(ROOT / "ctspy" / "tools"), str(ROOT / "asn1core")]

from asn1core import decode  # noqa: E402
from ctspy.entry import MerkleTreeLeaf  # noqa: E402
from fetch_evidence import get_json  # noqa: E402

SWEEP = json.loads(
    (ROOT / "ctspy" / "tests" / "fixtures" / "log-list-sweep.json").read_text(encoding="utf-8")
)
PAGE = 32


def triple(data: bytes, at: int) -> int | None:
    if at + 3 > len(data):
        return None
    return int.from_bytes(data[at : at + 3], "big")


def is_certificate_at(data: bytes, at: int, declared: int) -> bool:
    """The declared length must be the DER span of a SEQUENCE, not merely a number that fits.

    Byte arithmetic alone calls the x509 form ambiguous, because a length covering the rest of the blob is
    also a plausible certificate length. The certificate field is a DER document, so the tag and the span
    settle what the lengths only suggest.
    """
    if at + 3 + declared > len(data) or data[at + 3 : at + 4] != b"\x30":
        return False
    try:
        _, end = decode(data[at + 3 :], der=False)
    except Exception:  # noqa: BLE001
        return False
    return end == declared


def fits(extra: bytes, *, wrapped: bool) -> tuple[int, int] | None:
    """(cert_len, chain_len) if this framing accounts for every byte; chain_len -1 when absent."""
    offset = 3 if wrapped else 0
    if wrapped and triple(extra, 0) != len(extra) - 3:
        return None
    cert_len = triple(extra, offset)
    if not cert_len or not is_certificate_at(extra, offset, cert_len):
        return None
    after = offset + 3 + cert_len
    if after == len(extra):
        return cert_len, -1  # no trailing chain vector at all
    chain_len = triple(extra, after)
    if chain_len is not None and after + 3 + chain_len == len(extra):
        return cert_len, chain_len
    return None


tally: dict[tuple[int, str], int] = {}
logs_seen = 0
for record in SWEEP["logs"]:
    origin = record["url"]
    try:
        entries = get_json(f"{origin}/ct/v1/get-entries?start=0&end={PAGE - 1}")["entries"]
    except Exception:  # noqa: BLE001
        continue
    logs_seen += 1
    for raw in entries:
        leaf = MerkleTreeLeaf.parse(base64.b64decode(raw["leaf_input"]))
        entry_type = leaf.entry.entry.entry_type
        extra = base64.b64decode(raw["extra_data"])
        bare, wrapped = fits(extra, wrapped=False), fits(extra, wrapped=True)
        if bare and not wrapped:
            key = "bare"
        elif wrapped and not bare:
            key = "wrapped"
        elif bare and wrapped:
            key = "ambiguous"
        else:
            key = "neither"
        bucket = (entry_type, key)
        tally[bucket] = tally.get(bucket, 0) + 1

print(f"{logs_seen} logs answered, {sum(tally.values())} entries examined\n")
for (entry_type, key), count in sorted(tally.items()):
    kind = "precert" if entry_type == 1 else "x509"
    print(f"  {kind:8s} {key:10s} {count:5d}")
