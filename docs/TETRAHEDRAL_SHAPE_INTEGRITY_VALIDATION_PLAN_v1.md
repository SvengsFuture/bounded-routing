# Tetrahedral Shape Integrity Validation Plan

**Version:** 1.0  
**Status:** Frozen — approved for implementation  
**Controlling architecture:** `TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1.md`  
**Controlling routing baseline:** bounded-routing v3, primary `K_REQUALIFY = 5`  
**Implementation artifact:** `scripts/bounded_routing_sim_v4.py`

**Freeze approval:** External review confirmed that all seven freeze conditions are satisfied. The arm isolation, observer inputs, invariant formulas, persistence and restoration semantics, arm-independent schedules, executable assertions, and verdict branches are frozen.

## Purpose

This plan freezes the first experiment for the live tetrahedral shape-integrity gate.

The experiment asks one narrow question:

> Can a live structural signal derived only from tetrahedral control-plane state revoke unsafe bypass authority earlier than the existing flat bounded-routing gates detect post-promotion route degradation?

This experiment does not attempt to prove the entire tetrahedral architecture.

It does not test whether the selected thresholds are optimal.

It does not permit post-run threshold adjustment.

It does not allow route outcomes, `C_success`, wrong-bypass labels, task-processing latency, or evaluator-only deformation labels to enter the structural observer.

The direct isolation comparison is V4-C against V4-D. Those two arms must be identical except that V4-D consumes the independent shape-integrity gate.

## Series Continuity

V1 showed that anti-oscillation gating can prevent repeated wrong bypasses when route confidence remains misleadingly high.

V2 showed that stale authority can be removed and earned back through fresh requalification evidence.

V3 showed that the flat gate stack did not revoke unsafe post-promotion authority earlier than simpler comparison controls under the tested relapse workload. The confidence gate remained the first blocking gate in the eligible borderline route instances.

V4 preserves the verified v3 routing mechanics and adds one isolated variable: a live structural gate in V4-D.

The v3 verdict remains unchanged regardless of the v4 result.

## Experimental Arms

| Arm | Label | Definition |
|---|---|---|
| V4-A | `A_FULL_ANALYSIS` | Every task uses full analysis. No bypass. |
| V4-B | `B_NAIVE_CACHE` | Bypass depends on route confidence only. |
| V4-C | `C_FLAT_BOUNDED` | The v3 requalifying bounded-routing arm with the full flat gate stack and `K_REQUALIFY = 5`, but no shape-integrity gate. |
| V4-D | `D_TETRAHEDRAL_GATE` | Identical to V4-C, with the independent shape-integrity gate added conjunctively. |

V4-C is the v3 `D_REQUALIFYING` mechanism under a new v4 label.

V4-D must inherit the same route state, task manifest, route outcomes, route-confidence updates, depreciation behavior, recovery behavior, anti-oscillation behavior, structural-cost behavior, and requalification rules as V4-C.

No route-level parameter may differ between V4-C and V4-D.

## Frozen Scope

The first experiment uses:

```text
scope_type = GLOBAL
scope_id = ACTIVE_TETRAHEDRAL_SUBSTRATE
```

Every tested route is treated as dependent on one shared tetrahedral substrate.

A valid non-admissible GLOBAL record therefore denies bypass for every route in V4-D.

This broad effect is not hidden. It must be reported through fallback rate, global-scope fallback cost, and lost-bypass-opportunity metrics.

A route that is individually healthy during a true GLOBAL deformation is not counted as a false revocation. It is counted as a cost of the declared GLOBAL scope assumption.

Route-specific and regional scope are outside v4.

## Frozen Inherited Routing Parameters

The following values are inherited from the verified v3 primary run and must remain unchanged.

`T_RECOVERY_BLACKOUT_MS` is retained in the complete inherited parameter block for auditability even though the V4-C and V4-D mechanisms do not consult the timer-bound recovery-blackout gate:

```text
SEEDS                     = [42, 99, 500, 777, 1337]
N_PATTERNS                = 8
DT_MS                     = 20.0

T_BYPASS                  = 0.75
T_DEPRECIATE              = 0.55
T_RECOVER_ARD             = 0.70
T_COST_MAX                = 1.5
ALPHA                     = 0.85
OBS_WINDOW_SIZE           = 20
DEPRECIATION_N            = 5
DEPRECIATION_M            = 10
RECOVER_K                 = 8
T_RETIRE_MS               = 60000.0
T_FLIP_COOLDOWN_MS        = 2000.0
MAX_FLIPS_PER_WINDOW      = 3
T_FLIP_WINDOW_MS          = 10000.0
T_RECOVERY_BLACKOUT_MS     = 5000.0

K_REQUALIFY               = 5

W_LAT                     = 0.30
W_ADM                     = 0.40
W_DEG                     = 0.20
W_STAB                    = 0.10

COST_BYPASS_NORMAL        = 0.3
COST_BYPASS_DRIFTED       = 0.8
COST_FULL_ANALYSIS        = 1.0
COST_BYPASS_FAILED        = 2.0

LATENCY_FULL_ANALYSIS     = 40.0
LATENCY_BYPASS_FAST       = 8.0
LATENCY_BYPASS_SLOW       = 25.0
LATENCY_NOISE_STD         = 3.0

PHASE_STABLE_END_MS       = 30000.0
PHASE_DRIFT_END_MS        = 60000.0
PHASE_FAULT_END_MS        = 80000.0
PHASE_RECOVERY_END_MS     = 110000.0
SIM_DURATION_MS           = 120000.0

Q_REQUALIFY_HIGH          = 0.92
Q_RELAPSE_FLOOR_5         = 0.25
Q_RELAPSE_FLOOR_6         = 0.15
T_REQUALIFY_WINDOW_MS     = 5000.0
T_RELAPSE_RAMP_MS         = 4000.0
T_OSC_PERIOD_MS           = 3000.0
Q_OSC_HIGH                = 0.90
Q_OSC_LOW                 = 0.20

CONTROL_PATTERNS          = [1, 2, 3, 4]
PERSISTENT_PATTERN        = 0
BORDERLINE_PATTERNS       = [5, 6, 7]
```

The fixed seed offsets remain:

```text
42   -> 0 ms
99   -> 500 ms
500  -> 1000 ms
777  -> 1500 ms
1337 -> 2000 ms
```

The structural-deformation onset for each seed is:

```text
deformation_onset_ms =
    PHASE_FAULT_END_MS
    + T_REQUALIFY_WINDOW_MS
    + SEED_RELAPSE_OFFSET_MS[seed]
```

The environment must never delay deformation because an arm promoted late.

A borderline route instance that does not complete v3 route requalification before its fixed deformation onset is ineligible for the primary matched efficacy claim and must be reported separately.

## Frozen V4 Structural Parameters

```text
SHAPE_OBSERVATION_INTERVAL_MS = 100.0
T_SHAPE_FRESHNESS_MS          = 120.0
K_SOFT_PERSIST                = 3
K_RESTORE                     = 3

AUTHORIZED_SOURCE_ID          = TETRAHEDRAL_COORDINATOR_V4
AUTHORIZED_OBSERVER_TYPE      = DETERMINISTIC_STRUCTURAL_OBSERVER
VERIFICATION_METHOD           = DETERMINISTIC_REPLAY_SHA256

T_ROLE_SEPARATION_SOFT_DEG    = 90.0
T_ROLE_SEPARATION_HARD_DEG    = 60.0

T_ROLE_IMBALANCE_SOFT         = 0.20
T_ROLE_IMBALANCE_HARD         = 0.45

T_COVERAGE_SOFT               = 0.75
T_COVERAGE_HARD               = 0.50

T_COORDINATOR_OFFSET_SOFT     = 0.15
T_COORDINATOR_OFFSET_HARD     = 0.35

T_PROBE_LATENCY_SKEW_SOFT     = 0.50

ACTIVE_SCOPE_TYPE             = GLOBAL
ACTIVE_SCOPE_ID               = ACTIVE_TETRAHEDRAL_SUBSTRATE

STRUCTURAL_DEFORMATION_MS     = 4000.0
EVIDENCE_INVALIDITY_MS        = 500.0
```

The primary run has no parameter sweep.

No threshold, persistence count, freshness interval, or verdict boundary may be changed after results are examined.

Sensitivity work, if justified by the primary result, belongs in a separately declared v4.1 plan.

## Decision Ordering Within Each Task

At each task timestamp, the harness must use this order:

```text
1. Apply any pre-generated structural-manifest event at the current time.
2. Produce a shape record if the current time is a shape-observation time.
3. Verify and classify the latest shape record.
4. Evaluate the ordinary V4-C route gates.
5. In V4-D only, conjunctively evaluate the shape gate.
6. Execute bypass or full analysis.
7. Update route-level SMS and ARD state from the task outcome.
8. Write the task row.
```

This ordering prevents the current task outcome from influencing the shape record used for that same task.

A shape record timestamp must be less than or equal to the routing-decision timestamp.

## Pre-Generated Artifacts

For every `(scenario_id, seed)` pair, the harness must create and save all manifests before any arm runs.

### Task Manifest

The task manifest contains the inherited v3 task stream and route-performance fields.

Required fields include:

```text
scenario_id
seed
task_key
time_ms
pattern_id
phase
route_class
route_quality
candidate_admissible
candidate_latency_ms
candidate_cost
deformation_onset_ms
deformation_clear_ms
```

`task_key` must be unique and identical across all four arms.

### Structural Input Manifest

The structural input manifest contains only control-plane state available to the observer.

Required fields include:

