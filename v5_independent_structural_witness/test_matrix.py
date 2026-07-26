"""
Executable test matrix implementing V5 Test Matrix v1.6 against
Architecture Freeze v0.5 and Harness Profile v1.6.

Run with: pytest -v test_matrix.py
"""
import copy
import hashlib
import json
import pytest
from cryptography.exceptions import InvalidSignature

from canonical import canonical_bytes, FIELD_ORDER
from fixtures import (
    build_standard_registry, build_e9_registry, baseline_fields,
    derive_keypair, pubkey_hex, GATE_NOW_NS_BASELINE, ControllableClock, TrustedClock,
)
from gate import AuthorityGate
from witness_source import sign_payload, envelope_to_bytes, compute_shape_integrity


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_gate(registry=None, seed_consumed=False, gate_fault_hook=None, clock=None):
    if registry is None:
        registry, _ = build_standard_registry()
    if clock is None:
        clock = TrustedClock(GATE_NOW_NS_BASELINE)
    gate = AuthorityGate(registry, structural_epoch=1, scope_type="route",
                          scope_id="route-A", clock=clock, gate_fault_hook=gate_fault_hook)
    if seed_consumed:
        gate.seed_watermark("source-1", "witness-1", 1, source_seq=10, observer_seq=10)
    return gate


def sign_baseline(privs, **overrides):
    fields = baseline_fields(**overrides)
    return sign_payload(fields, privs["key-1"])


def submit(gate, envelope, route_admissible=True, gate_now_ns=None):
    if gate_now_ns is not None:
        gate._clock.t = gate_now_ns  # test-fixture-level clock control, not a verify() argument
    raw = envelope_to_bytes(envelope)
    return gate.verify(raw, route_admissible)


# ===========================================================================
# Category L -- Canonical Known-Answer Vector
# ===========================================================================

FROZEN_SEED = "957eba143691d419a813315baa86b8dd0df3aa7af1770a2b2ddf720c7d50dfe8"
FROZEN_PUBKEY = "ef5f63d3671be7b17daef2431d77c00af615f17fc79bc26f4909374656349005"
FROZEN_PAYLOAD_SHA256 = "66e4a1e1159e3e036966797a8daa81f36ea68711832f5a849c1557fbd0580a43"
FROZEN_SIGNATURE = ("b87269a046160c69c2a8a630d15569c06be75b7542b0cc4076058874988fa4"
                     "deab7e8fefab4105185ea13463cbb82d7ef81db2fb2f10d673b1774df587820106")


def test_L1_seed_and_pubkey():
    priv, pub = derive_keypair("v5-harness-test-key-1")
    assert hashlib.sha256(b"v5-harness-test-key-1").hexdigest() == FROZEN_SEED
    assert pubkey_hex(pub) == FROZEN_PUBKEY


def test_L2_L3_canonical_payload():
    fields = baseline_fields()
    canon = canonical_bytes(fields)
    assert len(canon) == 140
    assert hashlib.sha256(canon).hexdigest() == FROZEN_PAYLOAD_SHA256


def test_L4_signature():
    priv, _ = derive_keypair("v5-harness-test-key-1")
    canon = canonical_bytes(baseline_fields())
    sig = priv.sign(canon)
    assert sig.hex() == FROZEN_SIGNATURE


def test_L5_witness_and_gate_encoders_agree():
    """
    Genuine cross-check: canonical_alt.py is an INDEPENDENTLY-WRITTEN second
    implementation (different code structure, re-derived from Profile §4
    directly, imports nothing from canonical.py). Comparing canonical.py's
    output to canonical.py's own output would be tautological (proving only
    that a function returns the same thing twice) -- this instead compares
    two textually-separate implementations of the same spec.
    """
    from canonical_alt import canonical_bytes_independent
    fields = baseline_fields()
    a = canonical_bytes(fields)
    b = canonical_bytes_independent(fields)
    assert a == b
    assert hashlib.sha256(a).hexdigest() == FROZEN_PAYLOAD_SHA256
    assert hashlib.sha256(b).hexdigest() == FROZEN_PAYLOAD_SHA256


# ===========================================================================
# Category A -- Signature and Witness Authentication
# ===========================================================================

def test_A1_no_signature_component():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = {"payload": baseline_fields()}  # no "signature" key at all
    r = submit(gate, envelope)
    assert r.fail_step == 2
    assert r.structural_authority is False
    assert r.watermarks_advanced is False


def test_A2_signature_stripped():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    del envelope["signature"]
    r = submit(gate, envelope)
    assert r.fail_step == 2


def test_A3_signature_corrupted_same_length():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    sig_bytes = bytearray(bytes.fromhex(envelope["signature"]))
    sig_bytes[0] ^= 0x01  # one-bit flip, same length
    envelope["signature"] = bytes(sig_bytes).hex()
    r = submit(gate, envelope)
    assert r.fail_step == 5


def test_A4_unauthorized_signer():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    priv2, pub2 = derive_keypair("v5-harness-test-key-2")  # never registered
    fields = baseline_fields(key_id="key-2")  # names its OWN (unregistered) id
    envelope = sign_payload(fields, priv2)
    r = submit(gate, envelope)
    assert r.fail_step == 4


def test_A5_observer_id_mismatch():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    envelope["payload"]["observer_id"] = "witness-9"  # tamper post-signing
    r = submit(gate, envelope)
    # Step 4 (registry binding) precedes step 5 (signature) in the frozen
    # order, so an observer_id mismatch is caught at step 4 regardless of
    # whether it came from tampering or genuine signing -- confirmed by
    # this failing the way my first draft's comment incorrectly predicted
    # step 5. Fixed to match the actual, correct gate behavior.
    assert r.fail_step == 4


