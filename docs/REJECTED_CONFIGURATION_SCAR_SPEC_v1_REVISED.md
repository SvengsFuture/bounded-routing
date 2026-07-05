# Rejected Configuration Scar Specification

**Document:** `REJECTED_CONFIGURATION_SCAR_SPEC_v1.md`  
**Version:** 1.0  
**Status:** First-pass architecture specification for review, targeted scar-boundary corrections applied  
**Depends on:** `TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1.md` and `TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md`  
**Next artifact after review:** `REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1.md`

## Purpose

This document defines a minimal scar layer for the tetrahedral routing and recovery architecture.

The scar is not a diagnostic record.

The scar is not a semantic memory.

The scar is not a replacement for live `shape_integrity`.

The scar is not a replacement for historical route confidence.

The scar is a compact rejected-configuration record written only when the system extended authority to a structural configuration and that trusted configuration later failed or became non-admissible under valid structural evidence.

The scar answers one narrow question:

> Has this authorized structural configuration failed here before?

The system does not need to understand why the configuration failed in order to avoid repeating it. It only needs to recognize the structural pattern and respond differently.

This is closer to an immune response than a diagnostic explanation. The system does not need to understand the disease. It needs to recognize the pattern and not keep admitting the same bad configuration.

## Governing Principle

Only betrayed authority creates a scar.

A cheap failed retry does not create a scar.

A non-admitted candidate does not create a scar.

A stale, missing, unverifiable, or out-of-scope record does not create a scar.

A prospective rejection does not create a scar.

A configuration that had authority and then failed under valid structural evidence may create a scar.

The scar should be minimal by design. If a field requires semantic interpretation to be useful, it does not belong in the scar record.

The turpentine example captures the boundary.

The system does not need to know why turpentine ruined the cake. It only needs to know that this ingredient configuration produced a bad result, so the same configuration should not be admitted again without mutation, extra proof, or elevation.

The scar is the record that says:

```text
Do not use this configuration again as-is.
```

It is not the layer that figures out why the configuration appeared.

## Relationship To Existing Signals

`C_success` answers how well a route has performed over time.

`shape_integrity` answers whether the live tetrahedral structure is currently admissible.

The scar registry answers whether a previously authorized structural configuration has already failed in this scope.

These three signals must remain separate.

A scar must not feed into `C_success`.

A scar must not alter the live structural observer.

A scar must not be readable by the structural observer that produces shape-integrity records.

A scar must not change whether live geometry is classified as `ADMISSIBLE`, `DEGRADED`, `FAILED`, or `UNKNOWN`.

The structural observer sees live structural geometry.

The scar registry is consulted only by the authority layer when deciding whether a candidate or regenerated cell may be promoted, restored, or reauthorized.

A currently admissible shape may still match a scar.

That does not mean the shape is live-failed.

It means the authority layer has a structural memory that this configuration, or a declared matching configuration, failed after being trusted.

## Scope

This v1 specification defines only the rejected-configuration scar layer.

It does not define cellular shedding.

It does not define lineage inheritance.

It does not define a prospective filter.

It does not define semantic diagnosis.

It does not define substitution reasoning.

It does not define why a failed configuration kept appearing.

Those mechanisms may consume scar outputs later, but they are not part of this first scar specification.

## Definitions

### Candidate Configuration

A candidate configuration is a structural arrangement being considered for authority.

It has not yet been trusted.

A candidate may fail admission without creating a scar.

### Authorized Configuration

An authorized configuration is a structural arrangement that has been granted authority by the relevant authority layer.

In routing terms, this may mean it was permitted to support bypass, restoration, promotion, or an equivalent trusted operation.

A scar can only be written after this level of authority has existed.

### Betrayed Authority

Betrayed authority occurs when an authorized configuration later becomes non-admissible under valid structural evidence.

The v1 scar layer treats the following as scar-eligible betrayed-authority events:

```text
AUTHORIZED_HARD_STRUCTURAL_FAILURE
AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION
AUTHORIZED_RESTORATION_FAILURE
```

Evidence invalidity is not betrayed authority.

A stale record, missing record, failed verification, epoch mismatch, or scope mismatch denies authority but does not prove that the configuration itself failed.

### Scar

A scar is a compact structural record of a rejected authorized configuration.

