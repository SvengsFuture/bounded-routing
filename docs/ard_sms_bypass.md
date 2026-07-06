# ARD, SMS, and Bypass Component Reference

## Purpose

This document defines the route-state model, confidence update process, structural-integrity gate, scar check, and bypass decision sequence used by bounded routing.

Bounded routing is the authority layer for the tetrahedral recovery architecture.

The Adaptive Routing Database stores route-level state and decision references.

The Success Measurement System updates historical route confidence.

The Intelligent Bypass Mechanism decides whether a learned route currently has permission to execute.

Live tetrahedral structural state remains separate from route confidence and enters the bypass decision through an independent structural-integrity gate.

Rejected-configuration scars remain separate from both route confidence and current structural state. A scar records that an authorized structural configuration failed and should not be promoted again as-is.

## Adaptive Routing Database

Each ARD entry corresponds to one task and route class identified by S_pat.

An ARD entry may include:

s_pat, the task and route-class identifier.

p_opt, the current learned route identifier.

c_success, the historical route-performance confidence.

obs_count, the number of qualifying route observations.

obs_window, the recent route-outcome window.

last_used_ms, the timestamp of the most recent route attempt.

depreciation_state, the current route depreciation state.

depreciation_count, the count of consecutive below-threshold route outcomes.

last_flip_ms, the timestamp of the most recent p_opt change.

flip_count, the total number of route changes.

structural_cost, the current route-level structural cost.

recovery_sensitive, whether recovery affects this route's authority.

recovery_state, the current recovery or requalification condition.

authority_state, whether bypass authority is active, blocked, requalifying, or revoked.

structural_record_ref, a reference to the independent structural observation used by the current decision.

shape_integrity, the current authorized structural condition consumed by the bypass gate.

scar_match_ref, a reference to any rejected-configuration scar match used by the current decision.

scar_status, the current scar result for the candidate structural configuration.

The ARD stores route-level evidence and authority state.

It does not compute tetrahedral structural integrity.

It does not create scar records.

A structural record may be referenced by an ARD entry for traceability, but its contents must remain independently sourced and must not be blended into c_success.

A scar result may also be referenced by an ARD entry for traceability, but it must remain separate from c_success and shape_integrity.

A deprecated route does not become active merely because old confidence rises or time passes.

Any return to active authority must follow the declared requalification process.

A route that matches a hard scar cannot be promoted again as-is.

## Depreciation and Authority State

Depreciation state describes route health over time.

ACTIVE means the route may be considered for bypass.

WARNED means the route has crossed the depreciation warning boundary but has not yet become fail-closed.

DEPRECATED means the route cannot bypass and may enter a declared requalification path.

RETIRED means the route is removed from active ARD use.

Authority state is separate from depreciation state.

ACTIVE means the route may be considered for bypass.

BLOCKED means one or more current gates prevent bypass.

REQUALIFYING means the route is accumulating fresh evidence but cannot bypass.

REVOKED means prior bypass authority has been withdrawn.

A route may have acceptable historical confidence and still be blocked or revoked.

A route may remain non-deprecated while requalifying after recovery.

A route may pass route confidence and still fail shape integrity.

A route may pass route confidence and shape integrity but still fail the scar check.

## ARD Write Policy

Only the Success Measurement System writes c_success.

No other component may directly increase or decrease route confidence.

Full analysis may propose or replace p_opt when a better route is found.

Each p_opt change increments flip_count and updates last_flip_ms.

Recovery logic may change recovery_state and authority_state.

The structural observer may publish a new structural-integrity record, but it does not modify c_success.

The scar registry may return a match result, but it does not modify c_success or shape_integrity.

The Intelligent Bypass Mechanism reads all required state and produces an allow or fallback decision. It does not rewrite historical evidence to make a route pass.

## Success Measurement System

The Success Measurement System records how well a route has performed over time.

It answers the historical route question: how successful has this route been?

It does not answer the structural question: is the tetrahedral substrate currently intact enough to permit bypass?

It does not answer the rejected-configuration question: has this same structural configuration already failed after holding authority?

After a qualifying route observation, SMS computes an outcome score between 0.0 and 1.0.

The outcome score may include latency, admissibility, degradation, and stability.

Admissibility carries the highest weight because an inadmissible route result is more serious than an ordinary performance shortfall.

The confidence update has the form:

c_success_new equals alpha times c_success_old plus one minus alpha times outcome_score.

The V1 simulation used alpha equals 0.85.