def test_A5_observer_id_mismatch_genuinely_signed():
    # The *intended* step-4 test: genuinely sign a payload whose observer_id
    # doesn't match what key-1 is registered against.
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(observer_id="someone-else")
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 4


def test_A6_observer_type_mismatch_genuinely_signed():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(observer_type="auxiliary_observer")
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 4


def test_A7_unbound_observer_identity():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    # genuinely signed with key-1, but claims a different (unbound) observer_id
    fields = baseline_fields(observer_id="witness-unbound")
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 4


# ===========================================================================
# Category B -- Gate-Path Field Mutation
# ===========================================================================

@pytest.mark.parametrize("field,new_value,expected_step", [
    ("fact_evidence", 500_000, 5),
    ("logic_evidence", 500_000, 5),
    ("coherence_evidence", 500_000, 5),
    ("shape_integrity", False, 5),
    ("source_id", "source-9", 5),
    ("source_sequence", 11, 5),
    ("source_observation_time_ns", 9_000_000_000, 5),
    ("observer_sequence", 11, 5),
    ("witness_sign_time_ns", 10_150_000_000, 5),
    ("structural_epoch", 2, 5),
    ("scope_type", "system", 5),
    ("scope_id", "route-B", 5),
])
def test_B_gate_path_mutation(field, new_value, expected_step):
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    envelope["payload"][field] = new_value
    r = submit(gate, envelope)
    assert r.fail_step == expected_step, f"{field}: expected step {expected_step}, got {r.fail_step} ({r.reason})"
    assert r.watermarks_advanced is False


def test_B13_schema_version_mutation():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    envelope["payload"]["schema_version"] = "v4.9"
    r = submit(gate, envelope)
    assert r.fail_step == 2  # only one supported version exists


def test_B14_observer_id_mutation():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    envelope["payload"]["observer_id"] = "witness-9"
    r = submit(gate, envelope)
    assert r.fail_step == 4


def test_B15_observer_type_mutation():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    envelope["payload"]["observer_type"] = "auxiliary_observer"
    r = submit(gate, envelope)
    assert r.fail_step == 4


def test_B16_key_id_mutation():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    envelope["payload"]["key_id"] = "key-9"
    r = submit(gate, envelope)
    assert r.fail_step == 4


# ===========================================================================
# Category B-Encoder -- Canonical Sensitivity (all 16 fields)
# ===========================================================================

FIELD_ALT_VALUES = {
    "schema_version": "v5.1",
    "source_id": "source-2",
    "observer_id": "witness-2",
    "observer_type": "auxiliary_observer",
    "key_id": "key-2",
    "source_sequence": 11,
    "source_observation_time_ns": 9_000_000_000,
    "observer_sequence": 11,
    "witness_sign_time_ns": 10_150_000_000,
    "structural_epoch": 2,
    "scope_type": "system",
    "scope_id": "route-B",
    "fact_evidence": 500_000,
    "logic_evidence": 500_000,
    "coherence_evidence": 500_000,
    "shape_integrity": False,
}


@pytest.mark.parametrize("field", FIELD_ORDER)
def test_BE_canonical_sensitivity(field):
    base = baseline_fields()
    altered = baseline_fields(**{field: FIELD_ALT_VALUES[field]})
    assert canonical_bytes(base) != canonical_bytes(altered), f"{field} did not affect canonical bytes"


# ===========================================================================
# Category C -- Source Snapshot Integrity (interface-shape tests)
# ===========================================================================

from witness_source import TrustedStructuralSource, StructuralWitness, compute_shape_integrity


def test_C1_C2_C3_no_write_path_reachable_from_witness():
    """
    C1/C2/C3, as ACTUAL attacks against the real boundary (not just an
    absence-of-method-name check on the wrong object): construct a witness
    the normal way, with only a SourceReadCapability, and confirm there is
    no path from anything the witness holds to the source's writer.
    """
    clock = TrustedClock()
    src = TrustedStructuralSource("source-1", clock)
    priv, _ = derive_keypair("v5-harness-test-key-1")
    reader = src.make_read_capability()
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv, reader, clock)

    # Attack: try to write through whatever the witness holds.
    assert not hasattr(witness, "source"), "witness must not hold a reference to the raw source object"
    assert isinstance(witness._source_reader, type(reader))
    assert not hasattr(witness._source_reader, "publish")
    with pytest.raises(AttributeError):
        witness._source_reader.publish(1, "route", "route-A", 1, 1, 1)

    # Attack: construct a witness directly with the raw source (the exact
    # mistake that caused the original vulnerability) -- must be rejected.
    with pytest.raises(TypeError):
        StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv, src, clock)


def test_C_capability_closure_blocks_the_specific_dunder_self_exploit():
    """
    Confirms the specific, previously-working one-liner exploit
    (`capability._read_fn.__self__.publish(...)`) is now blocked: the
    capability's internal read function is a closure, not a bound method,
    so it has no __self__ attribute at all.
    """
    src = TrustedStructuralSource("source-1", TrustedClock())
    reader = src.make_read_capability()
    assert not hasattr(reader._read_fn, "__self__")
    with pytest.raises(AttributeError):
        reader._read_fn.__self__.publish(1, "route", "route-A", 1, 1, 1)


