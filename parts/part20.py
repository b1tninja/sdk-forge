# ---------------------------------------------------------------------------
# Part 20: portfolio position (docs/plan.md)
#
# PORTFOLIO.md at the workspace root decides which projects are worked on, in
# what order, and against what. ROADMAP.md inside a project decides protocol
# obligations. Nothing inside a generated repository carried the first of
# those, so an agent reading one project alone could not tell that its wave is
# 4, that two other projects are allowed to be in flight before it, or that
# the codec it plans to verify signatures with has no code anywhere.
#
# What this part writes is a transcription of PORTFOLIO.md sections 4, 6 and 7
# - tier, wave, and the arrows that mean "cannot deliver behaviour without" -
# rather than a reinterpretation of them. Section 10 of that file records the
# ASN.1 role having been mis-assigned to asnkit, with the correction that
# until asn1core exists no certificate-shaped project can ship behaviour. Every
# plan that cites asn1core repeats that sentence, because a caveat kept in one
# file nobody opens is a caveat that gets planned around.
#
# This part also owns the __main__ guard, moved from part 19: it has to run
# after every wrapper in the build chain has been installed, so the last part
# is the one that calls run().
# ---------------------------------------------------------------------------

# name -> (tier, wave, hard dependencies). Transcribed from PORTFOLIO.md
# sections 4 and 6; an arrow means "cannot deliver behaviour without".
POSITION = {
    # Tier 1, wave 1: the chokepoint itself.
    "rpkit": (1, 1, ("asn1core",)),
    # Tier 2, wave 2: the certificate cluster.
    "ctspy": (2, 2, ("asn1core",)),
    "pkix": (2, 2, ("asn1core",)),
    "revokekit": (2, 2, ("asn1core", "pkix")),
    # Tier 2, wave 2: the routing-security cluster, anchored on rpkit.
    "rtrkit": (2, 2, ("rpkit",)),
    "routevalid": (2, 2, ("rpkit", "rtrkit")),
    # Tier 2, wave 4: naming and address allocation.
    "dnssd-srp": (2, 4, ("namespy",)),
    "leasespy": (2, 4, ()),
    # Tier 3, wave 3: the routing-operations story.
    "asnkit": (3, 3, ("rpkit", "rtrkit")),
    "bgpfeed": (3, 3, ("asnkit",)),
    # Tier 3, wave 3: solid gaps with no dependency in front of them.
    "rpslkit": (3, 3, ()),
    "bmpkit": (3, 3, ()),
    "pathattr": (3, 3, ()),
    "lgc": (3, 3, ()),
    "turnkit": (3, 3, ()),
    "ohttp": (3, 3, ()),
    "h3tunnel": (3, 3, ()),
    "sfields": (3, 3, ()),
    "syslogkit": (3, 3, ()),
    # Tier 3, wave 2: certificate-shaped, so gated on the substrate.
    "signeddata": (3, 2, ("asn1core",)),
    # Tier 4, wave 5: the rest, in tier order, one at a time.
    "ntspy": (4, 5, ()),
    "tacacs": (4, 5, ()),
    "pgpenv": (4, 5, ("asn1core",)),
    "enrollkit": (4, 5, ("asn1core", "pkix")),
    "shaken": (4, 5, ("asn1core",)),
    "srtpkit": (4, 5, ("asn1core",)),
    "cwmp": (4, 5, ()),
    "devicespy": (4, 5, ()),
}

TIER_NOTE = {
    1: "Tier 1 is work on now: its absence hurts, and finishing it makes several "
       "other projects cheaper.",
    2: "Tier 2 is next: high value, and each entry needs something from Tier 1 "
       "before it can produce behaviour.",
    3: "Tier 3 is planned: a solid gap with no urgency, and better work once "
       "Tier 1 exists.",
    4: "Tier 4 is hold: a real protocol with a weaker case for now, whether "
       "through adequate incumbents, a narrow audience or a long dependency chain.",
}

WAVE_NOTE = {
    1: "the chokepoint and the ambient-trust hole",
    2: "the first real answer",
    3: "the routing-operations story",
    4: "naming and address allocation",
    5: "the rest in tier order, one at a time",
}


