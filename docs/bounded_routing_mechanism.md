# Bounded Routing — Core Mechanism

## What This Is

Bounded routing is a route-selection discipline for adaptive systems. It governs when a learned route may bypass full analysis and when the system must fall back.

The governing constraint is admissibility, not speed alone.

Bounded routing is the authority layer for the tetrahedral recovery architecture. It grants, maintains, and revokes route authority based on route-level evidence and the continuing structural integrity of the substrate beneath it.

A route may bypass only while every required condition remains inside declared bounds.

Those conditions include sufficient route history, confidence above the bypass threshold, structural cost within tolerance, recovery context that permits bypass, acceptable anti-oscillation state, an admissible depreciation state, and valid structural-integrity evidence from the tetrahedral substrate.

If any required condition fails, the task goes through full analysis.

Fallback is the correct safety behavior. It is not a failure state.

## Separation of Responsibilities

The tetrahedral substrate produces live structural state through the Fact, Logic, and Coherence roles and their coordinator.

The bounded-routing layer governs whether a learned route currently has execution authority.

The recovery layer reconstructs the tetrahedral structure when its invariants fail.

These responsibilities must remain separate.

Route confidence cannot substitute for structural integrity.

Structural integrity cannot be inferred from route confidence alone.

Recovery cannot silently restore earlier bypass authority.

## Pattern Recognition Engine

The Pattern Recognition Engine receives a task or query and produces a pattern signature, `S_pat`.

`S_pat` identifies the task and route class and connects the task to the applicable routing record.

It may include task type, route class, and other information required to identify the correct learned pathway.

It must not contain the current tetrahedral structural condition.

It must not be used as a substitute for live structural evidence.

Structural cost may be associated with the candidate route, but live shape integrity remains a separate input to the bypass decision.

## Adaptive Routing Database

The Adaptive Routing Database stores route-level state for each pattern.

| Field | Type | Meaning |
|---|---|---|
| `S_pat` | signature | Task and route-class identifier |
| `P_opt` | route | Current learned pathway |
| `C_success` | float `[0,1]` | Historical route-performance confidence |
| `obs_count` | integer | Number of qualifying observations |
| `last_used_ms` | timestamp | Most recent route use |
| `depreciation_state` | enum | `ACTIVE`, `WARNED`, `DEPRECATED`, or `RETIRED` |
| `last_flip_ms` | timestamp | Most recent route change |
| `structural_cost` | float | Current route-level structural cost |
| `recovery_state` | enum | Current recovery and requalification condition |
| `authority_state` | enum | Whether bypass authority is active, blocked, or being re-earned |

A deprecated route cannot bypass.

A retired route is removed from active routing.

A route affected by recovery cannot regain authority from pre-recovery confidence alone. It must satisfy the declared requalification process using fresh evidence.

The ARD may reference a structural-integrity observation used by the current decision, but that observation must retain its independent source, timestamp, epoch, and scope. It must not be collapsed into `C_success`.

## Success Measurement System

The Success Measurement System updates `C_success` from route-level performance evidence.

A general update has the form:

`C_success_new = alpha * C_success_old + (1 - alpha) * outcome_score`

The outcome score may include route latency, route admissibility, degradation, and stability.

Admissibility carries the highest weight.

The Success Measurement System is the only component that changes route confidence directly.

Live tetrahedral structural state does not become part of the moving confidence average.

`C_success` answers a historical question:

How well has this route performed?

It does not answer the structural question:

Is the tetrahedral substrate currently intact enough to permit bypass?

## Structural-Integrity Record

The tetrahedral substrate supplies a separate structural-integrity record.

A valid structural record must identify:

- the authorized source
- the observation timestamp
- the structural epoch
- the applicable route or system scope
- the Fact, Logic, and Coherence evidence or the coordinator-derived result
- the resulting structural-integrity condition

The record may expose a scalar gate result, but the underlying role-separated or geometric evidence must remain available for inspection and replay.

The record is admissible only when its source is authorized, its timestamp is fresh, its epoch matches the active substrate, and its scope applies to the route being considered.

Missing, stale, unverifiable, epoch-mismatched, or out-of-scope structural evidence cannot preserve bypass authority.

The system must fail closed to full analysis.

## Intelligent Bypass Mechanism

The Intelligent Bypass Mechanism decides whether a learned route may execute.

At task arrival:

1. The Pattern Recognition Engine produces `S_pat`.
2. The Adaptive Routing Database returns the applicable route record.
3. The system verifies that route history is sufficient.
4. The system checks that `C_success` is at or above `T_bypass`.
5. The system checks the depreciation state.
6. The system checks route-level structural cost.
7. The system checks recovery and requalification state.
8. The system checks anti-oscillation status.
9. The system checks the current tetrahedral structural-integrity record.
10. If every required gate passes, the task may execute through `P_opt`.
11. If any required gate fails, the task goes through full analysis.
12. The Success Measurement System records the route outcome and updates route confidence where applicable.

`T_bypass` is a system parameter, not a universal constant.

A higher threshold produces more conservative bypass behavior.

A lower threshold produces more aggressive bypass behavior.

No threshold can override a failed structural-integrity gate.

## Recovery and Requalification

A recovery event removes bypass authority from affected routes.

The current task goes through full analysis.

The candidate route may be evaluated in shadow, but that evidence applies only to future authority.

Pre-recovery confidence cannot silently reactivate the route.

The route must earn authority again through fresh post-recovery evidence.

Persistent-failure routes may become deprecated and remain fail-closed.

A route that successfully requalifies may return to active bypass, but its authority remains conditional and revocable.

## Why Confidence Alone Is Not Enough

A naive adaptive cache treats confidence as the primary or only bypass gate.

That fails under several conditions.

A route may retain high historical confidence after the operating structure has changed.

A recovery event may invalidate observations gathered under an earlier topology or epoch.

A route may oscillate between competing pathways while each retains misleading confidence.

A route may requalify correctly and later degrade faster than its moving confidence average can detect.

The v3 simulation exposed this last limit.

In the flat harness, the first blocking gate for every eligible borderline route was the confidence gate. The additional route-level gates did not provide an earlier revocation signal.

This does not invalidate bounded authority or earned requalification.

It shows that route-level scalar evidence is insufficient as the only post-promotion degradation detector.

The tetrahedral structural-integrity gate is intended to test whether live deformation of the substrate can withdraw authority before ordinary confidence decay responds.

## Tetrahedral Relationship

The tetrahedral architecture is not an analogy placed around the router after the fact.

It is the substrate the router was designed to govern.

Fact, Logic, and Coherence occupy distinct structural roles.

The coordinator observes or derives the continuing integrity of that role-separated structure.

Bounded routing uses that structural condition as an independent authority gate.

The router does not reconstruct the tetrahedron.

The recovery layer does not decide route confidence.

The confidence score does not define shape integrity.

The architecture depends on preserving these distinctions.

## What Bounded Routing Does Not Claim

Bounded routing is not claimed to be the fastest possible routing scheme.

It does not guarantee zero wrong bypasses.

It does not replace full analysis.

It does not prove that the selected thresholds are optimal.

It does not establish a general safety advantage across all workloads.

It does not yet prove that tetrahedral deformation provides an earlier revocation signal.

The supported findings are narrower.

V1 supports the anti-oscillation mechanism under the tested oscillation workload.

V2 supports removal of stale authority, earned requalification through fresh evidence, and fail-closed handling of persistent-failure routes.

V3 does not support the stronger claim that the current flat gate stack revokes unsafe post-promotion authority faster than simpler controls.

The next design task is to define and test the tetrahedral structural-integrity record without blending it into route confidence.
