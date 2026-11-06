"""Why does a strict ASN.1 parse refuse half the precerts a production log stores?

`certledger/der.py` defaults to `der=True`, which rejects non-canonical encodings at the door, and
`asn1core.parse_certificate` validates as it reads. Sampling `get-entries` showed 23 of 64 and 32 of 64
precert entries refusing to parse at Cloudflare and DigiCert - which is not a rounding error, and either
means those logs serve something other than a certificate in `extra_data`, or it means real production
certificates are not canonical DER. The two answers imply completely different stores, so this prints the
message, then tries the same bytes with validation turned off, and dumps the leading structure so the
shape is visible rather than inferred.
"""

import base64
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "ctspy"), str(ROOT / "ctspy" / "tools"), str(ROOT / "asn1core")]

from asn1core import certificate_parts, decode, parse_certificate  # noqa: E402
from fetch_evidence import get_json, parse_extra_data  # noqa: E402

ORIGINS = {
    "Cloudflare Nimbus2026": "https://ct.cloudflare.com/logs/nimbus2026",
    "DigiCert Wyvern2026h2": "https://wyvern.ct.digicert.com/2026h2",
}


def get_entries(origin: str, count: int, page: int = 64) -> list[dict]:
    """Paged `get-entries`: Google answers 32 however many are asked for."""
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


shown = 0
for name, origin in ORIGINS.items():
    for index, raw in enumerate(get_entries(origin, 40)):
        subject, chain = parse_extra_data(base64.b64decode(raw["extra_data"]))
        try:
            parse_certificate(subject)
            continue
        except Exception as strict:  # noqa: BLE001
            print(f"\n{name} entry {index}: strict parse -> {type(strict).__name__}: {strict}")
            print(f"  subject {len(subject)} bytes, chain of {len(chain)}")
            print(f"  leading bytes: {subject[:24].hex()}")
            for label, attempt in (
                ("certificate_parts(der=False)", lambda: certificate_parts(subject, der=False)),
                ("decode(der=False)", lambda: decode(subject, der=False)),
                ("parse_certificate(der=False)", lambda: parse_certificate(subject, der=False)),
            ):
                try:
                    result = attempt()
                    print(f"  {label}: OK -> {type(result).__name__}")
                except Exception as exc:  # noqa: BLE001
                    print(f"  {label}: {type(exc).__name__}: {str(exc)[:110]}")
            shown += 1
            if shown >= 4:
                raise SystemExit(0)