It does not explain the failure.

It identifies the configuration that should not be admitted again as-is.

### Scar Match

A scar match occurs when a candidate or regenerated configuration matches a stored scar under the declared matching policy.

For v1, the default policy is exact canonical structural fingerprint match.

Near-match or fuzzy scar matching is deferred to later work unless a validation plan explicitly declares the tolerance function before implementation.

### Elevation

Elevation occurs when repeated scars of the same fingerprint cross a declared threshold.

Elevation hands the compact record upward for analysis, substitution, human review, or upstream correction.

Elevation does not occur inside the scar itself.

The scar counts and emits the signal. A higher layer asks why.

## Scar Write Rules

The scar layer must distinguish failure types before writing a record.

### No Scar

The following events do not create a scar:

```text
NON_ADMITTED_REJECT
CHEAP_RETRY_FAILURE
EVIDENCE_INVALIDITY
STALE_RECORD_DENIAL
FAILED_VERIFICATION_DENIAL
EPOCH_MISMATCH_DENIAL
SCOPE_MISMATCH_DENIAL
PROSPECTIVE_FILTER_REJECTION
TRANSIENT_SOFT_WARNING_BELOW_PERSISTENCE
CANDIDATE_REJECTED_BEFORE_AUTHORITY
```

The governing reason is simple. The system did not extend authority to the configuration and then get betrayed by it.

The gate either did its job, the evidence was invalid, or the candidate was never trusted.

### Scar Eligible

The following events may create or update a scar:

```text
AUTHORIZED_HARD_STRUCTURAL_FAILURE
AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION
AUTHORIZED_RESTORATION_FAILURE
```

A scar may be written only when all of the following are true:

```text
configuration_had_authority = true
valid_structural_evidence = true
non_admissible_condition_is_structural = true
configuration_fingerprint_available = true
scope_applicability_established = true
```

If any of these are false, the event may be logged for audit, but it must not create a scar.

## Minimal Scar Schema

A v1 scar record is:

```text
RejectedConfigurationScarRecord:
  scar_id                     : str
  configuration_fingerprint   : str
  fingerprint_method          : str
  fingerprint_version         : str
  match_policy                : enum
  scope_type                  : str
  scope_id                    : str
  first_authorized_epoch      : str or int
  failure_epoch               : str or int
  first_seen_ms               : float
  last_seen_ms                : float
  failure_count               : int
  scar_event_class            : enum
  failed_invariant_class      : str
  retirement_policy           : enum
  successful_cycles_since_last_seen : int
  elevation_state             : enum
  elevation_count             : int
  verification_reference      : str
```

The record is intentionally small.

It does not contain task text.

It does not contain route history.

It does not contain `C_success`.

It does not contain task outcome labels.

It does not contain a natural-language explanation.

It does not contain a diagnosis.

## Configuration Fingerprint

`configuration_fingerprint` is a canonical hash derived from structural geometry only.

For v1, the fingerprint payload contains structural geometry and scope only:

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

`failed_invariant_class` is intentionally excluded from the fingerprint hash payload and retained only as adjacent metadata. The fingerprint's job is to recognize the rejected structural geometry. The same dangerous geometry should still match the same scar even if it presents later through a different first-failed invariant.

The fingerprint payload must not contain:

