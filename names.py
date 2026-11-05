"""Check whether a Python package name is really free on PyPI.

Written because a bare 404 is not evidence. Three things have to be true before a
name can be called free, and this tool enforces all three:

  1. Both registry signals agree. ``/simple/<name>/`` answers for the name and
     ``/pypi/<name>/json`` answers for the project. simple=200 with json=404 is a
     registered-but-empty squat, which blocks a name as firmly as a release does.
  2. The endpoint is actually answering. Blanket 404s from a rate limiter look
     identical to an unclaimed name, so a canary that must exist and a canary that
     must not are probed first, and the run refuses to report FREE if either lies.
  3. Nothing one keystroke away is live. ``asn1kit`` is unusable because ``asnkit``
     exists, and ``der-py`` is unusable because ``derpy`` exists. PEP 503 folds
     ``DERPY``, ``der_py`` and ``der.py`` together, so case and separator variants are
     one name, and near-misses are checked against the full namespace with --index.

Usage:
    python names.py rpkit ctspy derpy der-py           probe these names
    python names.py --index derkit asn1core            also distance-check namespace
    python names.py --portfolio D:/code                probe every project name
    python names.py --json --out survey.json derkit    machine-readable snapshot

Exit status is 0 when every probed name is free, 1 when any is blocked, 2 when the
registry could not be trusted to answer. CI can gate a release on it.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import pathlib
import re
import string
import sys
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "sdk-forge-names/1.0 (project name survey)", "Accept-Encoding": "gzip"}
MUST_EXIST = ("pip",)
MUST_NOT_EXIST = ("sdk-forge-canary-zx17q4",)
SLEEP = 0.15
ALPHABET = string.ascii_lowercase + string.digits + "-"


def canonical(name: str) -> str:
    """PEP 503: lowercase, and runs of - . _ collapse to a single -."""
    return re.sub(r"[-_.]+", "-", name).lower()


def fetch(url: str) -> tuple[int, bytes]:
    """Return (status, body). Status -1 means a transport fault, not a verdict."""
    request = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read()
            if response.headers.get("Content-Encoding") == "gzip":
                raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            return response.status, raw
    except urllib.error.HTTPError as error:
        return error.code, b""
    except Exception as error:  # noqa: BLE001 - a network fault is a result, not a crash
        return -1, type(error).__name__.encode()


def probe(name: str, retries: int = 3) -> dict:
    """Query both registry signals for one name and classify it."""
    key = canonical(name)
    row = {"name": name, "canonical": key}
    for field, url in (
        ("simple", "https://pypi.org/simple/" + key + "/"),
        ("json", "https://pypi.org/pypi/" + key + "/json"),
    ):
        for _ in range(retries):
            row[field] = fetch(url)[0]
            if row[field] != -1:
                break
            time.sleep(1.5)
        time.sleep(SLEEP)
    if row["json"] == 200:
        code, body = fetch("https://pypi.org/pypi/" + key + "/json")
        payload = json.loads(body or b"{}")
        info = payload.get("info") or {}
        files = payload.get("urls") or []
        row["version"] = info.get("version")
        row["summary"] = (info.get("summary") or "")[:70]
        row["release_count"] = len(payload.get("releases") or {})
        row["uploaded"] = (files[0].get("upload_time") or "")[:10] if files else ""
        row["owner"] = info.get("author") or ""
        row["yanked"] = bool(files[0].get("yanked")) if files else False
        if row["uploaded"]:
            try:
                age = (time.time() - time.mktime(time.strptime(row["uploaded"], "%Y-%m-%d"))) / 86400
                row["dormant_days"] = int(age)
            except ValueError:
                pass
    row["verdict"] = verdict(row["simple"], row["json"])
    return row


def verdict(simple: int, code: int) -> str:
    if code == 200:
        return "TAKEN"
    if simple == 200:
        return "RESERVED-EMPTY"
    if simple == -1 or code == -1:
        return "ERROR"
    if simple == 429 or code == 429:
        return "RATE-LIMITED"
    if simple == 404 and code == 404:
        return "FREE"
    return "UNKNOWN"


def neighbours(name: str, limit: int = 1) -> set:
    """Every spelling within `limit` single edits, as a set.

    Generating the candidate's neighbourhood and testing membership is far cheaper
    than scoring a 600k-name namespace: eight characters yields about five hundred
    candidates at distance one.
    """
    found = {name}
    for _ in range(limit):
        wave = set()
        for word in found:
            for i in range(len(word)):
                wave.add(word[:i] + word[i + 1 :])
                for char in ALPHABET:
                    wave.add(word[:i] + char + word[i + 1 :])
                    wave.add(word[:i] + char + word[i:])
            for char in ALPHABET:
                wave.add(word + char)
        found |= wave
    return found - {name}


def index_namespace(refresh: bool = False) -> set:
    """All canonical project names, from one cached copy of the simple index."""
    cache = pathlib.Path(__file__).with_name("cache") / "pypi-simple.json"
    if cache.exists() and not refresh:
        return set(json.loads(cache.read_text(encoding="utf-8")))
    code, body = fetch("https://pypi.org/simple/")
    if code != 200 or not body:
        raise SystemExit("could not download the namespace index (status " + str(code) + ")")
    text = body.decode("utf-8", "replace")
    names = {canonical(match) for match in re.findall(r">([^<>]+)/?</a>", text)}
    names.discard("")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(sorted(names)), encoding="utf-8")
    return names


def check_canaries() -> list:
    """Refuse to call anything free if the registry is not answering honestly."""
    problems = []
    for name in MUST_EXIST:
        if probe(name)["json"] != 200:
            problems.append("canary " + name + " did not answer 200")
    if probe(MUST_NOT_EXIST[0])["json"] != 404:
        problems.append("canary " + MUST_NOT_EXIST[0] + " unexpectedly exists")
    return problems


def portfolio_names(root: pathlib.Path) -> dict:
    """Project names under a directory, and where each came from.

    A directory with no pyproject.toml still needs checking, because the whole point of
    this tool is to test a name before the project exists: a plan directory with only a
    PLAN.md is exactly the case that must not be silently skipped.
    """
    found = {}
    for project in sorted(root.iterdir()):
        if not project.is_dir():
            continue
        marker = project / "pyproject.toml"
        if marker.is_file():
            match = re.search(r'^name = "([^"]+)"', marker.read_text(encoding="utf-8"), re.M)
            if match:
                found[match.group(1)] = "pyproject"
                continue
        if (project / "PLAN.md").is_file() or (project / "ROADMAP.md").is_file() or (project / "TRUST-MODEL.md").is_file():
            found[project.name] = "directory"
    return found


def self_test() -> int:
    """Offline checks: no network, so CI can run it on a train."""
    cases = [
        (canonical("DERPY"), "derpy"),
        (canonical("der_py"), "der-py"),
        (canonical("der.py"), "der-py"),
        (canonical("a..b__c-d"), "a-b-c-d"),
    ]
    near = neighbours("asnkit", 1)
    cases.append(("asn1kit" in near, True))
    cases.append(("der-py" in neighbours("derpy", 1), True))
    cases.append(("asn1kit" in neighbours("asnkit", 0), False))
    verdicts = [
        (verdict(404, 404), "FREE"),
        (verdict(200, 404), "RESERVED-EMPTY"),
        (verdict(200, 200), "TAKEN"),
        (verdict(429, 429), "RATE-LIMITED"),
        (verdict(-1, 404), "ERROR"),
    ]
    failures = 0
    for got, want in cases + verdicts:
        if got != want:
            failures += 1
            print("FAIL: got " + repr(got) + " want " + repr(want))
    print("self-test:", "passed" if not failures else str(failures) + " failed")
    return 1 if failures else 0


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="PyPI name availability, honestly")
    parser.add_argument("names", nargs="*", help="names to probe")
    parser.add_argument("--portfolio", type=pathlib.Path, help="probe every project name here")
    parser.add_argument("--index", action="store_true", help="flag live names one keystroke away")
    parser.add_argument("--refresh", action="store_true", help="re-download the namespace snapshot")
    parser.add_argument("--json", action="store_true", help="emit rows as JSON")
    parser.add_argument("--out", type=pathlib.Path, help="also write rows to this file")
    parser.add_argument("--self-test", action="store_true", help="offline checks only, no network")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    names = list(args.names)
    origin = {name: "argument" for name in names}
    if args.portfolio:
        for name, source in portfolio_names(args.portfolio).items():
            origin.setdefault(name, source)
            names.append(name)
    if not names:
        parser.error("no names given; pass names or --portfolio PATH")

    problems = check_canaries()
    if problems:
        for problem in problems:
            print("REFUSING TO REPORT: " + problem, file=sys.stderr)
        return 2

    rows = [probe(name) for name in dict.fromkeys(names)]
    blocked = {}
    for row in rows:
        if row["name"] != row["canonical"]:
            blocked[row["name"]] = "  (normalises to " + row["canonical"] + ")"
    if args.index:
        namespace = index_namespace(args.refresh)
        print("# namespace snapshot: " + str(len(namespace)) + " canonical names", file=sys.stderr)
        ours = {row["canonical"] for row in rows}
        for row in rows:
            if row["verdict"] != "FREE":
                continue
            live = sorted(n for n in neighbours(row["canonical"]) if n in namespace)
            peers = sorted(n for n in neighbours(row["canonical"]) if n in ours - {row["canonical"]})
            notes = []
            if live:
                notes.append("one keystroke from live: " + ", ".join(live))
            if peers:
                notes.append("one keystroke from ours: " + ", ".join(peers))
            if notes:
                # Both notes are kept: an earlier version wrote the live flag and then
                # overwrote it with the ours flag, which hid real neighbours.
                previous = blocked.get(row["name"], "")
                blocked[row["name"]] = previous + "  (" + "; ".join(notes) + ")"
    if args.out:
        args.out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            extra = ""
            if row["verdict"] == "TAKEN":
                extra = "v" + str(row.get("version")) + " " + str(row.get("uploaded")) + " " + str(row.get("summary"))
            print("{:<18} canonical={:<18} simple={:<4} json={:<4} {:<14} {}{}".format(
                row["name"], row["canonical"], row["simple"], row["json"], row["verdict"],
                extra, blocked.get(row["name"], "")))
    return 1 if blocked or any(r["verdict"] != "FREE" for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

