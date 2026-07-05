# Rejected Configuration Scar Validation Plan

**Document:** `REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1.md`  
**Version:** 1.0  
**Status:** Frozen for implementation  
**Controlling specification:** `REJECTED_CONFIGURATION_SCAR_SPEC_v1_REVISED.md`  
**Next artifact after approval:** `rejected_configuration_scar_sim_v1.py`

**Freeze date:** 2026-07-04  
**Freeze condition:** All eleven freeze checklist items confirmed by external review. No simulation code should change this plan without a new validation-plan version.

## Purpose

This plan freezes the first validation test for the rejected-configuration scar layer.

The experiment asks one narrow question:

> Can the system write scars only for betrayed authority, ignore cheap or non-admitted failures, reject exact scarred configurations on reappearance, elevate only after the declared threshold, and retire scars only after declared successful cycles?

This validation does not test cellular shedding.

It does not test lineage inheritance.

It does not test prospective filtering.

It does not test semantic diagnosis.

It tests the scar boundary.

The governing rule is:

```text
Only betrayed authority creates a scar.
```

A scar is a minimal structural record. It records that an authorized configuration failed and should not be promoted again as-is.

The scar does not explain why the configuration failed.

## Controlling Definitions

### Betrayed Authority

A scar may be written only when the system extended authority to a structural configuration and that trusted configuration later failed under valid structural evidence.

For v1, `configuration_had_authority = true` only when all of the following are true:

```text
configuration passed the full bounded-routing authority stack
configuration passed the live shape-integrity gate
configuration was admitted for trusted execution
configuration completed at least one structural operation or bypass task under that authority
```

A configuration that was authorized in principle but whose first operation was denied before completion does not satisfy the v1 scar authority threshold.

A configuration that was considered but never admitted does not satisfy the authority threshold.

A configuration that failed only because the evidence was missing, stale, unverifiable, epoch-mismatched, or out of scope does not satisfy the scar trigger.

### Scar-Eligible Events

The following trusted failures are scar-eligible in v1:

```text
AUTHORIZED_HARD_STRUCTURAL_FAILURE
AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION
AUTHORIZED_RESTORATION_FAILURE
```

The following are not scar-eligible:

```text
NON_ADMITTED_REJECT
CHEAP_RETRY_FAILURE
EVIDENCE_INVALIDITY
STALE_RECORD_DENIAL
FAILED_VERIFICATION_DENIAL
EPOCH_MISMATCH_DENIAL
SCOPE_MISMATCH_DENIAL
TRANSIENT_SOFT_WARNING_BELOW_PERSISTENCE
PROSPECTIVE_FILTER_REJECTION
AUTHORIZED_BUT_NO_COMPLETED_OPERATION
```

### Default Scar Responses

The response table for v1 is:

```text
AUTHORIZED_HARD_STRUCTURAL_FAILURE
    -> REJECT_AS_IS

AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION
    -> REQUIRE_EXTRA_PROOF

AUTHORIZED_RESTORATION_FAILURE
    -> REQUIRE_EXTRA_PROOF
```

`REJECT_AS_IS` means the exact scarred configuration cannot be promoted again without mutation, retirement, or a later declared override.

`REQUIRE_EXTRA_PROOF` means the exact scarred configuration cannot be silently re-promoted, but it is not treated as a permanently rejected hard failure. The validation plan does not define the later extra-proof protocol. It only verifies that the scar response is classified correctly.

## Frozen Fingerprint Declaration

The v1 fingerprint method is:

```text
fingerprint_method  = GEOMETRY_ONLY_SHA256
fingerprint_version = scar-fp-v1-geom-only
hash_algorithm      = SHA-256
payload_format      = canonical JSON
```

The fingerprint payload is structural only.

It contains:

```text
role_angles
role_weights
role_coverage_values
coordinator_position
scope_type
scope_id
fingerprint_method
fingerprint_version
```

It does not contain:

```text
failed_invariant_class
task text
task type
route history
C_success
route outcome
wrong-bypass label
recovery event label
human explanation
semantic category
diagnostic note
```

`failed_invariant_class` is adjacent metadata only.

The same geometry must match the same scar even if it later presents through a different `failed_invariant_class`.

### Canonical Field Order

The canonical JSON payload uses this exact field order:

