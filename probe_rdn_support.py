"""Does this cryptography release support multi-valued RDNs, and how is one built?

Checked before writing the fixture generator rather than discovering it mid-run.
"""

from __future__ import annotations

from cryptography import x509
from cryptography.x509.oid import NameOID

rdn_type = getattr(x509, "RelativeDistinguishedName", None)
print("RelativeDistinguishedName:", rdn_type)
print("public members:", [m for m in dir(rdn_type) if not m.startswith("_")] if rdn_type else "-")

one = x509.RelativeDistinguishedName(
    [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Example S.A."),
    ]
)
print("built rdn, len:", len(one))
print("iteration:", [a.oid.dotted_string for a in one])

try:
    name = x509.Name([one, x509.NameAttribute(NameOID.COMMON_NAME, "Root")])
except TypeError as exc:
    print("Name() rejected a mixed list:", exc)
    try:
        name = x509.Name(
            [
                one,
                x509.RelativeDistinguishedName([x509.NameAttribute(NameOID.COMMON_NAME, "Root")]),
            ]
        )
        print("Name() accepts a list of RelativeDistinguishedName")
    except Exception as exc2:  # noqa: BLE001
        print("and also failed:", type(exc2).__name__, exc2)
        raise SystemExit(1)

print("rfc4514:", name.rfc4514_string())
print("rdn arities:", [len(r) for r in name.rdns])