def test_C_deeper_reflection_via_closure_cells_is_a_documented_non_goal():
    """
    Honest limitation: __closure__ cell introspection can still recover the
    captured source reference. This is NOT claimed to be fixed -- it is a
    fundamental property of same-process Python (no code construction can
    prevent a caller with reflection access from walking closure cells,
    __dict__, gc.get_referrers, etc.). Architecture Freeze v0.5 explicitly
    defers physical/process trust-boundary enforcement to a later,
    separate experiment -- this harness does not attempt to simulate that
    boundary in-process, which would overclaim what a same-process
    capability object can honestly provide.
    """
    src = TrustedStructuralSource("source-1", TrustedClock())
    reader = src.make_read_capability()
    assert reader._read_fn.__closure__ is not None
    recovered = [c.cell_contents for c in reader._read_fn.__closure__
                 if isinstance(c.cell_contents, TrustedStructuralSource)]
    assert len(recovered) == 1 and recovered[0] is src
    # ^ this SUCCEEDING is the expected, documented outcome: it shows the
    # limit of what a same-process capability object can enforce.


def test_C_reflection_level_bypass_is_a_documented_non_goal():
    """
    Honest limitation, not a passing security test: Python has no true
    private attributes. Code that can execute arbitrary statements in the
    same process can always reassign `witness._source_reader` directly,
    bypassing the capability model entirely. This is equivalent to
    process/host-level compromise of the witness itself -- explicitly out
    of scope for V5 (Architecture Freeze v0.5 tests process-domain
    separation between the routed AGENT and the witness, not compromise of
    the witness's own internals). This test documents that the bypass
    exists and is out of scope, rather than silently ignoring it.
    """
    clock = TrustedClock()
    src = TrustedStructuralSource("source-1", clock)
    priv, _ = derive_keypair("v5-harness-test-key-1")
    reader = src.make_read_capability()
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv, reader, clock)

    class MaliciousReader:
        def read_latest(self):
            return {"source_id": "source-1", "source_sequence": 999, "source_observation_time_ns": 1,
                     "structural_epoch": 1, "scope_type": "route", "scope_id": "route-A",
                     "fact_evidence": 1_000_000, "logic_evidence": 1_000_000, "coherence_evidence": 1_000_000}

    witness._source_reader = MaliciousReader()  # direct attribute reassignment -- reflection-level, not normal API use
    result = witness.sign_current_snapshot()
    assert result is not None and result["payload"]["source_sequence"] == 999
    # ^ this SUCCEEDING is the expected, documented outcome of this test:
    # it demonstrates the boundary of what a software-only capability model
    # can enforce in Python, consistent with V5's frozen scope (host/process
    # compromise of the witness itself is out of scope).


def test_C11_no_historical_readback_method():
    """The only read method on the capability is read_latest(), which
    takes no sequence parameter -- there is no method signature through
    which a historical source_sequence could be requested."""
    import inspect
    src = TrustedStructuralSource("source-1", ControllableClock())
    reader = src.make_read_capability()
    sig = inspect.signature(reader.read_latest)
    assert len(sig.parameters) == 0
    assert not hasattr(reader, "read_sequence")
    assert not hasattr(reader, "read_history")
    assert not hasattr(reader, "read_at")
    assert not hasattr(reader, "publish")  # the capability has no writer either


def test_C12_no_torn_snapshot_under_concurrent_publish():
    """
    Each publication carries CORRELATED values derived from its sequence
    number (fact = seq*3, logic = seq*3+1, coherence = seq*3+2), so a
    snapshot torn between two different publish() calls would fail the
    correlation check even though source_id stayed the same throughout --
    the original version of this test only checked source_id, which never
    changes and therefore could never have caught a real tear.
    """
    import threading
    src = TrustedStructuralSource("source-1", ControllableClock())
    reader = src.make_read_capability()
    stop = threading.Event()
    bad_reads = []

    def publisher():
        seq = 0
        while not stop.is_set():
            seq += 1
            fact = seq * 3
            logic = seq * 3 + 1
            coherence = seq * 3 + 2
            src.publish(1, "route", "route-A", fact, logic, coherence)

    def reader_fn():
        for _ in range(5000):
            snap = reader.read_latest()
            if snap is not None:
                seq = snap["source_sequence"]
                expected = (seq * 3, seq * 3 + 1, seq * 3 + 2)
                actual = (snap["fact_evidence"], snap["logic_evidence"], snap["coherence_evidence"])
                if actual != expected:
                    bad_reads.append((seq, actual, expected))

    t = threading.Thread(target=publisher)
    t.start()
    reader_fn()
    stop.set()
    t.join()
    assert bad_reads == [], f"torn snapshots detected: {bad_reads[:5]}"


# ===========================================================================
# Category C-Witness -- shape_integrity Derivation Isolation
# ===========================================================================

def test_CW_isolation_route_outcome_has_no_path_into_computation():
    """There is no parameter on compute_shape_integrity other than the
    three evidence values -- route outcomes, latency, confidence, env vars
    etc. have no path in, by construction (the function signature itself
    is the proof)."""
    import inspect
    sig = inspect.signature(compute_shape_integrity)
    assert list(sig.parameters.keys()) == ["fact", "logic", "coherence"]


def test_CW5_determinism():
    results = {compute_shape_integrity(700_000, 800_000, 900_000) for _ in range(1000)}
    assert results == {True}


# ===========================================================================
# Category CW-Boundary -- Frozen Rule Threshold Tests
# ===========================================================================

def test_CW6_exact_threshold_inclusive():
    assert compute_shape_integrity(500_000, 500_000, 500_000) is True


def test_CW7_fact_below_threshold():
    assert compute_shape_integrity(499_999, 1_000_000, 1_000_000) is False


def test_CW8_logic_below_threshold():
    assert compute_shape_integrity(1_000_000, 499_999, 1_000_000) is False


