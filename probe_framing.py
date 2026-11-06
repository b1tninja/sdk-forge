"""Which framing does each implementation use for `extra_data`? Test two, on every entry.

Two candidate layouts, checked against the byte count rather than against a parser's error message:

  bare    [3B len][pre_cert or leaf_cert][3B len][chain blob]          total == 6 + L + M
  wrapped [3B len == total-3] then the bare layout inside it           an extra opaque layer

Google's Trillian logs are bare - that much is established, because hashing the SPKI of the first
certificate in the trailing vector reproduced the log's own `issuer_key_hash` thirteen times out of
thirteen. Roughly a third of Cloudflare, DigiCert and Sectigo entries refuse the bare reading with
"bytes follow the certificate", and the refused slice begins with yet another length, which is what a
wrapped layer looks like from the outside. Whether the split correlates with the entry type decides how a
store must read a fleet, so it is printed per entry rather than aggregated.
"""

import base64
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "ctspy"), str(ROOT / "ctspy" / "tools"), str(ROOT / "asn1core")]

from asn1core import parse_certificate  # noqa: E402
from ctspy.entry import MerkleTreeLeaf  # noqa: E402
from fetch_evidence import get_json  # noqa: E402

SWEEP = json.loads(
    (ROOT / "ctspy" / "tests" / "fixtures" / "log-list-sweep.json").read_text(encoding="utf-8")
)
BY_NAME = {record["description"]: record["url"] for record in SWEEP["logs"]}
NAMES = ("Google Argon2026h2", "Cloudflare Nimbus2026", "DigiCert Wyvern2026h2", "Sectigo Mammoth2026h2")


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


def triple(data: bytes, at: int) -> int:
    return int.from_bytes(data[at : at + 3], "big")


def bare(extra: bytes) -> tuple[int, int] | None:
    """(cert_len, chain_len) if the bare layout accounts for every byte."""
    if len(extra) < 6:
        return None
    cert_len = triple(extra, 0)
    if not cert_len or len(extra) < 3 + cert_len + 3:
        return None
    chain_len = triple(extra, 3 + cert_len)
    if 6 + cert_len + chain_len == len(extra):
        return cert_len, chain_len
    return None


def wrapped(extra: bytes) -> tuple[int, int] | None:
    if len(extra) < 3 or triple(extra, 0) != len(extra) - 3:
        return None
    return bare(extra[3:])


tally: dict[str, dict[str, int]] = {}
for name in NAMES:
    origin = BY_NAME.get(name)
    if origin is None:
        print(f"{name}: not in the captured log list")
        continue
    print(f"\n{name}")
    counts = {"bare": 0, "wrapped": 0, "neither": 0}
    for index, raw in enumerate(get_entries(origin, 24)):
        leaf = MerkleTreeLeaf.parse(base64.b64decode(raw["leaf_input"]))
        entry_type = leaf.entry.entry.entry_type
        extra = base64.b64decode(raw["extra_data"])
        b, w = bare(extra), wrapped(extra)
        label = "bare" if b else "wrapped" if w else "neither"
        counts[label] += 1
        note = ""
        if b or w:
            body = extra[3:] if w else extra
            cert_len = (b or w)[0]
            try:
                parse_certificate(body[3 : 3 + cert_len])
                note = "cert parses"
            except Exception as exc:  # noqa: BLE001
                note = f"cert refused: {str(exc)[:60]}"
        if label != "bare" or index < 2:
            print(f"  entry {index:2d} type={entry_type} extra={len(extra):5d}B {label:8s} {note}")
    tally[name] = counts

print("\n=== framing by implementation ===")
for name, counts in tally.items():
    print(f"  {name:26s} {counts}")
