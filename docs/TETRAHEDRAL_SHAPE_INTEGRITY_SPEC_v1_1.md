# Tetrahedral Shape Integrity Specification

**Version:** 1.1  
**Status:** Architecture frozen for validation planning  
**Next required artifact:** `TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md`

## Purpose

This document defines a first-pass architecture for a live tetrahedral shape-integrity signal that can govern bounded routing.

The goal is not to create another blended confidence score.

The goal is to preserve the distinction between historical route performance and current structural condition.

`C_success` answers how well a route has performed over time.

`shape_integrity` answers whether the tetrahedral substrate is currently intact enough to permit bypass authority.

The signal defined here is intended to sit between the tetrahedral substrate and the bounded-routing authority layer.

It does not replace route confidence.

It does not replace recovery.

It does not reconstruct the tetrahedron.

It reports whether the current structural state remains admissible for the route or system scope being evaluated.

## Governing Principle

Bounded routing is the authority layer for the tetrahedral recovery architecture.

The tetrahedral substrate produces live structural evidence.

The routing layer grants, maintains, or revokes bypass authority.

The recovery layer reconstructs the substrate when confirmed recovery invariants fail.

The shape-integrity signal must remain independent of route confidence and must fail closed when its evidence is missing, stale, unverifiable, epoch-mismatched, or outside the applicable scope.

Failing closed does not by itself prove that the substrate is structurally broken.

The architecture must distinguish between an inability to establish authority and a confirmed structural failure. Evidence invalidity denies bypass but must not automatically trigger reconstruction.

## Structural Model

The tetrahedral substrate contains three specialist vertices and one coordinator.

The specialist roles are:

- Fact
- Logic
- Coherence

The coordinator is not treated as a fourth peer role.

It observes, reconciles, or derives the continuing integrity of the role-separated structure.

The structural signal should preserve both role state and relational geometry.

A healthy tetrahedral state is not defined only by the condition of each role in isolation.

It also depends on whether the roles remain distinct, balanced, mutually compatible, and correctly related to the coordinator.

## Required Inputs

The shape-integrity record should be derived from live control-plane structural observations.

For the first experiment, the observer must not consume route correctness, bypass success, task-processing latency, `C_success`, wrong-bypass labels, or any field derived from those outcomes.

### Role-State Evidence

Each specialist role should expose a bounded structural state record.

At minimum:

```text
role_id
timestamp_ms
structural_epoch
presence_state
health_state
health_probe_latency_ms
control_plane_load_or_stress
structural_error_state
recovery_state
```

`health_probe_latency_ms` means the time required for the specialist role to answer a coordinator health probe or structural query.

It does not mean task-processing latency, route latency, answer latency, or any route-performance measure already represented in the bounded-routing system.

`structural_error_state` may describe a role-process, communication, state, or recovery error. It must not encode whether a route answer was correct or whether a bypass was wrong.

`confidence_or_quality` is intentionally excluded from the first-experiment role-state record because it could become a route-outcome leakage path.

The role identity and structural epoch must remain explicit.

### Relational Evidence

The system should preserve evidence about the structural relationships among Fact, Logic, and Coherence.

Candidate relational measures include:

```text
pairwise angular separation
role-collapse distance
role-overlap score
role-dominance imbalance
structural-state disagreement
health-probe latency skew
coverage loss
coordinator offset
```

Every relational measure used in the first experiment must be computable from structural state available at the decision time.

`health-probe latency skew` means skew among control-plane health-probe responses. It must not reuse task-processing latency from the route-performance system.

`structural-state disagreement` must describe disagreement among role-state or geometry observations. It must not be calculated from task correctness or route outcomes.

The initial architecture should not assume that one measure is sufficient.

### Coordinator Evidence

The coordinator should publish an authorized structural observation or signed equivalent.

At minimum:

```text
source_id
observer_type
timestamp_ms
structural_epoch
scope_type
scope_id
verification_status
verification_method
verification_reference
fact_state_ref
logic_state_ref
coherence_state_ref
relational_evidence
shape_integrity_state
all_failed_invariants
first_failed_invariant
```