```text
fingerprint_method
fingerprint_version
scope_type
scope_id
fact_angle_deg_q
logic_angle_deg_q
coherence_angle_deg_q
fact_weight_q
logic_weight_q
coherence_weight_q
fact_coverage_q
logic_coverage_q
coherence_coverage_q
coordinator_x_q
coordinator_y_q
```

The role order is always:

```text
Fact
Logic
Coherence
```

### Angle Normalization

Angles are normalized to:

```text
[0, 360)
```

Then quantized to:

```text
0.01 degrees
```

For example:

```text
360.004 degrees -> 0.00 degrees
-0.004 degrees  -> 360.00 degrees after normalization and quantization if represented as 359.996
120.004 degrees -> 120.00 degrees
120.006 degrees -> 120.01 degrees
```

The implementation must declare the exact rounding mode. The v1 default is decimal half-up rounding to the declared quantum.

### Numeric Quantization

Role weights are quantized to:

```text
0.0001
```

Coverage values are quantized to:

```text
0.0001
```

Coordinator `x` and `y` are quantized to:

```text
0.0001
```

The v1 default rounding mode is decimal half-up rounding to the declared quantum.

### Scope Representation

Scope is represented by exact strings:

```text
scope_type
scope_id
```

No case-folding, stemming, semantic normalization, or aliasing is allowed.

### Missing-Value Policy

A missing required geometry field produces:

```text
fingerprint_available = false
scar_written = false
audit_only = true
```

A missing required geometry field must not create a scar.

### Hash Rule

The canonical JSON payload is serialized without extra whitespace and hashed using SHA-256.

Two equivalent canonical payloads must produce the same fingerprint.

Two payloads that differ after quantization must produce different fingerprints, except for ordinary cryptographic collision risk.

## Frozen Scar Parameters

```text
K_SOFT_PERSIST                 = 3
T_SCAR_ELEVATE                 = 3
T_SCAR_RETIRE_SUCCESS_CYCLES   = 5
```

The validation plan uses exact canonical fingerprint matching only:

```text
match_policy = EXACT_CANONICAL_FINGERPRINT
```

No fuzzy matching is allowed in v1.

No near-match scar behavior is allowed in v1.

## Baseline Geometry

The baseline structural geometry is:

```text
Fact angle       =   0.00 degrees
Logic angle      = 120.00 degrees
Coherence angle  = 240.00 degrees

Fact weight      = 0.3333
Logic weight     = 0.3333
Coherence weight = 0.3334

Fact coverage      = 1.0000
Logic coverage     = 1.0000
Coherence coverage = 1.0000

Coordinator x = 0.0000
Coordinator y = 0.0000

scope_type = GLOBAL
scope_id   = ACTIVE_TETRAHEDRAL_SUBSTRATE
```

The weights sum to 1.0 after quantization.

All tests use this baseline unless a scenario states otherwise.

## Scenario Suite

The scenario suite is divided into five groups.

Fingerprint mechanism tests run first because every scar-write and scar-match test depends on fingerprint correctness.

Authority-boundary tests run second because no scar-write test is meaningful unless the scar trigger is defined.

Scar-write tests run third.

Scar-match and response tests run fourth.

Elevation and retirement tests run last.

## Fingerprint Mechanism Tests

### F0 Float Drift Still Matches

Purpose:

Verify that near-identical regenerated geometry with ordinary floating-point drift produces the same canonical fingerprint.

Input A:

```text
Fact angle       = 0.0000
Logic angle      = 120.0000
Coherence angle  = 240.0000
Fact weight      = 0.33330000
Logic weight     = 0.33330000
Coherence weight = 0.33340000
Coordinator x    = 0.00000000
Coordinator y    = 0.00000000
```

Input B:

```text
Fact angle       = 0.00004
Logic angle      = 120.00004
Coherence angle  = 239.99996
Fact weight      = 0.33330004
Logic weight     = 0.33329996
Coherence weight = 0.33340000
Coordinator x    = 0.00000004
Coordinator y    = -0.00000004
```

Expected result:

```text
fingerprint_A == fingerprint_B
```

No scar is written in this test. It validates canonicalization only.

### F1 Beyond Quantization Does Not Match

Purpose:

Verify that geometry beyond the declared quantization boundary does not accidentally match.

Input A is the baseline geometry.