def test_CW9_coherence_below_threshold():
    assert compute_shape_integrity(1_000_000, 1_000_000, 499_999) is False


# ===========================================================================
# Category D -- Replay and Sequence Manipulation
# ===========================================================================

def duplicate_record_pair(privs, source_seq=10, epoch=1):
    """Shared duplicate-record hook (Profile §6): two independently, genuinely
    signed records from 'the same source snapshot', differing only in
    observer_sequence."""
    f1 = baseline_fields(source_sequence=source_seq, observer_sequence=source_seq, structural_epoch=epoch)
    f2 = baseline_fields(source_sequence=source_seq, observer_sequence=source_seq + 1, structural_epoch=epoch)
    return sign_payload(f1, privs["key-1"]), sign_payload(f2, privs["key-1"])


def test_D1_exact_replay():
    registry, privs = build_standard_registry()
    gate = make_gate(registry, seed_consumed=True)
    envelope = sign_baseline(privs)  # seq 10/10, already consumed
    r = submit(gate, envelope)
    assert r.fail_step == 10
    assert r.watermarks_advanced is False


def test_D2_same_source_seq_new_observer_seq():
    registry, privs = build_standard_registry()
    gate = make_gate(registry, seed_consumed=True)  # watermarks at 10/10
    rec1, rec2 = duplicate_record_pair(privs, source_seq=10)
    r = submit(gate, rec2)  # source_seq=10 (== watermark, replay), observer_seq=11 (new)
    assert r.fail_step == 10
    assert r.watermarks_advanced is False


def test_D3_same_observer_seq_new_source_seq_fault_injected():
    """Witness reusing an observer_sequence for a genuinely new snapshot
    violates its own monotonicity invariant -- constructed directly
    (fault-injected-signer), not via the honest witness pipeline."""
    registry, privs = build_standard_registry()
    gate = make_gate(registry, seed_consumed=True)  # watermarks 10/10
    fields = baseline_fields(source_sequence=11, observer_sequence=10)  # reused obs seq
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 10
    assert r.watermarks_advanced is False


def test_D4_lower_source_seq_new_observer_seq_fault_injected():
    registry, privs = build_standard_registry()
    gate = make_gate(registry, seed_consumed=True)  # watermarks 10/10
    fields = baseline_fields(source_sequence=9, observer_sequence=11)  # resurrect old source content
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 10
    assert r.watermarks_advanced is False


def test_D5_lower_observer_seq_new_source_seq_fault_injected():
    registry, privs = build_standard_registry()
    gate = make_gate(registry, seed_consumed=True)  # watermarks 10/10
    fields = baseline_fields(source_sequence=11, observer_sequence=9)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 10
    assert r.watermarks_advanced is False


def test_D6_fresh_observer_seq_wrapping_consumed_source():
    registry, privs = build_standard_registry()
    gate = make_gate(registry, seed_consumed=True)  # watermarks 10/10
    rec1, rec2 = duplicate_record_pair(privs, source_seq=10)
    r = submit(gate, rec2)
    assert r.fail_step == 10  # source_seq=10 already consumed
    assert r.watermarks_advanced is False


def test_D7_fresh_source_seq_reused_observer_seq_fault_injected():
    registry, privs = build_standard_registry()
    gate = make_gate(registry, seed_consumed=True)  # watermarks 10/10
    fields = baseline_fields(source_sequence=11, observer_sequence=10)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 10
    assert r.watermarks_advanced is False


def test_witness_signs_at_most_one_record_per_snapshot_sequential():
    """
    Direct test of the honest witness's own duplicate-prevention: calling
    sign_current_snapshot() twice against the same unchanged snapshot must
    yield exactly one real record and one None, not two distinct records
    with different observer_sequence values -- which is what an honestly-
    operating witness reading one bound source can never legitimately
    produce (D2/D6/D8a/D8b's duplicate pairs are constructed via
    fault-injected-signer specifically because this path is closed).
    """
    clock = TrustedClock()
    src = TrustedStructuralSource("source-1", clock)
    priv1, _ = derive_keypair("v5-harness-test-key-1")
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv1, src.make_read_capability(), clock)

    src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)
    rec1 = witness.sign_current_snapshot()
    rec2 = witness.sign_current_snapshot()  # same snapshot, no intervening publish()

    assert rec1 is not None
    assert rec2 is None

    # A genuinely new snapshot restores normal signing.
    src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)
    rec3 = witness.sign_current_snapshot()
    assert rec3 is not None
    assert rec3["payload"]["source_sequence"] == rec1["payload"]["source_sequence"] + 1