```text
scenario_id
seed
observation_key
observation_index
timestamp_ms
active_structural_epoch

fact_present
logic_present
coherence_present

fact_theta_deg
logic_theta_deg
coherence_theta_deg

fact_weight
logic_weight
coherence_weight

fact_coverage
logic_coverage
coherence_coverage

fact_probe_latency_ms
logic_probe_latency_ms
coherence_probe_latency_ms

fact_structural_error_state
logic_structural_error_state
coherence_structural_error_state

coordinator_x
coordinator_y

source_id
observer_type
scope_type
scope_id

verification_method
verification_reference
canonical_input_hash
```

The structural input manifest must not contain route correctness, `candidate_admissible`, route quality, route latency, bypass decisions, wrong-bypass labels, `C_success`, or arm identity.

### Deformation Schedule

The deformation schedule declares the structural intervention independently of arm state.

Required fields include:

```text
scenario_id
seed
deformation_type
deformation_onset_ms
deformation_clear_ms
repair_or_refresh_type
epoch_before
epoch_after
```

### Evaluator Ground Truth

Evaluator-only labels must be stored separately from the observer input.

Required fields include:

```text
scenario_id
seed
observation_key
ground_truth_class
ground_truth_active
expected_first_effective_observation
expected_gate_classification
expected_reconstruction
```

The observer and all arm objects must be structurally unable to access this file during execution.

## Structural State Model

The baseline specialist geometry is:

```text
Fact      theta =   0 degrees
Logic     theta = 120 degrees
Coherence theta = 240 degrees
```

Baseline weights are:

```text
Fact      = 1/3
Logic     = 1/3
Coherence = 1/3
```

Baseline coverage is:

```text
Fact      = 1.0
Logic     = 1.0
Coherence = 1.0
```

Baseline health-probe latency is generated in the manifest from a bounded structural-only band:

```text
8.0 ms <= role_probe_latency_ms <= 12.0 ms
```

The three baseline role points lie on the unit circle.

The coordinator baseline position is the centroid of the three role points.

The observer computes all invariant values from the structural input row. It does not receive precomputed invariant verdicts.

## Frozen Invariant Formulas

### Role Presence

```text
role_presence_pass =
    fact_present
    and logic_present
    and coherence_present
```

A valid observation confirming any specialist role as absent is a hard structural failure.

A missing role record is evidence invalidity, not confirmed absence.

### Pairwise Angular Separation

For each pair of role angles:

```text
circular_distance(a, b) =
    min(abs(a - b), 360 - abs(a - b))
```

Then:

```text
role_separation_min_deg =
    min(
        circular_distance(fact_theta_deg, logic_theta_deg),
        circular_distance(logic_theta_deg, coherence_theta_deg),
        circular_distance(coherence_theta_deg, fact_theta_deg)
    )
```

Classification:

```text
role_separation_min_deg < 60.0
    -> hard structural failure

60.0 <= role_separation_min_deg < 90.0
    -> raw soft angular degradation

role_separation_min_deg >= 90.0
    -> inside v4 bound
```

### Role Imbalance

The three weights must be non-negative and must sum to 1.0 within floating-point tolerance `1e-9`.

```text
role_imbalance =
    max(fact_weight, logic_weight, coherence_weight)
    - min(fact_weight, logic_weight, coherence_weight)
```

Classification:

```text
role_imbalance > 0.45
    -> hard structural failure

0.20 < role_imbalance <= 0.45
    -> raw soft role imbalance

role_imbalance <= 0.20
    -> inside v4 bound
```

An invalid weight vector is evidence invalidity.

### Coverage

```text
coverage_min =
    min(fact_coverage, logic_coverage, coherence_coverage)
```

Classification:

```text
coverage_min < 0.50
    -> hard structural failure

0.50 <= coverage_min < 0.75
    -> raw soft coverage degradation

coverage_min >= 0.75
    -> inside v4 bound
```

Coverage values must lie in `[0.0, 1.0]`. An out-of-range value is evidence invalidity.

### Coordinator Alignment

Role points are:

```text
role_x = cos(theta)
role_y = sin(theta)
```

The role centroid is the arithmetic mean of the three role points.

```text
coordinator_offset =
    euclidean_distance(
        coordinator_position,
        role_centroid
    )
```

Classification:

```text
coordinator_offset > 0.35
    -> hard structural failure

0.15 < coordinator_offset <= 0.35
    -> raw soft coordinator degradation

coordinator_offset <= 0.15
    -> inside v4 bound
```

### Health-Probe Latency Skew

Only control-plane health-probe latency may be used.

```text
probe_latency_skew =
    (
        max(role_probe_latencies)
        - min(role_probe_latencies)
    )
    / median(role_probe_latencies)
```

Classification:

```text
probe_latency_skew > 0.50
    -> raw soft latency-skew degradation

probe_latency_skew <= 0.50
    -> inside v4 bound
```

V4 does not define a hard latency-skew threshold.

A missing, non-finite, zero, or negative probe-latency value is evidence invalidity.

### Structural Error State

A valid role record containing:

```text
structural_error_state = FAILED
```

is a hard structural failure.