The coordinator record must be auditable.

A scalar may be logged for diagnostic analysis, but the routing gate must not use that scalar in the v4 bypass decision.

The underlying evidence and individual invariant results must remain available.

## Shape-Integrity Record

A provisional shape-integrity record is:

```text
ShapeIntegrityRecord:
  record_id                 : str
  source_id                 : str
  observer_type             : str
  timestamp_ms              : float
  structural_epoch          : str or int
  scope_type                : str
  scope_id                  : str
  fact_state                : structured record
  logic_state               : structured record
  coherence_state           : structured record
  relational_evidence       : structured record
  coordinator_result        : structured record
  integrity_state           : enum
  integrity_score           : optional float, diagnostic only
  all_failed_invariants     : list[str]
  first_failed_invariant    : optional str
  verification_status       : enum
  verification_method       : str
  verification_reference    : str
  evidence_hash             : optional str
```

The `integrity_state` should be one of:

```text
ADMISSIBLE
DEGRADED
FAILED
UNKNOWN
```

`UNKNOWN` is fail-closed.

A route may bypass only when the record is `ADMISSIBLE` and every provenance, freshness, epoch, scope, and verification requirement also passes.

`integrity_score` is diagnostic-only in v4. It may be recorded for post-run analysis, but it must not participate in the bypass decision, override a failed invariant, repair an invalid record, or restore authority.

`all_failed_invariants` is the authoritative set of invariant failures observed in the record.

`first_failed_invariant` must be selected from that set using a canonical invariant evaluation order declared before the experiment. It must not depend on incidental source-code ordering.

## Three-Way Gate Classification

The gate must distinguish three different classes of non-admissible condition.

### Evidence Invalidity

Evidence invalidity means the gate cannot establish that bypass is authorized.

Examples include:

```text
missing structural record
unauthorized source
missing verification path
failed verification
stale record
epoch mismatch
scope mismatch
missing required evidence reference
```

The required authority response is fail-closed denial of bypass.

The normal downstream action is to request or await valid evidence and execute the declared safe fallback.

Evidence invalidity must not, by itself, be classified as tetrahedral collapse and must not, by itself, trigger substrate reconstruction.

### Confirmed Hard Structural Failure

A confirmed hard structural failure means valid structural evidence shows that a hard invariant has failed.

Examples include:

```text
confirmed specialist-role absence
confirmed role collapse
coverage below the declared minimum
hard coordinator-alignment failure
coordinator result marked FAILED from valid evidence
another predeclared hard invariant violation
```

The required authority response is immediate revocation.

A confirmed hard structural failure may also satisfy a separately declared recovery trigger, but routing revocation and substrate reconstruction remain distinct decisions.

### Soft Structural Degradation

Soft structural degradation means valid evidence shows movement toward or across a predeclared soft bound without satisfying a hard-failure condition.

Examples include:

```text
rising role imbalance
increasing angular deviation
growing health-probe latency skew
increasing structural-state disagreement
approaching coverage threshold
```

Each soft-degradation type must map deterministically to one declared response mode:

```text
BLOCKED
FULL_ANALYSIS
REQUALIFYING
```

The mapping, entry rule, exit rule, persistence requirement, and authority effect must be declared in the validation plan before the run.

All three soft-degradation modes deny bypass while active. No mode may silently preserve bypass authority through a hidden score adjustment.

## Independent Gate Logic

The shape-integrity gate should be evaluated independently of `C_success`.

A provisional decision sequence is:

```text
1. Is a structural record present?
2. Is the source authorized?
3. Is a declared verification path present?
4. Does verification pass?
5. Is the record fresh?
6. Does the structural epoch match the active substrate?
7. Does the scope apply to the system being evaluated?
8. Is the integrity state ADMISSIBLE?
9. Are all required invariants inside bounds?
10. Has the restoration requirement, when applicable, been satisfied?
```

Failure at steps 1 through 7 is evidence invalidity.

Failure at steps 8 or 9 must be classified from valid structural evidence as either confirmed hard structural failure or soft structural degradation.

Step 10 applies only when authority is being restored after a non-admissible period. It has no effect on revocation speed.