def test_witness_signs_at_most_one_record_per_snapshot_concurrent():
    """Same property under genuine concurrency: many threads racing to sign
    the same unchanged snapshot must produce exactly one real record."""
    import threading
    clock = TrustedClock()
    src = TrustedStructuralSource("source-1", clock)
    priv1, _ = derive_keypair("v5-harness-test-key-1")
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv1, src.make_read_capability(), clock)
    src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)

    N = 20
    barrier = threading.Barrier(N)
    results = [None] * N

    def go(idx):
        barrier.wait()
        results[idx] = witness.sign_current_snapshot()

    threads = [threading.Thread(target=go, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    real_records = [r for r in results if r is not None]
    assert len(real_records) == 1, f"expected exactly 1 real record from {N} concurrent callers, got {len(real_records)}"


def test_witness_signing_failure_does_not_consume_the_snapshot():
    """
    A transient signing failure must not permanently mark a snapshot as
    already-signed. State (_sequence_by_epoch, _highest_signed_source_seq)
    must only be committed after sign_payload() actually succeeds --
    otherwise a one-time signer failure destroys the only opportunity to
    ever produce a record from that snapshot.
    """
    clock = TrustedClock()
    src = TrustedStructuralSource("source-1", clock)
    priv1, _ = derive_keypair("v5-harness-test-key-1")
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv1, src.make_read_capability(), clock)
    src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)

    class FlakyKey:
        """Fails on its first call, signs normally thereafter."""
        def __init__(self, real_key):
            self.real_key = real_key
            self.calls = 0

        def sign(self, data):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("simulated signing failure")
            return self.real_key.sign(data)

    witness.private_key = FlakyKey(priv1)

    with pytest.raises(RuntimeError):
        witness.sign_current_snapshot()

    # State must be completely unchanged after the failed attempt.
    assert witness._sequence_by_epoch == {}
    assert witness._highest_signed_source_seq == {}

    # Retrying the same (still-current) snapshot must succeed and must
    # produce observer_sequence 1 -- as if the failed attempt never
    # happened, because from the witness's committed-state point of view,
    # it didn't.
    record = witness.sign_current_snapshot()
    assert record is not None
    assert record["payload"]["observer_sequence"] == 1
    assert record["payload"]["source_sequence"] == 1


def test_D8a_duplicate_pair_sequential():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)  # watermarks 9/9, UNCONSUMED
    rec1, rec2 = duplicate_record_pair(privs, source_seq=10)
    r1 = submit(gate, rec1)
    assert r1.fail_step is None
    assert r1.structural_authority is True
    assert r1.watermarks_advanced is True

    r2 = submit(gate, rec2)
    assert r2.fail_step == 10
    assert r2.watermarks_advanced is False


def test_D8b_duplicate_pair_concurrent():
    """
    Uses the gate's real contention_hook, which fires immediately before
    the replay lock is acquired (see gate.py), forcing both threads to pile
    up at exactly the critical section's boundary rather than merely
    synchronizing thread start times outside verify() entirely (which
    proves nothing about the critical section itself -- this was the exact
    defect identified in review of the previous version of this test).

    Run across many trials, since a single passing trial does not rule out
    scheduling-dependent flakiness.
    """
    import threading
    registry_privs = [build_standard_registry() for _ in range(50)]
    failures = []
    for trial, (registry, privs) in enumerate(registry_privs):
        gate = make_gate(registry)  # watermarks 9/9
        rec1, rec2 = duplicate_record_pair(privs, source_seq=10)

        barrier = threading.Barrier(2)
        gate.contention_hook = barrier.wait
        results = [None, None]

        def go(idx, envelope):
            results[idx] = submit(gate, envelope)

        t1 = threading.Thread(target=go, args=(0, rec1))
        t2 = threading.Thread(target=go, args=(1, rec2))
        t1.start(); t2.start()
        t1.join(); t2.join()

        accepted = [r for r in results if r.structural_authority]
        rejected = [r for r in results if not r.structural_authority]
        if not (len(accepted) == 1 and len(rejected) == 1 and rejected[0].fail_step == 10):
            failures.append((trial, results))

    assert failures == [], f"{len(failures)}/50 trials violated exactly-one-winner: {failures[:3]}"


# ===========================================================================
# Category E -- Delivery Order, Staleness, Scope/Epoch Substitution
# ===========================================================================

def test_E1_E2_out_of_order_delivery_fails_both_predicates():
    """Two honestly-produced records from an honestly-advancing source: the
    earlier one is necessarily lower on BOTH sequences. Delivering it after
    the later one fails SourceReplaySafe AND ObserverReplaySafe together.
    Source, witness, and gate all share ONE clock instance here, exactly as
    the corrected design requires."""
    registry, privs = build_standard_registry()
    clock = TrustedClock(10_000_000_000)
    src = TrustedStructuralSource("source-1", clock)
    priv1, _ = derive_keypair("v5-harness-test-key-1")
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv1, src.make_read_capability(), clock)
    gate = make_gate(registry, clock=clock)

    src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)  # source_observation_time_ns = 10_000_000_000
    clock.advance(50_000)
    early = witness.sign_current_snapshot()  # witness_sign_time_ns = 10_000_050_000

    clock.advance(50_000_000)  # source_observation_time_ns = 10_050_050_000 at next publish
    src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)
    clock.advance(50_000)
    later = witness.sign_current_snapshot()

    clock.advance(149_900_000)  # advance to a gate-evaluation time within the freshness window of `later`
    r_later = submit(gate, later)
    assert r_later.structural_authority is True

    r_early = submit(gate, early)
    assert r_early.fail_step == 10
    # both predicates individually would be false: verify directly
    src_wm, obs_wm = gate.watermark_snapshot()
    assert early["payload"]["source_sequence"] < src_wm[("source-1", 1)]
    assert early["payload"]["observer_sequence"] < obs_wm[("witness-1", 1)]


def test_E4_stale_source_fresh_sign_time():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(
        source_observation_time_ns=8_199_999_998,  # stale
        witness_sign_time_ns=10_100_000_000,       # fresh sign time
    )
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope, gate_now_ns=10_200_000_000)
    assert r.fail_step == 11
    assert r.watermarks_advanced is True  # passes step 10 before failing step 11


def test_E5_prior_epoch_replay():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)  # current epoch = 1
    fields = baseline_fields(structural_epoch=1)
    envelope = sign_payload(fields, privs["key-1"])
    r0 = submit(gate, envelope)
    assert r0.structural_authority is True

    gate.current_epoch = 2  # epoch advances
    r1 = submit(gate, envelope)  # same old-epoch record replayed
    assert r1.fail_step == 7


