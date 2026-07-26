# V5 Independent Structural Witness — Executable Harness

Implements Architecture Freeze v0.5, Harness Profile v1.6, and Test Matrix
v1.6. This is the smallest executable harness that implements the frozen
requirements.

**141 tests, all passing**, stable across repeated runs including the
threading-based tests. Run with:

```
pip install cryptography pytest
pytest -v test_matrix.py
```

## ⚠️ Test fixtures only

The Ed25519 seed in `fixtures.py` (`SHA-256("v5-harness-test-key-1")`,
`"v5-harness-test-key-2"`) and the resulting derived key pairs are
**deterministic test fixtures, not deployment credentials.** They exist so
the Category L known-answer vector is reproducible across independent
runs and independent implementations. Never use these seeds, or any seed
derived this predictably, for anything other than this test harness.

## Fifth-round fixes (this revision)

A fourth independent review found two more real defects, both narrow.

1. **Witness state committed before the signature existed.** The previous
   fix (round four) correctly prevented re-signing an unchanged snapshot,
   but it advanced `_sequence_by_epoch` and `_highest_signed_source_seq`
   *before* calling `sign_payload()`, not after. Reproduced directly: a
   signer that fails once and then works normally left the witness's state
   permanently marking the snapshot as signed, even though no record was
   ever produced — retrying returned `None` instead of a valid record,
   because the witness believed (wrongly) that this exact snapshot had
   already been handled. A transient signing failure destroyed the only
   opportunity to ever produce that record. Fixed: `sign_current_snapshot()`
   now builds the complete candidate `observer_sequence` and payload,
   calls `sign_payload()`, and only commits both state dictionaries
   *after* signing genuinely succeeds. If signing raises, execution never
   reaches the commit lines, so state is provably unchanged — verified by
   reproducing the exact original scenario (a signer failing on its first
   call) and confirming both state dicts are empty after the failure and
   the retry succeeds with `observer_sequence = 1`
   (`test_witness_signing_failure_does_not_consume_the_snapshot`).

2. **Step 13 reported an error while claiming every step had passed.** For
   a non-Boolean `route_admissible`, the gate correctly forced
   `BypassAuthority = False` but left `fail_step = None` — and `GateResult`
   defines `fail_step = None` as "fully passed." The result contradicted
   itself: a `reason` string describing a step-13 error, alongside a
   `fail_step` claiming no step had failed. Reproduced directly, then
   fixed: the non-Boolean branch now sets `result.fail_step = 13`
   explicitly. The existing parametrized test was strengthened to check
   `fail_step == 13`, `structural_authority is True`,
   `bypass_authority is False`, and `watermarks_advanced is True` together,
   not just that the word "step13" appeared somewhere in the reason string
   (which is how this passed review once already without actually checking
   the field that mattered).

## Scope correction (not a code change)

The previous README described restart persistence as a gate-only
limitation. That understated the scope: the source's `_sequence_by_epoch`,
the witness's `_sequence_by_epoch` and `_highest_signed_source_seq`, and
the gate's `_replay_state` are **all** memory-only. Restarting any one of
the three components loses that component's state, not just the gate's
replay watermarks — see the corrected out-of-scope section below.

## Files

- `canonical.py` / `canonical_alt.py` — primary and independently-written
  cross-check encoders (Profile §4).
- `fixtures.py` — registry, named fixtures, key derivation (test-only, see
  warning above), and `TrustedClock`.
- `gate.py` — the `AuthorityGate`: all 13 Ordered Verification Sequence
  steps, thread- and failure-atomic step 10, `gate_fault_hook` (J1),
  `contention_hook` (D8b), no caller-suppliable timestamp, and strict
  Boolean-only `route_admissible` handling at step 13 with a consistent
  `fail_step`.
- `witness_source.py` — `SourceReadCapability` (closure-based),
  `TrustedStructuralSource` (locked writer, clock-based timestamp
  stamping), `StructuralWitness` (locked sequence assignment,
  constructor-enforced capability type, shared-clock sign time, no
  timestamp fallback, no duplicate signing of an unchanged snapshot, and
  now: state committed only after signing genuinely succeeds).
- `test_matrix.py` — the executable tests, organized by category to mirror
  Test Matrix v1.6.

## Honest simplifications (documented, not hidden)

- **Category C4–C10** collapse to one structural test: the witness's only
  interface to the source is a capability with one parameterless method, so
  every listed influence vector has the same null result for the same
  reason.
- **Category CW1–CW4** collapse to one signature-inspection test on
  `compute_shape_integrity`: exactly three parameters, so nothing else has
  a way in, by construction.

## What remains explicitly out of scope (per v0.5 and Profile v1.6)

- **Host/process compromise of the witness or source themselves.** The
  witness is defined as trusted throughout V5's threat model
  ("assume the independent structural observer and its signing authority
  are outside that compromise domain"); reflection-level attacks on its own
  internal state (e.g. Python `__closure__` introspection recovering a
  captured reference) are a distinct, later problem, explicitly deferred by
  v0.5 to "a later hardware experiment."
  `test_C_deeper_reflection_via_closure_cells_is_a_documented_non_goal`
  demonstrates this succeeding, on purpose, rather than hiding it.
- **State persistence across a process restart, for all three
  components** — not only the gate's replay watermarks, but also the
  source's sequence counter and the witness's sequence counter and
  duplicate-signing memory. All of this is in-memory only; a restart of
  any component loses that component's state, and this harness does not
  attempt to solve that, consistent with V5's frozen scope.
- Truthful physical sensing / sensor fidelity of the Trusted Structural
  Source — evidence values are asserted inputs, not measured from external
  reality, exactly as specified.

