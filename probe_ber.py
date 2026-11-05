"""Measure snmpy's `ber` codec against the encodings asn1core must get right.

This is evidence-gathering for the extract-versus-clean-room decision in
PORTFOLIO.md section 9, and the input to asn1core/VECTORS.md's defect rows. It reads
D:/code/snmpy as an unmodified third-party tree: nothing here writes to snmpy, and
nothing imports the `snmp` package, so no SNMP side effects are in play.

Every `expected` value below comes from the X.690 encoding rule restated in
asn1core/VECTORS.md, never from what this codec happens to do. Where observed differs
from expected, that is a defect, and the row names the rule it violates.
"""

from __future__ import annotations

import sys
import traceback

sys.path.insert(0, "D:/code/snmpy")

from ber.enums import TagClassEnum  # noqa: E402
from ber.object import Object, ObjectLength, ObjectTag  # noqa: E402

ROWS: list[tuple[str, str, str, str]] = []


def record(case: str, rule: str, expected: str, fn) -> None:
    try:
        observed = fn()
    except Exception as exc:  # noqa: BLE001 - the exception IS the finding
        observed = f"{type(exc).__name__}: {str(exc)[:60]}"
    ROWS.append((case, rule, expected, str(observed)))


# --- 1. Tag round-trip: encode is right, decode is not -----------------------
for number in (1, 30, 31, 63, 127, 128, 16383, 16384):
    tag = ObjectTag(TagClassEnum.context_specific, False, number)

    def probe(t=tag, n=number):
        encoded = bytes(t)
        back, _ = ObjectTag.decode(encoded)
        return f"id={back.tag_id} bytes={encoded.hex()} round_trip={back.tag_id == n}"

    record(f"tag-{number}", "identifier high-tag-number form round-trips", f"id={number}", probe)

# --- 2. Tag decode against hand-written bytes --------------------------------
for case, raw, rule in [
    ("decode-9F1F", "9f1f", "context 31, first two-octet tag"),
    ("decode-9F8100", "9f8100", "context 128"),
    ("decode-9FFF7F", "9fff7f", "context 16383"),
    ("decode-9F818000", "9f81800000", "context 16384"),
    ("decode-truncated-tag", "9f", "runs past buffer: must be a clean error"),
]:
    data = bytes.fromhex(raw)

    def probe(d=data):
        t, off = ObjectTag.decode(d)
        return f"id={t.tag_id} off={off}"

    record(case, rule, "clean error or correct id", probe)

# --- 3. Length encode: float log2 boundary -----------------------------------
for length in (127, 128, 255, 256, 65535, 65536, 16777216):
    record(
        f"len-encode-{length}",
        "definite form: n length octets then big-endian n",
        "no exception",
        lambda L=length: ObjectLength.encode(L).hex(),
    )

# --- 4. Length decode: DER canonicality and indefinite form -------------------
for case, raw, rule in [
    ("len-decode-8180", "8180", "128"),
    ("len-decode-nonminimal", "817f", "127 is non-minimal: DER must refuse"),
    ("len-decode-leading-zero", "82007f", "leading zero octet: DER must refuse"),
    ("len-decode-undefined", "8f01", "reserved high tag number: refuse"),
]:
    data = bytes.fromhex(raw)
    record(
        case,
        rule,
        "value or refusal",
        lambda d=data: f"len={ObjectLength.decode(d)[0]}",
    )

# Indefinite length whose own content contains 00 00: EOC search must not stop early.
# NOTE: ObjectLength.decode expects to start AT the length octet, not at the tag.
# Passing the whole TLV makes it read the tag byte 0x04 as a definite length of 4, which
# measured nothing at all the first time this ran.
indef = bytes.fromhex("0480410000420000")
record(
    "len-indef-inner-nul",
    "content is 41 00 00 42 then EOC, so length is 4",
    "len=4",
    lambda: f"len={ObjectLength.decode(indef, 1)[0]}",
)

# --- 5. Object.decode framing: silent truncation ------------------------------
for case, raw, want in [
    ("obj-truncated-body", "04044141", "error: declares 4 content bytes, supplies 2"),
    ("obj-truncated-nested", "3006040441", "error: child claims 4, only 1 present"),
    ("obj-eoc-indefinite", "30800201000000", "error: indefinite constructed needs an EOC"),
    ("obj-zero-len-child", "30023000", "ACCEPT: a valid empty constructed child"),
]:
    data = bytes.fromhex(raw)
    record(case, want, "error" if "error" in want else "accept", lambda d=data: f"next={Object.decode(d)[1]} buflen={len(d)}")

# --- 6. Raw-byte retention: the I3 requirement --------------------------------
noncanonical = bytes.fromhex("02810100")  # INTEGER 0 with a long-form length of 1
record(
    "retain-raw-bytes",
    "decode must preserve the original TLV octets for signing",
    "original bytes recoverable",
    lambda: f"reencode={bytes(Object.decode(noncanonical)[0]).hex()} original={noncanonical.hex()}",
)

# --- 7. OID first content octet -----------------------------------------------
# Inspect the decoded object rather than assuming its shape: the universal-tag table
# maps object_identifier to a value class, and an earlier version of this probe called
# .value on whatever came back and died with an AttributeError that said nothing about
# the codec.
def oid_probe():
    obj = Object.decode(bytes.fromhex("06027f01"))
    return f"{type(obj).__name__} {obj!r}"


record(
    "oid-first-arc-illegal",
    "first octet 0x7F implies arc 3: illegal, must refuse",
    "refusal",
    oid_probe,
)


def oid_139():
    obj = Object.decode(bytes.fromhex("06014f"))
    return f"{type(obj).__name__} {obj!r}"


record("oid-1-39", "0x4F = 40*1+39", "1.39", oid_139)

# --- report -------------------------------------------------------------------
print(f"{'case':26} {'expected':38} observed")
print("-" * 108)
mismatches = 0
for case, rule, expected, observed in ROWS:
    flag = " "
    if "Error" in observed or "error" in expected.lower() and "Error" not in observed:
        flag = "!"
    if "Error" in observed:
        mismatches += 1
    print(f"{case:26} {expected:38} {observed} {flag}")
print("-" * 108)
print(f"rows={len(ROWS)} raised={mismatches}")
print("read asn1core/VECTORS.md for the rule behind each case; a value here is an")
print("observation about snmpy, never an expectation for asn1core.")
traceback  # noqa: B018  (kept so import failures surface loudly above)
