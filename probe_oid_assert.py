"""Does snmpy validate object identifiers with a bare ``assert``?

Its own suite says so: ``test_objectIdentifier.test_invalid_oids`` expects ``AssertionError``
for ``"3.0"`` and ``"1.41"``. If that is the mechanism, then ``python -O`` - which is how this
portfolio runs CI, precisely so that a parser does not lean on asserts - deletes the
validation, and an illegal OID is accepted silently rather than loudly.

Run this both ways and read the ``__debug__`` line. It measures snmpy; it says nothing about
asn1core, which imports nothing from it.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "D:/code/snmpy")

from ber.object import ObjectIdentifier  # noqa: E402

print(f"__debug__={__debug__}  (python -O sets this False and strips assert statements)")
for text in ("3.0", "1.41", "2.28.0", "1.3.6.1"):
    try:
        oid = ObjectIdentifier.from_string(text)
    except AssertionError as exc:
        print(f"  {text:<10} rejected: AssertionError {exc}")
    except Exception as exc:  # noqa: BLE001 - the type is the finding
        print(f"  {text:<10} rejected: {type(exc).__name__}: {exc}")
    else:
        print(f"  {text:<10} ACCEPTED as {str(oid)!r}")

# --- the encoder, which is a separate question from the validation above -------------
#
# snmpy's own suite asserts that 2.100.3 encodes to B4 03. Under X.690 the first pair is one
# base-128 value, and 0xB4 has the continuation bit set, so a conforming parser reads B4 03 as
# the single value 6659 and yields 2.6579. The minimal spelling of 2.100.3 is 81 34 03. Note
# that B4 03 is not invalid DER - it is valid DER *for a different OID*.
print()
print("encoder: does what snmpy writes decode back to what it was given?")
for text in ("2.100.3", "2.47.1", "1.3.128", "2.5.29.19", "2.16.840.1.113733.1"):
    try:
        raw = bytes(ObjectIdentifier.from_string(text))
    except Exception as exc:  # noqa: BLE001
        print(f"  {text:<22} encode raised {type(exc).__name__}: {exc}")
        continue
    print(f"  {text:<22} wrote {raw.hex()}  decodes-as-arcs={ObjectIdentifier(raw)._as_tuple()}")

