"""
Trusted Structural Source and Structural Witness -- the honest-operation
pipeline. Category C/CW tests attack this pipeline's boundaries; Category I
tests its own invariants directly.

Clock ownership: source, witness, and gate are all constructed with a
reference to the SAME TrustedClock instance (see fixtures.py). Neither
`StructuralWitness.sign_current_snapshot()` nor `AuthorityGate.verify()`
accepts a timestamp argument from its caller -- both read the shared
clock internally. This closes a real bug from the previous revision: a
caller of `verify()` could previously supply an arbitrary `gate_now_ns`,
which meant the gate was trusting whoever invoked it to report the correct
time rather than enforcing freshness against a time source it owned.

Capability boundary, precisely scoped: `make_read_capability()` returns an
object built from a plain closure rather than a bound method, which closes
the specific one-line exploit `capability._read_fn.__self__.publish(...)`
(closures have no `__self__` attribute). This does NOT make the capability
a genuine trust boundary in any absolute sense -- Python's `__closure__`
introspection can still recover captured references by a sufficiently
determined caller with reflection access, and no purely same-process
Python construction can prevent that. Architecture Freeze v0.5 explicitly
excludes host/process compromise from V5's scope and defers genuine
physical/process trust-boundary enforcement to "a later hardware
experiment" -- so this harness does not attempt to build real OS-process
separation, which would be scope creep beyond what V5 itself claims. What
this capability object DOES correctly enforce, matching the actual frozen
attack classes (C1-C3, C11): no writer method is exposed to normal
attribute/method access, and there is no method signature accepting a
historical sequence number.
"""
import json
import threading
from canonical import canonical_bytes

SHAPE_THRESHOLD = 500_000  # inclusive, per Profile §3d


def compute_shape_integrity(fact, logic, coherence):
    """Frozen structural-observer rule (Profile §3d). Deterministic, pure."""
    return fact >= SHAPE_THRESHOLD and logic >= SHAPE_THRESHOLD and coherence >= SHAPE_THRESHOLD


class SourceReadCapability:
    """
    The interface handed to the witness: exactly one method, `read_latest()`,
    no parameters. Built from a closure (see `TrustedStructuralSource.
    make_read_capability`), not a bound method, so it has no `__self__`
    attribute -- see module docstring for the precise, honest scope of what
    this closes and what it does not.
    """
    __slots__ = ("_read_fn",)

    def __init__(self, read_fn):
        self._read_fn = read_fn

    def read_latest(self):
        return self._read_fn()


class TrustedStructuralSource:
    """
    Atomic latest-state source. No historical read-back, no queue. The
    writer (`publish`) is a method on this object; the only way anything
    else gets read access is via `make_read_capability()`.
    """
    def __init__(self, source_id, clock):
        """
        clock: a TrustedClock instance (fixtures.py), shared with the
        witness and gate constructed alongside this source.
        """
        self.source_id = source_id
        self._clock = clock
        self._lock = threading.Lock()
        self._latest = None          # dict snapshot, or None
        self._sequence_by_epoch = {}  # epoch -> last-issued source_sequence

    def publish(self, structural_epoch, scope_type, scope_id, fact, logic, coherence):
        """Writer endpoint. Only code holding a direct reference to this
        TrustedStructuralSource instance can call this."""
        with self._lock:
            last_seq = self._sequence_by_epoch.get(structural_epoch, 0)
            new_seq = last_seq + 1
            self._sequence_by_epoch[structural_epoch] = new_seq
            snapshot = {
                "source_id": self.source_id,
                "source_sequence": new_seq,
                "source_observation_time_ns": self._clock.now_ns(),  # stamped HERE, by the source itself
                "structural_epoch": structural_epoch,
                "scope_type": scope_type,
                "scope_id": scope_id,
                "fact_evidence": fact,
                "logic_evidence": logic,
                "coherence_evidence": coherence,
            }
            self._latest = snapshot
            return dict(snapshot)

    def make_read_capability(self):
        """
        Returns a SourceReadCapability built from a closure, not a bound
        method -- `capability._read_fn.__self__` does not exist. The
        closure still captures `self` and `lock` via its cell variables,
        recoverable via `__closure__` introspection by a caller with
        reflection access; see module docstring.
        """
        lock = self._lock
        # Deliberately reference `self` only inside the nested function so
        # the returned callable is a plain function object, not a bound
        # method -- this is what removes the __self__ attribute.
        def read():
            with lock:
                return None if self._latest is None else dict(self._latest)
        return SourceReadCapability(read)