When no restoration period is active, `restoration_requirement_satisfied` is vacuously true. The absence of a restoration record in an always-admissible state must not be treated as evidence invalidity.

If a new evidence-invalidity, soft-degradation, or confirmed hard-failure event occurs during restoration, the system exits the restoration period immediately, resets the restoration count, and enters the response required by the new classification.

If any required answer is no, bypass authority is denied.

The gate must not repair, average away, or reinterpret a failed structural record in order to preserve bypass.

## Candidate Structural Invariants

The first implementation should preserve invariant categories rather than prematurely freeze one final formula.

### Role Presence

All three specialist roles must be present and observable.

```text
fact_present = true
logic_present = true
coherence_present = true
```

An absent record or unobservable role may produce evidence invalidity or `UNKNOWN`.

A valid observation confirming that a specialist role is structurally absent may produce `FAILED` and immediate revocation.

The validation plan must distinguish those cases.

### Role Distinction

The three specialist roles must remain structurally distinct.

A role-collapse measure should detect when two roles become functionally or geometrically indistinguishable.

Candidate form:

```text
role_separation_min >= T_role_separation
```

The first experiment should use a structural or geometric distinction measure that does not depend on route correctness.

### Balance

No specialist role should dominate the substrate beyond a declared tolerance.

Candidate form:

```text
max(role_weight) - min(role_weight) <= T_role_imbalance
```

This is not a demand for equal outputs.

It is a bound against structural capture by one role.

The role-weight measure used in the first experiment must be derived from structural state rather than successful task volume or route outcome.

### Coordinator Alignment

The coordinator must remain aligned with the three-role structure.

Candidate measures include centroid offset, angular deviation, or disagreement with the role-derived envelope.

Candidate form:

```text
coordinator_offset <= T_coordinator_offset
```

### Coverage Preservation

The role set must continue to cover the required Fact, Logic, and Coherence functions.

Candidate form:

```text
coverage_fact >= T_coverage
coverage_logic >= T_coverage
coverage_coherence >= T_coverage
```

A route should not retain authority if one structural role has become nominal rather than functional.

For v4, coverage must be represented through predeclared structural state rather than answer correctness.

### Relational Consistency

The three roles may disagree, but their structural disagreement must remain inside a recoverable envelope.

Candidate form:

```text
structural_state_disagreement <= T_disagreement
```

The measure should distinguish productive structural tension from fracture without reading route outcomes.

### Restoration Stability

A single clean observation should not automatically erase a recent non-admissible condition.

Candidate form:

```text
ADMISSIBLE for K_restore consecutive valid observations
```

`K_restore` is one-directional.

It governs when bypass authority may be restored after evidence invalidity, soft degradation, or hard structural failure.

It does not govern how quickly bypass is revoked.

A confirmed hard structural failure revokes authority on the first valid confirming observation.

Evidence invalidity denies authority as soon as the invalidity is detected.

Soft degradation enters its predeclared response mode as soon as the mapping and any predeclared persistence rule are satisfied.

All observations counted toward `K_restore` must be valid, fresh, applicable to the same active structural epoch, and inside the declared invariant bounds.

A new failure or evidence-invalidity event resets the restoration count.

A structural epoch change also resets the restoration count. Clean observations from an earlier epoch cannot contribute toward restoration in the new epoch.

## Freshness

Structural evidence must expire.

A valid record should satisfy:

```text
current_time_ms - timestamp_ms <= T_shape_freshness
```

`T_shape_freshness` must be defined from the update rate and failure timescale of the substrate.

It must not be chosen only for convenience.

A stale record is evidence invalidity and becomes non-admissible for bypass.

Staleness alone does not establish structural failure and does not trigger reconstruction.

## Epoch Integrity

Every shape-integrity record must belong to the currently active structural epoch.

A new recovery or reconstruction event should create a new epoch.

A route cannot use structural evidence from an earlier epoch.

Candidate rule:

```text
record.structural_epoch == active_structural_epoch
```

Any mismatch denies bypass because the evidence is invalid for the active substrate.

An epoch mismatch does not, by itself, prove structural deformation.