`WARN` is recorded diagnostically but has no independent gate effect in v4 unless another frozen invariant also crosses its bound.

## Canonical Invariant Evaluation Order

The canonical order is:

```text
1. ROLE_PRESENCE
2. STRUCTURAL_ERROR_STATE
3. ROLE_SEPARATION
4. COVERAGE
5. COORDINATOR_ALIGNMENT
6. ROLE_IMBALANCE
7. HEALTH_PROBE_LATENCY_SKEW
```

`all_failed_invariants` contains every gate-effective invariant violation in the current record.

`first_failed_invariant` is the lowest-index member of `all_failed_invariants` under this order.

Raw soft warnings that have not yet satisfied `K_SOFT_PERSIST` are stored separately as:

```text
raw_soft_warnings
```

They do not appear in `all_failed_invariants` until their persistence requirement is satisfied.

## Record Verification

Every observation uses:

```text
verification_method = DETERMINISTIC_REPLAY_SHA256
```

The manifest writer must canonicalize the structural input fields in a declared field order and compute `canonical_input_hash`.

The observer must write:

```text
verification_reference = observation_key
evidence_hash = canonical_input_hash
```

The gate independently reconstructs the same canonical payload and recomputes the hash.

A record is verifiable only when:

```text
verification_method is accepted
and verification_reference resolves to the correct observation
and recomputed_hash == evidence_hash
```

A bare `verification_status = VERIFIED` is insufficient.

## Evidence-Validity Classification

The following conditions produce evidence invalidity:

```text
no current structural record
unauthorized source
unauthorized observer type
missing verification method
missing verification reference
failed hash replay
record age greater than 120 ms
record epoch not equal to active epoch
scope type not GLOBAL
scope id not ACTIVE_TETRAHEDRAL_SUBSTRATE
missing required structural field
non-finite required structural value
invalid weight vector
out-of-range coverage value
invalid probe-latency value
```

Evidence invalidity produces:

```text
integrity_state = UNKNOWN
shape_gate_classification = EVIDENCE_INVALID
bypass_allowed_by_shape = false
authority_state = NOT_AUTHORIZED
fallback_action = FULL_ANALYSIS
reconstruction_triggered = false
```

Evidence invalidity must not populate `all_failed_invariants` with a structural-failure claim.

## Hard-Failure Classification

When valid evidence contains one or more hard invariant failures:

```text
integrity_state = FAILED
shape_gate_classification = CONFIRMED_HARD_FAILURE
bypass_allowed_by_shape = false
authority_state = REVOKED
fallback_action = FULL_ANALYSIS
```

Revocation occurs on the first task decision using the first valid hard-failing record.

`K_SOFT_PERSIST` and `K_RESTORE` must not delay this response.

V4-D may log that a recovery trigger would be eligible for evaluation, but the shape gate must not autonomously alter the pre-generated repair schedule.

## Soft-Degradation Classification

Each soft invariant maintains an independent consecutive-observation counter.

A raw soft condition increments only its own counter.

A clean observation for that invariant resets its counter to zero.

When any soft counter reaches:

```text
K_SOFT_PERSIST = 3
```

the record becomes gate-effective:

```text
integrity_state = DEGRADED
shape_gate_classification = SOFT_DEGRADATION
bypass_allowed_by_shape = false
authority_state = FULL_ANALYSIS
fallback_action = FULL_ANALYSIS
```

For v4, every soft-degradation type maps to `FULL_ANALYSIS`.

`BLOCKED` and `REQUALIFYING` remain valid architecture modes but are intentionally not used in the first experiment. Using one common response prevents response-mode differences from becoming a second changed variable.

A raw soft condition lasting one or two consecutive observations does not deny bypass.

## Restoration

A restoration period begins only after V4-D has entered a non-admissible shape state.

When no restoration period is active:

```text
restoration_requirement_satisfied = true
```

After the invalidity or deformation clears, authority remains denied until:

```text
K_RESTORE = 3
```

consecutive observations are:

```text
present
authorized
verifiable
fresh
in the active epoch
in GLOBAL scope
free of hard failures
free of gate-effective soft degradation
free of raw soft warnings
```

Requiring restoration observations to be free of raw soft warnings is a deliberate plan-level tightening beyond the minimum architecture language. V4 restoration requires a genuinely clean structural window, not merely the absence of a gate-effective soft-degradation state.

The first clean record counts as restoration observation one.

Authority may be restored immediately after the third qualifying clean record, subject to every ordinary route gate also passing.

Any new evidence invalidity, raw soft warning, gate-effective soft degradation, hard failure, or structural epoch change:

```text
exits the current restoration attempt
resets restore_count to zero
enters the newly applicable classification
```

A structural epoch change always resets `restore_count`.

Route requalification and shape restoration are separate conjunctive requirements:

```text
K_REQUALIFY = 5
    governs route-level fresh evidence

K_RESTORE = 3
    governs structural-gate restoration
```

Neither count may satisfy the other.

