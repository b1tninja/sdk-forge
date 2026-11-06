"""Which certificate spells its validity against RFC 5280 §4.1.2.5, and how.

`tools/crosscheck_x509.py` reported one shipped trust anchor whose notBefore is GeneralizedTime
for a year the profile says must be UTCTime. This names it, so the finding is about a real issuer
rather than a hash fragment - and so that the decision not to enforce that rule in the decoder is
attached to the evidence for it.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from cryptography import x509

sys.path.insert(0, "D:/code/asn1core/tools")
sys.path.insert(0, "D:/code/asn1core")

import crosscheck_store  # noqa: E402

from asn1core import decode, validity_encoding_issue  # noqa: E402
from asn1core.x509 import certificate_parts  # noqa: E402

dest = Path(tempfile.mkdtemp(prefix="validity_case_"))
for path in crosscheck_store.collect(dest):
    der = path.read_bytes()
    try:
        issue = validity_encoding_issue(der)
    except Exception:  # noqa: BLE001 - this probe is not the thing under test
        continue
    if issue is None:
        continue
    cert = x509.load_der_x509_certificate(der)
    parts = certificate_parts(der)
    window, _ = decode(parts.validity)
    print(f"issuer     : {cert.issuer.rfc4514_string()}")
    print(f"subject    : {cert.subject.rfc4514_string()}")
    print(f"thumbprint : {path.stem}")
    print(f"validity   : {' '.join(hex(k.raw[0]) + ':' + repr(k.payload) for k in window.children)}")
    print(f"issue      : {issue}")
