"""Settle the v1 STH signature-input question with production data rather than memory.

RFC 6962 section 3.5 declares the TreeHeadSignature as a TLS "digitally-signed struct" whose first
two fields are `Version version;` and `SignatureType signature_type = tree_hash;`. RFC 5246
section 4.7 says the signature is "over the contents of the element" and does not say whether a
field declared with a fixed value is part of those contents, so the text supports a 48-byte input
(timestamp || tree_size || root) or a 50-byte one (with version and signature_type prepended).

Production logs answer it: a real STH from Xenon2026h2 is verified against that log's published key
under exactly one of the two candidates.
"""

import base64
import json
import struct

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.exceptions import InvalidSignature

# Fetched 2026-11-05 from https://ct.googleapis.com/logs/eu1/xenon2026h2/ct/v1/get-sth
STH = json.loads(
    """
{"tree_size": 3024195456, "timestamp": 1793970166342,
 "sha256_root_hash": "f3NbYxNJZb2TI/FykqNm71aho2/6fdpl5/L/k68Ozig=",
 "tree_head_signature": "BAMARzBFAiEAhQDC8D5LYjs1rNGVyVEfiAx4i1ZEpk5QQalh+U0wO5gCICa2aT4UGbCvY5RrfhOoDcfXAOHK9vCjV1GRPQBUrF7A"}
"""
)
# Chrome log list v96.2 (log_list_timestamp 2026-11-05T13:36:08Z), "Google Xenon2026h2"
LOG_KEY_DER = base64.b64decode(
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE5Xd4lXEos5XJpcx6TOgyA5Z7/C4duaTbQ6C9aXL5Rbqaw+mW1XDnDX7JlRUninIwZYZDU9wRRBhJmCVopzwFvw=="
)
LOG_ID = base64.b64decode("2AlVO5RPev/IFhlvlE+Fq7D4/F6HVSYPFdEucrtFSxQ=")

root = base64.b64decode(STH["sha256_root_hash"])
digitally_signed = base64.b64decode(STH["tree_head_signature"])
print("DigitallySigned header:", digitally_signed[:4].hex(), "payload len", len(digitally_signed) - 4)
print("  hash alg byte:", digitally_signed[0], "(4 = sha256)  sig alg byte:", digitally_signed[1], "(3 = ecdsa)")
print("  declared length:", struct.unpack(">H", digitally_signed[2:4])[0], "actual:", len(digitally_signed) - 4)
signature = digitally_signed[4:]

public_key = load_der_public_key(LOG_KEY_DER)

t = struct.pack(">Q", STH["timestamp"])
n = struct.pack(">Q", STH["tree_size"])
candidates = {
    "48: timestamp||tree_size||root": t + n + root,
    "50: version(0)||sigtype(tree_hash=1)||timestamp||tree_size||root": bytes([0, 1]) + t + n + root,
    "50: version(0)||sigtype(certificate_timestamp=0)||timestamp||tree_size||root": bytes([0, 0]) + t + n + root,
}
for label, message in candidates.items():
    try:
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        print(f"VERIFIES  [{len(message)}] {label}")
    except InvalidSignature:
        print(f"no        [{len(message)}] {label}")

import hashlib

print("log_id == sha256(SPKI DER)?", hashlib.sha256(LOG_KEY_DER).digest() == LOG_ID)
