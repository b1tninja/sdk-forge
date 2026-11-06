"""Copy two trust-store roots into asn1core's fixtures and print the facts to freeze.

The expected digests here come from `cryptography`, an implementation nobody in this repository
authored - the same reason `tools/crosscheck_store.py` exists. Freezing a digest rather than the
whole blob keeps the test readable, and the cross-check tool covers the byte-level comparison
across the entire store on every run.

Run: `python probe_fixture_facts.py` from D:\\code\\sdk-forge.
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

# The smallest ECDSA and RSA roots found by probe_store_keys.py, named by the leading digits of
# their SHA-1 thumbprint. Prefix rather than exact match: the lookup below resolves it, and a
# machine whose store lacks these prints MISSING instead of quietly substituting another root.
PICKS = {
    "843573112A3B319344E5E4ECABC9F26C7CD54D07": "root-ecdsa.der",
    "742C3192E607E424EB4549542BE1BBC53E6174E2": "root-rsa.der",
}
FIXTURES = Path("D:/code/asn1core/tests/fixtures")


def main() -> None:
    sys.path.insert(0, "D:/code/asn1core/tools")
    import crosscheck_store  # noqa: PLC0415

    dest = Path(tempfile.mkdtemp(prefix="fixture_facts_"))
    by_thumbprint = {p.stem.upper(): p for p in crosscheck_store.collect(dest)}
    FIXTURES.mkdir(parents=True, exist_ok=True)

    for thumbprint, filename in PICKS.items():
        found = next(
            (p for tp, p in by_thumbprint.items() if tp.startswith(thumbprint.upper())),
            None,
        )
        if found is None:
            print(f"  MISSING {thumbprint} (store contents differ on this machine)")
            continue
        der = found.read_bytes()
        cert = x509.load_der_x509_certificate(der)
        spki = cert.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
        tbs = cert.tbs_certificate_bytes
        (FIXTURES / filename).write_bytes(der)
        print(f"{filename}")
        print(f"  der      = {len(der)} bytes  sha256 {hashlib.sha256(der).hexdigest()}")
        print(f"  tbs      = {len(tbs)} bytes  sha256 {hashlib.sha256(tbs).hexdigest()}")
        print(f"  spki     = {len(spki)} bytes  sha256 {hashlib.sha256(spki).hexdigest()}")
        print(f"  spki head/tail = {spki[:8].hex()} ... {spki[-4:].hex()}")
        print(f"  tbs  head      = {tbs[:12].hex()}")
        print(f"  sigalg oid     = {cert.signature_algorithm_oid.dotted_string}")
        print(f"  sig value len  = {len(cert.signature)}")


if __name__ == "__main__":
    main()
