# File Map

What each file is and why it exists.

## Root

README.md

Public entry point. Mechanism summary, current status, V4 shape-gate result, scar-layer result, scope boundaries, and repository status. Start here.

ROUTING_VERDICT.md

Current bounded-routing verdict record. Summarizes the supported, unsupported, and unresolved findings across the simulation series without retroactively changing earlier tests.

FILE_MAP.md

This file.

## docs/

bounded_routing_mechanism.md

Core mechanism reference. Defines bounded routing, the PRE, ARD, SMS, and IBM components, the admissibility constraint, and the limits of the claim.

ard_sms_bypass.md

Component data model and parameter reference. Includes the ARD entry structure, depreciation states, SMS scoring, IBM decision sequence, and anti-oscillation gate logic.

validation_plan.md

Original V1 validation plan. Defines the three simulation arms, five workload phases, expected behavior, go/no-go criteria, and scope boundaries. Written before the V1 simulation was run.

validation_plan_v2.md

Pre-run plan for the V2 recovery requalification test. Defines the four arms, fresh post-recovery evidence requirement, route-state transitions, sensitivity values, assertions, and partial-support verdict boundary.

validation_plan_v3.md

Frozen pre-run plan for the V3 post-requalification relapse test. Defines the matched comparison cohort, three route classes, fixed degradation schedules, K sensitivity sweep, assertions A1 through A16, output requirements, and the pre-declared verdict pipeline.

V3_RESULT_AND_VERDICT.md

Final V3 result record. Reports the matched post-requalification comparison, sensitivity results, assertion coverage, NOT SUPPORTED verdict, and the engineering boundary exposed by the test.

TETRAHEDRAL_ROUTING_PRINCIPLE.md

Project-level architecture principle connecting bounded routing to the tetrahedral recovery substrate. Defines signal separation, provenance, freshness, epoch integrity, structural scope, integration sites, and constraints for tetrahedral routing work.

TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1.md

Frozen shape-integrity specification. Defines the independent tetrahedral structural condition used by bounded routing as a separate bypass-authority gate.

TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md

Frozen V4 validation plan for the shape-integrity gate. Defines the matched structural-deformation workload, comparison arms, assertions, expected outputs, and verdict boundary.

V4_SHAPE_GATE_VERDICT.md

Final V4 shape-gate result record. Reports the SUPPORTED verdict, 26/26 assertions, 96.53 percent wrong-bypass reduction, clean suppression check, and limits of the claim.

REJECTED_CONFIGURATION_SCAR_SPEC_v1_REVISED.md

Revised scar-layer specification. Defines the rejected-configuration scar primitive and the governing rule that only betrayed authority creates a scar.

REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1_FROZEN.md

Frozen scar validation plan. Defines the scar write boundary, geometry-only fingerprinting, match behavior, elevation threshold, retirement rule, assertions, and scope exclusions.

REJECTED_CONFIGURATION_SCAR_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md

Final scar validation result record. Reports the SUPPORTED verdict, 30/30 assertions, clean stderr, runtime, hashes, and limits of the scar-layer claim.

## scripts/

bounded_routing_sim_v1.py

Original three-arm simulation harness. Uses stable, drift, fault, recovery, and oscillation phases. Preserved as the V1 technical record.

Run directly:

python scripts/bounded_routing_sim_v1.py

bounded routing sim v2.py

Four-arm recovery requalification simulation. Compares full analysis, naive cache restoration, timer-bound restoration, and earned restoration using fresh shadow evidence.

Run directly:

python "scripts/bounded routing sim v2.py"

bounded routing sim v3.py

Final V3 post-requalification relapse simulation. Uses shared pre-generated manifests, matched post-promotion comparison windows, borderline relapse patterns, sensitivity runs at K=3, K=5, and K=8, and assertions A1 through A16.

Run directly:

python "scripts/bounded routing sim v3.py"

rejected_configuration_scar_sim_v1_REVIEWED.py

Reviewed scar validation harness. Implements the frozen scar plan without shedding, lineage inheritance, fuzzy matching, prospective filtering, or extra-proof protocol claims.

Run directly:

python scripts/rejected_configuration_scar_sim_v1_REVIEWED.py

## data/

bounded_routing_v1_raw.csv

One row per task, arm, and seed from the V1 harness.

bounded_routing_v1_summary.csv

Aggregated V1 metrics by arm and workload phase.

bounded routing v2 recovery summary.csv

Primary V2 recovery results. Records wrong bypasses, wrong-bypass rates, fallback behavior, requalification timing, and final route states.

bounded routing v2 sensitivity summary.csv

Sensitivity results for K=3, K=5, and K=8. Shows the tradeoff between faster restoration, fallback cost, and wrong-bypass exposure.

bounded_routing_v3_raw.csv

Complete V3 task-level output across arms, seeds, phases, and K values.

bounded_routing_v3_summary.csv

Aggregated V3 results by arm and workload phase.

bounded_routing_v3_recovery_summary.csv

