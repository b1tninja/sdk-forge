"""Measure full RFC 4518 preparation against the names actually in circulation.

The question this answers before any code is written: if `normalize_value` grew the whole profile -
the §2.2 mapping lists, the §2.4 prohibited set, Map-before-NFC ordering - how many of the 577
attribute values in the local trust store would change, and how many would be refused? A profile
step that rejects a shipped trust anchor is the OID first-arc mistake waiting to happen again, so
the strictness is measured first and only then chosen.

It also prices erratum 860: RFC 4518 §2.2 as printed maps "FF00-FE0F" to nothing, and the verified
erratum says FE00-FE0F was meant. The code counts how many real values contain characters in the
range the printed text would have deleted.
"""

from __future__ import annotations

import pathlib
import stringprep
import sys
import tempfile
import unicodedata

sys.path.insert(0, str(pathlib.Path("D:/code/asn1core/tools").resolve()))
sys.path.insert(0, "D:/code/asn1core")

from crosscheck_x509 import collect  # noqa: E402

from asn1core import parse_certificate  # noqa: E402

# §2.2 as corrected by erratum 860: variation selectors are FE00-FE0F, not FF00-FE0F.
MAP_NOTHING = (
    [0x00AD, 0x1806, 0x034F, 0xFFFC, 0x200B, 0xFEFF]
    + list(range(0x180B, 0x180E))
    + list(range(0xFE00, 0xFE10))
    + list(range(0x0000, 0x0009))
    + list(range(0x000E, 0x0020))
    + list(range(0x007F, 0x0085))
    + list(range(0x0086, 0x00A0))
    + [0x06DD, 0x070F, 0x180E]
    + list(range(0x200C, 0x2010))
    + list(range(0x202A, 0x202F))
    + list(range(0x2060, 0x2064))
    + list(range(0x206A, 0x2070))
    + list(range(0xFFF9, 0xFFFC))
    + list(range(0x1D173, 0x1D17B))
    + [0xE0001]
    + list(range(0xE0020, 0xE0080))
)
MAP_SPACE = (
    [0x0009, 0x000A, 0x000B, 0x000C, 0x000D, 0x0085]
    + [0x00A0, 0x1680, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000]
    + list(range(0x2000, 0x200B))
)
PRINTED_WRONG = set(range(0xFF00, 0xFE10))  # the descending range as printed, read upward
ERRATUM_RANGE = set(range(0xFF00, 0xFF61))  # fullwidth forms: what the printed text would delete

PROHIBIT = {
    "A.1 unassigned (Unicode 3.2, per RFC 3454)": stringprep.in_table_a1,
    "Cn unassigned in this Unicode version": lambda c: unicodedata.category(c) == "Cn",
    "C.3 private use": stringprep.in_table_c3,
    "C.4 non-character": stringprep.in_table_c4,
    "C.5 surrogate": stringprep.in_table_c5,
    "C.8 change display / deprecated": stringprep.in_table_c8,
    "U+FFFD replacement": lambda c: c == "\ufffd",
}


def map_full(text: str) -> str:
    nothing = set(MAP_NOTHING)
    space = set(MAP_SPACE)
    return "".join(
        "" if ord(c) in nothing else " " if ord(c) in space else c for c in text
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        paths = collect(pathlib.Path(tmp))
        values: list[tuple[str, str, str]] = []
        for path in paths:
            try:
                cert = parse_certificate(path.read_bytes())
            except Exception:  # noqa: BLE001 - inventory, not validation
                continue
            for label, name in (("subject", cert.subject), ("issuer", cert.issuer)):
                for rdn in name.rdnsets:
                    for attr in rdn:
                        values.append((path.name[:12], label, attr.value))

    print(f"attribute values measured: {len(values)} across {len(paths)} certificates\n")

    hits: dict[str, list[str]] = {label: [] for label in PROHIBIT}
    for _, _, text in values:
        for label, predicate in PROHIBIT.items():
            if any(predicate(c) for c in text):
                hits[label].append(text)
    print("prohibited-character step (§2.4), values that would FAIL preparation:")
    for label, found in hits.items():
        sample = "" if not found else f" e.g. {found[0]!r}"
        print(f"  {label:44s} {len(found):4d}{sample}")

    printed_range = [t for _, _, t in values if any(c in ERRATUM_RANGE for c in t)]
    print(
        f"\nvalues containing fullwidth forms (what the printed FF00-FE0F would delete): "
        f"{len(printed_range)}"
    )
    for text in printed_range[:5]:
        print(f"  {text!r}")

    changed_map = [
        (t, map_full(t)) for _, _, t in values if map_full(t) != _map_current(t)
    ]
    print(f"\nvalues where full §2.2 mapping differs from the current subset: {len(changed_map)}")
    for before, after in changed_map[:8]:
        print(f"  {before!r} -> {after!r}")

    order = []
    for _, _, t in values:
        nfc_then_fold = unicodedata.normalize("NFC", map_full(t)).casefold()
        fold_then_nfc = unicodedata.normalize("NFC", map_full(t).casefold())
        if nfc_then_fold != fold_then_nfc:
            order.append((t, nfc_then_fold, fold_then_nfc))
    print(
        f"\nvalues where Map->NFC->casefold differs from Map->casefold->NFC: {len(order)}"
    )
    for before, a, b in order[:8]:
        print(f"  {before!r}: NFC-then-fold {a!r} vs fold-then-NFC {b!r}")

    prohibited_any = {t for label in hits for t in hits[label]}
    print(f"\nvalues that strict preparation would refuse (any table): {len(prohibited_any)}")
    return 0


def _map_current(text: str) -> str:
    """The mapping name.py does today: Zs to SPACE, soft hyphen removed."""
    return "".join(
        " " if c != " " and unicodedata.category(c) == "Zs" else c for c in text
    ).replace("\u00ad", "")


if __name__ == "__main__":
    raise SystemExit(main())
