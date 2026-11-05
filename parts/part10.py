README = """
# @NAME@

<!-- PyPI badges go live with the first release. Until then a version badge renders
     "no version" on the landing page, which reads as a defect rather than a date, so
     the badges stay commented out until the tag exists.
-->

**Pre-alpha shell.** The package surface, the obligation matrix and the CI gates exist.
No protocol behaviour is implemented: every public function raises `NotImplementedError`,
and the test suite records that rather than hiding it. Read
[ROADMAP.md](ROADMAP.md) before depending on any of it.

@TITLE@

@WHY@

## The gap, with a date

PyPI was queried on @SURVEY_DATE@ for this name and for every neighbouring project. Landscape
claims rot quickly: two projects in this portfolio shipped within five days of the survey,
which is why the table below carries dates instead of adjectives.

@PRIOR@

What this project intends to add:

@GAPS@

## Specification spine

Status and publication dates below were read from the RFC Editor record on @SURVEY_DATE@. A
section number is cited only where that section was read in full; everything else cites the
document, which is the honest grain size for a plan. See [docs/rfc-map.md](docs/rfc-map.md).

@DOCS@

### Errata watch

@ERRATA@

## Module layout

@MODULES@

## What it does not do

@NONGOALS@

@DEPSNOTE@
## Install

```bash
git clone https://github.com/@ORG@/@NAME@.cd @NAME@
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\\\Scripts\\\\Activate.ps1
pip install -e \".[dev]\"
```

Not published to PyPI yet. The name is reserved for this repository's trusted publisher at
the moment of the first release.

## Development

All four gates must pass, on Linux and Windows alike:

```bash
ruff check . && ruff format --check .
mypy @PKG@
pytest -q --cov
python -O -m pytest -q
```

The last line is the one that matters most in a protocol library. `-O` strips `assert`, and a
parser whose bounds checks were asserts stops being a parser under production flags. Wire
paths raise named exceptions; asserts belong in tests and nowhere else.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
"""

ROADMAP = """
# Specification completeness -- and the roadmap it implies

This is the project's north star: every protocol obligation @NAME@ could plausibly take on,
with an honest status against the code at `HEAD`. It is blunt about gaps on purpose. A
roadmap that overstates its coverage is not a plan, it is marketing.

**The honesty rule:** a row may read `[ok]` only when a named test would fail if the
behaviour regressed. Reading the code and agreeing with it is not enough. That is how
"decoded but never sent" quietly becomes "implemented".

Legend: `[ok]` implemented and pinned by a named test -- `[part]` partial, with what is
missing stated -- `[ ]` not implemented -- `[no]` deliberate non-goal.

Update the affected row in the same commit that changes the behaviour. A row and its test
drift apart within one release, and the document becomes useless exactly when it is needed.

## 1. Obligations

@ROWS@

## 2. Milestones

@STEPS@

Every milestone is accepted by its rows above flipping to `[ok]` with a named test, not by
the code existing. Coverage in `pyproject.toml` ratchets in the same commit.

## 3. Errata watch

@ERRATA@

## 4. Deliberate non-goals

@NONGOALSROWS@

## 5. Open questions

@OPEN@

## 6. Publication checklist

- [ ] every `[ ]` row above either `[ok]` or moved to a named later milestone
- [ ] `docs/research.md` claims re-verified and the dated ones either promoted or deleted
- [ ] interoperability evidence recorded in `docs/` against a non-Python implementation
- [ ] `tools/check_dist.py` proves the wheel ships the fixtures the README promises
- [ ] version 0.1.0 tagged, trusted publisher configured, README badges uncommented
"""

OPEN_QUESTIONS = {
    "rpkit": [
        "rsync or RRDP first: rsync is universal, RRDP is the future and the easier test target",
        "repository cache format, and whether it is shared with rtrkit on disk",
    ],
    "rtrkit": [
        "does the server hold a full assertion set or stream from rpkit incrementally",
    ],
    "asnkit": [
        "pure-Python radix versus an optional native one, decided by a benchmark on a full RIB",
    ],
    "h3tunnel": [
        "which adapter lands first: qh3 or aioquic, given both expose datagrams today",
        "does the proxy side need CONNECT-TCP before users ask for it",
    ],
    "dnssd-srp": [
        "share the DNS codec with namespy through a dependency, or keep a thin local layer",
        "how much of the registrar is a server rather than a validator",
    ],
    "turnkit": [
        "does the ICE agent need to be wire compatible with aioice for a shared test harness",
    ],
    "leasespy": [
        "which lease store interface keeps a production server possible without embedding one",
        "how far to chase RFC 9915 conformance while peers still speak RFC 8415 behaviour",
    ],
    "cwmp": [
        "which TR revision is the baseline, and how the chosen revision is pinned in tests",
    ],
    "devicespy": [
        "depend on the maintained ssdp library or speak multicast HTTP directly",
    ],
    "ohttp": [
        "is the HPKE layer a dependency on hpke or a pinned local implementation",
    ],
    "ntspy": [
        "how much of RFC 5905 is in scope once the errata and RFC 9748 registry changes apply",
    ],
    "tacacs": [
        "verify the scope of pytacs before assuming the field is empty",
        "which vendor deviations become conformance fixtures",
    ],
    "signeddata": [
        "how far the EnvelopedData recipient-info matrix extends in a first release",
    ],
    "pgpenv": [
        "which algorithm policy is default, and whether v4 writing is ever offered",
    ],
    "syslogkit": [
        "does the receiver own backpressure policy or expose a hook for the operator to",
    ],
    "sfields": [
        "vendor the working group test suite as data, and record its provenance",
    ],
    "shaken": [
        "how x5u retrieval is bounded so a verifier cannot be turned into a traffic amplifier",
    ],
    "srtpkit": [
        "which profiles are negotiable by default once RFC 3711 and RFC 7714 are applied",
    ],
}


def modules_table(p: dict[str, Any]) -> str:
    rows = [("`" + m + "`", d) for m, d in p["mods"]]
    return table(("Module", "Responsibility"), rows)


def obligation_rows(p: dict[str, Any]) -> str:
    rows = []
    for mod, _kind, fn, _params, _ret, cite in p["api"]:
        rows.append(
            (
                "`" + mod + "." + fn + "()`",
                cite,
                "`[ ]`",
                "`tests/test_obligations.py::" + fn + "`",
            )
        )
    return table(("Obligation", "Spec", "Status", "Where"), rows)


def nongoal_rows(p: dict[str, Any]) -> str:
    return table(
        ("Non-goal", "Status", "Revisit when"),
        [(g, "`[no]`", "a named document requires it") for g in p["nongoals"]],
    )


def steps_block(p: dict[str, Any]) -> str:
    return "\n".join("- " + s for s in p["steps"])