After an epoch change, restoration requires fresh evidence from the new epoch and satisfaction of `K_restore` when the validation plan requires restoration persistence.

## Scope

The architecture should support:

```text
scope_type = GLOBAL
scope_type = ROUTE_CLASS
scope_type = ROUTE_INSTANCE
scope_type = SUBSTRATE_REGION
```

The first experiment freezes:

```text
scope_type = GLOBAL
scope_id = ACTIVE_TETRAHEDRAL_SUBSTRATE
```

This assumption is appropriate for the first experiment because every tested route is treated as dependent on one shared tetrahedral substrate.

The limitation must be counted honestly. A GLOBAL gate may suspend routes that are not individually affected by a localized deformation. Those suspensions must remain visible through fallback-rate, false-revocation, and lost-bypass-opportunity metrics.

Route-specific and regional scope remain later design questions.

If GLOBAL scope applicability cannot be established in the first experiment, the record is evidence-invalid and cannot authorize bypass.

## Provenance and Verification

Every structural record should preserve its origin and verification path.

At minimum:

```text
authorized source
observer type
timestamp
epoch
scope
verification status
verification method
verification reference
evidence references
```

At least one declared verification method is required for every record that enters the gate.

Acceptable methods may include an internal trust boundary, signed record, deterministic replay, evidence hash, or another method frozen in the validation plan.

`evidence_hash` may remain optional only when another accepted verification method is present and identified through `verification_method` and `verification_reference`.

A record with no declared verification path is evidence-invalid and cannot authorize bypass.

The routing layer should not accept a bare `verification_status = VERIFIED` without an auditable method and reference.

## Relationship to Route Confidence

`C_success` and `shape_integrity` must remain separate.

`C_success` is historical and route-specific.

`shape_integrity` is live and structural.

A high `C_success` cannot override evidence invalidity, soft structural degradation, or a confirmed hard structural failure.

A strong shape record cannot reactivate a deprecated or unrequalified route.

The bypass decision is conjunctive.

Candidate rule:

```text
bypass_allowed =
    route_history_sufficient
    and c_success >= T_bypass
    and depreciation_state permits
    and recovery_state permits
    and anti_oscillation_state permits
    and structural_cost <= T_cost
    and shape_record_present
    and shape_record_authorized
    and shape_record_verifiable
    and shape_record_fresh
    and shape_epoch_matches
    and shape_scope_applies
    and shape_integrity_state == ADMISSIBLE
    and all_required_invariants_pass
    and restoration_requirement_satisfied
```

`integrity_score` is intentionally absent from this rule.

## Authority and Revocation Behavior

### Evidence Invalidity Response

Candidate rule:

```text
if evidence_invalidity:
    bypass_allowed = false
    authority_state = NOT_AUTHORIZED
    current_task = declared_safe_fallback
    request_or_await_valid_evidence
    do_not_trigger_reconstruction_from_invalidity_alone
```

Evidence invalidity denies authority without claiming that a structural invariant has failed.

### Confirmed Hard Structural Failure Response

Candidate rule:

```text
if confirmed_hard_structural_failure:
    bypass_allowed = false
    authority_state = REVOKED
    current_task = full_analysis
    record all_failed_invariants
    select first_failed_invariant by canonical order
    evaluate separate recovery_trigger rules
```

Revocation is immediate on the first valid confirming observation.

`K_restore` must not delay this response.

### Soft Structural Degradation Response

Candidate rule:

```text
if soft_structural_degradation:
    bypass_allowed = false
    authority_state = declared_mode
    current_task = action declared for that mode
```

The validation plan must provide a frozen table that maps every soft-degradation type to `BLOCKED`, `FULL_ANALYSIS`, or `REQUALIFYING` and declares any persistence threshold and exit condition.

No response may be chosen after results are observed.

## Recovery Interaction

A gate denial does not automatically mean that the tetrahedral substrate should be reconstructed.

The routing layer and recovery layer remain distinct.

Candidate separation:

```text
evidence invalidity
    -> deny bypass and obtain valid evidence

soft structural degradation
    -> enter declared bounded response mode

confirmed hard structural failure
    -> revoke bypass immediately

separately satisfied recovery invariant
    -> initiate tetrahedral reconstruction
```