Input B:

```text
Logic angle      = 120.0060
Coordinator x    = 0.00016
```

Expected result:

```text
fingerprint_A != fingerprint_B
```

No scar is written in this test.

### F2 Same Geometry Different Failed Invariant Class Matches

Purpose:

Verify that `failed_invariant_class` is not part of the hash payload.

Input A:

```text
baseline geometry
failed_invariant_class = ROLE_SEPARATION
```

Input B:

```text
same baseline geometry
failed_invariant_class = COORDINATOR_ALIGNMENT
```

Expected result:

```text
fingerprint_A == fingerprint_B
```

The two records may carry different adjacent metadata, but they must match the same scar fingerprint.

### F3 Missing Geometry Produces No Fingerprint

Purpose:

Verify that missing required geometry does not create a scar.

Input:

```text
missing coordinator_y
all other fields present
```

Expected result:

```text
fingerprint_available = false
scar_written = false
audit_only = true
```

## Authority Boundary Tests

### A0 Non-Admitted Candidate Leaves No Scar

Purpose:

A candidate fails before authority is extended.

Input:

```text
configuration_had_authority = false
valid_structural_evidence = true
candidate_rejected_before_authority = true
```

Expected result:

```text
scar_written = false
failure_count_increment = 0
```

### A1 Cheap Retry Failure Leaves No Scar

Purpose:

A local retry fails cheaply and is passed to the next candidate.

Input:

```text
configuration_had_authority = false
event_class = CHEAP_RETRY_FAILURE
```

Expected result:

```text
scar_written = false
audit_optional = true
```

### A2 Evidence Invalidity Leaves No Scar

Purpose:

A stale, unverifiable, or out-of-scope record denies authority but does not prove the configuration failed.

Input:

```text
configuration_had_authority = false or true
valid_structural_evidence = false
event_class = EVIDENCE_INVALIDITY
```

Expected result:

```text
scar_written = false
failure_count_increment = 0
```

### A3 Authorized But No Completed Operation Leaves No Scar

Purpose:

A configuration passes initial authority checks but its first operation is denied before completion by a simultaneous gate failure.

Input:

```text
passed_bounded_routing_stack = true
passed_shape_integrity_gate = true
admitted_for_trusted_execution = true
completed_trusted_operation = false
event_class = AUTHORIZED_BUT_NO_COMPLETED_OPERATION
```

Expected result:

```text
configuration_had_authority_for_scar = false
scar_written = false
```

### A4 Completed Authority Establishes Scar Eligibility

Purpose:

A configuration passes the authority stack and completes one trusted operation.

Input:

```text
passed_bounded_routing_stack = true
passed_shape_integrity_gate = true
admitted_for_trusted_execution = true
completed_trusted_operation = true
```

Expected result:

```text
configuration_had_authority_for_scar = true
```

This does not write a scar by itself. It only establishes eligibility if a later valid structural failure occurs.

## No-Scar Soft Boundary Test

### S0 Transient Soft Warning Below Persistence Leaves No Scar

Purpose:

Verify that a transient soft warning does not create a scar.

Input:

```text
configuration_had_authority = true
valid_structural_evidence = true
raw_soft_warning_count = K_SOFT_PERSIST - 1
then one clean observation
event_class = TRANSIENT_SOFT_WARNING_BELOW_PERSISTENCE
```

With `K_SOFT_PERSIST = 3`, the test uses:

```text
exactly 2 consecutive raw soft warnings
then 1 clean observation
```

Expected result:

```text
gate_effective_soft_degradation = false
scar_written = false
failure_count_increment = 0
```

## Scar Write Tests

### S1 Authorized Hard Structural Failure Writes Scar

Purpose:

Verify the core betrayed-authority rule.

Input:

```text
configuration_had_authority = true
valid_structural_evidence = true
event_class = AUTHORIZED_HARD_STRUCTURAL_FAILURE
failed_invariant_class = ROLE_SEPARATION
fingerprint_available = true
```

Expected result:

```text
scar_written = true
failure_count = 1
scar_event_class = AUTHORIZED_HARD_STRUCTURAL_FAILURE
scar_response = REJECT_AS_IS
```

### S2 Authorized Gate-Effective Soft Degradation Writes Soft Scar

Purpose:

