"""Leaf hash of entry 0 of Xenon2026h2, and the URL-encoded form the proof endpoint wants."""

import base64
import hashlib
import urllib.parse

LEAF_INPUT = (
    "AAAAAAGQETJORwAB43aJADBzoMZJzGVt6UbAMXTSXFZv48OAW4RvUjaUN5gAAtswggLXoAMCAQICBwYawyyA6E4wDQYJKo"
    "ZIhvcNAQELBQAwfzELMAkGA1UEBhMCR0IxDzANBgNVBAgMBkxvbmRvbjEXMBUGA1UECgwOR29vZ2xlIFVLIEx0ZC4xITAf"
    "BgNVBAsMGENlcnRpZmljYXRlIFRyYW5zcGFyZW5jeTEjMCEGA1UEAwwaTWVyZ2UgRGVsYXkgSW50ZXJtZWRpYXRlIDEw"
    "HhcNMjQwNjEzMTA0MzQ3WhcNMjYxMTE4MjAxNzU5WjBjMQswCQYDVQQGEwJHQjEPMA0GA1UEBwwGTG9uZG9uMSgwJgYD"
    "VQQKDB9Hb29nbGUgQ2VydGlmaWNhdGUgVHJhbnNwYXJlbmN5MRkwFwYDVQQFExAxNzE4Mjc1NDI3ODU0NDE0MIIBIjAN"
    "BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsVotl/HczabMfG5DseuE4PZyKfDcm2po5j3CzpBo9ErKd9a8/BQOnd9+"
    "HKhTDEFYRkgiOxNX5+GtSHoBuAa28FU1p+w6uQLDjE1acDWvxXwqgpRqLl8LeyoMA8LbHsuMUVQarSa/OkiZISGddQRa"
    "2GxbGW4ITvYnkgdx4KOgCoIimyhu1GrZJg9DcUVteWiO65VoXu9+n0XBWAyiykfuzVSP1fps9zWfxjx2yxEqxhkofulI"
    "z1ti5f8ZQPpUu9GJPEVkO1qFeokcNB/z/u5xhJ2QCM46+bSsQmYZ4CqNAI+LufdIgTBpIK9DijqbjfCzMjNaBIi88T4k"
    "qB9vyLcwmwIDAQABo4GLMIGIMBMGA1UdJQQMMAoGCCsGAQUFBwMBMCMGA1UdEQQcMBqCGGZsb3dlcnMtdG8tdGhlLXdv"
    "cmxkLmNvbTAMBgNVHRMBAf8EAjAAMB8GA1UdIwQYMBaAFOk8BOGAL8KEEy0mcJ7y/RrPqv7GMB0GA1UdDgQWBBS4AeyN"
    "NX7ncgTELxVjttf+N/JAGAAA="
)

raw = base64.b64decode(LEAF_INPUT)
print("leaf_input bytes:", len(raw))

# RFC 6962 sections 3.4 and 3.2: the leaf is version, leaf_type, then a TimestampedEntry whose first
# fields are the 8-byte timestamp and the 2-byte entry type. (An earlier version of this probe read
# entry_type at offset 2 and printed nonsense, which is the mistake the length checks below catch.)
cursor = 0
version, leaf_type = raw[cursor], raw[cursor + 1]
cursor += 2
timestamp = int.from_bytes(raw[cursor : cursor + 8], "big")
cursor += 8
entry_type = int.from_bytes(raw[cursor : cursor + 2], "big")
cursor += 2
print(f"version={version} leaf_type={leaf_type} timestamp={timestamp} entry_type={entry_type}")
assert (version, leaf_type) == (0, 0), "v1 timestamped_entry"
assert 1_700_000_000_000 < timestamp < 1_800_000_000_000, "a millisecond epoch in the last decade"

if entry_type == 0:
    length = int.from_bytes(raw[cursor : cursor + 3], "big")  # ASN.1Cert: opaque<1..2^24-1>
    cursor += 3 + length
    print(f"x509_entry: certificate {length} bytes")
else:
    issuer_key_hash = raw[cursor : cursor + 32]  # PreCert: fixed 32, no length prefix
    cursor += 32
    length = int.from_bytes(raw[cursor : cursor + 3], "big")
    cursor += 3 + length
    print(f"precert_entry: issuer_key_hash={issuer_key_hash.hex()[:16]}... tbs={length} bytes")

extensions = int.from_bytes(raw[cursor : cursor + 2], "big")
cursor += 2 + extensions
assert cursor == len(raw), f"{len(raw) - cursor} bytes left over after the extensions vector"
print(f"extensions={extensions} bytes; structure consumes the whole {len(raw)} bytes")

leaf = hashlib.sha256(b"\x00" + raw).digest()
encoded = base64.b64encode(leaf).decode()
print("leaf hash b64:", encoded)
print("url:", urllib.parse.quote(encoded, safe=""))

