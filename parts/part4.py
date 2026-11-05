# ------------------------------------------------- clusters: address assignment and provisioning

PROJECTS_C: list[dict[str, Any]] = [
    {
        "name": "leasespy",
        "pkg": "leasespy",
        "title": "leasespy -- DHCP clients, servers and relays on asyncio",
        "desc": "DHCPv4 and DHCPv6 on asyncio: sans-IO state machines, the option registry, "
        "relay agents with option 82, leasequery and the failover peer protocol",
        "kw": [
            "dhcp",
            "dhcpv6",
            "dhcpv4",
            "relay",
            "leasequery",
            "failover",
            "rfc9915",
            "rfc2131",
        ],
        "why": (
            "DHCPv6 was reissued in January 2026 as RFC 9915, an Internet Standard (STD 102) "
            "that obsoletes RFC 8415 and deliberately removes IA_TA and the server unicast "
            "option. No implementation in any language has finished that transition, and no "
            "Python library is written against it. The Python field is contested but shallow: "
            "pydhcp 0.9.1 (2026-10-21) is young and IPv4-first, dhcpkit 1.0.7 has not moved "
            "since 2017, pydhcplib stopped in 2014, and dhcpy 0.0.7 drives the Kea control API "
            "rather than the protocol. leasespy takes the ground nobody holds: the relay and "
            "failover half of DHCP, where an operator's problem actually lives.",
        ),
        "docs": [
            {
                "n": "9915",
                "status": "Internet Standard (STD 102)",
                "date": "2026-01",
                "why": "current DHCPv6: message formats, DUID, IA, relay, options",
            },
            {
                "n": "2131",
                "status": "Draft Standard",
                "date": "1997-03",
                "why": "DHCPv4 client and server state machines",
            },
            {
                "n": "2132",
                "status": "Draft Standard",
                "date": "1997-03",
                "why": "the DHCP option and BOOTP vendor extension registry",
            },
            {
                "n": "3046",
                "status": "Proposed Standard",
                "date": "2001-01",
                "why": "relay agent information, option 82",
            },
            {
                "n": "6422",
                "status": "Proposed Standard",
                "date": "2011-12",
                "why": "relay-supplied options for DHCPv6",
            },
            {
                "n": "5007",
                "status": "Proposed Standard",
                "date": "2007-09",
                "why": "DHCPv6 leasequery",
            },
            {
                "n": "7653",
                "status": "Proposed Standard",
                "date": "2015-10",
                "why": "DHCPv6 active leasequery",
            },
            {
                "n": "8156",
                "status": "Proposed Standard",
                "date": "2017-06",
                "why": "DHCPv6 failover between cooperating servers",
            },
        ],
        "errata": [
            "RFC 2131 carries 7 verified errata and is updated by RFC 3396, RFC 4361, RFC 5494 and RFC 6842. The errata change packet handling, so the codec is written against them, not the 1997 text alone.",
            "RFC 2132 carries 2 verified errata and 5 updates.",
            "RFC 9915 carries 1 verified erratum and removes IA_TA plus server unicast: implementing RFC 8415 today builds the obsolete behaviour in.",
        ],
        "prior": [
            {
                "name": "pydhcp",
                "version": "0.9.1",
                "date": "2026-10-21",
                "note": "active and IPv4-centred; no relay, leasequery or failover",
            },
            {
                "name": "dhcpy",
                "version": "0.0.7",
                "date": "2024-10-09",
                "note": "an ISC Kea control API client, not the DHCP protocol",
            },
            {
                "name": "dhcpkit",
                "version": "1.0.7",
                "date": "2017-06-25",
                "note": "IPv6 only, unmaintained for nine years",
            },
            {
                "name": "scapy",
                "version": "2.8.0",
                "date": "2026-10-02",
                "note": "packet forgery; no allocation state machine or lease store",
            },
        ],
        "gaps": [
            "DHCPv6 written to RFC 9915 from the first commit, with IA_TA and server unicast absent by construction",
            "a sans-IO state machine per RFC 2131 and RFC 9915 sec. 14 through sec. 18, testable on a virtual clock",
            "relay agent with option 82 and RFC 6422 relay-supplied options, which is where real deployments break",
            "leasequery and active leasequery so a monitoring system can read a live server",
            "failover peer state machine, which no Python library attempts at all",
        ],
        "nongoals": [
            "a packet crafting tool: use scapy for that and this library will not pretend otherwise",
            "a complete production server: leases persist behind an interface, storage is the operator's choice",
            "PXE, PXP or DOCSIS suboptions in the first release, only the registry hooks for them",
        ],
        "mods": [
            (
                "wire",
                "DHCPv4 and DHCPv6 message formats (RFC 2131, RFC 9915 sec. 8, sec. 9)",
            ),
            (
                "options",
                "option registry, encoders and decoders (RFC 2132, RFC 9915 sec. 21)",
            ),
            ("duid", "DUID types and stability rules (RFC 9915 sec. 11)"),
            (
                "identity",
                "identity associations: address and prefix binding (RFC 9915 sec. 12)",
            ),
            (
                "fsm",
                "client and server state machines with retransmission (RFC 9915 sec. 14, sec. 15, sec. 18)",
            ),
            ("validate", "message validation and error handling (RFC 9915 sec. 16)"),
            (
                "relay",
                "relay forwarding and option 82 (RFC 9915 sec. 19, RFC 3046, RFC 6422)",
            ),
            ("leasequery", "query and active query (RFC 5007, RFC 7653)"),
            ("failover", "peer protocol and states (RFC 8156)"),
            ("clock", "sans-IO timers so every timeout is testable without sleeping"),
        ],
        "api": [
            ("wire", "def", "decode_v6", "raw: bytes", "Message", "RFC 9915 sec. 8"),
            ("wire", "def", "encode_v6", "msg: Message", "bytes", "RFC 9915 sec. 8"),
            ("wire", "def", "decode_v4", "raw: bytes", "Bootp", "RFC 2131"),
            (
                "options",
                "def",
                "encode_option",
                "code: int, value: object",
                "bytes",
                "RFC 2132, RFC 9915 sec. 21",
            ),
            (
                "options",
                "def",
                "decode_options",
                "raw: bytes",
                "Options",
                "RFC 9915 sec. 21",
            ),
            ("duid", "def", "parse_duid", "raw: bytes", "Duid", "RFC 9915 sec. 11"),
            (
                "fsm",
                "def",
                "client_step",
                "state: ClientState, event: Event, now: float",
                "Step",
                "RFC 9915 sec. 18",
            ),
            (
                "validate",
                "def",
                "check_message",
                "msg: Message, context: ServerContext",
                "list",
                "RFC 9915 sec. 16",
            ),
            (
                "relay",
                "def",
                "wrap_relay_forward",
                "peer: Endpoint, link: Endpoint, msg: Message",
                "bytes",
                "RFC 9915 sec. 9",
            ),
            (
                "leasequery",
                "def",
                "build_query",
                "server: Endpoint, iaid: Optional[int]",
                "Message",
                "RFC 5007",
            ),
            (
                "failover",
                "def",
                "peer_transition",
                "state: FailoverState, event: PeerEvent",
                "FailoverState",
                "RFC 8156",
            ),
        ],
        "steps": [
            "M1 wire codec and option registry for both families, with RFC 2131 errata applied",
            "M2 sans-IO client state machines on a virtual clock, including RFC 9915 retransmission",
            "M3 server allocation for addresses and prefixes, DUID stability included",
            "M4 relay with option 82 and RFC 6422, verified against a real relay",
            "M5 leasequery and active leasequery",
            "M6 failover peer protocol, then publication: 0.1.0",
        ],
        "extras": {},
        "cli": "leasespy discover --6 --interface eth0 -- print the OFFER and every option decoded",
    },
    {
        "name": "cwmp",
        "pkg": "cwmp",
        "title": "cwmp -- TR-069 CWMP for ACS and CPE",
        "desc": "CWMP remote management: SOAP 1.2 RPC codec, session machinery, Digest "
        "authentication, parameter path trees and file transfer, ACS and CPE sides",
        "kw": [
            "tr-069",
            "cwmp",
            "acs",
            "cpe",
            "provisioning",
            "tr-181",
            "soap",
            "hntl",
        ],
        "why": (
            "CWMP is how almost every customer premises device on earth is configured, and "
            "Python cannot speak it. GenieACS, the serious open source ACS, is Node.js; on "
            "PyPI the name tr069 is a registered but empty squat, acs belongs to Azure Container "
            "Service, pyacs is an oceanographic sensor library, and inform is a logging "
            "utility. Meanwhile the provisioning chain is already half built in Python: "
            "DHCP hands the CPE its ACS URL, cwmp takes it from there. This is a deliberately "
            "non-IETF project: the specification lives at the Broadband Forum, so every claim "
            "below cites a document number that must be re-verified against the Forum's current "
            "revision before it reaches code.",
        ),
        "docs": [
            {
                "label": "TR-069 (CWMP)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the protocol: Inform, Get and SetParameterValues, TransferFile",
            },
            {
                "label": "TR-181 (Device:2)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the data model object and parameter tree",
            },
            {
                "label": "TR-098 (InternetGatewayDevice)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the model most deployed CPE still exposes",
            },
            {
                "label": "TR-069 Annex 2 (SOAP)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the envelope and encoding rules the RPC layer obeys",
            },
            {
                "label": "TR-369 (USP)",
                "status": "Broadband Forum",
                "date": "-",
                "why": "the WebSocket successor; a roadmap target, not a first release",
            },
            {
                "n": "9110",
                "status": "Internet Standard (STD 97)",
                "date": "2022-06",
                "why": "HTTP semantics under the transport, including authentication",
            },
        ],
        "errata": [
            "Outside the RFC series, so there is no errata mechanism to consult: pin the exact TR revision in every docstring and test, and record it in docs/research.md.",
            "The ACS URL a CPE learns usually arrives from DHCP option 43 or a DHCPv6 vendor option, so leasespy is the natural partner and the two must agree on the encoding.",
        ],
        "prior": [
            {
                "name": "tr069",
                "version": "-",
                "date": "-",
                "note": "registered but empty on PyPI: a squat that blocks the obvious name",
            },
            {
                "name": "GenieACS",
                "version": "-",
                "date": "-",
                "note": "the reference open source ACS, written in Node.js",
            },
            {
                "name": "acs, pyacs, inform",
                "version": "-",
                "date": "-",
                "note": "Azure tooling, an ocean sensor library and a logging utility",
            },
        ],
        "gaps": [
            "SOAP 1.2 RPC codec that refuses hostile XML: no DTDs, no external entities, bounded depth",
            "CWMP session engine: Inform, RPC method dispatch, fault codes, keep-alive and nonce-based retry",
            "HTTP Digest authentication on both sides, since most CPE ship nothing else",
            "parameter path tree with wildcards, instance addition and deletion, typed constraints",
            "both endpoints: an ACS side that can manage a real device and a CPE side to test against",
        ],
        "nongoals": [
            "a web UI, ticket system or firmware repository: an ACS product composes those, this is the protocol",
            "business provisioning logic beyond the data model",
            "USP transport in the first release, only the seam that will allow it",
        ],
        "mods": [
            ("envelope", "SOAP 1.2 envelope codec with XML hardening (TR-069 Annex 2)"),
            ("methods", "one class per RPC method, request and response (TR-069)"),
            (
                "session",
                "ACS session state, authentication and fault handling (TR-069)",
            ),
            (
                "endpoint",
                "CPE side: inform, connection request, method dispatch (TR-069)",
            ),
            (
                "datamodel",
                "object tree, parameter paths, types and constraints (TR-181, TR-098)",
            ),
            ("auth", "HTTP Digest challenge and response (RFC 9110, TR-069)"),
            (
                "transfer",
                "TransferFile, Download and Upload with resumable semantics (TR-069)",
            ),
            ("clock", "periodic inform, session timeout and connection request retry"),
        ],
        "api": [
            (
                "envelope",
                "def",
                "encode_envelope",
                "rpc: Rpc, session: SessionContext",
                "bytes",
                "TR-069 Annex 2",
            ),
            (
                "envelope",
                "def",
                "decode_envelope",
                "raw: bytes",
                "Rpc",
                "TR-069 Annex 2",
            ),
            (
                "methods",
                "def",
                "build_inform",
                "device: DeviceIdentity, events: list",
                "Rpc",
                "TR-069",
            ),
            ("methods", "def", "set_parameter_values", "params: dict", "Rpc", "TR-069"),
            (
                "session",
                "async def",
                "handle_session",
                "request: HttpRequest, acs: AcsApp",
                "HttpResponse",
                "TR-069, RFC 9110",
            ),
            (
                "endpoint",
                "async def",
                "run_inform",
                "acs_url: str, identity: DeviceIdentity",
                "Session",
                "TR-069",
            ),
            (
                "datamodel",
                "def",
                "resolve_path",
                "tree: DataModel, path: str",
                "list",
                "TR-181",
            ),
            (
                "datamodel",
                "def",
                "coerce_value",
                "parameter: Parameter, value: object",
                "object",
                "TR-181",
            ),
            (
                "auth",
                "def",
                "digest_challenge",
                "nonce: bytes, realm: str",
                "str",
                "RFC 9110",
            ),
            (
                "transfer",
                "def",
                "build_download",
                "command_key: str, url: str, file_type: str",
                "Rpc",
                "TR-069",
            ),
        ],
        "steps": [
            "M1 hardened SOAP envelope codec, with an entity-expansion and depth bomb test",
            "M2 RPC method classes and fault codes against a captured CPE session",
            "M3 ACS session engine with Digest auth and keep-alive",
            "M4 CPE endpoint able to complete a real Inform against the ACS in the same repo",
            "M5 data model tree with wildcards, instance add and delete",
            "M6 file transfer and connection request, then publication: 0.1.0",
        ],
        "extras": {},
        "cli": "cwmp inform --acs http://acs.local:7547/ --id serial-1234",
    },
    {
        "name": "devicespy",
        "pkg": "devicespy",
        "title": "devicespy -- be the UPnP device, not the control point",
        "desc": "UPnP device side: SSDP advertisement, device and service descriptions, SOAP "
        "control handling and GENA eventing, with hardened XML",
        "kw": [
            "upnp",
            "ssdp",
            "gena",
            "scpd",
            "device",
            "media-server",
            "printer",
            "uda",
        ],
        "why": (
            "Every Python UPnP library is a control point. async-upnp-client 0.49.0 "
            "(2026-10-11), upnpclient 2.0.3 (2026-04-07) and python-upnp 1.0.0 (2024-07-12) "
            "all talk to devices, and ssdp 1.3.1 (2025-09-06) plus ssdpy 0.4.1 do discovery. "
            "Nothing lets a Python program be a device: advertise itself, publish its "
            "description and SCPD, answer control requests and push events. That is the half a "
            "printer, scanner or media server needs, and it is also the security-sensitive "
            "half, because a device parses XML that a stranger on the LAN wrote.",
        ),
        "docs": [
            {
                "label": "UDA 2.0 (UPnP Device Architecture)",
                "status": "UPnP Forum",
                "date": "-",
                "why": "device and service description, control, eventing, boot sequence",
            },
            {
                "label": "GENA 1.0",
                "status": "OASIS",
                "date": "-",
                "why": "subscribe, renew, notify, unsubscribe",
            },
            {
                "label": "SDDL 1.0",
                "status": "UPnP Forum",
                "date": "-",
                "why": "device and service description discovery layout",
            },
            {
                "n": "9110",
                "status": "Internet Standard (STD 97)",
                "date": "2022-06",
                "why": "the HTTP semantics every UPnP exchange rides on",
            },
        ],
        "errata": [
            "UDA and GENA are outside the RFC series: pin the exact specification revision in every docstring.",
            "SSDP itself has a maintained Python owner already (ssdp 1.3.1), so the design decision is whether to depend on it or speak multicast HTTP directly. Record the reasoning in docs/strategy.md before writing code.",
        ],
        "prior": [
            {
                "name": "async-upnp-client",
                "version": "0.49.0",
                "date": "2026-10-11",
                "note": "the reference control point; it is not a device stack",
            },
            {
                "name": "upnpclient",
                "version": "2.0.3",
                "date": "2026-04-07",
                "note": "client only, revived",
            },
            {
                "name": "ssdp, ssdpy",
                "version": "1.3.1, 0.4.1",
                "date": "2025-09-06",
                "note": "discovery transport, already solved",
            },
            {
                "name": "upnp-device, upnp-server, deviceupnp",
                "version": "-",
                "date": "-",
                "note": "all absent from PyPI (2026-11-05)",
            },
        ],
        "gaps": [
            "advertise and live lifecycle: alive, byebye, search response, and bootId changes on restart",
            "description and SCPD authoring with validation, so a malformed service does not ship",
            "SOAP control dispatch with argument typing and action-level authorisation",
            "GENA subscription manager: renewals, evented properties, seqnum, and resubscribe on loss",
            "defensive XML: no DTDs, no external entities, bounded size, since the peer is a stranger",
        ],
        "nongoals": [
            "a control point: use async-upnp-client, which is better at it than this will be",
            "DLNA or IGD semantics in the first release, only the generic device layer beneath them",
            "port mapping through an Internet Gateway Device, which is a profile, not the protocol",
        ],
        "mods": [
            (
                "advertise",
                "SSDP alive, byebye and search responses (UDA 2.0, SDDL 1.0)",
            ),
            ("description", "device and service description documents (UDA 2.0)"),
            (
                "scpd",
                "service control protocol definition: actions, state variables, allowed values",
            ),
            ("control", "SOAP action dispatch with argument coercion (UDA 2.0)"),
            (
                "events",
                "GENA subscriptions and evented property change notifications (GENA 1.0)",
            ),
            ("xmlsafe", "the hardened parser every other module must use"),
            ("httpd", "the small asyncio HTTP surface the device serves (RFC 9110)"),
        ],
        "api": [
            (
                "advertise",
                "async def",
                "announce",
                "device: Device, interfaces: list",
                "None",
                "UDA 2.0",
            ),
            (
                "advertise",
                "def",
                "search_response",
                "device: Device, stn: str",
                "Response",
                "UDA 2.0",
            ),
            (
                "description",
                "def",
                "render_device_xml",
                "device: Device",
                "bytes",
                "UDA 2.0",
            ),
            (
                "scpd",
                "def",
                "parse_scpd",
                "raw: bytes",
                "ServiceDescription",
                "UDA 2.0",
            ),
            (
                "control",
                "def",
                "dispatch",
                "service: Service, action: str, args: dict",
                "ActionResult",
                "UDA 2.0",
            ),
            (
                "events",
                "async def",
                "notify",
                "subscription: Subscription, props: dict",
                "None",
                "GENA 1.0",
            ),
            (
                "events",
                "def",
                "renew",
                "subscription: Subscription, requested: int",
                "Subscription",
                "GENA 1.0",
            ),
            ("xmlsafe", "def", "parse", "raw: bytes, limit: int", "Element", "design"),
        ],
        "steps": [
            "M1 hardened XML parser plus description and SCPD round trip",
            "M2 SSDP advertisement and search responses on Windows and Linux multicast",
            "M3 control dispatch with typed arguments and error codes",
            "M4 GENA subscriptions, renewals and evented properties",
            "M5 a reference example device, then interop testing against a real control point",
            "M6 publication: 0.1.0",
        ],
        "extras": {},
        "cli": "devicespy serve --device ./device.xml --listen 0.0.0.0:49152",
    },
]