Verify that persisted soft degradation after authority creates a scar with the soft response.

Input:

```text
configuration_had_authority = true
valid_structural_evidence = true
raw_soft_warning_count = K_SOFT_PERSIST
event_class = AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION
failed_invariant_class = ROLE_IMBALANCE
fingerprint_available = true
```

Expected result:

```text
scar_written = true
failure_count = 1
scar_event_class = AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION
scar_response = REQUIRE_EXTRA_PROOF
```

### S3 Authorized Restoration Failure Writes Soft Scar

Purpose:

Verify restoration failure handling.

Input:

```text
configuration_had_authority = true
valid_structural_evidence = true
event_class = AUTHORIZED_RESTORATION_FAILURE
failed_invariant_class = RESTORATION_FAILURE
fingerprint_available = true
```

Expected result:

```text
scar_written = true
failure_count = 1
scar_event_class = AUTHORIZED_RESTORATION_FAILURE
scar_response = REQUIRE_EXTRA_PROOF
```

## Scar Match And Response Tests

### M0 Hard Scar Match Rejects As-Is

Purpose:

Verify that the same hard-failed geometry is not silently re-promoted.

Setup:

```text
active scar from S1 exists
same configuration_fingerprint appears again
candidate seeks authority
```

Expected result:

```text
scar_match = true
authority_response = REJECT_AS_IS
candidate_promoted_as_is = false
```

### M1 Soft Scar Match Requires Extra Proof

Purpose:

Verify that soft scar response is not permanent hard rejection.

Setup:

```text
active scar from S2 exists
same configuration_fingerprint appears again
candidate seeks authority
```

Expected result:

```text
scar_match = true
authority_response = REQUIRE_EXTRA_PROOF
candidate_silently_promoted = false
candidate_hard_rejected_by_default = false
```

### M2 Similar But Non-Identical Geometry Does Not Match Under V1

Purpose:

Verify exact-match behavior.

Setup:

```text
active scar from S1 exists
candidate geometry differs beyond quantization boundary
```

Expected result:

```text
scar_match = false
authority_response_from_scar = NONE
```

This test does not claim the candidate is safe. It only verifies that v1 exact matching does not act as fuzzy or prospective filtering.

### M3 Same Geometry Different Failure Class Matches Same Scar

Purpose:

Verify that the scar recognizes geometry rather than first-failed-invariant labels.

Setup:

```text
active scar from S1 exists with failed_invariant_class = ROLE_SEPARATION
same geometry appears with failed_invariant_class = COORDINATOR_ALIGNMENT
```

Expected result:

```text
configuration_fingerprint matches active scar
scar_match = true
```

## Failure Count Tests

### C0 Repeated Trusted Failure Increments Failure Count

Purpose:

Verify that repeated betrayed authority increments the scar count.

Setup:

```text
active scar exists with failure_count = 1
same configuration_fingerprint receives authority again under declared extra-proof or override path
configuration completes one trusted operation
configuration fails again under valid structural evidence
```

For this validation scenario, re-admission of the scarred configuration is a test-harness override used only to verify failure-count behavior. It is not a demonstration or implementation of the later extra-proof protocol.

Expected result:

```text
failure_count = 2
last_seen_ms updates
```

### C1 Cheap Rejected Repeat Does Not Increment Failure Count

Purpose:

Verify that repeated rejected nominations do not become scar failures.

Setup:

```text
active scar exists with failure_count = 1
same configuration_fingerprint is proposed 10 times
each proposal is rejected before authority
no trusted operation completes
```

Expected result:

```text
failure_count remains 1
nomination_pressure_metric may increment if implemented
scar_failure_count does not increment
```

## Elevation Tests

### E0 Elevation Does Not Fire Below Threshold

Purpose:

Verify the elevation boundary.

Setup:

```text
T_SCAR_ELEVATE = 3
same scar failure_count = 2
```

Expected result:

```text
elevation_state != ELEVATED
ScarElevationEvent emitted = false
```

### E1 Elevation Fires At Threshold

Purpose:

Verify that repeated betrayed authority can hand the compact record upward.

Setup:

```text
T_SCAR_ELEVATE = 3
same scar failure_count increments to 3
```

Expected result:

```text
elevation_state = ELEVATED
ScarElevationEvent emitted = true
```

The elevation event contains only:

```text
configuration_fingerprint
scope_type
scope_id
failure_count
failed_invariant_class
first_seen_ms
last_seen_ms
verification_reference
```

No semantic explanation is emitted by the scar layer.

## Retirement Tests

### R0 Idle Time Alone Does Not Retire Scar

Purpose:

Verify that retirement is success-count based, not idle-time based.

Setup:

```text
active scar exists
successful_cycles_since_last_seen = 0
idle_time_passes = large
```

Expected result:

```text
scar_retired = false
scar_blocks_or_constrains_authority = true
```

### R1 Successful Cycles Retire Scar At Threshold

Purpose:

Verify success-count retirement.

Setup:

```text
T_SCAR_RETIRE_SUCCESS_CYCLES = 5
same scope completes 5 declared successful cycles
same configuration_fingerprint does not recur
no scar-eligible failure carrying same configuration_fingerprint occurs
```

Expected result:

```text
successful_cycles_since_last_seen = 5
scar_retired = true
scar no longer blocks authority
```

### R2 New Trusted Failure Resets Retirement Progress

Purpose:

Verify that retirement cannot continue through repeated failure.

Setup:

```text
active scar exists
successful_cycles_since_last_seen = 4
same configuration_fingerprint receives authority and fails again
```

Expected result:

```text
failure_count increments
successful_cycles_since_last_seen = 0
scar_retired = false
```

## Metrics

The implementation must report:

```text
fingerprint_match_count
fingerprint_mismatch_count
fingerprint_unavailable_count
scar_written_count
no_scar_correct_count
false_scar_count
missed_scar_count
hard_scar_count
soft_scar_count
restoration_scar_count
scar_match_count
scar_false_match_count
scar_missed_match_count
failure_count_increment_count
failure_count_false_increment_count
elevation_event_count
false_elevation_count
missed_elevation_count
retired_scar_count
false_retirement_count
missed_retirement_count
```

It must also report each scenario result by scenario id.

## Required Assertions

Any failed assertion invalidates the run.

```text
A1  F0 near-identical float drift produces identical fingerprints.

A2  F1 geometry beyond the quantization boundary produces different fingerprints.

A3  F2 same geometry with different failed_invariant_class produces identical fingerprints.

A4  F3 missing required geometry produces no fingerprint and no scar.

A5  A0 non-admitted candidate writes no scar.

A6  A1 cheap retry failure writes no scar.

A7  A2 evidence invalidity writes no scar.

A8  A3 authorized-but-no-completed-operation writes no scar.

A9  A4 completed trusted operation establishes scar eligibility.

A10 S0 exactly K_SOFT_PERSIST - 1 raw soft warnings followed by a clean observation writes no scar.

A11 S1 authorized hard structural failure writes one scar with REJECT_AS_IS.

A12 S2 authorized gate-effective soft degradation writes one scar with REQUIRE_EXTRA_PROOF.

A13 S3 authorized restoration failure writes one scar with REQUIRE_EXTRA_PROOF.

A14 M0 hard scar match rejects the same configuration as-is.

A15 M1 soft scar match requires extra proof and does not hard-reject by default.

A16 M2 similar but non-identical geometry beyond quantization boundary does not match under v1 exact policy.

A17 M3 same geometry with different failed_invariant_class matches the same scar.

A18 C0 repeated trusted failure increments failure_count.

A19 C1 repeated cheap rejected nominations do not increment failure_count.

A20 E0 elevation does not fire below T_SCAR_ELEVATE.

A21 E1 elevation fires when failure_count reaches T_SCAR_ELEVATE.

A22 E1 elevation event contains no semantic explanation field.

A23 R0 idle time alone does not retire an active scar.

A24 R1 successful cycles retire scar at T_SCAR_RETIRE_SUCCESS_CYCLES.

A25 R2 new trusted failure resets successful_cycles_since_last_seen to zero.

A26 The scar registry is not readable by the structural observer. This may be verified by
    structural-observer signature inspection, dependency inspection, or a positive isolation
    test showing that scar-registry contents cannot change structural-observer output.

A27 The scar registry does not alter live shape_integrity classification.

A28 The scar registry does not update C_success.

A29 No task text, route history, route outcome, wrong-bypass label, or semantic category enters the fingerprint payload.

A30 Every scar written has valid structural evidence, an available fingerprint, and completed prior authority.
```

