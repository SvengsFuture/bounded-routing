"""
Registry and named fixtures, per Harness Profile v1.6 §5 and §5a.
"""
import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

SCHEMA_VERSION = "v5.0"
OBSERVER_TYPE_ENUM = {"tetrahedral_coordinator", "auxiliary_observer"}
SCOPE_TYPE_ENUM = {"route", "system"}
FRESHNESS_WINDOW_NS = 2_000_000_000


def derive_keypair(seed_string: str):
    seed = hashlib.sha256(seed_string.encode("ascii")).digest()
    priv = Ed25519PrivateKey.from_private_bytes(seed)
    pub = priv.public_key()
    return priv, pub


def pubkey_hex(pub: Ed25519PublicKey) -> str:
    return pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


class Registry:
    """
    Gate-side trusted registry: key_id -> (public_key, observer_id, observer_type),
    and source_id -> bound observer_id.
    """
    def __init__(self):
        self.keys = {}       # key_id -> (Ed25519PublicKey, observer_id, observer_type)
        self.sources = {}    # source_id -> observer_id (the witness it is bound to)

    def register_witness(self, key_id, public_key, observer_id, observer_type):
        self.keys[key_id] = (public_key, observer_id, observer_type)

    def register_source(self, source_id, bound_observer_id):
        self.sources[source_id] = bound_observer_id

    def resolve_key(self, key_id):
        """Returns (public_key, observer_id, observer_type) or None."""
        return self.keys.get(key_id)

    def source_bound_to(self, source_id):
        """Returns observer_id the source is bound to, or None if unregistered."""
        return self.sources.get(source_id)


def build_standard_registry():
    """
    Standard baseline registry: exactly one witness, one key, one source.
    key-2 exists as a real, derivable keypair but is NEVER registered here --
    used by unauthorized-signer (A4) and as the basis for key-2's real
    identity in the E9 fixture below (where it IS registered, deliberately).
    """
    reg = Registry()
    priv1, pub1 = derive_keypair("v5-harness-test-key-1")
    reg.register_witness("key-1", pub1, "witness-1", "tetrahedral_coordinator")
    reg.register_source("source-1", "witness-1")
    return reg, {"key-1": priv1}


def build_e9_registry():
    """
    E9_SOURCE_BINDING_FIXTURE (Harness Profile v1.6 §5a):
    extends the standard registry with a second, fully registered
    witness/key (witness-2/key-2), while source-1 remains bound only
    to witness-1. This is the one deliberate exception to the
    single-entry registry, existing solely to make E9 constructible.
    """
    reg, privs = build_standard_registry()
    priv2, pub2 = derive_keypair("v5-harness-test-key-2")
    reg.register_witness("key-2", pub2, "witness-2", "tetrahedral_coordinator")
    # source-1 stays bound to witness-1 only -- do NOT rebind it.
    privs["key-2"] = priv2
    return reg, privs


def baseline_fields(**overrides):
    """
    UNCONSUMED_BASELINE healthy record fields (Harness Profile v1.6 §5),
    source_sequence=10 / observer_sequence=10, gate watermarks start at 9/9
    (caller sets watermarks separately -- see Gate.seed_watermark).
    """
    fields = {
        "schema_version": SCHEMA_VERSION,
        "source_id": "source-1",
        "observer_id": "witness-1",
        "observer_type": "tetrahedral_coordinator",
        "key_id": "key-1",
        "source_sequence": 10,
        "source_observation_time_ns": 10_000_000_000,
        "observer_sequence": 10,
        "witness_sign_time_ns": 10_100_000_000,
        "structural_epoch": 1,
        "scope_type": "route",
        "scope_id": "route-A",
        "fact_evidence": 1_000_000,
        "logic_evidence": 1_000_000,
        "coherence_evidence": 1_000_000,
        "shape_integrity": True,
    }
    fields.update(overrides)
    return fields


GATE_NOW_NS_BASELINE = 10_200_000_000


class TrustedClock:
    """
    The single shared trusted clock. Source, witness, and gate are all
    constructed with a reference to the SAME instance -- per Architecture
    Freeze v0.5's Source Freshness Rule ("both processes use the same
    monotonic clock domain"), and per the correction that neither the
    witness's sign time nor the gate's notion of "now" should be a value
    an arbitrary caller can supply per-call. Only code that legitimately
    owns fixture/trusted-environment construction (test setup, in this
    harness) may advance or set `.t` directly -- that is fixture
    construction, not a bypass of any public verification method.
    """
    def __init__(self, start_ns=10_000_000_000):
        self.t = start_ns

    def now_ns(self):
        return self.t

    def advance(self, delta_ns):
        self.t += delta_ns


class ControllableClock(TrustedClock):
    """Backward-compatible alias; identical to TrustedClock."""
    pass
