# Bounded Routing

## What This Is

Bounded routing is a route-selection discipline for adaptive systems. It governs when a learned route may bypass full analysis and when the system must fall back.

The governing constraint is admissibility, not speed alone.

A route may bypass only while its confidence, structural cost, recovery context, depreciation state, oscillation behavior, and applicable structural conditions remain inside declared bounds.

The current simulation series provides partial support for this mechanism.

V1 showed that an anti-oscillation gate can prevent repeated wrong bypasses when confidence remains misleadingly high.

V2 showed that bypass authority can be removed after recovery and earned back using fresh evidence rather than restored automatically through elapsed time or stale confidence.

V3 showed that the current flat gate stack does not revoke unsafe post-promotion authority faster than simpler comparison controls under the tested relapse workload.

The project now records bounded routing as the authority layer for the tetrahedral recovery architecture rather than as a standalone routing system.

## Governing Architecture

Bounded routing grants, maintains, and revokes route authority.

The tetrahedral substrate supplies live structural state through the Fact, Logic, and Coherence roles and their coordinator.

The recovery layer reconstructs the tetrahedral structure when its invariants fail.

These responsibilities remain separate.

`S_pat` identifies the task and route class.

`C_success` records historical route performance.

`shape_integrity` represents the current authorized structural condition of the tetrahedral substrate.

Structural condition must remain independent of route-confidence scoring. Missing, stale, unverifiable, epoch-mismatched, or inapplicable structural state cannot preserve bypass authority.

## Core Mechanism

### Pattern Recognition Engine

The Pattern Recognition Engine receives a task and produces a pattern signature.

The signature identifies the task and route class and connects the task to the applicable routing record.

It does not determine structural integrity.

### Adaptive Routing Database

The Adaptive Routing Database stores the current learned pathway, confidence, observation history, depreciation state, route-flip history, structural cost, recovery state, and route-authority state for each pattern.

Future tetrahedral integration must also preserve the source, timestamp, epoch, and scope of any structural observation used by the routing decision.

### Success Measurement System

The Success Measurement System updates route confidence using route-level performance evidence.

Admissibility carries the highest weight.

The Success Measurement System is the only component that changes route confidence directly.

Live tetrahedral structural state must not be blended into this moving confidence value.

### Intelligent Bypass Mechanism

The Intelligent Bypass Mechanism decides whether a learned route may execute.

In the current flat harness, a route must pass the confidence, depreciation, structural-cost, recovery-context, and anti-oscillation gates.

Future tetrahedral routing adds an independent structural-integrity gate.

If any required gate fails, the task goes through full analysis.

## v1 Initial Harness

V1 compared three arms across stable, drift, fault, recovery, and oscillation phases.

Arm A always used full analysis.

Arm B used a naive confidence-based cache.

Arm C used bounded routing with the full gate stack.

The clearest v1 result occurred during route oscillation.

Arm B recorded 64 wrong bypasses.

Arm C recorded zero.

The recovery blackout increased conservative fallback, but it did not establish a general per-bypass safety advantage.

## v2 Recovery Requalification

V2 replaced timer-only restoration with earned route requalification.

A recovery event removes bypass authority.

The current task goes through full analysis.

The candidate learned route is evaluated in shadow on the same task, but that evidence applies only to future bypass authority.

Pre-recovery confidence cannot restore the route.

A route must build fresh post-recovery evidence before it may bypass again.

The primary test required five consecutive admissible shadow checks and fresh confidence of at least 0.75.

### Primary v2 Results

| Arm | Wrong bypasses | Wrong-bypass rate | Fallback rate |
|---|---:|---:|---:|
| Naive cache | 35 | approximately 1.01% | approximately 7.4% |
| Timer-bound recovery | 33 | approximately 1.38% | approximately 36.3% |
| Requalifying recovery | 0 | 0% | approximately 17.23% |

The requalifying arm did not remain locked in fallback.

Thirty-five route instances earned bypass authority back.

Five route instances failed the fresh checks and remained deprecated.

The mean requalification time for eligible routes was approximately 816 milliseconds.

### v2 Sensitivity Result

The requalification requirement was tested at three, five, and eight consecutive admissible checks.

Three checks restored authority sooner and reduced fallback, but allowed 15 wrong bypasses.

Five checks produced zero wrong bypasses with approximately 17.23 percent fallback.

Eight checks also produced zero wrong bypasses, but increased fallback to approximately 20.03 percent.

This demonstrated the expected tradeoff between restoration speed and conservative fallback in the v2 workload.

The v2 matched post-requalification comparison remained inconclusive because the routes that requalified stayed clean and the failing route remained shut down.

## v3 Post-Authority Relapse