## Recovery and Epoch Handling

The shape gate does not control the environment.

For hard-deformation scenarios, the deformation manifest schedules a common repair event at:

```text
deformation_clear_ms =
    deformation_onset_ms
    + 4000 ms
```

At that event:

```text
active_structural_epoch increments by 1
structural inputs return to baseline
all earlier shape records become invalid
K_RESTORE begins from zero
```

The repair timestamp is identical across all arms and must not depend on whether any arm revoked, bypassed, or reconstructed.

For soft-degradation scenarios, the structural state returns to baseline after 4000 ms without an epoch change.

For evidence-invalidity scenarios, valid evidence resumes after 500 ms without claiming that a reconstruction occurred. The epoch changes only in the explicit epoch-mismatch scenario.

No evidence-invalidity event may trigger reconstruction.

## Route-Performance Workload

The task stream remains manifest-driven.

During the clean requalification interval, borderline patterns 5, 6, and 7 use deterministic admissible observations exactly as in v3 so route promotion can occur before the fixed onset.

For structural-deformation scenarios that are intended to test earlier unsafe-authority withdrawal, the post-onset route-quality profiles remain:

```text
Pattern 5:
    linear ramp from 0.92 to 0.25 over 4000 ms

Pattern 6:
    immediate step to 0.15

Pattern 7:
    oscillation between 0.90 and 0.20
    with a 3000 ms period
```

Post-onset candidate admissibility remains pre-generated from those route-quality profiles.

For the clean-control scenario, transient-soft scenario, and evidence-invalidity suite, patterns 5, 6, and 7 remain at:

```text
route_quality = 0.92
candidate_admissible = true
```

through the test window.

This prevents evidence-invalidity behavior or a sub-persistence soft warning from being misreported as successful unsafe-route detection.

## Structural-Deformation Scenarios

Each scenario is run independently for all five seeds.

### D0 Clean Control

```text
scenario_id = D0_CLEAN_CONTROL
```

No structural field crosses a bound.

No route-quality relapse occurs.

Expected V4-D behavior:

```text
shape gate remains ADMISSIBLE
no shape-caused fallback
no restoration period
```

### D1 Transient Soft Imbalance

```text
scenario_id = D1_TRANSIENT_SOFT_IMBALANCE
active_observation_count = 2
nominal_interval_ms = 200
weights = [0.58, 0.21, 0.21]
role_imbalance = 0.37
```

The manifest activates the deformation by structural-observation index rather than by floating-point interval membership. It is active on exactly two scheduled observation rows and returns to baseline before the third scheduled observation.

This crosses the soft imbalance bound but not the hard bound.

It clears before `K_SOFT_PERSIST = 3`.

No route-quality relapse occurs.

Expected V4-D behavior:

```text
raw soft warning recorded
no gate-effective degradation
no shape-caused fallback
no restoration period
```

### D2 Persistent Soft Imbalance

```text
scenario_id = D2_PERSISTENT_SOFT_IMBALANCE
duration = 4000 ms
weights = [0.58, 0.21, 0.21]
role_imbalance = 0.37
```

The route-quality relapse workload is active.

Expected V4-D behavior:

```text
first two soft observations do not deny bypass
third consecutive soft observation enters FULL_ANALYSIS
revocation delay from onset = 200 ms
same-epoch K_RESTORE required after clear
```

### D3 Persistent Health-Probe Latency Skew

```text
scenario_id = D3_PERSISTENT_PROBE_LATENCY_SKEW
duration = 4000 ms
probe latencies = [10 ms, 10 ms, 18 ms]
probe_latency_skew = 0.80
```

The route-quality relapse workload is active.

Expected V4-D behavior:

```text
third consecutive soft observation enters FULL_ANALYSIS
revocation delay from onset = 200 ms
same-epoch K_RESTORE required after clear
```

### D4 Confirmed Specialist-Role Absence

```text
scenario_id = D4_HARD_ROLE_ABSENCE
duration = 4000 ms
coherence_present = false
```

The record remains otherwise present and verifiable, so this is confirmed absence rather than missing evidence.

The route-quality relapse workload is active.

Expected V4-D behavior:

```text
FAILED on first valid observation
immediate revocation
epoch increment at manifest repair
new-epoch K_RESTORE required
```

### D5 Hard Angular Compression

```text
scenario_id = D5_HARD_ANGULAR_COMPRESSION
duration = 4000 ms
angles = [0 degrees, 50 degrees, 240 degrees]
minimum pairwise separation = 50 degrees
```

The route-quality relapse workload is active.

Expected V4-D behavior:

```text
FAILED on first valid observation
immediate revocation
epoch increment at manifest repair
new-epoch K_RESTORE required
```

### D6 Hard Coverage Loss

```text
scenario_id = D6_HARD_COVERAGE_LOSS
duration = 4000 ms
coverage = [0.40, 1.00, 1.00]
```

The route-quality relapse workload is active.