# One sentence per edge, on why the arrow is a hard dependency rather than a
# preference. Keyed by (project, dependency).
DEPENDS_WHY = {
    ("rpkit", "asn1core"): "every RPKI signed object rpkit fetches is a CMS structure "
                         "that has to be decoded from the bytes it arrived as before "
                         "its signature means anything, and that codec is asn1core's job",
    ("ctspy", "asn1core"): "a signed certificate timestamp and a Merkle leaf are verified "
                         "over encoded bytes, so an inclusion proof is only as good as "
                         "a codec that keeps the original bytes instead of re-encoding "
                         "them",
    ("pkix", "asn1core"): "RFC 5280 section 6 validates paths over certificates and CRLs, "
                        "and RFC 5280 section 4.1.3.2 checks the CA signature over the "
                        "DER encoding of the TBSCertificate, so validation cannot be "
                        "written above a codec that re-encodes what it parsed",
    ("revokekit", "asn1core"): "an OCSP response is a signed DER object and a CRL is DER "
                             "all the way down, so a revocation answer that cannot be "
                             "re-derived from the bytes it arrived in is not an answer",
    ("revokekit", "pkix"): "deciding whether a responder may sign for a CA is path "
                           "validation against the same trust anchors pkix already "
                           "resolves, and a second validator here would only disagree "
                           "with the first",
    ("rtrkit", "rpkit"): "RTR announces what has been validated, so the serial "
                         "discipline of a cache server is worth nothing unless the "
                         "assertions underneath it came from rpkit's repository fetch "
                         "and signed-object checks",
    ("routevalid", "rpkit"): "a validity verdict is an RPKI assertion plus its anchor, "
                             "and rpkit is the only thing in this portfolio that fetches "
                             "and validates the repository content",
    ("routevalid", "rtrkit"): "what a router was actually told to believe is the RTR "
                              "stream, and without it there is no live state to join a "
                              "RIB dump or an observed AS path against",
    ("dnssd-srp", "namespy"): "SRP is unicast DNS with authenticated updates and pushed "
                              "record changes, so the message codec, the iterative "
                              "resolver and the DNSSEC, DoT and DoH legs are namespy's "
                              "and are shared rather than rebuilt",
    ("asnkit", "rpkit"): "the question asnkit answers is which AS, on which date, and "
                         "what did RPKI say about it, and the last clause is an rpkit "
                         "assertion rather than anything derivable from a RIB dump",
    ("asnkit", "rtrkit"): "validation state is joined at query time from the RTR feed "
                          "rtrkit holds, because a prefix's history with no state "
                          "announced for it is a lookup with no answer attached",
    ("bgpfeed", "asnkit"): "a feed is a stream of UPDATE records until its prefixes "
                           "resolve to an AS with a date and a validation state, which "
                           "is the lookup asnkit owns",
    ("signeddata", "asn1core"): "CMS is a DER container end to end - SignedData, "
                              "EnvelopedData and AuthenticatedData, their attribute "
                              "sets, and the issuer and serial that identifies a signer "
                              "- so the encoding layer underneath is not this project's",
    ("enrollkit", "asn1core"): "CMP messages, CRMF requests and PKCS#10 are all DER, and a "
                             "request whose encoding changes on the way to the CA is an "
                             "enrollment for a different key",
    ("enrollkit", "pkix"): "an issued certificate is only useful once it validates to a "
                           "trust anchor, and that verdict belongs to pkix rather than "
                           "being restated at the end of an enrollment flow",
    ("pgpenv", "asn1core"): "OpenPGP bindings reach X.509 identities through encoded key "
                          "material, and pgpenv is scoped to packets and keys, so "
                          "reading the DER under a key belongs to asn1core",
    ("shaken", "asn1core"): "a PASSporT is only as trustworthy as the certificate the "
                          "originating provider publishes at its x5u, and parsing that "
                          "certificate is asn1core's job, not shaken's",
    ("srtpkit", "asn1core"): "RFC 5764 key establishment presents certificates, and SRTP "
                           "keys are only as strong as the identity that negotiated "
                           "them, so certificate parsing stays in asn1core",
}