## Verdict Logic

The verdict is evaluated in order.

### Step 0: Fingerprint Integrity

If any of A1 through A4 fails:

```text
verdict = INVALID_RUN
reason = fingerprint mechanism invalid
```

No scar-write result may be interpreted from a run with invalid fingerprint behavior.

### Step 1: Authority Boundary

If any of A5 through A10 fails:

```text
verdict = INVALID_RUN
reason = scar authority boundary invalid
```

The system must not proceed to scar-write claims if it cannot distinguish cheap rejection, evidence invalidity, transient soft warnings, and betrayed authority.

### Step 2: Scar Write Correctness

If any of A11 through A13 fails:

```text
verdict = NOT_SUPPORTED
reason = scar write behavior incorrect
```

### Step 3: Scar Match Correctness

If any of A14 through A17 fails:

```text
verdict = NOT_SUPPORTED
reason = scar match or response behavior incorrect
```

### Step 4: Count, Elevation, And Retirement

If any of A18 through A25 fails:

```text
verdict = NOT_SUPPORTED
reason = scar count, elevation, or retirement behavior incorrect
```

### Step 5: Separation Assertions

If any of A26 through A30 fails:

```text
verdict = INVALID_RUN
reason = scar separation or leakage violation
```

### Supported Result

If all assertions pass:

```text
verdict = SUPPORTED
```

A supported result means only that the v1 scar layer correctly enforces the rejected-configuration boundary under this synthetic scenario suite.

It does not validate shedding.

It does not validate lineage.

It does not validate prospective filtering.

It does not validate fuzzy scar matching.

## Required Output Files

The implementation must write:

```text
data/rejected_configuration_scar_v1_raw.csv
data/rejected_configuration_scar_v1_summary.csv
data/rejected_configuration_scar_v1_scar_registry.csv
data/rejected_configuration_scar_v1_assertions.csv
data/rejected_configuration_scar_v1_verdict.csv
data/rejected_configuration_scar_v1_run_record.txt
```

Recommended plots:

```text
plots/scar_v1_assertion_status.png
plots/scar_v1_write_boundary.png
plots/scar_v1_match_behavior.png
plots/scar_v1_elevation_retirement.png
```

Every plot must be reproducible from the written CSV files.

## Run Record

The run record must contain:

```text
script SHA-256
validation-plan SHA-256
scar-spec SHA-256
Python version
hashlib algorithm and provider information
OpenSSL version when used by Python hash provider
numpy version
pandas version
matplotlib version
run start and completion timestamps
parameter block
scenario list
assertion results
final verdict
```

## No Post-Hoc Changes

After implementation begins, none of the following may be changed without creating a new validation-plan version:

```text
fingerprint payload fields
field order
angle normalization
numeric quantization
rounding mode
scope representation
hash algorithm
authority threshold
scar write rules
scar response table
K_SOFT_PERSIST
T_SCAR_ELEVATE
T_SCAR_RETIRE_SUCCESS_CYCLES
matching policy
scenario definitions
assertions
verdict logic
```

A code correction that only makes implementation conform to this plan may be made without changing the plan, but the full primary run must be repeated.

## Interpretation Boundary

A supported result would validate only the v1 rejected-configuration scar boundary.

It would show that scars are written only for betrayed authority, that cheap failures vanish, that evidence invalidity does not scar the system, that exact scar matches affect authority as declared, and that elevation and retirement obey the frozen thresholds.

It would not show that the scar layer knows why a configuration failed.

It would not show that the system can predict bad configurations before trying them.

It would not show that a shed cell can regrow safely.

It would not show that lineage propagation is correct.

Those are later mechanisms.

## Freeze Condition

This validation plan may be marked frozen only after review confirms that:

```text
the fingerprint canonicalization is deterministic
the fingerprint tests precede scar-write interpretation
the authority threshold is explicit
non-authorized and invalid-evidence cases write no scar
transient soft warning below persistence writes no scar
hard and soft scar responses are separated
same geometry with different failed_invariant_class matches the same scar
failure_count increments only after repeated trusted failure
elevation and retirement rules are unambiguous
the scar registry is isolated from C_success and live shape_integrity
the verdict logic has no contradictory branch
```

No scar simulation code should be written until this review is complete.