```text
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

The purpose of the fingerprint is not to explain why the configuration failed.

The purpose is to recognize the same rejected structural configuration if it appears again.

### Canonicalization

The validation plan must declare the exact canonicalization method before implementation.

At minimum, it should define:

```text
field order
float rounding or quantization
angle normalization
scope representation
missing-value policy
hash algorithm
fingerprint version string
```

The canonicalization method must be deterministic.

Two implementations receiving the same structural payload must produce the same fingerprint.

### Failed Invariant Class

`failed_invariant_class` is adjacent metadata, not a fingerprint input.

It is included only as a coarse structural discriminator for reporting, elevation, validation, and later analysis.

It may identify classes such as:

```text
ROLE_PRESENCE
ROLE_SEPARATION
COVERAGE
COORDINATOR_ALIGNMENT
ROLE_IMBALANCE
HEALTH_PROBE_LATENCY_SKEW
RESTORATION_FAILURE
```

It must not become a semantic explanation.

It says what structural boundary was involved, not why the failure happened.

## Matching Policy

The v1 default matching policy is:

```text
match_policy = EXACT_CANONICAL_FINGERPRINT
```

Under this policy, a candidate matches a scar only when its canonical structural fingerprint equals a stored scar fingerprint in the applicable scope.

The v1 specification intentionally does not define fuzzy matching.

Fuzzy or near-match policies are dangerous because they can become a prospective filter in disguise.

If later work admits near-match scar matching, the tolerance function must be declared in a separate validation plan before implementation.

## Immediate Authority Effect

A scar does not classify live structural state.

A scar does not make the structural observer report `FAILED`.

A scar does not change `shape_integrity`.

A scar can affect authority only when a candidate, regenerated cell, or restored configuration is being considered for authority.

When a candidate matches an active scar, the authority layer may apply one of the following predeclared responses:

```text
REJECT_AS_IS
REQUIRE_MUTATION
REQUIRE_EXTRA_PROOF
ROUTE_AROUND
ELEVATE_IF_THRESHOLD_REACHED
```

The validation plan may declare different default responses by `scar_event_class`.

The v1 hard-failure default response is:

```text
AUTHORIZED_HARD_STRUCTURAL_FAILURE -> REJECT_AS_IS
```

The v1 soft-degradation default response should be declared separately in the validation plan. A conservative starting choice is:

```text
AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION -> REQUIRE_EXTRA_PROOF
```

This avoids treating every persisted soft-bound crossing as permanent rejection while still preventing silent re-promotion of a configuration that has already failed after authority.

The exact same hard-failed scarred configuration cannot be promoted again as-is unless a later validation plan declares mutation, extra proof, retirement, or elevation handling.

## Failure Count

`failure_count` increments when the same active scar fingerprint appears again as a scar-eligible betrayed-authority event within the same applicable scope.

A rejected non-admitted candidate does not increment `failure_count`.

A scar match that is rejected before authority does not increment `failure_count` by default.

The count represents repeated trusted failure, not repeated cheap rejection.

If a later system wants to count repeated rejected nominations, that should be a separate nomination-pressure metric, not the scar failure count.

## Elevation

Elevation is separate from the scar.

The scar remains local, minimal, and structural.

When the scar count crosses a declared threshold, the scar registry emits an elevation event.

Candidate rule:

```text
if failure_count >= T_SCAR_ELEVATE:
    elevation_state = ELEVATED
    emit ScarElevationEvent
```

The elevation event may contain:

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

The elevated layer may ask why the pattern keeps appearing.

The scar layer does not.

For v1, the elevation threshold is not frozen in the architecture specification. It must be frozen in the validation plan before implementation.

## Retirement

A scar should not necessarily persist forever.

However, v1 should not use idle time alone as the retirement mechanism.

Time-only retirement can allow a bad configuration to re-enter merely because the system was idle long enough.

The v1 retirement mechanism is success-count based.

Candidate rule:

```text
retirement_policy = RETIRE_AFTER_SUCCESSFUL_CYCLES

if successful_cycles_since_last_seen >= T_SCAR_RETIRE_SUCCESS_CYCLES:
    elevation_state = RETIRED
    scar no longer blocks authority
