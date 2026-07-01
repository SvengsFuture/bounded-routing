# File Map

What each file is and why it exists.

## Root

**README.md**  
Public entry point. Mechanism summary, component overview, key results, scope boundaries, and repository status. Start here.

**ROUTING_VERDICT.md**  
Current bounded-routing verdict record. Summarizes the supported, unsupported, and unresolved findings across the simulation series without retroactively changing earlier tests.

**FILE_MAP.md**  
This file.

## docs/

**bounded_routing_mechanism.md**  
Core mechanism reference. Defines bounded routing, the PRE, ARD, SMS, and IBM components, the admissibility constraint, and the limits of the claim.

**ard_sms_bypass.md**  
Component data model and parameter reference. Includes the ARD entry structure, depreciation states, SMS scoring, IBM decision sequence, and anti-oscillation gate logic.

**validation_plan.md**  
Original v1 validation plan. Defines the three simulation arms, five workload phases, expected behavior, go/no-go criteria, and scope boundaries. Written before the v1 simulation was run.

**validation_plan_v2.md**  
Pre-run plan for the v2 recovery requalification test. Defines the four arms, fresh post-recovery evidence requirement, route-state transitions, sensitivity values, assertions, and partial-support verdict boundary.

**validation_plan_v3.md**  
Frozen pre-run plan for the v3 post-requalification relapse test. Defines the matched comparison cohort, three route classes, fixed degradation schedules, K sensitivity sweep, assertions A1 through A16, output requirements, and the pre-declared verdict pipeline.

**V3_RESULT_AND_VERDICT.md**  
Final v3 result record. Reports the matched post-requalification comparison, sensitivity results, assertion coverage, NOT SUPPORTED verdict, and the engineering boundary exposed by the test.

**TETRAHEDRAL_ROUTING_PRINCIPLE.md**  
Project-level architecture principle connecting bounded routing to the tetrahedral recovery substrate. Defines signal separation, provenance, freshness, epoch integrity, structural scope, integration sites, and constraints for future tetrahedral routing work.

## scripts/

**bounded_routing_sim_v1.py**  
Original three-arm simulation harness. Uses stable, drift, fault, recovery, and oscillation phases. Preserved as the v1 technical record.

Run directly: `python scripts/bounded_routing_sim_v1.py`

**bounded routing sim v2.py**  
Four-arm recovery requalification simulation. Compares full analysis, naive cache restoration, timer-bound restoration, and earned restoration using fresh shadow evidence.

The script includes deterministic task manifests, state-machine assertions, primary K=5 testing, and sensitivity runs at K=3, K=5, and K=8.

Run directly: `python "scripts/bounded routing sim v2.py"`

**bounded routing sim v3.py**  
Final v3 post-requalification relapse simulation. Uses shared pre-generated manifests, matched post-promotion comparison windows, borderline relapse patterns, sensitivity runs at K=3, K=5, and K=8, and assertions A1 through A16.

The script tests whether the full requalifying gate stack revokes unsafe post-promotion bypass authority faster than the simpler comparison arms.

Run directly: `python "scripts/bounded routing sim v3.py"`

## data/

**bounded_routing_v1_raw.csv**  
One row per task, arm, and seed from the v1 harness.

**bounded_routing_v1_summary.csv**  
Aggregated v1 metrics by arm and workload phase.

**bounded routing v2 recovery summary.csv**  
Primary v2 recovery results. Records wrong bypasses, wrong-bypass rates, fallback behavior, requalification timing, and final route states.

**bounded routing v2 sensitivity summary.csv**  
Sensitivity results for K=3, K=5, and K=8. Shows the tradeoff between faster restoration, fallback cost, and wrong-bypass exposure.

**bounded_routing_v3_raw.csv**  
Complete v3 task-level output across arms, seeds, phases, and K values.

**bounded_routing_v3_summary.csv**  
Aggregated v3 results by arm and workload phase.

**bounded_routing_v3_recovery_summary.csv**  
Primary v3 recovery-phase metrics, including bypass, wrong-bypass, fallback, and route-state results.

**bounded_routing_v3_sensitivity_summary.csv**  
Arm D sensitivity results for K=3, K=5, and K=8, including requalification timing, fallback cost, wrong bypasses, eligibility, and final route states.

**bounded_routing_v3_matched_comparison.csv**  
Primary and relapse-only matched cohort results for Arms A, B, C, and D on identical post-requalification task keys.

**bounded_routing_v3_per_route_instance.csv**  
One row per borderline route instance with promotion timing, degradation onset, eligibility, state history, revocation timing, and per-arm matched metrics.

**bounded_routing_v3_aggregate_metrics.csv**  
Aggregate v3 matched-window, relapse-window, revocation, gate, and requalification metrics.

**manifest_seed42_v3.csv**  
**manifest_seed99_v3.csv**  
**manifest_seed500_v3.csv**  
**manifest_seed777_v3.csv**  
**manifest_seed1337_v3.csv**  
Shared deterministic task manifests used by every v3 arm. Each manifest was generated and validated before arm execution.

**bounded_routing_v3_run_record.txt**  
Final execution record containing environment versions, runtime, script and artifact hashes, assertion results, verdict path, key metrics, and complete file inventory.

## plots/

**latency_by_phase_v1.png**  
Mean and p95 latency by arm and v1 workload phase.

**safety_metrics_v1.png**  
Admissibility violations and wrong-bypass rates by arm and phase.

**cost_fallback_v1.png**  
Structural cost and fallback behavior by arm and phase.

**oscillation_wrong_bypass_v1.png**  
Wrong bypasses by phase and oscillation detail across seeds. Shows the strongest v1 anti-oscillation separation.

**latency_timeseries_v1.png**  
Rolling mean latency for seed 42 with phase boundaries marked.

**recovery_wrong_bypass_timeseries_v3.png**  
Cumulative wrong bypasses during the v3 recovery phase for the naive-cache, timer-bound, and requalifying arms.

**recovery_fallback_timeseries_v3.png**  
Fallback-rate progression during the v3 recovery phase.

**requalification_by_pattern_v3.png**  
Requalification timing by control and borderline relapse pattern, with degradation-onset boundaries shown for the borderline group.

**post_requalification_matched_v3.png**  
Primary matched-cohort comparison of wrong-bypass count, exposure-normalized rate, and actual wrong-bypass rate.

**revocation_timeline_v3.png**  
Per-instance timing of first wrong bypasses, confidence-gate failure, and Arm D authority blocking after degradation begins.

**requalification_sensitivity_v3.png**  
K=3, K=5, and K=8 comparison of Arm D wrong-bypass and fallback rates, with route-state and eligibility counts.

## Series Status

V1 is the original bounded-routing harness and established the clearest anti-oscillation separation.

V2 added earned post-recovery route requalification. It showed that stale authority can be removed, qualified routes can regain authority using fresh evidence, and persistent-failure routes can remain fail-closed.

V3 added matched post-requalification relapse conditions. Earned requalification and fail-closed recovery behavior remained supported. The stronger claim that the full Arm D gate stack revokes unsafe post-promotion authority faster than the simpler comparison arms was NOT SUPPORTED in the v3 workload.

The tetrahedral routing principle now records that bounded routing is an authority layer for the tetrahedral recovery architecture rather than a standalone system. Future work must preserve live role-separated or coordinator-derived structural state as an independent bypass condition.