class StructuralWitness:
    def __init__(self, observer_id, observer_type, key_id, private_key, source_reader, clock):
        """
        `source_reader` MUST be a SourceReadCapability, not a
        TrustedStructuralSource. `clock` MUST be the same TrustedClock
        instance the source and gate were constructed with.
        """
        if not isinstance(source_reader, SourceReadCapability):
            raise TypeError(
                "StructuralWitness must be constructed with a SourceReadCapability, "
                "not a TrustedStructuralSource -- use source.make_read_capability(). "
                "Handing the witness the full source object defeats the write-path "
                "isolation this class exists to enforce."
            )
        self.observer_id = observer_id
        self.observer_type = observer_type
        self.key_id = key_id
        self.private_key = private_key
        self._source_reader = source_reader
        self._clock = clock
        self._lock = threading.Lock()
        self._sequence_by_epoch = {}  # epoch -> last-issued observer_sequence
        self._highest_signed_source_seq = {}  # (source_id, epoch) -> highest source_sequence already signed

    def sign_current_snapshot(self):
        """
        Honest production path: read the one current snapshot through the
        read-only capability, compute shape_integrity via the frozen rule,
        assign a fresh strictly-increasing observer_sequence, stamp
        witness_sign_time_ns from the SHARED trusted clock (not a caller-
        supplied argument), sign, return the envelope dict. Returns None
        if no snapshot is available, if the snapshot is missing its source
        timestamp (defensive -- no fallback is ever substituted), or if
        this exact (source_id, source_sequence, epoch) has already been
        signed by this witness -- an honest witness reading its one bound
        source has no way to observe the same snapshot as "new" twice in a
        row without an intervening publish(), so it must not manufacture a
        second record from it. (Genuinely producing two records from one
        snapshot, for D2/D6/D8a/D8b, is a fault-injected-signer
        construction that calls `sign_payload` directly -- never this
        method twice against an unchanged snapshot.)
        """
        with self._lock:
            snap = self._source_reader.read_latest()
            if snap is None:
                return None
            if "source_observation_time_ns" not in snap or snap["source_observation_time_ns"] is None:
                return None

            epoch = snap["structural_epoch"]
            src_key = (snap["source_id"], epoch)
            highest_signed = self._highest_signed_source_seq.get(src_key, 0)
            if snap["source_sequence"] <= highest_signed:
                # This exact snapshot (or an older one) has already been
                # signed. An honest witness produces no record rather than
                # re-signing it.
                return None

            # Build the CANDIDATE observer_sequence and full payload, but do
            # not touch any witness state yet. State is committed only
            # after sign_payload() actually succeeds below -- a signing
            # failure (transient or otherwise) must not consume the only
            # opportunity to produce a record from this snapshot.
            candidate_obs_seq = self._sequence_by_epoch.get(epoch, 0) + 1

            shape = compute_shape_integrity(
                snap["fact_evidence"], snap["logic_evidence"], snap["coherence_evidence"]
            )

            payload = {
                "schema_version": "v5.0",
                "source_id": snap["source_id"],
                "observer_id": self.observer_id,
                "observer_type": self.observer_type,
                "key_id": self.key_id,
                "source_sequence": snap["source_sequence"],
                "source_observation_time_ns": snap["source_observation_time_ns"],  # preserved exactly
                "observer_sequence": candidate_obs_seq,
                "witness_sign_time_ns": self._clock.now_ns(),  # from the shared clock, not an argument
                "structural_epoch": epoch,
                "scope_type": snap["scope_type"],
                "scope_id": snap["scope_id"],
                "fact_evidence": snap["fact_evidence"],
                "logic_evidence": snap["logic_evidence"],
                "coherence_evidence": snap["coherence_evidence"],
                "shape_integrity": shape,
            }

            # This is the only line that can raise from here on in the
            # normal case (a signing failure). If it raises, execution
            # never reaches the two state-commit lines below, so neither
            # _sequence_by_epoch nor _highest_signed_source_seq changes --
            # the snapshot remains signable on a subsequent call.
            envelope = sign_payload(payload, self.private_key)

            # Commit state only now that signing has genuinely succeeded.
            self._sequence_by_epoch[epoch] = candidate_obs_seq
            self._highest_signed_source_seq[src_key] = snap["source_sequence"]

            return envelope


def sign_payload(payload: dict, private_key) -> dict:
    """Build a complete envelope dict {payload, signature} by signing the
    canonical bytes of `payload` with `private_key`. This is the one place
    every construction mode (honest or fault-injected) funnels through, so
    the signature is always cryptographically real. Fault-injected
    timestamp tests (F7-F9) construct `payload` directly with explicit,
    deliberately anomalous timestamp values and call this function
    directly -- they never go through `sign_current_snapshot`, which is
    exactly the "separate explicit test helper for fault-injected
    timestamp tests" this design calls for."""
    canon = canonical_bytes(payload)
    sig = private_key.sign(canon)
    return {"payload": dict(payload), "signature": sig.hex()}


def envelope_to_bytes(envelope: dict) -> bytes:
    return json.dumps(envelope).encode("utf-8")