```

A successful cycle must be defined by the validation plan.

At minimum, a successful cycle should require that the applicable scope completes a declared structural operation or recovery interval without reproducing the scarred fingerprint and without a scar-eligible failure carrying the same `configuration_fingerprint`.

The retirement threshold is not frozen in this architecture specification.

It must be frozen in the validation plan before implementation.

A retired scar may remain in audit history but must not continue to block authority unless reactivated by a new scar-eligible event.

## Propagated Or Inherited Scars

A scar can be acquired in more than one way.

The simplest source is direct local failure.

A regenerated cell may also inherit a scar from a predecessor cell.

A neighboring cell may receive a propagated scar when the architecture declares that the rejected configuration is relevant to its local scope.

This is analogous to learning that turpentine is not food from a warning rather than from direct injury.

A propagated or inherited scar still must remain minimal.

It carries the rejected structural fingerprint and count context.

It does not carry a semantic explanation.

Lineage and propagation rules are out of scope for this v1 scar specification, but the scar record must be small enough to support them later.

## What The Scar Is Not

The scar is not a diagnostic log.

The scar is not a semantic memory.

The scar is not a context window.

The scar is not a route-confidence update.

The scar is not a live shape-integrity observation.

The scar is not a prospective compatibility filter.

The scar is not an explanation of why the configuration failed.

The scar is not a reconstruction plan.

The scar is not a substitute ingredient generator.

The scar is not a human-readable causal story.

If the system needs to ask why the configuration failed, that question belongs to elevation or a later interpretive layer, not to the scar.

## Prospective Filter Boundary

The scar is retrospective.

It requires at least one scar-eligible trusted failure before the rejected configuration exists in the registry.

A prospective filter is different.

A prospective filter would reject a configuration before failure because its structural properties predict incompatibility.

That may become a useful later mechanism, but it is out of scope for v1.

The scar layer must not pretend to be a prospective filter by using broad semantic labels or fuzzy causal reasoning.

The scar says:

```text
We tried this authorized configuration.
It failed.
Do not promote it again as-is.
```

A prospective filter would say:

```text
This untried configuration is likely incompatible.
Reject it before trying.
```

Those mechanisms must remain separate.

## Interaction With Shedding

Shedding is out of scope for v1, but the scar provides the record that shedding will leave behind.

When a damaged cell is shed, the scar layer may record the rejected configuration if and only if the shed cell had authority and failed under valid structural evidence.

The shed cell can be quarantined, retired, studied, or discarded by a later mechanism.

The scar itself remains compact.

It tells the rebuilt or adjacent cell what not to reproduce as-is.

## Interaction With Lineage

Lineage is out of scope for v1, but the scar provides the minimal record that lineage may carry forward.

A regenerated cell should not inherit the whole history of its predecessor.

It should inherit only compact rejected-configuration records relevant to its scope.

The new cell may start fresh in every other respect.

This preserves the goal of low-memory structural recovery.

## Audit Separation

Events that do not create scars may still be recorded in an audit log.

The audit log is not the scar registry.

The audit log may be useful for review, debugging, or research.

The scar registry is an authority-facing structural registry.

The two must remain separate.

An audit entry should not block authority.

Only an active scar match under the declared policy may affect future authority.

## First Validation Objective

The first scar validation should not test shedding or lineage.

It should test the scar boundary.

The first validation should answer one narrow question:

> Can the system write scars only for betrayed authority, ignore cheap or non-admitted failures, reject exact scarred configurations on reappearance, and elevate only after the declared scar count threshold?

The first validation should include cases where:

```text
a candidate fails before authority and writes no scar
evidence invalidity denies authority and writes no scar
an authorized hard failure writes a scar
an authorized gate-effective soft degradation writes a scar
the same scarred configuration reappears and is rejected as-is
a similar but non-identical configuration does not match under exact v1 policy
failure_count increments only after repeated trusted failure
cheap rejected repeats do not increment failure_count
a scar retires only after successful cycles, not idle time
elevation fires only after T_SCAR_ELEVATE
```

## Open Design Questions

The following questions remain intentionally unresolved until validation planning.

What exact quantization should the canonical structural fingerprint use?

Should later versions allow `failed_invariant_class` to influence near-match policy while keeping the v1 exact fingerprint geometry-only?

What authority level qualifies as sufficient authority for scar eligibility?

Should gate-effective soft degradation always create a scar, or should some soft classes create only a scar candidate?

What threshold should trigger elevation?

What successful-cycle count should retire a scar?

Should inherited scars preserve original `failure_count`, or should inherited count be marked separately from local count?

How should scar scope narrow from GLOBAL to ROUTE_CLASS, ROUTE_INSTANCE, or SUBSTRATE_REGION in later systems?

Can near-match policies be validated without becoming a prospective filter?

How should nomination pressure be counted when the same scarred configuration is repeatedly proposed but rejected before authority?

## Current Status

This document is an architecture specification, not a validated mechanism.

The scar layer is defined as a minimal rejected-configuration registry.

Its governing rule is that only betrayed authority creates a scar.

The next required artifact is:

```text
REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1.md
```

Implementation should not begin until the validation plan declares the fingerprint canonicalization, scar write rules, matching policy, retirement threshold, elevation threshold, authority threshold, metrics, assertions, and go/no-go criteria.
