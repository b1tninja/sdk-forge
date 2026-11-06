"""Characterising verify_consistency: does it pin `second`, or only its bit length?

Found by production data, not by a synthetic case. `tests/test_production_proofs.py` asks whether a
real consistency proof for (1, 3024266407) still verifies when `second` is claimed as one less. It
does. That is either a coincidence or an under-constrained verifier, and only an oracle can tell:
for small trees, "tree(first) is a prefix of tree(second)" is decidable by brute force, so every
accept can be checked against the truth.
"""

import base64
import hashlib
import itertools
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "ctspy" / "ctspy"))

import merkle  # noqa: E402

FIXTURE = json.loads(
    (
        pathlib.Path(__file__).resolve().parent.parent / "ctspy" / "tests" / "fixtures" / "production-proofs.json"
    ).read_text(encoding="utf-8")
)
AUDIT = tuple(
    base64.b64decode(node) for node in FIXTURE["consistency_proof"][FIXTURE["consistency_field"]]
)
LEAF = base64.b64decode(FIXTURE["entry"]["leaf_input"])
LEAF_HASH = merkle.leaf_hash(LEAF)

print(f"proof has {len(AUDIT)} nodes; does it begin with the leaf hash? {AUDIT[0] == LEAF_HASH}")

H = lambda *parts: hashlib.sha256(b"".join(parts)).digest()  # noqa: E731


def spec_verify(first, second, proof, first_hash, second_hash, prepend_one=True):
    """RFC 9162 2.1.4.2 written out again here, so the library's version can disagree with it."""
    if not proof:
        return False
    path = list(proof)
    power_of_two = first & (first - 1) == 0
    if power_of_two and (first > 1 or prepend_one):
        path.insert(0, first_hash)
    fn, sn = first - 1, second - 1
    if fn & 1:
        while fn & 1:
            fn >>= 1
            sn >>= 1
    fr = sr = path[0]
    for c in path[1:]:
        if sn == 0:
            return False
        if fn & 1 or fn == sn:
            fr = H(b"\x01", c, fr)
            sr = H(b"\x01", c, sr)
            if not fn & 1:
                while not fn & 1 and fn != 0:
                    fn >>= 1
                    sn >>= 1
        else:
            sr = H(b"\x01", sr, c)
        fn >>= 1
        sn >>= 1
    return fr == first_hash and sr == second_hash and sn == 0


print("--- the production fixture, claimed at several tree sizes ---")
for delta in (0, 1, 2, 1000):
    claimed = int(FIXTURE["head"]["tree_size"]) - delta
    root = base64.b64decode(FIXTURE["head"]["sha256_root_hash"])
    lib = merkle.verify_consistency(1, claimed, AUDIT, LEAF_HASH, root)
    spec = spec_verify(1, claimed, AUDIT, LEAF_HASH, root)
    print(f"  second={claimed} (delta {delta}): library={lib} spec={spec}")

print("--- brute force over small trees: is a proof for (f, s2) accepted for s1 != s2? ---")
worst = []
for size in range(2, 14):
    entries = [f"e{i}".encode() for i in range(size)]
    for first in range(1, size):
        proof = merkle.consistency_path(first, entries)
        old_root = merkle.tree_hash(entries[:first])
        for second in range(first + 1, size + 1):
            if second == size:
                continue
            new_root = merkle.tree_hash(entries[:second])
            if merkle.verify_consistency(first, second, proof, old_root, new_root):
                worst.append((first, second, size))
print(f"  mismatched (claimed_second, real_proof_second) pairs accepted: {len(worst)}")
for row in worst[:12]:
    print(f"    first={row[0]} claimed second={row[1]} but the proof was for {row[2]}")

print("--- same sweep using the literal spec transcription ---")
worst2 = []
for size in range(2, 14):
    entries = [f"e{i}".encode() for i in range(size)]
    for first in range(1, size):
        proof = merkle.consistency_path(first, entries)
        old_root = merkle.tree_hash(entries[:first])
        for second in range(first + 1, size + 1):
            if second == size:
                continue
            new_root = merkle.tree_hash(entries[:second])
            if spec_verify(first, second, proof, old_root, new_root):
                worst2.append((first, second, size))
print(f"  accepted mismatches: {len(worst2)}")
for row in worst2[:12]:
    print(f"    first={row[0]} claimed second={row[1]} but the proof was for {row[2]}")

print("--- does the library agree with the literal spec on honest proofs? ---")
disagree = 0
for size in range(2, 14):
    entries = [f"e{i}".encode() for i in range(size)]
    for first in range(1, size):
        proof = merkle.consistency_path(first, entries)
        old_root = merkle.tree_hash(entries[:first])
        new_root = merkle.tree_hash(entries)
        if merkle.verify_consistency(first, size, proof, old_root, new_root) != spec_verify(
            first, size, proof, old_root, new_root
        ):
            disagree += 1
            print(f"    disagree at first={first} second={size}")
print(f"  disagreements on honest proofs: {disagree}")