V3 created the harder matched workload identified after v2.

Borderline routes were allowed to requalify and then degrade after bypass authority had been restored.

All arms received identical pre-generated task manifests, route conditions, degradation timing, and comparison keys.

The primary question was whether the full requalifying gate stack revoked unsafe post-promotion authority faster than the naive-cache and timer-bound comparison arms.

### Primary v3 Matched Results

| Arm | Wrong bypasses | Actual wrong-bypass rate |
|---|---:|---:|
| Naive cache | 105 | 12.04% |
| Timer-bound recovery | 123 | 25.41% |
| Requalifying recovery | 126 | 13.86% |

Arm D executed 909 matched bypasses.

Its result was not caused by permanent suppression or lack of exposure.

Arm D recorded more wrong bypasses than both comparison arms.

The first blocking gate was the confidence gate in all 15 eligible borderline route instances.

Depreciation, structural cost, anti-oscillation, and cooldown did not provide an earlier revocation signal in the tested workload.

### v3 Sensitivity Result

The v3 requalification requirement was tested at K=3, K=5, and K=8.

All three settings produced 126 wrong bypasses.

Increasing K delayed route restoration and increased fallback, but did not improve post-promotion relapse safety.

### v3 Verdict

The stronger claim that the current Arm D gate stack revokes unsafe post-promotion authority faster than simpler comparison arms is **NOT SUPPORTED**.

Earned requalification remains supported.

Removal of stale authority remains supported.

Fail-closed deprecation remains supported.

The anti-oscillation result from v1 remains supported.

The v3 result identifies a limit in the flat harness. Scalar route confidence was too slow, and the additional route-level gates did not detect degradation first.

V3 did not test live tetrahedral deformation as an independent structural signal.

## Current Verdict

The overall verdict is **PARTIAL SUPPORT**.

The simulation series supports the following claims.

Recovery can remove stale bypass authority.

Fresh evidence can govern route restoration.

Eligible routes can regain authority.

Failed routes can remain shut down.

Anti-oscillation controls can prevent repeated wrong bypasses under the tested oscillation workload.

The simulation series does not support a general claim that the current flat bounded-routing gate stack is safer than simpler controls under every workload.

It does not support the claim that increasing the requalification evidence requirement improves safety after a restored route later degrades.

The next design problem is not stricter requalification. It is defining and testing an independent tetrahedral structural-integrity signal that may withdraw authority before ordinary confidence decay detects the problem.

## Repository Structure

```text
bounded-routing/
|-- README.md
|-- ROUTING_VERDICT.md
|-- FILE_MAP.md
|-- docs/
|   |-- bounded_routing_mechanism.md
|   |-- ard_sms_bypass.md
|   |-- validation_plan.md
|   |-- validation_plan_v2.md
|   |-- validation_plan_v3.md
|   |-- V3_RESULT_AND_VERDICT.md
|   |-- TETRAHEDRAL_ROUTING_PRINCIPLE.md
|-- scripts/
|   |-- bounded_routing_sim_v1.py
|   |-- bounded routing sim v2.py
|   |-- bounded routing sim v3.py
|-- data/
|   |-- bounded_routing_v1_raw.csv
|   |-- bounded_routing_v1_summary.csv
|   |-- bounded routing v2 recovery summary.csv
|   |-- bounded routing v2 sensitivity summary.csv
|   |-- bounded_routing_v3_raw.csv
|   |-- bounded_routing_v3_summary.csv
|   |-- bounded_routing_v3_recovery_summary.csv
|   |-- bounded_routing_v3_sensitivity_summary.csv
|   |-- bounded_routing_v3_matched_comparison.csv
|   |-- bounded_routing_v3_per_route_instance.csv
|   |-- bounded_routing_v3_aggregate_metrics.csv
|   |-- manifest_seed42_v3.csv
|   |-- manifest_seed99_v3.csv
|   |-- manifest_seed500_v3.csv
|   |-- manifest_seed777_v3.csv
|   |-- manifest_seed1337_v3.csv
|   |-- bounded_routing_v3_run_record.txt
|-- plots/
    |-- latency_by_phase_v1.png
    |-- safety_metrics_v1.png
    |-- cost_fallback_v1.png
    |-- oscillation_wrong_bypass_v1.png
    |-- latency_timeseries_v1.png
    |-- recovery_wrong_bypass_timeseries_v3.png
    |-- recovery_fallback_timeseries_v3.png
    |-- requalification_by_pattern_v3.png
    |-- post_requalification_matched_v3.png
    |-- revocation_timeline_v3.png
    |-- requalification_sensitivity_v3.png

Full analysis remains the safety baseline and the correct fallback whenever bypass authority is not earned.

