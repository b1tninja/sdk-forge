"""What distinguished names in the local trust store actually look like.

Run before writing any name code, because the shape of the problem is the shape of the data. The
questions that change the design: do RDNs hold more than one attribute (multi-valued), which
string types appear (PrintableString against UTF8String), does any name carry characters that
case-folding or whitespace compression would touch, and do attribute types repeat.

Printed per certificate, then summarised.
"""

from __future__ import annotations

import collections
import sys
import tempfile
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID

sys.path.insert(0, "D:/code/asn1core/tools")
sys.path.insert(0, "D:/code/asn1core")

import crosscheck_store  # noqa: E402

from asn1core import decode  # noqa: E402
from asn1core.x509 import certificate_parts  # noqa: E402

# Universal tags of the AttributeValue choices that appear in practice.
STRING_TAGS = {
    12: "utf8String",
    13: "numericString",
    14: "printableString",
    19: "teletexString",
    20: "videotexString",
    22: "ia5String",
    26: "visibleString",
    27: "generalString",
    30: "bmpString",
}

stats: collections.Counter[str] = collections.Counter()
multi = []
odd_strings: list[tuple[str, str, str]] = []

dest = Path(tempfile.mkdtemp(prefix="namesurvey_"))
for path in crosscheck_store.collect(dest):
    der = path.read_bytes()
    try:
        parts = certificate_parts(der)
        tbs, _ = decode(parts.tbs_certificate, der=True)
    except Exception as exc:  # noqa: BLE001
        print(f"  skip {path.name[:20]}: {type(exc).__name__}")
        continue
    fields = list(tbs.children)
    if fields and fields[0].tag.is_context(0):
        fields.pop(0)
    issuer, subject = fields[2], fields[4]
    for label, name in (("issuer", issuer), ("subject", subject)):
        if name.tag.number != 16:
            continue
        stats["names"] += 1
        for rdn in name.children:
            stats[f"rdn-arity-{len(rdn.children)}"] += 1
            if len(rdn.children) > 1:
                multi.append((path.stem[:16], label, len(rdn.children)))
            for ava in rdn.children:
                _oid_node, value = ava.children
                tag_number = value.tag.number
                stats[f"string-{STRING_TAGS.get(tag_number, f'tag{tag_number}')}"] += 1
                text = (value.payload or b"").decode("utf-8", "replace")
                if tag_number == 19 or text != text.casefold() or "  " in text:
                    odd_strings.append((path.stem[:16], STRING_TAGS.get(tag_number, "?"), text))
        stats[f"rdns-{len(name.children)}"] += 1

print("\nmulti-valued RDNs:", multi or "none")
print("\nstring types and shapes:")
for key, count in sorted(stats.items(), key=lambda kv: -kv[1]):
    print(f"  {count:>4}  {key}")
print("\nvalues needing case folding or holding mixed case / double space:")
for name, kind, text in odd_strings[:12]:
    print(f"  {name} {kind}: {text!r}")
print(f"  ({len(odd_strings)} total)")

# A short-name sample to show what cryptography renders for the same names.
print("\nsample rfc4514 renderings:")
for path in list(crosscheck_store.collect(dest))[:3]:
    cert = x509.load_der_x509_certificate(path.read_bytes())
    print(f"  {cert.subject.rfc4514_string()}")