# How to state each dependency's current existence. An arrow to something that
# is not there is said as missing, not as a to-do: PORTFOLIO.md section 10 is
# explicit that until asn1core exists no certificate-shaped project can ship
# behaviour, and a shell that ships none is a gate of its own.
DEP_STATE = {
    "asn1core": (
        "does not exist yet",
        "There is no asn1core project and no asn1core code: the workspace holds only its "
        "extraction plan at ../../asn1core/PLAN.md.",
    ),
    "pkix": (
        "exists only as a generated shell, with no protocol behaviour yet",
        "Its public functions raise NotImplementedError until its own roadmap rows are "
        "done, so a row here that consumes it cannot be closed on the strength of a "
        "directory existing.",
    ),
    "rpkit": (
        "exists only as a generated shell, with no protocol behaviour yet",
        "Its public functions raise NotImplementedError until its own roadmap rows are "
        "done, so a row here that consumes it cannot be closed on the strength of a "
        "directory existing.",
    ),
    "rtrkit": (
        "exists only as a generated shell, with no protocol behaviour yet",
        "Its public functions raise NotImplementedError until its own roadmap rows are "
        "done, so a row here that consumes it cannot be closed on the strength of a "
        "directory existing.",
    ),
    "asnkit": (
        "exists only as a generated shell, with no protocol behaviour yet",
        "Its public functions raise NotImplementedError until its own roadmap rows are "
        "done, so a row here that consumes it cannot be closed on the strength of a "
        "directory existing.",
    ),
    "namespy": (
        "exists",
        "namespy is implemented software outside the generator - a wire codec, an "
        "iterative resolver, DNSSEC, DoT and DoH legs - and it is the one place in this "
        "portfolio where the pattern has been proven end to end.",
    ),
}

# Edges the portfolio plan records as candidate rather than load-bearing.
CANDIDATE_EDGES = {("dnssd-srp", "namespy")}
CANDIDATE_NOTE = (
    "This edge is recorded as a candidate: the message layer and the resolver are shared "
    "with namespy, and the stateful half - SRP updates, registrar checks and pushed "
    "record changes - is what is built here."
)

INTRO = (
    "This file is generated by sdk-forge/forge.py from the portfolio plan, and a hand "
    "edit here is overwritten at the next run. Two documents govern this project and "
    "they govern different things: the obligation table in "
    "[../ROADMAP.md](../ROADMAP.md) governs protocol work - which rows exist, and what "
    "evidence closes one - and this file governs sequencing, which is which wave this "
    "project sits in, what has to exist before it can ship behaviour, and what must not "
    "be started while it is unfinished. "
    "[PORTFOLIO.md](../../PORTFOLIO.md) at the workspace root is the authority on both, "
    "so a change to a tier, a wave or an arrow is made there and regenerated here, never "
    "the other way round."
)

NO_DEPS_NOTE = (
    "None. The portfolio plan puts no other project between this one and a first "
    "release: every obligation in [../ROADMAP.md](../ROADMAP.md) is this repository's "
    "own, and nothing "
    "outside it has to land first. That cuts both ways - a missing dependency is never "
    "the reason this project has not shipped, and its wave position is the only thing "
    "holding it back."
)

BLOCKED_NOTE = (
    "**Blocked, not in progress.** asn1core does not exist yet, so @NAME@ cannot ship "
    "behaviour until asn1core does. A roadmap row that parses, encodes or verifies a DER "
    "structure is not deferred work here: it is gated on a project that has no code and "
    "no test suite. Any plan, milestone or release note that cites asn1core says blocked "
    "rather than in progress, and no release of @NAME@ is promised before asn1core has one "
    "of its own."
)

SHELL_NOTE = (
    "A dependency that exists only as a shell is the same gate in weaker form: @DEPS@ "
    "@AGREE@ a directory, CI and an obligation table, and no behaviour, so work here can "
    "be designed against such a dependency and cannot be finished against it."
)