Expected V4-D behavior:

```text
FAILED on first valid observation
immediate revocation
epoch increment at manifest repair
new-epoch K_RESTORE required
```

### D7 Hard Coordinator Offset

```text
scenario_id = D7_HARD_COORDINATOR_OFFSET
duration = 4000 ms
baseline role centroid = [0.00, 0.00]
coordinator position = [0.45, 0.00]
coordinator_offset = 0.45
T_COORDINATOR_OFFSET_HARD = 0.35
```

Therefore:

```text
coordinator_offset = 0.45 > 0.35
```

The route-quality relapse workload is active.

Expected V4-D behavior:

```text
FAILED on first valid observation
immediate revocation
epoch increment at manifest repair
new-epoch K_RESTORE required
```

### D8 Hard Role Dominance

```text
scenario_id = D8_HARD_ROLE_DOMINANCE
duration = 4000 ms
weights = [0.75, 0.125, 0.125]
role_imbalance = 0.625
```

The route-quality relapse workload is active.

Expected V4-D behavior:

```text
FAILED on first valid observation
immediate revocation
epoch increment at manifest repair
new-epoch K_RESTORE required
```

## Evidence-Invalidity Scenarios

Each evidence-invalidity scenario lasts 500 ms and uses a clean route-performance workload.

### E1 Missing Record

No new record is emitted during the invalidity interval.

The previous record becomes stale after 120 ms.

Expected behavior:

```text
deny bypass when freshness expires
classification = EVIDENCE_INVALID
no structural-failure claim
no reconstruction
K_RESTORE after valid evidence resumes
```

### E2 Unauthorized Source

```text
source_id = UNAUTHORIZED_COORDINATOR
```

Expected behavior:

```text
immediate fail-closed denial
classification = EVIDENCE_INVALID
no reconstruction
```

### E3 Failed Verification

The record hash is intentionally corrupted after record creation.

Expected behavior:

```text
hash replay fails
classification = EVIDENCE_INVALID
no reconstruction
```

### E4 Stale Timestamp

A record is emitted with:

```text
timestamp_ms =
    current_observation_time_ms
    - 121 ms
```

Expected behavior:

```text
record age exceeds freshness bound
classification = EVIDENCE_INVALID
no reconstruction
```

### E5 Epoch Mismatch

At invalidity onset, the active epoch changes from 1 to 2 while emitted records continue to claim epoch 1 for 500 ms.

Expected behavior:

```text
classification = EVIDENCE_INVALID
no reconstruction caused by mismatch alone
restore_count reset by epoch change
K_RESTORE uses only valid epoch-2 records
```

### E6 Scope Mismatch

```text
scope_type = ROUTE_CLASS
scope_id = BORDERLINE_RELAPSE
```

Expected behavior:

```text
classification = EVIDENCE_INVALID
GLOBAL applicability not established
no reconstruction
```

## Matched Comparison Windows

### Eligibility Window

For each `(scenario_id, seed, pattern_id)` where `pattern_id` is 5, 6, or 7:

```text
eligible_for_primary_comparison =
    V4-C route requalified before fixed deformation_onset_ms
```

Because V4-C and V4-D are route-mechanically identical before the shape gate becomes non-admissible, their pre-onset route-requalification timestamps must match. Any V4-D mismatch is an assertion failure under A24 rather than a second eligibility condition.

Ineligible instances are reported but excluded from the primary efficacy calculation.

### Primary Deformation Exposure Window

For D2 through D8:

```text
deformation_onset_ms <= task_time_ms < deformation_clear_ms
```

Only eligible pattern 5, 6, and 7 task keys enter the primary wrong-bypass comparison.

Window membership comes only from manifest timestamps and task keys.

### Structural Restoration Window

For D2 through D8:

```text
deformation_clear_ms <= task_time_ms < deformation_clear_ms + 1000 ms
```

This window measures `K_RESTORE`, epoch handling, and lost bypass opportunities during restoration.

### Clean Cost Window

The clean cost window includes all tasks outside any active deformation, invalidity, or restoration period.

This window is used for the suppression check.

### GLOBAL Scope Cost Window

During a true structural deformation, tasks from control patterns 1 through 4 are measured separately.

Their V4-D fallback is reported as GLOBAL-scope cost, not false revocation.

## Primary Metrics

The run must report at least:

```text
time_to_first_raw_soft_warning_ms
time_to_effective_structural_detection_ms
time_to_shape_authority_revocation_ms
time_to_flat_gate_revocation_ms
revocation_lead_ms

tasks_exposed_before_shape_revocation
wrong_bypasses_after_deformation
wrong_bypass_rate_over_bypasses
wrong_bypass_rate_over_matched_tasks

bypass_count
fallback_count
fallback_rate
lost_bypass_opportunities
global_scope_fallback_cost

false_revocations_clean
false_revocations_transient_soft
missed_hard_revocations
missed_persistent_soft_revocations

evidence_invalidity_denials
evidence_invalidity_misclassified_as_failure
unnecessary_reconstruction_triggers

all_failed_invariants
first_failed_invariant
first_blocking_gate

shape_record_age_ms
verification_pass
epoch_match
scope_match

restore_count
K_restore_resets
restoration_time_ms
```