def test_E6_alternate_scope_context():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)  # gate context: route-A
    fields = baseline_fields(scope_id="route-B")  # legitimately signed, different scope
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 8


def test_E7_route_scoped_as_system_wide():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)  # gate context: scope_type=route
    fields = baseline_fields(scope_type="system")
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 8


def test_E8_unregistered_source_id_genuinely_signed():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_id="source-unregistered")
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 6


def test_E9_registered_source_unbound_witness():
    registry, privs = build_e9_registry()
    gate = make_gate(registry)
    fields = baseline_fields(observer_id="witness-2", key_id="key-2", source_id="source-1")
    envelope = sign_payload(fields, privs["key-2"])
    r = submit(gate, envelope)
    assert r.fail_step == 6  # source-1 is bound to witness-1, not witness-2


# ===========================================================================
# Category F -- Schema, Encoding, Temporal Sanity
# ===========================================================================

def test_F1_undecodable_bytes():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    r = gate.verify(b"{not valid json!!!", True)
    assert r.fail_step == 1


def test_F2a_duplicate_envelope_key():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    good = json.dumps(envelope)
    raw = good[:-1] + f', "payload": {json.dumps(envelope["payload"])}}}'
    r = gate.verify(raw.encode("utf-8"), True)
    assert r.fail_step == 2  # duplicate top-level "payload" key detected


def test_F2b_duplicate_payload_field():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    payload_json = json.dumps(envelope["payload"])
    dup_payload_json = payload_json[:-1] + ', "scope_id": "route-Z"}'
    raw = f'{{"payload": {dup_payload_json}, "signature": "{envelope["signature"]}"}}'
    r = gate.verify(raw.encode("utf-8"), True)
    assert r.fail_step == 2  # duplicate "scope_id" field inside payload detected


def test_F3_unsupported_schema_version():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(schema_version="v6.0")
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 2


def test_F4_required_field_missing():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    del envelope["payload"]["scope_id"]
    r = submit(gate, envelope)
    assert r.fail_step == 2


def test_F5_unrecognized_field():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    envelope["payload"]["extra_field"] = "unexpected"
    r = submit(gate, envelope)
    assert r.fail_step == 2


def test_F6_transport_variance_must_pass():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    # reorder keys, re-serialize with different whitespace -- meaning-preserving
    reordered_payload = {k: envelope["payload"][k] for k in reversed(list(envelope["payload"].keys()))}
    raw = json.dumps({"signature": envelope["signature"], "payload": reordered_payload}, indent=4)
    r = gate.verify(raw.encode("utf-8"), True)
    assert r.structural_authority is True


def test_F7_source_time_after_sign_time():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_observation_time_ns=10_150_000_000, witness_sign_time_ns=10_100_000_000)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 9


def test_F8_sign_time_future():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(witness_sign_time_ns=10_300_000_000)  # after gate_now
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 9


def test_F9_source_time_future():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_observation_time_ns=10_300_000_000, witness_sign_time_ns=10_300_000_000)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.fail_step == 9


def test_F10_stale_record():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_observation_time_ns=7_000_000_000, witness_sign_time_ns=10_100_000_000)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope, gate_now_ns=10_200_000_000)
    assert r.fail_step == 11
    assert r.watermarks_advanced is True


# ===========================================================================
# Category K -- Type and Boundary Strictness
# ===========================================================================

def _submit_raw_payload_override(registry, privs, raw_field_overrides, gate_now_ns=GATE_NOW_NS_BASELINE):
    """Build a valid baseline envelope, then splice raw (possibly
    type-invalid) JSON text into the payload for one field, bypassing
    Python-level type construction so we can submit e.g. a JSON float for
    an int field, or a JSON bool for an int field."""
    fields = baseline_fields()
    envelope = sign_payload(fields, privs["key-1"])
    payload_json = json.dumps(envelope["payload"])
    obj = json.loads(payload_json)
    obj.update(raw_field_overrides)
    raw = json.dumps({"payload": obj, "signature": envelope["signature"]})
    gate = make_gate(registry, clock=TrustedClock(gate_now_ns))
    return gate.verify(raw.encode("utf-8"), True)


@pytest.mark.parametrize("overrides,label", [
    ({"source_sequence": 0}, "K6 zero source_sequence"),
    ({"observer_sequence": 0}, "K6 zero observer_sequence"),
    ({"source_sequence": -1}, "K7 negative source_sequence"),
    ({"observer_sequence": -1}, "K7 negative observer_sequence"),
    ({"source_sequence": 2**64}, "K8 source_sequence overflow"),
    ({"observer_sequence": 2**64}, "K8 observer_sequence overflow"),
    ({"source_id": "bad id with spaces"}, "K9 invalid source_id format"),
    ({"observer_type": "not_a_real_type"}, "K10 observer_type outside enum"),
    ({"scope_type": "not_a_real_scope"}, "K10 scope_type outside enum"),
    ({"fact_evidence": -1}, "K11 evidence below range"),
    ({"fact_evidence": 1_000_001}, "K11 evidence above range"),
    ({"fact_evidence": 0.5}, "K12 evidence as fractional number"),
    ({"fact_evidence": "500000"}, "K13 evidence as string"),
    ({"source_sequence": 10.0}, "K14 sequence as float"),
    ({"structural_epoch": 1.0}, "K14 epoch as float"),
    ({"shape_integrity": 1}, "K15 shape_integrity as integer"),
    ({"structural_epoch": 0}, "K16 epoch zero"),
    ({"structural_epoch": -1}, "K17 epoch negative"),
    ({"structural_epoch": 2**64}, "K18 epoch overflow"),
    ({"source_observation_time_ns": -1}, "K19 negative source time"),
    ({"witness_sign_time_ns": -1}, "K20 negative sign time"),
    ({"source_observation_time_ns": 2**64}, "K21 source time overflow"),
    ({"witness_sign_time_ns": 2**64}, "K21 sign time overflow"),
    ({"source_sequence": True}, "K22 sequence as JSON boolean"),
    ({"structural_epoch": False}, "K22 epoch as JSON boolean"),
])
def test_K_type_boundary_strictness(overrides, label):
    registry, privs = build_standard_registry()
    r = _submit_raw_payload_override(registry, privs, overrides)
    assert r.fail_step == 2, f"{label}: expected step 2, got {r.fail_step} ({r.reason})"
    assert r.watermarks_advanced is False


