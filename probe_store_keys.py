"""What is actually in the local trust store, read with an independent parser.

Chosen before writing any asn1core certificate code, so the fixtures are picked from the
population rather than from what the implementation happens to handle. Expected values for
`tests/test_x509_corpus.py` are frozen from this script's output, which is the same move that
settled the OID first-arc question: ask real bytes, not my reading of the grammar.
"""

from __future__ import annotations

import collections
import hashlib
import sys
import tempfile
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def store_paths() -> list[Path]:
    """The local trust store, exported to per-certificate DER files.

    Reuses the exporter from asn1core's own cross-check tool rather than writing a second one,
    so the two scripts cannot drift into examining different populations.
    """
    sys.path.insert(0, "D:/code/asn1core/tools")
    import crosscheck_store  # noqa: PLC0415 - the tool is a script, not an installed module

    # mkdtemp rather than a context manager: the paths have to outlive this function.
    dest = Path(tempfile.mkdtemp(prefix="store_keys_"))
    return crosscheck_store.collect(dest)


def main() -> None:
    shapes: collections.Counter[str] = collections.Counter()
    smallest: dict[str, tuple[int, Path]] = {}
    unreadable: list[tuple[str, str, str]] = []
    total = 0

    for path in store_paths():
        der = path.read_bytes()
        try:
            cert = x509.load_der_x509_certificate(der)
        except Exception as exc:  # noqa: BLE001 - the population's shape is the finding
            print(f"  unparsable by cryptography: {path.name}: {type(exc).__name__}")
            continue
        total += 1
        alg = cert.signature_algorithm_oid.dotted_string
        try:
            spki_bytes = cert.public_key().public_bytes(
                Encoding.DER, PublicFormat.SubjectPublicKeyInfo
            )
        except ValueError as exc:
            # Measured, not hypothetical: some roots in the store carry key data that
            # cryptography cannot serialise at all ("unsupported key type... explicit
            # parameters"), so it cannot serve as an oracle for every certificate. A cross-check
            # against it has to report these as skipped rather than quietly shrinking.
            unreadable.append((path.name, alg, str(exc)[:60]))
            continue
        kind = "ec" if alg.startswith(("1.2.840.10045", "1.3.132", "1.3.36")) else "rsa"
        shapes[f"{kind} {alg} spki={len(spki_bytes)}"] += 1
        if kind not in smallest or len(der) < smallest[kind][0]:
            smallest[kind] = (len(der), path)
        print(
            f"  {path.name[:28]:<28} der={len(der):<6} tbs={len(cert.tbs_certificate_bytes):<6} "
            f"spki={len(spki_bytes):<5} sig={len(cert.signature):<5} alg={alg} "
            f"sha256={hashlib.sha256(der).hexdigest()[:16]}"
        )

    print(f"\ncertificates={total} spki-unreadable-by-cryptography={len(unreadable)}")
    for name, alg, why in unreadable:
        print(f"  SKIP {name[:32]} alg={alg} :: {why}")
    for shape, count in shapes.most_common():
        print(f"  {count:>3}  {shape}")
    print("\nsmallest per family (good fixtures):")
    for kind, (size, path) in sorted(smallest.items()):
        print(f"  {kind:<5} {size:>6} bytes  {path.name}")


if __name__ == "__main__":
    main()