Wrong-bypass counts and rates must be reported over identical matched task keys.

A zero-bypass denominator must produce `NA`, not zero.

## Required Assertions

Any failed assertion invalidates the affected run.

```text
A1  All manifests are generated and saved before any arm executes.

A2  Task-key sets and task-manifest values are identical across V4-A through V4-D.

A3  Structural-input keys and values are identical across all arms.

A4  Deformation onset, clear, repair, and epoch schedules are independent of arm state.

A5  The observer receives no arm identity, bypass decision, route correctness,
    wrong-bypass label, C_success value, route-performance latency, or future task field.

A6  The evaluator ground-truth file is not accessible to the observer or arm objects.

A7  Identical structural inputs produce byte-identical shape records across arms.

A8  Every shape record used by a decision has timestamp_ms <= decision_time_ms.

A9  health_probe_latency_ms is sourced only from the structural manifest and never
    from candidate_latency_ms or executed task latency.

A10 integrity_score is absent from the v4 bypass-decision function.

A11 Every admissible record has an accepted verification method, resolvable reference,
    and passing independently recomputed SHA-256 hash.

A12 The active scope is exactly GLOBAL / ACTIVE_TETRAHEDRAL_SUBSTRATE.

A13 Evidence invalidity produces UNKNOWN / EVIDENCE_INVALID and does not populate a
    confirmed structural-failure claim.

A14 Evidence invalidity alone never triggers reconstruction.

A15 A valid hard failure denies bypass on the first task using the first hard-failing record.

A16 K_SOFT_PERSIST and K_RESTORE are never consulted in the hard-revocation branch.

A17 D1 produces fewer than K_SOFT_PERSIST consecutive raw soft warnings and zero
    shape-caused denials.

A18 D2 and D3 produce their first shape-caused denial on the third consecutive soft observation.

A19 restoration_requirement_satisfied is true before any non-admissible shape period exists.

A20 Every new invalidity, raw soft warning, effective degradation, hard failure, or epoch
    change resets K_RESTORE exactly as declared.

A21 first_failed_invariant equals the lowest-index active invariant in the canonical order.

A22 Primary matched-window task-key sets are identical across all four arms.

A23 Every primary eligible route instance completed route requalification before its fixed
    manifest deformation onset. Ineligible instances are excluded and reported.

A24 V4-C and V4-D route state is identical through the last decision before the shape gate
    first becomes non-admissible.

A25 No arm outcome changes a later structural record, deformation duration, repair time,
    epoch transition, or evaluator label.

A26 The verdict-branch function passes synthetic self-tests for INVALID, INCONCLUSIVE,
    NOT_SUPPORTED, PARTIAL_SUPPORT, and SUPPORTED before arm execution.
```

## Workload-Discrimination Check

The primary efficacy verdict requires a discriminating workload.

The run is `INCONCLUSIVE` when either condition holds:

```text
fewer than 12 of the 15 possible seed-pattern route instances are eligible
```

or:

```text
V4-C records no wrong bypass in more than 50 percent of eligible
D2-through-D8 scenario-route instances
```

The experiment must not claim superiority when the flat arm was not meaningfully exposed.

## Suppression Check

Before safety improvement is evaluated, the harness must verify that V4-D is not winning by remaining broadly disabled outside declared non-admissible periods.

The suppression check passes only when:

```text
V4-D clean-window bypass count
    >= 90 percent of V4-C clean-window bypass count
```

and:

```text
V4-D clean-window false shape revocations = 0
```

and:

```text
D1 transient-soft shape-caused denials = 0
```

Fallback during a true GLOBAL deformation is not part of the clean suppression denominator. It is reported separately as GLOBAL-scope cost.

Failure of the suppression check produces `NOT_SUPPORTED`.

## Frozen Verdict Logic

The verdict is evaluated in this order.

### Step 0: Assertion Integrity

Any assertion failure:

```text
verdict = INVALID_RUN
```

No efficacy claim may be made from that run.

### Step 1: Workload Discrimination

Failure of the workload-discrimination check:

```text
verdict = INCONCLUSIVE
```

### Step 2: Suppression

Failure of the suppression check:

```text
verdict = NOT_SUPPORTED
reason = apparent improvement depends on excessive suppression
```

### Step 3: Structural Correctness

The following must all hold:

```text
D0 clean-control shape revocations = 0

D1 transient-soft shape revocations = 0

D2 and D3 effective soft detection occurs exactly at the third
consecutive soft observation in every valid instance

D4 through D8 hard revocation occurs on the first valid hard-failing record
in every valid instance

E1 through E6 deny bypass whenever their declared invalidity is active

E1 through E6 produce zero structural-collapse classifications

E1 through E6 produce zero reconstruction triggers

K_RESTORE never delays a hard revocation
```