Some confirmed hard structural failures may also satisfy a recovery trigger.

The architecture should record whether an event caused:

```text
evidence refresh request
route-only revocation
global bypass suspension
local reconstruction
global reconstruction
```

The experiment should also record whether reconstruction was triggered without a confirmed recovery invariant.

After reconstruction, the system enters a new structural epoch.

Earlier shape records become invalid.

Affected routes must follow the declared fresh-evidence and `K_restore` requalification process.

## First Experimental Objective

The first experiment should not try to prove the entire tetrahedral model.

It should answer one narrow question:

Can a live tetrahedral deformation signal revoke unsafe route authority earlier than route-confidence decay under a matched post-promotion degradation workload?

The comparison should preserve the v3 discipline.

All arms should receive identical pre-generated workloads, deformation timing, epoch schedules, and structural observation inputs.

The only changed authority variable between the direct comparison arms should be the presence or absence of the independent shape-integrity gate.

## Experimental Isolation Architecture

Before any arm runs, the harness must pre-generate and freeze:

```text
task manifest
fault and deformation manifest
structural epoch schedule
structural observation inputs
ground-truth deformation labels for evaluator use only
matched comparison keys
```

A deterministic structural observer must process the shared structural state and produce shape records for every arm.

For identical structural state, the observer must produce identical shape records regardless of arm behavior.

Only V4-D consumes those records as an additional bypass gate.

The observer must not read:

```text
arm identity when deriving structural state
bypass decisions
route correctness
wrong-bypass labels
C_success
route-performance latency
future task information
evaluator-only ground-truth labels
```

The evaluator may compare the completed shape-record stream against ground-truth deformation labels after the run.

The detector and gate may not access those labels during execution.

## Candidate Experimental Arms

The v4 arms should be named explicitly to avoid confusion with the earlier v3 arm labels.

```text
V4-A: full analysis baseline

V4-B: naive confidence-based bypass

V4-C: flat bounded routing without shape-integrity gate

V4-D: bounded routing with the independent tetrahedral shape-integrity gate
```

V4-C is not the timer-bound Arm C used in v3.

The existing recovery and requalification state machine should remain unchanged unless the experiment is specifically testing a recovery interaction.

The direct isolation comparison is V4-C against V4-D.

## Candidate Structural Deformation Patterns

The first experiment should include controlled structural deformations.

Candidate classes include:

```text
confirmed role collapse
role dominance
coordinator offset
coverage loss
pairwise angular compression
pairwise angular expansion
health-probe latency skew
role-specific structural degradation
```

At least one clean control pattern must remain structurally admissible.

At least one borderline pattern should remain near the threshold long enough to test false revocation and delayed revocation.

The validation plan must include both a transient soft-bound crossing that clears before the declared persistence threshold and a matched soft degradation that persists beyond the threshold. This pair must verify that persistence changes the authority response exactly as declared.

## Candidate Evidence-Invalidity Patterns

Evidence-invalidity tests should be reported separately from structural deformation tests.

Candidate classes include:

```text
missing structural record
unauthorized source
failed verification
missing verification reference
stale structural record
epoch mismatch
scope mismatch
```

These patterns should confirm fail-closed authority behavior without being counted as successful structural-deformation detection.

They should also confirm that evidence invalidity alone does not trigger reconstruction.

## Primary Metrics

The experiment should report:

```text
time_to_structural_detection
time_to_authority_revocation
wrong_bypasses_after_deformation
tasks_exposed_before_revocation
fallback_rate
lost_bypass_opportunities
false_revocations
missed_revocations
evidence_invalidity_denials
unnecessary_reconstruction_triggers
all_failed_invariants
first_failed_invariant
gate_that_blocked_first
shape_record_age_at_decision
epoch_match_rate
scope_match_rate
verification_pass_rate
restoration_time
K_restore_resets
```

Wrong-bypass counts should be reported both as raw counts and as rates over identical matched task keys.

False revocation and lost-bypass-opportunity costs created by the GLOBAL scope assumption must remain visible.

