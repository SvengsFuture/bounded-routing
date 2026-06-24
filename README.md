# Bounded Routing

## What this is

Bounded routing is a route-selection discipline for adaptive systems.
It governs when a learned route can be used and when a task must fall
back to full analysis. The constraint is admissibility, not only speed.

The supported mechanism is not that pattern matching makes routing faster.
The supported mechanism is bounded route admissibility: pattern history,
confidence, structural cost, recovery context, depreciation state, and
anti-oscillation rules jointly decide whether a learned route can execute.

In the v1 simulation, bounded routing reduces latency versus full analysis and shows its clearest safety advantage over naive confidence bypass when route instability triggers the anti-oscillation gate.


---

## Core components

**Pattern Recognition Engine (PRE)**
Receives a task and produces a Pattern Signature S_pat — a compact
descriptor identifying which class of task this is and what routing
history applies.

**Adaptive Routing Database (ARD)**
Stores per-pattern routing state: current best pathway P_opt, confidence
score C_success, observation history, depreciation state, route flip
history, and structural cost. ARD is the memory of the routing system.

**Success Measurement System (SMS)**
Updates C_success after each task using a weighted combination of
latency, admissibility, degradation, and stability scores.
Admissibility carries the highest weight. SMS is the only component
that writes confidence. No other component modifies C_success directly.

**Intelligent Bypass Mechanism (IBM)**
Five-gate decision at task arrival:
1. Confidence gate: C_success >= T_bypass?
2. Depreciation gate: route state still permits bypass?
3. Structural cost gate: cost within tolerance?
4. Recovery context gate: not in post-recovery blackout?
5. Anti-oscillation gate: flip count within bounds?

All five must pass for bypass. Any failure routes to full analysis.

---

## Repo structure

```
bounded_routing/
|-- README.md                  (this file)
|-- ROUTING_VERDICT.md         (simulation results and honest verdict)
|-- FILE_MAP.md                (what each file is and why it exists)
|-- docs/
|   |-- bounded_routing_mechanism.md   (core mechanism reference)
|   |-- ard_sms_bypass.md              (component data model and parameters)
|   |-- validation_plan.md             (what the simulation tests and why)
|-- scripts/
|   |-- bounded_routing_sim_v1.py      (three-arm simulation harness)
|-- data/
|   |-- bounded_routing_v1_raw.csv
|   |-- bounded_routing_v1_summary.csv
|-- plots/
    |-- latency_by_phase_v1.png
    |-- safety_metrics_v1.png
    |-- cost_fallback_v1.png        (annotated: recovery bar labeled as intended gating)
    |-- oscillation_wrong_bypass_v1.png  (replaces oscillation_v1: shows wrong bypass counts)
    |-- latency_timeseries_v1.png
```

---

## Key results (v1)

| Phase | B violations | C violations | Result |
|-------|-------------|-------------|--------|
| stable | 0 | 0 | Both clean |
| drift | 114 | 101 | Modest separation; structural-cost gating is not a strong discriminator in v1 |
| fault | 0 | 0 | Converged (fault is severe, both arms fall back) |
| recovery | 33 | 31 | Conservative fallback; fewer total violations, but no per-bypass safety advantage |
| oscillation | 64 | 0 | **C clearly safer** — anti-oscillation gate works |

Latency: C remains faster than full analysis across all phases.

Wrong bypass rate in oscillation phase: B=1.1%, C=0.0%.

---

## What this does not claim

- Magic speedup from pattern matching
- Zero wrong bypasses under all conditions
- Superiority over all possible adaptive schemes
- That full analysis is inferior in absolute terms — it remains the
  safety baseline and the correct fallback path

---

## Running the simulation

```bash
python scripts/bounded_routing_sim_v1.py
```

Output goes to `bounded_routing_output_v1/`. Runtime under 5 seconds.