Failure of any structural-correctness condition:

```text
verdict = NOT_SUPPORTED
```

### Step 4: Primary Efficacy

D0 and D1 are excluded from the wrong-bypass efficacy comparison because their route-performance workload remains clean and therefore contains no unsafe bypass authority to withdraw.

For `SUPPORTED`, all conditions must hold across eligible D2-through-D8 matched instances:

```text
V4-D wrong bypass count
    <= 50 percent of V4-C wrong bypass count

V4-D revokes earlier than V4-C
    in at least 80 percent of comparable instances

median revocation_lead_ms
    >= 500 ms

median tasks_exposed_before_shape_revocation:
    hard scenarios <= 1 task
    persistent-soft scenarios <= 10 tasks

paired bootstrap 95 percent confidence interval
for (V4-C wrong bypasses - V4-D wrong bypasses)
has lower bound > 0
```

The paired bootstrap uses 10000 resamples of eligible `(scenario_id, seed, pattern_id)` instances with replacement and seed-scenario-pattern as the indivisible sampling unit.

When all Step 4 conditions pass:

```text
verdict = SUPPORTED
```

### Step 5: Partial Support

When structural correctness and suppression pass, but the full support boundary does not, the result is `PARTIAL_SUPPORT` only when all of the following hold:

```text
V4-D wrong bypass reduction is at least 20 percent

V4-D revokes earlier than V4-C
    in at least 60 percent of comparable instances

median revocation_lead_ms > 0

V4-D clean-window bypass count
    >= 85 percent of V4-C
```

Otherwise:

```text
verdict = NOT_SUPPORTED
```

## Required Output Files

The implementation must write:

```text
data/bounded_routing_v4_raw.csv
data/bounded_routing_v4_summary.csv
data/bounded_routing_v4_per_instance.csv
data/bounded_routing_v4_matched_comparison.csv
data/bounded_routing_v4_structural_records.csv
data/bounded_routing_v4_assertions.csv
data/bounded_routing_v4_verdict.csv
data/bounded_routing_v4_run_record.txt

data/manifest_task_seed{seed}_{scenario_id}_v4.csv
data/manifest_structural_seed{seed}_{scenario_id}_v4.csv
data/manifest_deformation_seed{seed}_{scenario_id}_v4.csv
data/ground_truth_seed{seed}_{scenario_id}_v4.csv
```

The required plots are:

```text
plots/v4_revocation_timeline.png
plots/v4_wrong_bypass_matched.png
plots/v4_structural_detection_by_scenario.png
plots/v4_clean_suppression_check.png
plots/v4_global_scope_cost.png
plots/v4_restoration_timeline.png
plots/v4_evidence_invalidity_behavior.png
```

Every plot must be reproducible from the written CSV files.

## Run Record

The run record must contain:

```text
script SHA-256
validation-plan SHA-256
architecture-spec SHA-256
Python version
hashlib algorithm and provider information
OpenSSL version when used by the Python hash provider
numpy version
pandas version
matplotlib version
versions of any additional v4-specific dependencies
run start and completion timestamps
seed list
full inherited parameter block
full v4 parameter block
scenario list
manifest hashes
assertion results
eligible and ineligible instance counts
verdict branch taken
final verdict
```

## No Post-Hoc Changes

After implementation begins, none of the following may be changed without creating a new validation-plan version:

```text
arm definitions
route parameters
shape-observation interval
freshness interval
invariant formulas
hard or soft thresholds
persistence count
K_RESTORE
scenario values
scenario durations
manifest timing
scope
verification method
matched windows
assertions
suppression boundary
workload-discrimination boundary
verdict thresholds
seed list
```

A code correction that only makes the implementation conform to this plan may be made without changing the plan, but the correction must be documented in the run record and the entire primary run must be repeated from fresh manifests.

## Interpretation Boundaries

A supported result would show only that this declared structural observer and gate withdrew authority earlier than the inherited flat gate stack under this synthetic matched workload.

It would not establish that these thresholds are optimal.

It would not establish that GLOBAL scope is appropriate for a real deployment.

It would not establish that the coordinator can be trusted in a distributed system.

It would not prove that role geometry alone is sufficient for every failure class.

It would not establish real-world latency or production reliability.

A not-supported result would not disprove the broader tetrahedral architecture. It would show that this first frozen structural signal, threshold set, or workload did not produce the declared discriminating result.

An inconclusive result would mean the workload did not create enough matched unsafe-authority exposure to test the claim.

## Freeze Condition

This plan may be marked frozen only after external review confirms that:

```text
the direct comparison changes only the shape gate
the structural observer has no route-outcome leakage path
the invariant formulas are implementable
the persistence and restoration semantics are unambiguous
the scenario schedules are arm-independent
the assertions are executable
the verdict logic has no contradictory branch
```

No v4 simulation code should be written until that review is complete.