A higher alpha produces slower confidence movement.

A lower alpha responds faster to new outcomes but may increase sensitivity to noise and oscillation.

The V3 result showed that slow scalar confidence decay was not sufficient to provide early post-promotion revocation under the tested relapse workload.

The V4 result showed that an independent structural-integrity gate can revoke unsafe bypass authority earlier than the inherited flat route gate under the frozen matched structural-deformation workload.

## Stability Score

The stability score is derived from variation in recent route outcomes stored in obs_window.

High variation lowers the score.

This penalizes a route that alternates between good and bad outcomes even when its average confidence remains above the bypass threshold.

The stability score remains a route-performance measure.

It is not a substitute for live tetrahedral shape integrity.

It is not a substitute for a scar lookup.

## Tetrahedral Structural-Integrity Record

The tetrahedral substrate provides a separate structural record.

A valid record should contain the authorized source identity, observer type, observation timestamp, structural epoch, scope type, scope identifier, Fact evidence, Logic evidence, Coherence evidence, coordinator result, shape-integrity condition, and verification status.

The record must preserve enough evidence to inspect or replay how the structural conclusion was reached.

A single scalar may be exposed to the bypass gate, but the underlying role-separated or geometric evidence must not be discarded.

A structural record is usable only when its source is authorized, its timestamp is fresh, its structural epoch matches the active substrate, its scope applies to the route or system being evaluated, its integrity can be verified, and its structural condition remains inside the declared bound.

If any of these conditions fails, structural authority is absent.

The router must fall back to full analysis.

A previous valid structural record cannot preserve authority indefinitely.

## V4 Structural Gate Result

V4 tested the independent structural-integrity gate.

The comparison changed one authority variable: whether the independent shape-integrity gate was consumed.

The primary V4 result was SUPPORTED.

The V4 run passed 26 of 26 assertions.

The flat V4-C arm recorded 404 matched wrong bypasses.

The shape-gated V4-D arm recorded 14 matched wrong bypasses.

That was a 96.53 percent reduction under the frozen matched structural-deformation workload.

Earlier revocation occurred in 100 percent of eligible matched instances.

The median revocation lead was 1860 milliseconds.

The clean suppression check passed.

This supports the narrow claim that live structural evidence can revoke unsafe bypass authority earlier than the inherited flat route gate under the declared synthetic deformation workload.

It does not prove production reliability, threshold optimality, final route scope, or the complete tetrahedral architecture.

## Rejected-Configuration Scar Record

The scar registry stores compact rejected-configuration records.

The governing rule is: only betrayed authority creates a scar.

A cheap retry does not create a scar.

A non-admitted candidate does not create a scar.

Invalid, stale, unverifiable, epoch-mismatched, or out-of-scope evidence does not create a scar.

A scar is written only when a configuration had authority and later failed under valid structural evidence.

A scar record may include a geometry-only fingerprint, scar class, failure count, first seen time, last seen time, elevation state, retirement state, and adjacent metadata such as failed invariant class.

The failed invariant class may be stored as adjacent metadata, but it must not enter the geometry fingerprint hash payload.

A hard scar returns REJECT_AS_IS.

A soft or restoration scar returns REQUIRE_EXTRA_PROOF.

A no-match result does not block promotion by itself.

Scar matching must remain isolated from shape_integrity and c_success.

The scar registry does not explain why the configuration failed.

It is not semantic memory.

It is not a full history.

It is not cellular shedding.

It is not lineage inheritance.

It is not prospective filtering.

It is not fuzzy matching.

It is not an extra-proof protocol.

## Scar Layer V1 Result

The frozen scar validation used:

K_SOFT_PERSIST equals 3.

T_SCAR_ELEVATE equals 3.

T_SCAR_RETIRE_SUCCESS_CYCLES equals 5.

The primary scar result was SUPPORTED.

The run passed 30 of 30 assertions.

Runtime was 0.98 seconds.

stderr was empty.

The test supports the narrow claim that scars can be written only for betrayed authority, matched by exact geometry-only fingerprint, elevated only after the declared threshold, and retired only after declared successful cycles.

## Intelligent Bypass Mechanism

At task arrival, the Pattern Recognition Engine produces S_pat.

The ARD returns the applicable route record.

The system verifies that route history is sufficient.

The system checks that c_success is at or above T_bypass.

The system checks that the depreciation state permits bypass.

The system checks that structural_cost is at or below T_cost.

