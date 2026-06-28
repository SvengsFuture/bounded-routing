# Bounded Routing

## What This Is

Bounded routing is a route-selection discipline for adaptive systems. It governs when a learned route may bypass full analysis and when the system must fall back.

The governing constraint is admissibility, not speed alone.

A route is allowed to bypass only while its confidence, structural cost, recovery context, depreciation state, and oscillation behavior remain inside declared bounds.

The current simulation series provides partial support for this mechanism.

v1 showed that an anti-oscillation gate can prevent repeated wrong bypasses when confidence remains misleadingly high.

v2 showed that bypass authority can be removed after recovery and earned back using fresh evidence rather than restored automatically by time or stale confidence.

## Core Mechanism

### Pattern Recognition Engine

The Pattern Recognition Engine receives a task and produces a pattern signature. The signature identifies the task class and connects it to the applicable routing history.

### Adaptive Routing Database

The Adaptive Routing Database stores the current learned pathway, confidence, observation history, depreciation state, route-flip history, structural cost, and recovery state for each pattern.

### Success Measurement System

The Success Measurement System updates route confidence using latency, admissibility, degradation, and stability results.

Admissibility carries the highest weight.

The Success Measurement System is the only component that changes route confidence directly.

### Intelligent Bypass Mechanism

The Intelligent Bypass Mechanism decides whether a learned route may execute.

A route must pass the confidence, depreciation, structural-cost, recovery-context, and anti-oscillation gates.

If any required gate fails, the task goes through full analysis.

## v1 Initial Harness

v1 compared three arms across stable, drift, fault, recovery, and oscillation phases.

Arm A always used full analysis.

Arm B used a naive confidence-based cache.

Arm C used bounded routing with the full gate stack.

The clearest v1 result occurred during route oscillation.

Arm B recorded 64 wrong bypasses.

Arm C recorded zero.

The recovery blackout increased conservative fallback, but it did not establish a clean per-bypass safety advantage.

## v2 Recovery Requalification

v2 replaced timer-only restoration with earned route requalification.

A recovery event removes bypass authority.

The current task goes through full analysis.

The candidate learned route is evaluated in shadow on the same task, but that result applies only to future bypass authority.

Pre-recovery confidence cannot restore the route.

A route must build fresh post-recovery evidence before it may bypass again.

The primary test used five consecutive admissible shadow checks and fresh confidence of at least 0.75.

## Primary v2 Results

| Arm                   | Wrong bypasses |   Wrong-bypass rate |        Fallback rate |
| --------------------- | -------------: | ------------------: | -------------------: |
| Naive cache           |             35 | approximately 1.01% |   approximately 7.4% |
| Timer-bound recovery  |             33 | approximately 1.38% |  approximately 36.3% |
| Requalifying recovery |              0 |                  0% | approximately 17.23% |

The requalifying arm did not remain locked in fallback.

Thirty-five route instances earned bypass authority back.

Five route instances failed the fresh checks and remained deprecated.

The mean requalification time for eligible routes was approximately 816 milliseconds.

## Sensitivity Result

The requalification requirement was tested at three, five, and eight consecutive admissible checks.

Three checks restored authority sooner and reduced fallback, but allowed 15 wrong bypasses.

Five checks produced zero wrong bypasses with approximately 17.23 percent fallback.

Eight checks also produced zero wrong bypasses, but increased fallback to approximately 20.03 percent.

This shows the expected tradeoff between restoration speed and safety.

## Current Verdict

The overall verdict is **PARTIAL SUPPORT**.

The simulation supports the following claims.

Recovery can remove stale bypass authority.

Fresh evidence can govern route restoration.

Eligible routes can regain authority.

Failed routes can remain shut down.

Anti-oscillation controls can prevent repeated wrong bypasses.

The simulation does not yet prove that requalified routes remain safer than every competing arm under later degradation.

The successfully requalified routes in v2 were clean during the measured recovery period. The failing route did not requalify. A harder workload is required for a genuine matched post-requalification safety comparison.

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
|-- scripts/
|   |-- bounded_routing_sim_v1.py
|   |-- bounded routing sim v2.py
|-- data/
|   |-- bounded_routing_v1_raw.csv
|   |-- bounded_routing_v1_summary.csv
|   |-- bounded routing v2 recovery summary.csv
|   |-- bounded routing v2 sensitivity summary.csv
|-- plots/
    |-- latency_by_phase_v1.png
    |-- safety_metrics_v1.png
    |-- cost_fallback_v1.png
    |-- oscillation_wrong_bypass_v1.png
    |-- latency_timeseries_v1.png
```

## Running the Simulations

Run v1 with:

```text
python scripts/bounded_routing_sim_v1.py
```

Run v2 with:

```text
python "scripts/bounded routing sim v2.py"
```

## What This Does Not Claim

This project does not claim zero wrong bypasses under every condition.

It does not claim that the selected thresholds are optimal.

It does not claim superiority over every possible adaptive routing system.

It does not establish real-world latency.

It does not prove the correctness of the incoming pattern signature.

Full analysis remains the safety baseline and the correct fallback whenever bypass authority is not earned.

