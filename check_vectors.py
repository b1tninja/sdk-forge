"""Re-derive the arithmetic in asn1core/VECTORS.md from bits, not from memory.

Every vector here was written by hand. Hand-written byte sequences in a conformance
corpus are exactly where a wrong expectation hides, so this script decodes the bytes
with the X.690 rules restated independently and asserts the documented verdict.
"""

from __future__ import annotations


def decode_tag(octets: bytes) -> tuple[int, int, int]:
    """Return (tag_class, constructed, tag_number) for one identifier octet run."""
    first = octets[0]
    tag_class = first >> 6
    constructed = (first >> 5) & 1
    number = first & 0x1F
    if number != 0x1F:
        return tag_class, constructed, number
    number = 0
    for byte in octets[1:]:
        number = (number << 7) | (byte & 0x7F)
        if not byte & 0x80:
            break
    return tag_class, constructed, number


def decode_len(octets: bytes) -> int:
    first = octets[0]
    if first < 0x80:
        return first
    if first == 0x80:
        return -1  # indefinite
    count = first & 0x7F
    value = int.from_bytes(octets[1:1 + count], "big")
    return value


def decode_int(octets: bytes) -> int:
    return int.from_bytes(octets, "big", signed=True)


CHECKS: list[tuple[str, object, object]] = [
    # Tag numbers: the single-octet boundary and the multi-octet range.
    ("tag-c-30 class", decode_tag(b"\x9e")[0], 2),
    ("tag-c-30 constructed", decode_tag(b"\x9e")[1], 0),
    ("tag-c-30 number", decode_tag(b"\x9e")[2], 30),
    ("tag-c-31 number", decode_tag(b"\x9f\x1f")[2], 31),
    ("tag-c-63 number", decode_tag(b"\x9f\x3f")[2], 63),
    ("tag-c-127 number", decode_tag(b"\x9f\x7f")[2], 127),
    ("tag-c-128 number", decode_tag(b"\x9f\x81\x00")[2], 128),
    ("tag-c-16383 number", decode_tag(b"\x9f\xff\x7f")[2], 16383),
    ("tag-c-16384 number", decode_tag(b"\x9f\x81\x80\x00")[2], 16384),
    ("tag-nonminimal encodes 1", decode_tag(b"\x9f\x80\x01")[2], 1),
    # Class bits: 0xC1 is private, 0x81 is context. The mistake I made writing these.
    ("tag-p-1 class", decode_tag(b"\xc1")[0], 3),
    ("context tag-1 class", decode_tag(b"\x81")[0], 2),
    ("tag-a-9999 class", decode_tag(b"\x5f")[0], 1),
    ("tag-a-9999 constructed", decode_tag(b"\x5f")[1], 0),
    ("tag-a-9999 number", decode_tag(b"\x5f\xce\x0f")[2], 9999),
    # A high tag number needs 11111 in the low five bits, so bit 5 is the only place
    # constructed-ness can live: application/constructed is 0x7F, never 0x5F-with-flags.
    ("tag-a-constructed class", decode_tag(b"\x7f")[0], 1),
    ("tag-a-constructed bit", decode_tag(b"\x7f")[1], 1),
    ("tag-a-constructed number", decode_tag(b"\x7f\xce\x0f")[2], 9999),
    ("context-constructed", decode_tag(b"\xa5")[1], 1),
    ("context-constructed number", decode_tag(b"\xa5")[2], 5),
    ("universal-constructed-seq", decode_tag(b"\x30")[1], 1),
    ("universal-seq number", decode_tag(b"\x30")[2], 16),
    ("three-octet continuation count", decode_tag(b"\x9f\x81\x80\x00")[2], 16384),
    # Length forms.
    ("len-short-max", decode_len(b"\x7f"), 127),
    ("len-long-128", decode_len(b"\x81\x80"), 128),
    ("len-long-255", decode_len(b"\x81\xff"), 255),
    ("len-long-256", decode_len(b"\x82\x01\x00"), 256),
    ("len-long-65536", decode_len(b"\x83\x01\x00\x00"), 65536),
    ("len-nonminimal value", decode_len(b"\x81\x7f"), 127),
    ("len-leading-zero value", decode_len(b"\x82\x00\x7f"), 127),
    ("len-indefinite", decode_len(b"\x80"), -1),
    # INTEGER minimal form, derived from two's complement.
    ("int-minus129", decode_int(b"\xff\x7f"), -129),
    ("int-minus128-one-byte", decode_int(b"\x80"), -128),
    ("int-128", decode_int(b"\x00\x80"), 128),
    # BIT STRING unused-bit rule: low `unused` bits of the last content octet are zero.
    ("bits-unused-3-nonzero", 0x41 & ((1 << 3) - 1), 1),
    # OID first content octet: value = 40*a + b, b <= 39 while a <= 2.
    ("oid-4F-a", 0x4F // 40, 1),
    ("oid-4F-b", 0x4F % 40, 39),
    ("oid-7F-a", 0x7F // 40, 3),
]

# The two assertions that would have caught my own errors before they became tests.
assert decode_tag(b"\x9f\xce\x0f")[2] == 9999, "9999 needs CE 0F, not A3 0F"
assert 0x4F % 40 == 39, "06 01 4F is 1.39, not 1.47"
assert decode_tag(b"\xc1")[0] == 3, "private class is 11, and 0x81 is context"

failures = [name for name, got, want in CHECKS if got != want]
for name, got, want in CHECKS:
    if got != want:
        print(f"[FAIL] {name}: got {got!r} want {want!r}")
print(f"[{'ok' if not failures else 'FAIL'}] {len(CHECKS)} vector derivations checked")
print(f"oid-7F-a=3 means 127 is not a legal first octet where a must be <= 2")
