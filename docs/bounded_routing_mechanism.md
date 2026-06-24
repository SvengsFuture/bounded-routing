# Bounded Routing — Core Mechanism

## What this is

Bounded routing is a route-selection discipline for adaptive systems.
It governs when a learned route can be used and when a task must fall
back to full analysis. The constraint is admissibility, not only speed.

A route is selected only when all of the following remain inside bounds:

- Pattern history depth (minimum observations before a route is trusted)
- Confidence score above bypass threshold
- Structural cost within tolerance
- Recovery context allows bypass (system is not mid-recovery)
- Anti-oscillation rule not triggered (route has not recently flipped)
- Route has not been deprecated or retired

If any bound is violated, the task falls back to full analysis.
The fallback is the correct behavior, not a failure state.

---

## Components

### Pattern Recognition Engine (PRE)

Receives a task or query and produces a Pattern Signature S_pat.
S_pat is a compact descriptor that identifies which class of task
this is and what routing history applies to it.

S_pat is not a hash or cache key. It carries semantic structure:
task type, context class, structural cost estimate, and
recovery-sensitivity flag.

### Adaptive Routing Database (ARD)

Stores per-pattern routing state:

| Field | Type | Meaning |
|-------|------|---------|
| S_pat | signature | pattern identifier |
| P_opt | route | current best pathway |
| C_success | float [0,1] | route confidence score |
| obs_count | int | number of observations |
| last_used_ms | timestamp | recency |
| depreciation_state | enum | ACTIVE / WARNED / DEPRECATED / RETIRED |
| last_flip_ms | timestamp | last route change (anti-oscillation) |
| structural_cost | float | cost of this route in structural terms |

Routes are deprecated when C_success falls below a depreciation
threshold for a sustained window. Deprecated routes trigger fallback.
Retired routes are removed from ARD.

### Success Measurement System (SMS)

Updates C_success after each bypass attempt using a weighted combination:

    C_success_new = alpha * C_success_old + (1 - alpha) * outcome_score

where outcome_score is derived from:
- Latency: did the task complete within expected window?
- Admissibility: did the result satisfy structural constraints?
- Degradation: was output quality within tolerance?
- Stability: was this outcome consistent with recent history?

alpha is a decay factor. SMS is the only component that writes
C_success. No other component modifies route confidence directly.

### Intelligent Bypass Mechanism (IBM)

Decision logic at task arrival:

 1. PRE produces S_pat from the task
2. ARD lookup returns the current route state for S_pat
3. Check confidence: C_success >= T_bypass
4. Check depreciation state, structural cost, recovery context, and anti-oscillation status
5. If all five bypass checks pass: delegate along P_opt
6. If any check fails: route to full analysis
7. SMS records the outcome and ARD is updated

T_bypass is a per-system parameter, not hardcoded.
Higher T_bypass = more conservative bypass. Lower = more aggressive.

---

## Why admissibility, not just confidence

A naive adaptive cache uses confidence as the only gate.
When confidence is high, it bypasses. When low, it falls back.

This breaks under three conditions:

1. **Structural cost shift**: A route that was fast may become expensive
   if the system's load, topology, or context changes. Confidence does
   not track structural cost directly.

2. **Recovery context**: During or immediately after a system recovery
   event, previously reliable routes may be invalid. A high-confidence
   route built on pre-failure observations should not bypass into
   a changed topology.

3. **Oscillation**: A route that repeatedly flip-flops between two
   options builds false confidence on each direction. Without
   anti-oscillation gating, the system learns two contradictory routes
   and alternates between them at high confidence.

Bounded routing addresses all three by making admissibility a
structural gate, not a confidence threshold adjustment.

---

## What bounded routing does not claim

- It is not the fastest possible routing scheme
- It does not guarantee zero wrong bypasses
- It does not replace full analysis — it gates access to the bypass path
- The 120-degree spacing analogy does not apply here; topology is logical,
  not angular

The supported v1 result is narrower: bounded routing reduces latency versus full analysis and prevents oscillation-related wrong bypasses when the anti-oscillation gate is active. Drift separation is modest, recovery shows conservative fallback, and the structural-cost gate is not a strong discriminator in this configuration.
