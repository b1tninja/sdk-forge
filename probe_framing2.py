"""The third framing: is `extra_data` sometimes just DER?

`probe_framing.py` found that no single TLS-style layout explains the fleet: Google and Sectigo answer
some entries with an extra length layer, and DigiCert answers its x509 entries with something that fits
neither candidate. A 631-byte blob whose first two bytes are `30 82` would not be a TLS vector at all - it
would be `SEQUENCE OF Certificate`, which is what an X.509 person writes when handed a chain. If that is
what these are, then `extra_data` framing is a property of the implementation and the entry type together,
and any reader that assumes one layout silently mis-reads part of the fleet.

Printed per entry: the entry type, the leading bytes, and how much of the blob the first DER element
consumes. A first element that consumes the whole blob is DER; a 3-byte number followed by a SEQUENCE is
the TLS framing.
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
BY_NAME = {record["description"]: record["url"] for record in SWEEP["logs"]}


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


def first_element_span(data: bytes) -> int | None:
    """How many bytes the first DER element occupies, or None if it is not a DER TLV."""
    try:
        _, end = decode(data, der=False)
    except Exception:  # noqa: BLE001
        return None
    return end


for name in ("Google Argon2026h2", "Cloudflare Nimbus2026", "DigiCert Wyvern2026h2", "Sectigo Mammoth2026h2"):
    origin = BY_NAME[name]
    print(f"\n{name}")
    seen: dict[str, int] = {}
    for index, raw in enumerate(get_entries(origin, 24)):
        leaf = MerkleTreeLeaf.parse(base64.b64decode(raw["leaf_input"]))
        entry_type = leaf.entry.entry.entry_type
        extra = base64.b64decode(raw["extra_data"])
        span = first_element_span(extra)
        if extra[:1] == b"\x30" and span == len(extra):
            shape = "der-sequence-consumes-all"
        elif extra[:1] == b"\x30":
            shape = f"der-first-element-{span}of{len(extra)}"
        elif extra[:3] == len(extra).to_bytes(4, "big")[1:]:
            shape = "length-equals-total-minus-3"
        else:
            shape = "tls-vector"
        seen[shape] = seen.get(shape, 0) + 1
        if seen[shape] <= 2:
            print(f"  entry {index:2d} type={entry_type} {len(extra):5d}B {shape:30s} {extra[:8].hex()}")
    print("  ", seen)