Primary V3 recovery-phase metrics, including bypass, wrong-bypass, fallback, and route-state results.

bounded_routing_v3_sensitivity_summary.csv

Arm D sensitivity results for K=3, K=5, and K=8, including requalification timing, fallback cost, wrong bypasses, eligibility, and final route states.

bounded_routing_v3_matched_comparison.csv

Primary and relapse-only matched cohort results for Arms A, B, C, and D on identical post-requalification task keys.

bounded_routing_v3_per_route_instance.csv

One row per borderline route instance with promotion timing, degradation onset, eligibility, state history, revocation timing, and per-arm matched metrics.

bounded_routing_v3_aggregate_metrics.csv

Aggregate V3 matched-window, relapse-window, revocation, gate, and requalification metrics.

manifest_seed42_v3.csv

Shared deterministic task manifest used by every V3 arm for seed 42.

manifest_seed99_v3.csv

Shared deterministic task manifest used by every V3 arm for seed 99.

manifest_seed500_v3.csv

Shared deterministic task manifest used by every V3 arm for seed 500.

manifest_seed777_v3.csv

Shared deterministic task manifest used by every V3 arm for seed 777.

manifest_seed1337_v3.csv

Shared deterministic task manifest used by every V3 arm for seed 1337.

bounded_routing_v3_run_record.txt

Final V3 execution record containing environment versions, runtime, script and artifact hashes, assertion results, verdict path, key metrics, and complete file inventory.

rejected_configuration_scar_v1_raw.csv

Task-level scar validation output.

rejected_configuration_scar_v1_summary.csv

Primary scar validation summary metrics.

rejected_configuration_scar_v1_scenario_summary.csv

Scenario-level scar validation summary.

rejected_configuration_scar_v1_scar_registry.csv

Final scar registry output produced by the reviewed scar validation harness.

rejected_configuration_scar_v1_assertions.csv

Assertion-by-assertion scar validation results.

rejected_configuration_scar_v1_verdict.csv

Final scar verdict output.

rejected_configuration_scar_v1_run_record.txt

Scar validation execution record, including runtime, hashes, assertion status, and output inventory.

## plots/

latency_by_phase_v1.png

Mean and p95 latency by arm and V1 workload phase.

safety_metrics_v1.png

Admissibility violations and wrong-bypass rates by arm and phase.

cost_fallback_v1.png

Structural cost and fallback behavior by arm and phase.

oscillation_wrong_bypass_v1.png

Wrong bypasses by phase and oscillation detail across seeds. Shows the strongest V1 anti-oscillation separation.

latency_timeseries_v1.png

Rolling mean latency for seed 42 with phase boundaries marked.

recovery_wrong_bypass_timeseries_v3.png

Cumulative wrong bypasses during the V3 recovery phase for the naive-cache, timer-bound, and requalifying arms.

recovery_fallback_timeseries_v3.png

Fallback-rate progression during the V3 recovery phase.

requalification_by_pattern_v3.png

Requalification timing by control and borderline relapse pattern, with degradation-onset boundaries shown for the borderline group.

post_requalification_matched_v3.png

Primary matched-cohort comparison of wrong-bypass count, exposure-normalized rate, and actual wrong-bypass rate.

revocation_timeline_v3.png

Per-instance timing of first wrong bypasses, confidence-gate failure, and Arm D authority blocking after degradation begins.

requalification_sensitivity_v3.png

K=3, K=5, and K=8 comparison of Arm D wrong-bypass and fallback rates, with route-state and eligibility counts.

scar_v1_assertion_status.png

Scar validation assertion-status plot.

scar_v1_write_boundary.png

Scar validation write-boundary plot showing when scars are and are not created.

scar_v1_match_behavior.png

Scar validation match-behavior plot showing hard, soft, restoration, and no-match behavior.

scar_v1_elevation_retirement.png

Scar validation elevation and retirement plot.

## Series Status

V1 is the original bounded-routing harness and established the clearest anti-oscillation separation.

V2 added earned post-recovery route requalification. It showed that stale authority can be removed, qualified routes can regain authority using fresh evidence, and persistent-failure routes can remain fail-closed.

V3 added matched post-requalification relapse conditions. Earned requalification and fail-closed recovery behavior remained supported. The stronger claim that the full Arm D gate stack revokes unsafe post-promotion authority faster than the simpler comparison arms was NOT SUPPORTED in the V3 workload.

V4 added the independent tetrahedral shape-integrity gate. Under the frozen matched structural-deformation workload, the shape gate reduced matched wrong bypasses from 404 to 14 and supported the narrow claim that live structural evidence can revoke unsafe bypass authority earlier than the inherited flat gate.

The scar layer added a compact rejected-configuration registry. Under the frozen scar validation plan, scars were written only for betrayed authority, matched by exact geometry-only fingerprint, elevated only after the declared threshold, and retired only after declared successful cycles.

The next architectural work is cellular shedding, followed by lineage inheritance.
