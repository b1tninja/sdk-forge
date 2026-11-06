"""What is actually in a prefix of a production log? Measure before designing the store.

`certledger`'s `cl.dedupe` row says entries are not certificates, and `cl.cag-graph` says the CA layer is
every entry with cA=TRUE. Both are shape claims about data nobody has sampled, and PLAN.md lists the true
cardinality of the CA layer as an unmeasured phase-2 blocker. So: take a prefix from several logs run by
different operators, and count what is there - entries, distinct TBS hashes, cA=TRUE entries, distinct
issuer keys, distinct subject keys - and whether two logs' prefixes share certificates at all.

The dedupe question needs the answer to that last one most: duplicates across logs are the whole reason
raw entry counts are meaningless, and if a 64-entry prefix of two logs shares nothing, the dedupe test
has to be built from a bigger sample or from a longer overlap window, and it is better to learn that now
than after the store is written.
"""

import base64
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "ctspy"), str(ROOT / "ctspy" / "tools"), str(ROOT / "asn1core")]

from asn1core import parse_certificate  # noqa: E402
from ctspy.entry import MerkleTreeLeaf, PrecertEntry, X509Entry  # noqa: E402
from fetch_evidence import get_json, parse_extra_data  # noqa: E402

BASIC_CONSTRAINTS = (2, 5, 29, 19)
PREFIX = 64

SWEEP = json.loads(
    (ROOT / "ctspy" / "tests" / "fixtures" / "log-list-sweep.json").read_text(encoding="utf-8")
)
# Two Google logs because the overlap question needs a pair from an operator that runs several logs in
# parallel, and one log from each other operator in the list. URLs come from the captured list rather than
# from memory: a guessed hostname would just be reported as unreachable and the run would look empty.
wanted = {"Google": 2, "DigiCert": 1, "Cloudflare": 1, "Sectigo": 1, "TrustAsia": 1}
seen: dict[str, int] = {}
ORIGINS = {}
for record in SWEEP["logs"]:
    operator = record["operator"]
    if seen.get(operator, 0) >= wanted.get(operator, 0):
        continue
    seen[operator] = seen.get(operator, 0) + 1
    ORIGINS[f"{record['description']}"] = record["url"]


def is_ca(cert) -> bool:
    for extension in cert.extensions:
        if extension.oid == BASIC_CONSTRAINTS:
            body = extension.value
            # SEQUENCE { BOOLEAN cA DEFAULT FALSE, ... }: no BOOLEAN means cA=FALSE.
            return b"\x01\x01\xff" in body
    return False


def collect(origin: str) -> dict:
    raw = get_json(f"{origin}/ct/v1/get-entries?start=0&end={PREFIX - 1}")
    rows = []
    for item in raw["entries"]:
        leaf = MerkleTreeLeaf.parse(base64.b64decode(item["leaf_input"]))
        subject, chain = parse_extra_data(base64.b64decode(item["extra_data"]))
        try:
            cert = parse_certificate(subject)
        except Exception as exc:  # noqa: BLE001
            rows.append({"error": type(exc).__name__, "entry": leaf})
            continue
        issuer_hash = (
            leaf.entry.entry.issuer_key_hash
            if isinstance(leaf.entry.entry, PrecertEntry)
            else (hashlib.sha256(parse_certificate(chain[0]).subject_public_key_info).digest() if chain else None)
        )
        rows.append(
            {
                "leaf": leaf,
                "cert": cert,
                "tbs_hash": hashlib.sha256(cert.tbs_certificate).digest(),
                "subject_spki_hash": hashlib.sha256(cert.subject_public_key_info).digest(),
                "issuer_spki_hash": issuer_hash,
                "ca": is_ca(cert),
                "entry_type": 1 if isinstance(leaf.entry.entry, PrecertEntry) else 0,
                "chain": len(chain),
                "der": subject,
            }
        )
    return {"rows": rows, "count": len(raw["entries"])}


corpora = {}
for name, origin in ORIGINS.items():
    try:
        corpora[name] = collect(origin)
    except Exception as exc:  # noqa: BLE001
        print(f"{name}: unreachable ({type(exc).__name__})")
        continue
    rows = [row for row in corpora[name]["rows"] if "cert" in row]
    failed = len(corpora[name]["rows"]) - len(rows)
    tbs = {row["tbs_hash"] for row in rows}
    subjects = {row["subject_spki_hash"] for row in rows}
    issuers = {row["issuer_spki_hash"] for row in rows if row["issuer_spki_hash"]}
    ca = [row for row in rows if row["ca"]]
    der_distinct = {hashlib.sha256(row["der"]).digest() for row in rows}
    print(
        f"\n{name}: {corpora[name]['count']} entries, {len(rows)} parsed, {failed} refused parsing"
    )
    print(
        f"  entry types precert/x509: {sum(1 for r in rows if r['entry_type'] == 1)}/"
        f"{sum(1 for r in rows if r['entry_type'] == 0)}"
    )
    print(
        f"  distinct TBS {len(tbs)}; distinct DER {len(der_distinct)}; "
        f"cA=TRUE {len(ca)}; issuers {len(issuers)}; subjects {len(subjects)}"
    )
    if len(der_distinct) != len(tbs):
        print("  ** same TBS, different DER: the dedupe case, unforced **")
    if failed:
        names = {row["error"] for row in corpora[name]["rows"] if "error" in row}
        print(f"  parse failures: {names}")

print("\n--- overlap between logs, by TBS hash ---")
names = list(corpora)
for i, left in enumerate(names):
    for right in names[i + 1 :]:
        a = {row["tbs_hash"] for row in corpora[left]["rows"] if "cert" in row}
        b = {row["tbs_hash"] for row in corpora[right]["rows"] if "cert" in row}
        shared = a & b
        if shared:
            print(f"  {left} / {right}: {len(shared)} certificates in both prefixes")
print("  (silence above means these 64-entry prefixes share no certificates)")

print("\n--- issuer keys seen across logs (the CA layer, if any is present) ---")
by_issuer: dict[bytes, set] = {}
for name, corpus in corpora.items():
    for row in corpus["rows"]:
        if "cert" in row and row["ca"]:
            by_issuer.setdefault(row["subject_spki_hash"], set()).add(name)
print(f"  distinct cA=TRUE subject keys across all samples: {len(by_issuer)}")
for key, logs in list(by_issuer.items())[:6]:
    print(f"    {key.hex()[:16]}... in {sorted(logs)}")
