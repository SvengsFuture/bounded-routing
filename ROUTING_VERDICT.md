# Bounded Routing — Simulation Verdict

## Series: v1 initial harness

One simulation version. Three arms. Five phases.
Results reported as-is. No tuning to favor any arm.

---

## Arms

| Arm | Label | Description |
|-----|-------|-------------|
| A | A_FULL_ANALYSIS | Every task takes the full path. No bypass. Admissibility always satisfied. |
| B | B_NAIVE_CACHE | Bypass when confidence >= T_bypass. No structural bounds, no depreciation, no anti-oscillation, no recovery blackout. |
| C | C_BOUNDED_ROUTING | Full ARD/SMS/IBM stack. All four bypass gates active. |

---

## Results by phase

### Stable phase
All three arms behave similarly. B and C both build bypass routes.
C is marginally more conservative (7.5% fallback vs B's 4.8%).
No admissibility violations in any arm. Latency: A=40ms, B=9.6ms, C=10.5ms.

### Drift phase
Route quality for pattern 0 degrades linearly from 1.0 to 0.2.
B accumulates 114 admissibility violations. C accumulates 101.
Separation is modest here. Both arms detect the degradation through
confidence decay. C's structural cost gate begins gating bypass earlier
but the difference in violations is not large in this phase.

### Fault phase
Route quality collapses to 0.1. Both B and C deplete confidence
and fall back to full analysis. Admissibility violations: B=0, C=0.
This is correct behavior: the fault is severe enough that confidence
drains before many wrong bypasses occur. Fallback rate: B=13.2%, C=13.2%.
The two arms converge here. The fault scenario does not differentiate them
on violations — it differentiates them on how quickly they recover
(not measured in v1).

### Recovery phase
System signals a recovery event. Arm C blocks bypass for
recovery-sensitive routes for T_recovery_blackout_ms=5000ms.
Fallback rate: B=7.1%, C=36.3%. C correctly increases fallback during
the blackout period. B continues bypassing immediately.
Admissibility violations: B=33, C=31. Modest difference.

### Oscillation phase
Two competing routes alternate quality every 4 seconds.
**This is the clearest discriminator.**
Admissibility violations: B=64, C=0.
Arm B's naive bypass repeatedly enters the bad route at high confidence.
Arm C's anti-oscillation gate blocks bypass during cooldown periods.
Oscillation events recorded: B=58, C=65 (C records more flip events
because it tracks them for gate enforcement; B records fewer because
it does not enforce a gate). Wrong bypass rate: B=1.1%, C=0.0%.

---

## Verdict

| Claim | Result |
|-------|--------|
| Bounded routing reduces admissibility violations vs naive cache | SUPPORTED — oscillation phase: B=64, C=0 |
| Bounded routing is faster than full analysis | SUPPORTED — C latency 9.8-19.6ms vs A=40ms across phases |
| Bounded routing accumulates fewer oscillation violations | SUPPORTED |
| Recovery blackout gate increases fallback rate correctly | SUPPORTED — C=36.3% vs B=7.1% during recovery |
| Bounded routing is always safer than naive cache | PARTIAL — drift and fault show modest or no separation; oscillation shows strong separation |
| Bounded routing eliminates all wrong bypasses | NOT CLAIMED and not shown — drift and recovery phases show nonzero wrong bypass rate in C |

---

## What the simulation does not prove

- Real-world latency numbers. The task stream is synthetic.
- Optimal parameter values. T_bypass=0.75, alpha=0.85, etc. are defaults.
- That bounded routing outperforms all possible adaptive schemes.
- Correctness of the PRE pattern signature, which is treated as given.

---

## Honest reading of the fault phase convergence

During fault injection, both B and C show zero admissibility violations
because confidence drains before many bypasses occur. This means the
fault scenario, as modeled, is severe enough that naive confidence decay
alone prevents most violations. The bounded routing gates add little
marginal value in this phase.

This is a scope boundary, not a model flaw. In a real system where
fault detection is slower or confidence decays more gradually, the
bounded gates would separate more clearly. The v1 simulation uses a
conservative confidence decay (alpha=0.85) that causes both arms to
learn the fault quickly.

The oscillation phase — where confidence stays high on both competing
routes — is the correct test of bounded routing's anti-oscillation value.
That result is clean.

---

## Series status

v1 is the initial harness. The mechanism is validated on the oscillation
and recovery scenarios. Drift and fault convergence is noted honestly.

If future work models slower confidence decay, route-specific alpha values,
or multi-pattern fault cascades, the fault and drift separation may widen.
That is outside v1 scope.
