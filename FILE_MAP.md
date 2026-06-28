# File Map

What each file is and why it exists.

## Root

**README.md**
Public entry point. Mechanism summary, component overview, key results, scope boundaries, and repository status. Start here.

**ROUTING_VERDICT.md**
Honest verdict for the v1 and v2 simulation series. Records supported, unsupported, and inconclusive claims without retroactively changing the tests.

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

## scripts/

**bounded_routing_sim_v1.py**
Original three-arm simulation harness. Uses stable, drift, fault, recovery, and oscillation phases. Preserved as the v1 technical record.

Run directly:

`python scripts/bounded_routing_sim_v1.py`

**bounded routing sim v2.py**
Four-arm recovery requalification simulation. Compares full analysis, naive cache restoration, timer-bound restoration, and earned restoration using fresh shadow evidence.

The script includes deterministic task manifests, state-machine assertions, primary `K=5` testing, and sensitivity runs at `K=3`, `K=5`, and `K=8`.

Run directly:

`python "scripts/bounded routing sim v2.py"`

## data/

**bounded_routing_v1_raw.csv**
One row per task, arm, and seed from the v1 harness.

**bounded_routing_v1_summary.csv**
Aggregated v1 metrics by arm and workload phase.

**bounded routing v2 recovery summary.csv**
Primary v2 recovery results. Records wrong bypasses, wrong-bypass rates, fallback behavior, requalification timing, and final route states.

**bounded routing v2 sensitivity summary.csv**
Sensitivity results for `K=3`, `K=5`, and `K=8`. Shows the tradeoff between faster restoration, fallback cost, and wrong bypass exposure.

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

## Series Status

v1 is the original bounded-routing harness.

v2 adds earned post-recovery route requalification. It shows that stale authority can be removed, qualified routes can regain authority using fresh evidence, and failed routes can remain shut down.

The overall verdict remains partial support because the current workload does not establish a general post-requalification safety advantage under later route degradation.