def test_K1_wrong_top_level_type():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    r = gate.verify(b'["not", "an", "object"]', True)
    assert r.fail_step == 2


def test_K2_signature_wrong_json_type():
    registry, privs = build_standard_registry()
    envelope = sign_baseline(privs)
    raw = json.dumps({"payload": envelope["payload"], "signature": 12345})
    gate = make_gate(registry)
    r = gate.verify(raw.encode("utf-8"), True)
    assert r.fail_step == 2


def test_K3_signature_wrong_length():
    registry, privs = build_standard_registry()
    envelope = sign_baseline(privs)
    envelope["signature"] = envelope["signature"][:-2]  # too short
    r = _submit_env(registry, envelope)
    assert r.fail_step == 2


def test_K4_signature_non_hex():
    registry, privs = build_standard_registry()
    envelope = sign_baseline(privs)
    envelope["signature"] = "g" * 128
    r = _submit_env(registry, envelope)
    assert r.fail_step == 2


def test_K5_signature_uppercase():
    registry, privs = build_standard_registry()
    envelope = sign_baseline(privs)
    envelope["signature"] = envelope["signature"].upper()
    r = _submit_env(registry, envelope)
    assert r.fail_step == 2


def _submit_env(registry, envelope, gate_now_ns=GATE_NOW_NS_BASELINE):
    gate = make_gate(registry, clock=TrustedClock(gate_now_ns))
    return gate.verify(envelope_to_bytes(envelope), True)


# ===========================================================================
# Category KF -- Freshness Boundary Controls
# ===========================================================================

def test_KF1_zero_age_boundary():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_observation_time_ns=10_200_000_000, witness_sign_time_ns=10_200_000_000)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope, gate_now_ns=10_200_000_000)
    assert r.structural_authority is True
    assert r.bypass_authority is True


def test_KF2_exact_2s_boundary():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_observation_time_ns=8_200_000_000, witness_sign_time_ns=10_100_000_000)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope, gate_now_ns=10_200_000_000)
    assert r.structural_authority is True
    assert r.bypass_authority is True


def test_KF3_one_ns_past_boundary():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_observation_time_ns=8_199_999_999, witness_sign_time_ns=10_100_000_000)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope, gate_now_ns=10_200_000_000)
    assert r.fail_step == 11
    assert r.watermarks_advanced is True


# ===========================================================================
# Category G -- Availability
# ===========================================================================

def test_G1_no_snapshot_no_record():
    clock = TrustedClock()
    src = TrustedStructuralSource("source-1", clock)
    priv1, _ = derive_keypair("v5-harness-test-key-1")
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv1, src.make_read_capability(), clock)
    result = witness.sign_current_snapshot()
    assert result is None  # nothing published yet -- no record produced


def test_G2_delayed_delivery_stale_on_arrival():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_observation_time_ns=6_000_000_000, witness_sign_time_ns=6_100_000_000)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope, gate_now_ns=10_200_000_000)  # delivered late
    assert r.fail_step == 11
    assert r.structural_authority is False
    assert r.bypass_authority is False
    assert r.watermarks_advanced is True


# ===========================================================================
# Category H -- Positive and Negative Controls
# ===========================================================================

def test_H1_fully_healthy_accepted():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    r = submit(gate, envelope, route_admissible=True)
    assert r.structural_authority is True
    assert r.bypass_authority is True
    assert r.watermarks_advanced is True


def test_H2_genuinely_unhealthy_evidence():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(fact_evidence=499_999)  # witness computes shape_integrity itself
    shape = compute_shape_integrity(499_999, 1_000_000, 1_000_000)
    assert shape is False
    fields["shape_integrity"] = shape
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope)
    assert r.structural_authority is False
    assert r.bypass_authority is False
    assert r.watermarks_advanced is True
    assert r.fail_step == 12


def test_H3_route_not_admissible():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    r = submit(gate, envelope, route_admissible=False)
    assert r.structural_authority is True
    assert r.bypass_authority is False


def test_H4_stale_otherwise_valid():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    fields = baseline_fields(source_observation_time_ns=5_000_000_000, witness_sign_time_ns=10_100_000_000)
    envelope = sign_payload(fields, privs["key-1"])
    r = submit(gate, envelope, gate_now_ns=10_200_000_000)
    assert r.fail_step == 11
    assert r.watermarks_advanced is True


def test_H5_no_snapshot():
    clock = TrustedClock()
    src = TrustedStructuralSource("source-1", clock)
    priv1, _ = derive_keypair("v5-harness-test-key-1")
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv1, src.make_read_capability(), clock)
    assert witness.sign_current_snapshot() is None


