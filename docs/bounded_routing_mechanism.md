# Bounded Routing Core Mechanism

## What This Is

Bounded routing is a route-selection discipline for adaptive systems. It governs when a learned route may bypass full analysis and when the system must fall back.

The governing constraint is admissibility, not speed alone.

Bounded routing is the authority layer for the tetrahedral recovery architecture. It grants, maintains, and revokes route authority based on route-level evidence and the continuing structural integrity of the substrate beneath it.

A route may bypass only while every required condition remains inside declared bounds.

Those conditions include sufficient route history, confidence above the bypass threshold, structural cost within tolerance, recovery context that permits bypass, acceptable anti-oscillation state, an admissible depreciation state, and valid structural-integrity evidence from the tetrahedral substrate.

If any required condition fails, the task goes through full analysis.

Fallback is the correct safety behavior. It is not a failure state.

## Current Status

The mechanism has now been tested in stages.

V1 supports the anti-oscillation mechanism under the tested oscillation workload.

V2 supports stale-authority removal, earned requalification through fresh evidence, and fail-closed handling of persistent-failure routes.

V3 does not support the stronger claim that the flat gate stack revokes unsafe post-promotion authority faster than simpler comparison controls.

V4 supports the narrow claim that an independent tetrahedral shape-integrity gate can revoke unsafe bypass authority earlier than the inherited flat gate under the frozen matched structural-deformation workload.

Scar Layer V1 supports the narrow claim that a rejected-configuration scar registry can record betrayed structural authority and prevent the same configuration from being promoted again as-is under declared matching, elevation, and retirement rules.

The overall verdict remains partial support. The mechanism is supported as bounded, conditional, revocable authority. It is not proven as a universal safety advantage across all workloads.

## Separation of Responsibilities

The tetrahedral substrate produces live structural state through the Fact, Logic, and Coherence roles and their coordinator.

The bounded-routing layer governs whether a learned route currently has execution authority.

The recovery layer reconstructs the tetrahedral structure when its invariants fail.

The scar layer records rejected structural configurations after betrayed authority.

These responsibilities must remain separate.

Route confidence cannot substitute for structural integrity.

Structural integrity cannot be inferred from route confidence alone.

Recovery cannot silently restore earlier bypass authority.

A scar cannot replace recovery, diagnosis, shedding, or lineage inheritance.

## Pattern Recognition Engine

The Pattern Recognition Engine receives a task or query and produces a pattern signature, S_pat.

S_pat identifies the task and route class and connects the task to the applicable routing record.

It may include task type, route class, and other information required to identify the correct learned pathway.

It must not contain the current tetrahedral structural condition.

It must not be used as a substitute for live structural evidence.

Structural cost may be associated with the candidate route, but live shape integrity remains a separate input to the bypass decision.

## Adaptive Routing Database

The Adaptive Routing Database stores route-level state for each pattern.

S_pat is the task and route-class identifier.

P_opt is the current learned pathway.

C_success is the historical route-performance confidence.

obs_count records the number of qualifying observations.

last_used_ms records the most recent route use.

depreciation_state records whether the route is active, warned, deprecated, or retired.

last_flip_ms records the most recent route change.

structural_cost records current route-level structural cost.

recovery_state records the current recovery and requalification condition.

authority_state records whether bypass authority is active, blocked, or being re-earned.

shape_integrity records the current authorized structural condition consumed by the bypass decision.

scar_status records whether the proposed structural configuration matches a rejected-configuration scar.

A deprecated route cannot bypass.

A retired route is removed from active routing.

A route affected by recovery cannot regain authority from pre-recovery confidence alone. It must satisfy the declared requalification process using fresh evidence.

The ARD may reference a structural-integrity observation used by the current decision, but that observation must retain its independent source, timestamp, epoch, and scope. It must not be collapsed into C_success.

The ARD may also reference a scar match result, but that match must remain separate from C_success and shape_integrity. A scar does not change confidence. A scar does not define the current shape. A scar only records that a configuration has already betrayed authority and should not be promoted again as-is.

## Success Measurement System

The Success Measurement System updates C_success from route-level performance evidence.

A general update has the form:

C_success_new = alpha times C_success_old plus one minus alpha times outcome_score.

The outcome score may include route latency, route admissibility, degradation, and stability.

Admissibility carries the highest weight.

The Success Measurement System is the only component that changes route confidence directly.

Live tetrahedral structural state does not become part of the moving confidence average.

Scar matches do not become part of the moving confidence average.

C_success answers a historical question: how well has this route performed?

It does not answer the structural question: is the tetrahedral substrate currently intact enough to permit bypass?

It also does not answer the rejected-configuration question: has this same structural configuration already failed after holding authority?

## Structural-Integrity Record

The tetrahedral substrate supplies a separate structural-integrity record.

A valid structural record must identify the authorized source, the observation timestamp, the structural epoch, the applicable route or system scope, the Fact, Logic, and Coherence evidence or the coordinator-derived result, and the resulting structural-integrity condition.

The record may expose a scalar gate result, but the underlying role-separated or geometric evidence must remain available for inspection and replay.

The record is admissible only when its source is authorized, its timestamp is fresh, its epoch matches the active substrate, and its scope applies to the route being considered.

Missing, stale, unverifiable, epoch-mismatched, or out-of-scope structural evidence cannot preserve bypass authority.

The system must fail closed to full analysis.

V4 tested this condition as an independent shape-integrity gate. Under the frozen matched structural-deformation workload, the shape-gated arm reduced matched wrong bypasses from 404 to 14 compared with the flat bounded-routing arm.

That supports the narrow claim that live structural evidence can withdraw unsafe bypass authority earlier than the inherited flat gate under the declared workload.

