# File Map

## What each file is and why it exists

### Root

`README.md`
Public entry point. Mechanism summary, component overview, key results,
what this does not claim. Start here.

`ROUTING_VERDICT.md`
Honest simulation verdict. Results by phase, supported and unsupported
claims, notes on fault/drift convergence, series status.

`FILE_MAP.md`
This file.

---

### docs/

`bounded_routing_mechanism.md`
Core mechanism reference. Defines bounded routing, all four components
(PRE, ARD, SMS, IBM), the admissibility constraint, and what bounded
routing does not claim. The conceptual anchor for the whole package.

`ard_sms_bypass.md`
Component data model and parameter table. ARD entry schema,
depreciation state machine, SMS outcome scoring formula,
IBM decision sequence, anti-oscillation gate logic.
Reference document for simulation implementation.

`validation_plan.md`
What the simulation tests, why each phase was chosen, expected behavior
per arm per phase, go/no-go criteria, and scope boundaries.
Written before the simulation was run. Not updated to match results
retroactively.

---

### scripts/

`bounded_routing_sim_v1.py`
Three-arm simulation harness. Synthetic task stream with five phases:
stable, drift, fault injection, recovery event, oscillation trigger.
Deterministic seeding. All parameters documented in the file header.
Run directly: `python scripts/bounded_routing_sim_v1.py`.

---

### data/

`bounded_routing_v1_raw.csv`
One row per task per arm per seed. Fields: time_ms, pattern_id, phase,
arch, seed, bypassed, admissible, wrong_bypass, latency_ms,
structural_cost, fallback, oscillation_event, depreciation_event.

`bounded_routing_v1_summary.csv`
Aggregated metrics per arm per phase. Mean and p95 latency,
wrong bypass rate, fallback rate, admissibility violations,
oscillation events, structural cost, depreciation events,
successful bounded bypass count.

---

### plots/

`latency_by_phase_v1.png`
Mean and p95 latency per arm per phase. Shows C faster than A,
slightly slower than B in stable/drift.

`safety_metrics_v1.png`
Admissibility violations and wrong bypass rate per arm per phase.
B vs C only (A has zero violations by construction).
Oscillation phase is the clearest discriminator.

`cost_fallback_v1.png`
Mean structural cost and fallback rate per arm per phase.
Shows C fallback rising correctly during recovery phase.

`oscillation_wrong_bypass_v1.png`
Wrong bypass count per arm per phase (left panel) and oscillation-phase
detail with error bars across seeds (right panel). Shows B accumulating
~12.8 wrong bypasses per seed during oscillation; C accumulates 0.0
across all seeds. The anti-oscillation gate is the mechanism: C records
flip observations and blocks execution; B records flips and executes anyway.

`latency_timeseries_v1.png`
Rolling mean latency over time for seed=42. Phase boundaries
marked. Shows where each arm diverges.