RULES = [
    "At most two projects in the portfolio carry real effort at once. A third is not "
    "started, and no obligation is taken here, while those two are open.",
    "No new shell is created while any Tier 1 project still has an unimplemented "
    "obligation. Twenty-eight generated READMEs are already the maintenance liability, "
    "and the failure mode of this portfolio is prose outrunning code rather than "
    "under-building.",
    "A project freezes to Tier 4 when its first release finds no external user, and a "
    "shell is retired publicly when a competitor ships what it promised rather than left "
    "to rot - the retirement is announced, not a README quietly left to go stale.",
]

POINTER = (
    "Protocol facts come from docs/rfc-map.md and the RFC Editor record, never from "
    "memory. This file positions the work; it is not a source for anything a row cites."
)


# Dependencies the state table above describes as shells, derived rather than
# repeated so the two cannot disagree about what a shell is.
SHELL_DEPS = frozenset(dep for dep, state in DEP_STATE.items() if "shell" in state[0])


def para(text, width=DOC_WIDTH):
    """Wrap one prose paragraph to the generator's document width."""
    return "\n".join(wrap(collapse(text), width))


def bullet(text, width=DOC_WIDTH):
    """Wrap one prose paragraph as a hyphen bullet with a hanging indent."""
    return "\n".join(wrap(collapse(text), width, "  ", "- "))


def dep_line(name, dep):
    """One dependency bullet: the edge, why it is hard, and whether it exists."""
    why = DEPENDS_WHY.get((name, dep), "the portfolio plan records this as a hard dependency")
    label, detail = DEP_STATE[dep]
    text = "**" + dep + "** - " + why + ". **Status: " + label + ".** " + detail
    if (name, dep) in CANDIDATE_EDGES:
        text += " " + CANDIDATE_NOTE
    return bullet(text)


def position_block(name):
    tier, wave, _deps = POSITION[name]
    return para("**Tier " + str(tier) + ", wave " + str(wave) + "** - " + WAVE_NOTE[wave]
                + ". " + TIER_NOTE[tier])


def depends_block(name):
    deps = POSITION[name][2]
    if not deps:
        return para(NO_DEPS_NOTE)
    blocks = ["\n".join(dep_line(name, dep) for dep in deps)]
    shells = sorted(dep for dep in deps if dep in SHELL_DEPS)
    if shells:
        blocks.append(
            para(
                subs(
                    SHELL_NOTE,
                    {
                        "DEPS": ", ".join(shells),
                        "AGREE": "has" if len(shells) == 1 else "have",
                    },
                )
            )
        )
    if "asn1core" in deps:
        blocks.append(para(subs(BLOCKED_NOTE, {"NAME": name})))
    return "\n\n".join(blocks)


def rules_block():
    return "\n".join(bullet(rule) for rule in RULES)


def render_plan(p):
    """Render docs/plan.md: where this project sits, what gates it, what constrains it."""
    name = p["name"]
    return "\n".join(
        [
            "# Portfolio position",
            "",
            para(INTRO),
            "",
            "## Position",
            "",
            position_block(name),
            "",
            "## Depends on",
            "",
            depends_block(name),
            "",
            "## Sequencing rules",
            "",
            rules_block(),
            "",
            para(POINTER),
        ]
    ).strip() + "\n"


def write_plan(path, text):
    """Write one generated document as ASCII text with LF endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = ascii_prose(text).replace("\r\n", "\n")
    if not body.endswith("\n"):
        body += "\n"
    path.write_text(body, encoding="utf-8", newline="\n")


# Captured under a part-specific name. Every part lands in one module namespace,
# so reusing part 19's `_ORIG_BUILD` here would rebind the name part 19's wrapper
# reads and make the two wrappers call each other forever.
_BUILD_BEFORE_POSITIONS = build


def build(p):
    count = _BUILD_BEFORE_POSITIONS(p)
    name = p["name"]
    # Loud rather than skipped: a project with no row here is a project whose wave
    # nobody decided, and quietly omitting its plan.md is how a portfolio document
    # starts lying about the work.
    if name not in POSITION:
        raise KeyError(name + ": no POSITION row, so its tier and wave are undecided")
    write_plan(ROOT / name / "docs" / "plan.md", render_plan(p))
    return count + 1


if __name__ == "__main__":
    raise SystemExit(run())