def test_H6_source_replay_isolated_from_observer_replay():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)  # UNCONSUMED, watermarks 9/9

    N = 10
    # First record: unhealthy, seq N/N -- accepted (SA=0 due to shape_integrity,
    # but watermarks still advance to N/N).
    unhealthy_fields = baseline_fields(source_sequence=N, observer_sequence=N, fact_evidence=100_000)
    unhealthy_fields["shape_integrity"] = compute_shape_integrity(100_000, 1_000_000, 1_000_000)
    r1 = submit(gate, sign_payload(unhealthy_fields, privs["key-1"]))
    assert r1.structural_authority is False
    assert r1.fail_step == 12
    assert r1.watermarks_advanced is True

    # Second record: healthy, source_sequence=N-1 (lower, fails SourceReplaySafe),
    # observer_sequence=N+1 (higher, would pass ObserverReplaySafe alone).
    # This combination requires the witness to resurrect old source content
    # it cannot retrieve -- fault-injected-signer construction.
    healthy_fields = baseline_fields(source_sequence=N - 1, observer_sequence=N + 1)
    r2 = submit(gate, sign_payload(healthy_fields, privs["key-1"]))
    assert r2.fail_step == 10
    assert r2.structural_authority is False
    # Directly confirm which predicate specifically failed:
    src_wm, obs_wm = gate.watermark_snapshot()
    assert healthy_fields["source_sequence"] <= src_wm[("source-1", 1)]      # SourceReplaySafe = False
    assert healthy_fields["observer_sequence"] > obs_wm[("witness-1", 1)]    # ObserverReplaySafe = True (in isolation)


# ===========================================================================
# Category I -- Producer Invariants
# ===========================================================================

def test_I1_I2_source_sequence_monotonic_and_resets_on_epoch():
    src = TrustedStructuralSource("source-1", ControllableClock())
    seqs_epoch1 = [src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)["source_sequence"] for _ in range(5)]
    assert seqs_epoch1 == sorted(seqs_epoch1)
    assert len(set(seqs_epoch1)) == len(seqs_epoch1)  # strictly increasing, no repeats

    first_epoch2 = src.publish(2, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)["source_sequence"]
    assert first_epoch2 == 1  # resets to exactly 1 on epoch change


def test_I3_I4_observer_sequence_monotonic_and_resets_on_epoch():
    clock = TrustedClock()
    src = TrustedStructuralSource("source-1", clock)
    priv1, _ = derive_keypair("v5-harness-test-key-1")
    witness = StructuralWitness("witness-1", "tetrahedral_coordinator", "key-1", priv1, src.make_read_capability(), clock)

    seqs = []
    for _ in range(5):
        src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)
        env = witness.sign_current_snapshot()
        seqs.append(env["payload"]["observer_sequence"])
    assert seqs == sorted(seqs)
    assert len(set(seqs)) == len(seqs)

    src.publish(2, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)  # epoch change
    env2 = witness.sign_current_snapshot()
    assert env2["payload"]["observer_sequence"] == 1


def test_I5_extended_run_no_repeats_or_decreases():
    src = TrustedStructuralSource("source-1", ControllableClock())
    seqs = [src.publish(1, "route", "route-A", 1_000_000, 1_000_000, 1_000_000)["source_sequence"] for _ in range(500)]
    assert all(seqs[i] < seqs[i + 1] for i in range(len(seqs) - 1))


def test_I6_shape_integrity_deterministic():
    outputs = {compute_shape_integrity(600_000, 700_000, 800_000) for _ in range(1000)}
    assert outputs == {True}


# ===========================================================================
# Category J -- Atomic Replay-State Failure
# ===========================================================================

def test_J1_gate_fault_injected_atomic_commit():
    registry, privs = build_standard_registry()

    class InjectedFailure(Exception):
        pass

    def boom():
        raise InjectedFailure("simulated interruption before composite commit")

    gate = make_gate(registry, gate_fault_hook=boom)
    envelope = sign_baseline(privs)  # otherwise fully accept-eligible

    src_before, obs_before = gate.watermark_snapshot()
    r = submit(gate, envelope)
    src_after, obs_after = gate.watermark_snapshot()

    assert r.structural_authority is False
    assert r.bypass_authority is False
    assert r.fail_step == 10
    assert src_before == src_after
    assert obs_before == obs_after
    assert r.watermarks_advanced is False


# ===========================================================================
# Step 13 -- RouteAdmissible must be an actual Boolean, not a truthy coercion
# ===========================================================================

@pytest.mark.parametrize("bad_value", ["false", "0", "", 0, 1, None, [], {}])
def test_step13_route_admissible_rejects_non_boolean(bad_value):
    """
    bool("false") is True, since "false" is a non-empty string -- coercing
    with bool() would let a string literally spelling "false" grant
    BypassAuthority. Every non-Boolean input must fail closed: SA is left
    intact (it depends only on the structural predicates, not on this
    field), BA must be False, fail_step must be explicitly 13 (leaving it
    None while reporting an error and forcing BA=False would be a
    self-contradictory result -- "fully passed" and "failed" at once), and
    watermarks must still have advanced (the record genuinely was
    structurally valid; only the route-admissibility input was malformed).
    """
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    r = submit(gate, envelope, route_admissible=bad_value)
    assert r.fail_step == 13
    assert r.structural_authority is True
    assert r.bypass_authority is False
    assert r.watermarks_advanced is True
    assert "step13" in r.reason


def test_step13_route_admissible_accepts_real_booleans():
    registry, privs = build_standard_registry()
    gate = make_gate(registry)
    envelope = sign_baseline(privs)
    r_true = submit(gate, envelope, route_admissible=True)
    assert r_true.bypass_authority is True

    gate2 = make_gate(registry)
    envelope2 = sign_baseline(privs)
    r_false = submit(gate2, envelope2, route_admissible=False)
    assert r_false.structural_authority is True
    assert r_false.bypass_authority is False