## Go and No-Go Criteria

The experiment should be considered promising only if the shape gate produces a real earlier signal.

A provisional go condition is:

```text
V4-D revokes authority earlier than V4-C on matched structural deformations
and
V4-D records fewer wrong bypasses on identical matched tasks
and
the improvement is not caused by permanent or near-permanent suppression
and
false revocation remains inside a declared bound
and
evidence-invalidity cases fail closed without being misclassified as structural collapse
and
no route-outcome leakage assertion fails
```

A no-go condition is:

```text
shape integrity blocks no earlier than confidence
or
wrong bypasses are not reduced
or
the apparent improvement comes only from suppressing nearly all bypasses
or
false revocation exceeds the declared bound
or
the structural signal cannot be distinguished from route outcome leakage
or
evidence invalidity causes unjustified reconstruction
or
K_restore delays hard-failure revocation
```

The thresholds and final verdict rule must be declared before the run.

## Leakage Controls and Required Assertions

Leakage controls are a first-class assertion category.

The shape-integrity signal must be derived only from structural observations available at the decision time.

The validation plan must include explicit assertions that verify at least the following:

```text
no future task information enters the shape record
no route correctness or wrong-bypass label enters the observer
no C_success value enters the observer
no task-processing latency enters health_probe_latency_ms
no arm-specific bypass outcome changes the pre-generated deformation schedule
no arm-specific bypass outcome changes a shape record
identical structural states produce identical shape records across arms
matched comparison keys are identical across arms
shape-record timestamps precede or equal the routing decision
ground-truth deformation labels remain evaluator-only during execution
integrity_score does not participate in the v4 gate decision
K_restore is consulted only for restoration, never for revocation
```

Any failed leakage assertion invalidates the affected run.

## Validation-Plan Requirements

Before implementation begins, `TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md` must freeze:

```text
V4-A through V4-D arm definitions
GLOBAL scope declaration
task and deformation manifest format
structural observer inputs and prohibited inputs
candidate invariant formulas
hard and soft threshold values
canonical invariant evaluation order
all_failed_invariants and first_failed_invariant rules
soft-degradation response table
transient and persistent soft-degradation test patterns
response-mode entry and exit rules
T_shape_freshness
K_restore
verification method and reference format
recovery-trigger separation
leakage assertions
primary metrics
matched comparison keys
go and no-go thresholds
random seeds and run counts
```

None of these choices may be changed post-hoc to improve the verdict.

## Open Design Questions

The following items remain intentionally unresolved beyond the first experiment.

What exact geometry or role-state representation best captures tetrahedral deformation?

Should later shape-integrity systems expose a scalar, an enum, a vector, or a structured record to diagnostic consumers?

Which failures should ultimately be global and which should be route-specific?

What freshness interval is justified by the real substrate update rate?

Which soft degradations require persistence before entering their declared response mode?

How should coordinator failure be observed without allowing the coordinator to certify itself?

When an authorized coordinator result conflicts with valid direct role-state or relational evidence, which evidence takes precedence, and how is that conflict classified?

Can role-separated evidence be verified without creating a central single point of failure?

What is the minimum structural signal that preserves the architecture without overbuilding the first test?

Can route-outcome-adjacent evidence ever be admitted later without collapsing the separation between `C_success` and `shape_integrity`?

These questions should not be resolved through the first v4 result unless they are explicitly part of the frozen validation plan.

## Current Status

This document is an architecture specification, not a validated mechanism.

Version 1.1 incorporates the external review cycle and closes the identified implementation ambiguities around evidence invalidity, hard structural failure, soft degradation, restoration directionality, restoration interruption, scope, provenance, leakage, and deterministic invariant reporting.

No shape-integrity formula has been proven.

No threshold has been frozen.

No v4 simulation has been written.

The narrow contradiction and leakage review of this v1.1 specification is complete.

The architecture is frozen for validation planning. The next artifact is `TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md`.

Implementation must not begin until the validation plan declares the signal, thresholds, scope, provenance, freshness, epoch, restoration, leakage assertions, and go/no-go rules.