The system checks that recovery and authority state permit bypass.

The system checks that anti-oscillation state permits bypass.

The system checks that the structural record is authorized.

The system checks that the structural record is fresh.

The system checks that the structural epoch matches.

The system checks that the structural scope applies.

The system checks that shape integrity is inside the declared bound.

The system checks whether the candidate configuration matches a rejected-configuration scar.

If every required gate passes, the task may execute through p_opt.

If any required gate fails, the task goes through full analysis.

After execution, SMS records the qualifying route outcome and ARD state is updated where applicable.

No individual gate may override a failure in another required gate.

High confidence cannot override invalid structural state.

Valid structural state cannot override a deprecated route.

Elapsed time cannot override required fresh requalification evidence.

A hard scar cannot be overridden by historical route confidence.

## Anti-Oscillation Gate

Bypass is blocked when the route has flipped too recently or too often within the declared flip window.

This prevents rapid alternation between routes that retain misleading confidence.

The V1 oscillation workload produced the clearest early supported result in the simulation series.

The naive cache recorded 64 wrong bypasses.

The bounded-routing arm recorded zero.

## Recovery and Requalification Gate

A recovery event removes bypass authority from affected routes.

The current task goes through full analysis.

A candidate route may be evaluated in shadow on that task, but the result applies only to future authority.

Pre-recovery confidence does not count as fresh evidence.

A route in REQUALIFYING cannot bypass.

Promotion requires the declared number of consecutive admissible shadow checks and the declared fresh-confidence threshold.

A failed check may reset the consecutive count and reduce fresh confidence.

A persistent-failure route may become deprecated and remain fail-closed.

The V2 primary workload used K equals 5 and a fresh confidence threshold of 0.75.

Those values are simulation settings, not universal requirements.

The V3 sensitivity test showed that increasing K from 3 to 5 to 8 delayed restoration and increased fallback without reducing post-promotion wrong bypasses in the tested relapse workload.

## Why the Structural Gate Remains Independent

The route-confidence score records historical route performance.

The structural-integrity record describes the current condition of the tetrahedral substrate.

Blending both into one score would destroy the distinction between history and live structure.

A high confidence average could conceal a fresh structural failure.

A low confidence average could also obscure whether the route itself failed or whether the substrate changed.

Keeping the signals separate makes the decision auditable.

The system can record whether authority was denied because of confidence, depreciation, recovery, oscillation, structural cost, freshness, epoch mismatch, scope mismatch, actual shape deformation, or rejected-configuration scar status.

That distinction is necessary for recovery, replay, and future shedding work.

## Simulation Parameter Reference

The values below describe the early flat harness unless otherwise stated.

T_bypass was 0.75.

T_depreciate was 0.55.

T_recover was 0.70 in the earlier flat harness.

T_cost was 1.5.

alpha was 0.85.

obs_window_size was 20.

depreciation_N was 5.

depreciation_M was 10.

recover_K was 8 in the earlier flat harness.

T_retire_ms was 60000.

T_flip_cooldown_ms was 2000.

MAX_FLIPS_PER_WINDOW was 3.

T_flip_window_ms was 10000.

T_recovery_blackout_ms was 5000 in V1.

The V2 and V3 requalification tests used separate fresh-evidence rules and sensitivity values.

The V4 shape-gate test used its own frozen structural-deformation workload and assertion set.

The scar validation used K_SOFT_PERSIST equals 3, T_SCAR_ELEVATE equals 3, and T_SCAR_RETIRE_SUCCESS_CYCLES equals 5.

These are simulation settings and validation constants, not universal production defaults.

## Current Evidence Boundary

V1 supports anti-oscillation gating under the tested oscillation workload.

V2 supports removal of stale bypass authority, fresh-evidence requalification, and fail-closed handling of persistent-failure routes.

V3 does not support the claim that the flat Arm D gate stack revokes unsafe post-promotion authority faster than simpler comparison arms.

V4 supports the narrow claim that an independent structural-integrity gate can revoke unsafe bypass authority earlier than the inherited flat gate under the frozen matched structural-deformation workload.

Scar Layer V1 supports the narrow claim that rejected-configuration scars can be written, matched, elevated, and retired under declared authority and evidence rules.

The current evidence does not prove production reliability, threshold optimality, final route scope, cellular shedding, lineage inheritance, fuzzy scar matching, prospective filtering, or an extra-proof recovery protocol.

The next mechanism to define is cellular shedding.


