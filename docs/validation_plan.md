# Bounded Routing — Validation Plan

> **Note:** This plan was written before the v1 run. Some expected
> discriminators did not appear in the final results. Fault and drift
> phases showed modest or no separation between Arm B and Arm C.
> The oscillation phase was the clearest discriminator. The final
> interpretation is in `ROUTING_VERDICT.md`.


## What the simulation tests

The v1 harness compares three routing architectures under a synthetic
task stream with controlled fault injection, confidence drift, and
simulated recovery events.

The goal is not to prove a speed record. The goal is to show that
bounded routing is safer and more stable than naive adaptive bypass,
while still reducing cost versus full analysis.

---

## Three arms

### Arm A — Full analysis baseline
Every task takes the full analysis path. No learned bypass, no ARD,
no confidence tracking. Latency is the worst case but admissibility
violations are zero by construction (full analysis is assumed correct).
This is the upper bound on safety and the lower bound on throughput.

### Arm B — Naive adaptive cache
Uses learned P_opt when confidence exceeds T_bypass. No structural
cost bounds, no depreciation, no anti-oscillation protection, no
recovery context gate. Represents a simple "if confidence high,
bypass" implementation.
This arm will show good throughput under stable conditions and
break down under fault injection, confidence drift, and recovery events.

### Arm C — Bounded routing
Full ARD/SMS/IBM stack. All five bypass gates active. Depreciation
state machine, anti-oscillation, recovery blackout, structural cost
bounds. Falls back to full analysis when any bound is violated.

---

## Task stream design

Tasks arrive at a configurable rate. Each task has:
- A pattern class (draws from N_PATTERNS classes)
- A true admissibility flag (some tasks are structurally hard)
- A latency profile (fast / medium / slow route options)
- A structural cost

The stream includes:
- **Stable phase**: routes are consistent, confidence builds normally
- **Drift phase**: one or more route costs increase gradually
- **Fault injection**: a route fails abruptly, outcomes drop to zero
- **Recovery event**: system signals recovery, blackout period begins
- **Oscillation trigger**: two competing routes alternate in quality

---

## Metrics collected

| Metric | Description |
|--------|-------------|
| mean_latency_ms | mean task completion time |
| p95_latency_ms | 95th percentile latency |
| wrong_bypass_rate | fraction of bypasses that produced inadmissible results |
| fallback_rate | fraction of tasks that fell back to full analysis |
| oscillation_count | number of route flip events per pattern class |
| admissibility_violations | total inadmissible results across all tasks |
| route_depreciation_events | number of ARD entries that entered DEPRECATED state |
| total_structural_cost | sum of structural cost across all tasks |
| successful_bounded_bypass | tasks correctly bypassed and admissible |

---

## Expected behavior by phase

### Stable phase
All three arms perform similarly on latency. Arm A is slowest.
Arm B and C both build bypass routes. Arm C may be slightly more
conservative (fewer bypasses due to structural cost gate).

### Drift phase
Arm B continues bypassing as confidence decays slowly.
Arm C begins fallback earlier due to structural cost gate and
depreciation mechanism. Arm B accumulates admissibility violations.
Arm C does not.

### Fault injection
Arm B bypasses into the failed route until confidence drains.
Wrong-bypass rate spikes. Arm C detects the failure through
depreciation and falls back sooner. Arm A is unaffected (always
full analysis).

### Recovery event
Arm B does not have a recovery blackout. It may bypass into
stale routes immediately after recovery.
Arm C gates all recovery-sensitive routes for T_recovery_blackout_ms.
Fallback rate temporarily increases but admissibility violations do not.

### Oscillation trigger
Arm B accumulates flip events and may alternate between two routes
at high confidence. Oscillation count rises, wrong bypasses occur.
Arm C anti-oscillation gate blocks bypass during cooldown period.
Oscillation count is suppressed.

---

## Go/no-go criteria

The validation supports the bounded routing claim if:

1. Arm C wrong_bypass_rate < Arm B wrong_bypass_rate across all phases
2. Arm C admissibility_violations < Arm B under drift and fault injection
3. Arm C oscillation_count < Arm B under oscillation trigger
4. Arm C mean_latency < Arm A mean_latency (bypass still adds value)
5. Arm C total_structural_cost <= Arm B total_structural_cost

If Arm B and Arm C perform identically, the bounded gates are not
being exercised — check that drift, fault, and oscillation phases
are actually triggering the differences.

---

## What this simulation does not prove

- Real-world latency numbers (synthetic task stream, not hardware)
- Optimal parameter values for T_bypass, alpha, etc.
- That bounded routing is superior to all possible alternatives
- Correctness of the PRE pattern signature (treated as given)

These are scope boundaries, not failures.