## Rejected-Configuration Scar Record

A scar is a compact rejected-configuration record.

The governing rule is: only betrayed authority creates a scar.

A cheap retry does not create a scar.

A non-admitted candidate does not create a scar.

Invalid, stale, unverifiable, epoch-mismatched, or out-of-scope evidence does not create a scar.

A scar is written only when a configuration had authority and later failed under valid structural evidence.

The scar fingerprint is geometry-only. The failed invariant class may be stored as adjacent metadata, but it does not enter the hash payload.

A hard scar rejects the same configuration as-is.

A soft or restoration scar requires extra proof before promotion.

Failure counts increment only after repeated trusted failure.

Elevation occurs only at the declared threshold.

Retirement occurs only after declared successful cycles.

Scar matching is isolated from shape_integrity and C_success.

The scar layer does not explain why the configuration failed. It is not semantic memory. It is not a full history. It is not cellular shedding. It is not lineage inheritance. It is not fuzzy matching. It is not prospective filtering. It is not an extra-proof protocol.

## Intelligent Bypass Mechanism

The Intelligent Bypass Mechanism decides whether a learned route may execute.

At task arrival, the Pattern Recognition Engine produces S_pat.

The Adaptive Routing Database returns the applicable route record.

The system verifies that route history is sufficient.

The system checks that C_success is at or above T_bypass.

The system checks the depreciation state.

The system checks route-level structural cost.

The system checks recovery and requalification state.

The system checks anti-oscillation status.

The system checks the current tetrahedral structural-integrity record.

The system checks whether the candidate configuration matches a rejected-configuration scar.

If every required gate passes, the task may execute through P_opt.

If any required gate fails, the task goes through full analysis.

The Success Measurement System records the route outcome and updates route confidence where applicable.

T_bypass is a system parameter, not a universal constant.

A higher threshold produces more conservative bypass behavior.

A lower threshold produces more aggressive bypass behavior.

No threshold can override a failed structural-integrity gate.

No threshold can override a hard scar match.

## Recovery and Requalification

A recovery event removes bypass authority from affected routes.

The current task goes through full analysis.

The candidate route may be evaluated in shadow, but that evidence applies only to future authority.

Pre-recovery confidence cannot silently reactivate the route.

The route must earn authority again through fresh post-recovery evidence.

Persistent-failure routes may become deprecated and remain fail-closed.

A route that successfully requalifies may return to active bypass, but its authority remains conditional and revocable.

Valid structural evidence is still required after requalification.

A requalified route cannot bypass through a stale or failed structural condition.

A requalified route also cannot promote a configuration that matches a hard rejected-configuration scar as-is.

## Why Confidence Alone Is Not Enough

A naive adaptive cache treats confidence as the primary or only bypass gate.

That fails under several conditions.

A route may retain high historical confidence after the operating structure has changed.

A recovery event may invalidate observations gathered under an earlier topology or epoch.

A route may oscillate between competing pathways while each retains misleading confidence.

A route may requalify correctly and later degrade faster than its moving confidence average can detect.

The V3 simulation exposed this last limit.

In the flat harness, the first blocking gate for every eligible borderline route was the confidence gate. The additional route-level gates did not provide an earlier revocation signal.

This does not invalidate bounded authority or earned requalification.

It shows that route-level scalar evidence is insufficient as the only post-promotion degradation detector.

The V4 shape-integrity gate tested the missing structural signal. Under the declared structural-deformation workload, it withdrew authority before the inherited flat route gate and sharply reduced matched wrong bypasses.

## Tetrahedral Relationship

The tetrahedral architecture is not an analogy placed around the router after the fact.

It is the substrate the router was designed to govern.

Fact, Logic, and Coherence occupy distinct structural roles.

The coordinator observes or derives the continuing integrity of that role-separated structure.

Bounded routing uses that structural condition as an independent authority gate.

The router does not reconstruct the tetrahedron.

The recovery layer does not decide route confidence.

The confidence score does not define shape integrity.

The scar registry does not define current structural health.

The architecture depends on preserving these distinctions.

## What Bounded Routing Does Not Claim

Bounded routing is not claimed to be the fastest possible routing scheme.

It does not guarantee zero wrong bypasses.

It does not replace full analysis.

It does not prove that the selected thresholds are optimal.

It does not establish a general safety advantage across all workloads.

It does not prove production reliability.

It does not prove the complete tetrahedral architecture.

It does not prove final route scope.

It does not prove cellular shedding.

It does not prove lineage inheritance.

It does not prove fuzzy scar matching.

It does not prove prospective filtering.

It does not prove extra-proof recovery behavior.

The supported findings are narrower.

V1 supports the anti-oscillation mechanism under the tested oscillation workload.

V2 supports removal of stale authority, earned requalification through fresh evidence, and fail-closed handling of persistent-failure routes.

V3 does not support the stronger claim that the flat gate stack revokes unsafe post-promotion authority faster than simpler controls.

V4 supports the narrow claim that an independent tetrahedral shape-integrity gate can revoke unsafe bypass authority earlier than the inherited flat gate under the frozen matched structural-deformation workload.

Scar Layer V1 supports the narrow claim that a rejected-configuration scar registry can write, match, elevate, and retire scars under declared authority and evidence rules.

## Next Design Task

The next design task is cellular shedding.

The scar layer records that an authorized configuration failed and should not be promoted again as-is.

Shedding must define how damaged structure is cut away, how its authority is removed, how adjacent healthy structure carries the load, and how the system prevents the same damaged configuration from being reconstructed unchanged.

Lineage inheritance comes after shedding. It must define how regenerated structure inherits compact rejected-configuration evidence without inheriting full history.

