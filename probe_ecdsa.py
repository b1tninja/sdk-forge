"""Cross-check the pure-Python P-256 verifier against OpenSSL and against a production STH."""

import base64
import hashlib
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from ctspy.ecdsa import EcdsaKey, SignatureDecodeError, verify_sha256

LOG_KEY = base64.b64decode(
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE5Xd4lXEos5XJpcx6TOgyA5Z7/C4duaTbQ6C9aXL5Rbqaw+mW1XDnDX7JlRUninIwZYZDU9wRRBhJmCVopzwFvw=="
)
LOG_ID = base64.b64decode("2AlVO5RPev/IFhlvlE+Fq7D4/F6HVSYPFdEucrtFSxQ=")
STH = {
    "tree_size": 3024195456,
    "timestamp": 1793970166342,
    "sha256_root_hash": "f3NbYxNJZb2TI/FykqNm71aho2/6fdpl5/L/k68Ozig=",
    "tree_head_signature": "BAMARzBFAiEAhQDC8D5LYjs1rNGVyVEfiAx4i1ZEpk5QQalh+U0wO5gCICa2aT4UGbCvY5RrfhOoDcfXAOHK9vCjV1GRPQBUrF7A",
}

key = EcdsaKey.from_spki(LOG_KEY)
print("parsed key x:", hex(key.x)[:18])
print("log_id matches Chrome's:", key.log_id == LOG_ID)
root = base64.b64decode(STH["sha256_root_hash"])
ds = base64.b64decode(STH["tree_head_signature"])
message = bytes([0, 1]) + struct.pack(">Q", STH["timestamp"]) + struct.pack(">Q", STH["tree_size"]) + root
print("real STH verifies:", verify_sha256(key, message, ds[4:]))
print("rejects one flipped bit in the message:", verify_sha256(key, message[:-1] + bytes([message[-1] ^ 1]), ds[4:]))

agree = reject = 0
for i in range(150):
    private = ec.generate_private_key(ec.SECP256R1())
    public_der = private.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    our_key = EcdsaKey.from_spki(public_der)
    payload = b"ct payload %d" % i
    signature = private.sign(payload, ec.ECDSA(hashes.SHA256()))
    if verify_sha256(our_key, payload, signature):
        agree += 1
    tampered = payload + b"x"
    if verify_sha256(our_key, tampered, signature):
        reject += 1
print(f"agrees with OpenSSL on {agree}/150 valid; falsely accepted {reject} tampered messages")

# Negative structural cases.
private = ec.generate_private_key(ec.SECP256R1())
pub = EcdsaKey.from_spki(
    private.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
)
sig = private.sign(b"canonical", ec.ECDSA(hashes.SHA256()))
print("accepts canonical:", verify_sha256(pub, b"canonical", sig))
print("rejects trailing byte:", verify_sha256(pub, b"canonical", sig + b"\x00"))
r_len = sig[3]
respelled = sig[:2] + bytes([0x81, r_len]) + sig[4:]
print("rejects non-minimal outer length:", verify_sha256(pub, b"canonical", respelled))
print("rejects s=0 (constructed):", verify_sha256(pub, b"canonical", bytes.fromhex("3006020101020100")))
print("rejects empty sequence:", verify_sha256(pub, b"canonical", bytes.fromhex("3000")))
off_curve = bytearray(LOG_KEY)
off_curve[-1] ^= 0x01
try:
    EcdsaKey.from_spki(bytes(off_curve))
    print("accepted an off-curve key: BAD")
except SignatureDecodeError as exc:
    print("rejects off-curve key:", str(exc)[:48])
print("sha256 of spki:", hashlib.sha256(LOG_KEY).hexdigest()[:16])
