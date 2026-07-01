# Bounded Routing — V3 Result and Verdict

## Recovery Requalification with Post-Authority Relapse

---

## Status

This document reports the v3 simulation result as produced by the final approved
run (`bounded routing sim v3.py`, SHA-256 `2e45f4e663...`). The simulation
mechanics, parameters, workload, assertions, and verdict are frozen. Nothing
in this document attempts to reframe the NOT SUPPORTED finding or recover the
hypothesis tested in v3.

V1 and V2 findings are unchanged and remain the standing record.

---

## What v3 tested

V2 confirmed that the requalification state machine behaves correctly: routes
lose bypass authority at the recovery signal, live tasks are handled by full
analysis while the candidate route is evaluated in shadow, and authority is
restored only after fresh evidence satisfies both the K_REQUALIFY consecutive
admissible check and the confidence floor. V2 also confirmed that pattern 0
remained fail-closed and that control-group patterns requalified cleanly.

V2 did not resolve the matched post-requalification safety comparison because
all successfully requalifying patterns had route_quality=1.0 for the remainder
of the recovery phase. No wrong bypass was structurally possible for any arm
on those routes. The comparison could not show whether Arm D's gate stack
reduced wrong bypasses relative to Arm B or Arm C after authority was restored.

V3 introduced a discriminating workload to answer the question V2 left open.
Three borderline relapse patterns (5, 6, 7) were assigned high route quality
during a clean requalification interval and then degraded after a fixed manifest
timestamp. The degradation was encoded in the manifest before any arm ran and
was identical for all arms. All arms saw the same candidate conditions on the
same tasks.

The primary new question was whether Arm D's full gate mechanism — confidence
decay, depreciation, structural-cost gate, recovery-state gate, and
anti-oscillation gate — revoked or reduced unsafe bypass authority sooner than
Arms B and C when a route it had promoted later became unreliable.

---

## Why the matched cohort was necessary

Aggregate wrong-bypass counts across the full recovery phase cannot answer the
post-promotion question cleanly because they include all wrong bypasses before
and during requalification, not only the period when D had restored authority
and all arms were operating under comparable conditions.

The matched post-requalification cohort was constructed as follows. For each
eligible (seed, pattern_id) borderline route instance, the matched comparison
window began at the first manifest task after Arm D's `requalified_at_ms` and
ran to the end of the recovery phase. All four arms were observed on the same
(seed, time_ms, pattern_id) rows. The secondary relapse-only view restricted
this further to tasks at or after the first manifest row where
`candidate_admissible == False`, isolating the period after degradation had
already begun.

Both views were defined entirely by manifest timestamps and Arm D's promotion
record. No arm's bypass or fallback decision participated in selecting the
comparison window. Assertion A8 verified this independently by reconstructing
expected key sets from timestamps alone and confirming set equality across all
four arms.

The matched design was the only valid way to ask: when a route had actually
been restored to ACTIVE status by D, and that same route then degraded, did D
reduce the resulting wrong bypass exposure relative to B and C on identical
subsequent tasks?

---

## What v2 established and what remains supported

The following findings from v2 are not touched by the v3 result and remain the
standing record:

- The requalification state machine is structurally correct. Routes enter
  REQUALIFYING on the recovery signal, are blocked from bypass, receive live
  tasks through full analysis, and are evaluated in shadow. Pre-recovery
  confidence and history do not contribute to fresh requalification confidence.
  Assertions A2, A3, A4, A5, and A14 verified this in every (seed, K) run.

- Pattern 0 (persistent failure) was held fail-closed throughout recovery in
  all seeds at all K values. It was never promoted by Arm D. Assertion A14
  verified this.

- Control-group patterns 1 through 4 produced 20 route instances across five
  seeds, and all 20 requalified cleanly at K=5. Across the complete Arm D route
  set, 35 instances ended ACTIVE and the five persistent-failure instances ended
  DEPRECATED. The requalification mechanism did not lock out genuinely safe
  routes.

- V2 found improved aggregate recovery safety for Arm D under the v2 workload.
  V3 does not reproduce that aggregate advantage under its relapse workload. In
  the v3 recovery phase, Arm D recorded 126 wrong bypasses, compared with 105
  for Arm B and 123 for Arm C. The v2 result remains part of the earlier record,
  but it must not be presented as a v3 result.

- The fail-closed REQUALIFYING → DEPRECATED transition rule, added to v3 to
  cover ordinary post-promotion SMS decay as well as the shadow requalification
  path, functioned correctly. Assertion A5 verified it at row level.

---

## What the NOT SUPPORTED verdict applies to

The NOT SUPPORTED verdict applies specifically and only to the stronger claim
that Arm D's full gate mechanism revokes unsafe post-promotion authority faster
than the simpler comparison arms.

It does not apply to the requalification mechanism itself. It does not apply
to the fail-closed behavior of deprecated routes. It does not mean that earned
requalification adds no value. What it means is that in the v3 workload, after
authority was restored, Arm D accumulated wrong bypasses on degraded routes at
a rate no lower than Arms B or C — and slightly higher than Arm B in both
matched views.

The verdict was produced by the pre-declared pipeline. Step 0 confirmed 15
eligible borderline instances with nonzero Arm B wrong bypasses, entering the
main evaluation. Step 1 confirmed 909 total matched bypasses for Arm D, ruling
out total suppression as an explanation. Step 2 found no matched safety
improvement for D over either B or C, yielding NOT SUPPORTED.

---

## Primary matched results

All 15 borderline relapse route instances (patterns 5, 6, and 7 across all five
seeds) promoted before their respective degradation onset timestamps. Assertion
A11 verified this. Every eligible instance performed actual matched bypasses.
Arm D executed 909 matched bypasses in the primary window, confirming that the
result was not produced by D avoiding exposure through permanent suppression.

**Primary matched window (2,767 eligible tasks per arm)**

| Arm | Wrong bypasses | Wrong-bypass rate | Exposure-normalized rate |
|-----|---------------|-------------------|--------------------------|
| B\_NAIVE\_CACHE | 105 | 12.04% | 37.95 per 1,000 tasks |
| C\_TIMER\_BOUND | 123 | 25.41% | 44.45 per 1,000 tasks |
| D\_REQUALIFYING | 126 | 13.86% | 45.54 per 1,000 tasks |

**Relapse-only view (2,175 eligible tasks per arm, beginning at first inadmissible manifest row)**

| Arm | Wrong bypasses | Wrong-bypass rate | Exposure-normalized rate |
|-----|---------------|-------------------|--------------------------|
| B\_NAIVE\_CACHE | 105 | 37.50% | 48.28 per 1,000 tasks |
| C\_TIMER\_BOUND | 123 | 39.68% | 56.55 per 1,000 tasks |
| D\_REQUALIFYING | 126 | 39.75% | 57.93 per 1,000 tasks |

Arm D does not show fewer matched wrong bypasses than either Arm B or Arm C in
either view. The Step 2 SUPPORTED condition requires D to be strictly below both
comparison arms in both views. That condition is not met. By the pre-declared
verdict rules, the result is NOT SUPPORTED.

Arm C's actual wrong-bypass rate (25.41%) is substantially higher than both B
(12.04%) and D (13.86%) in the primary window. This reflects that the timer
blackout reduces Arm C's bypass volume during recovery, which shrinks its
denominator while the wrong bypasses it does execute are drawn from the same
degraded routes as B and D. The timer mechanism reduces throughput without
improving per-bypass safety. That finding was already visible in v2.

---

## Gate observations

For all 15 eligible borderline route instances, the first post-degradation gate
that blocked Arm D's bypass authority was the confidence gate. Confidence decay
was the mechanism: ordinary ALPHA-weighted averaging of admissibility scores
eventually drove c_success below T_BYPASS = 0.75.

No instance had depreciation, structural-cost, anti-oscillation, or cooldown as
its first blocking gate. These gates were present in the decision stack and
would have fired given the right conditions, but in this workload, confidence
decay reached T_BYPASS before any of them triggered on any eligible borderline
route instance.

Arm B's confidence-decay mechanism, with the same ALPHA = 0.85 and the same
T_BYPASS = 0.75, responded to degradation at effectively the same rate as Arm D.
Both arms start the post-promotion window with high confidence built from the
clean requalification interval. The initial conditions are comparable, and the
decay rates under admissibility loss are governed by the same parameter. The
extra gates Arm D carries did not fire first in any instance.

---

## Sensitivity sweep results

| K | ACTIVE | REQUALIFYING | DEPRECATED | Wrong bypasses | WBR | Fallback |
|---|--------|--------------|------------|---------------|-----|---------|
| 3 | 35 | 0 | 5 | 126 | 2.73% | 38.4% |
| 5 | 35 | 0 | 5 | 126 | 2.77% | 39.3% |
| 8 | 35 | 0 | 5 | 126 | 2.84% | 40.7% |

All 15 borderline instances were eligible (promoted before degradation onset)
at K = 3, K = 5, and K = 8. Ineligible instances: 0 at all K values. The
terminal state counts of 35 ACTIVE and 5 DEPRECATED reflect 20 control-group
instances and 15 borderline relapse instances ending ACTIVE, and the 5
persistent-failure instances (pattern 0, one per seed) ending DEPRECATED.

Mean requalification time at K = 3 was 394 ms. At K = 5 it was 709 ms. At
K = 8 it was 1,154 ms. As the requalification evidence requirement increased,
routes waited longer before regaining bypass authority, and fallback rates
rose from 38.4% at K = 3 to 40.7% at K = 8, an overall increase of 2.33
percentage points.

Despite this, wrong bypass counts in the matched cohort did not change.
K = 3, K = 5, and K = 8 all produced 126 matched wrong bypasses for Arm D.
Requiring more clean shadow evidence before restoring authority delayed
restoration and increased fallback cost. It did not reduce wrong bypasses after
authority was restored, because the first gate to fire after degradation onset
in every case was ordinary confidence decay — and confidence decay is
independent of how many shadow checks preceded promotion.

---

## Assertion coverage

All assertions A1 through A16 passed. The independent reconstructions
strengthened in the corrected v3 script ran against real data:

A3 reconstructed the K most-recent shadow observation sequence for all
35 promotions from raw row records, verified admissibility, consecutiveness,
and recovery-timing from the data rather than trusting stored fields, and
confirmed that recomputed confidence agreed with stored values to within 1e-6.

A8 independently reconstructed expected key sets for both matched windows from
manifest timestamps alone and verified set equality against the produced windows
across all four arms.

A9 read the sensitivity summary CSV back from disk and compared its terminal
state counts against a fresh computation from the raw dataframe for K = 3,
K = 5, and K = 8.

A15 identified clean-interval shadow observations by timestamp and route class
rather than by post-processing state, ensuring that promotion-completing rows
(stored as ACTIVE) were included in the check.

**A6 coverage:** The assertion guarding routes that were DEPRECATED at the
recovery signal was present in all 15 (seed, K) runs and was structurally
correct. It was unexercised in every run because no route was DEPRECATED at
the moment the recovery signal fired in this workload. Pattern 0 became
DEPRECATED during the recovery phase (via its shadow fail-closed path), but
it was not DEPRECATED before the recovery signal. A6 would detect and fail
the run if a future workload placed a route in DEPRECATED state before
recovery begins.

---

## Summary of conclusions

**Conclusion 1 — Earned requalification and fail-closed recovery behavior:
SUPPORTED**

Routes correctly lose bypass authority at the recovery signal, operate through
full analysis while REQUALIFYING, restore authority only after fresh shadow
evidence satisfies the declared K and confidence gates, and remain fail-closed
once deprecated during recovery. This is the structural correctness finding
from v2 and it holds in v3.

**Conclusion 2 — Post-promotion revocation speed advantage: NOT SUPPORTED in
this workload**

After authority was restored, Arm D accumulated wrong bypasses at a rate no
lower than Arms B or C on identical matched tasks. D's 126 matched wrong
bypasses exceeded B's 105 in both the primary window and the relapse-only view.
The pre-declared verdict condition was not met.

**Conclusion 3 — Extra gates did not act before confidence decay**

In all 15 eligible borderline route instances, the first gate to block bypass
after degradation onset was the confidence gate. The depreciation, cost,
anti-oscillation, and cooldown gates were present in the gate stack and
correctly implemented, but none fired before confidence decay reached T_BYPASS
in any instance. The safety difference between Arm D and the comparison arms
in the post-promotion window, if any, would have to come from earlier or faster
confidence decay. In this workload, Arm D's confidence at the moment of
promotion was comparable to Arm B's (both were built from high-quality
clean-interval observations), and subsequent decay under the same ALPHA and the
same inadmissible bypass outcomes was comparable.

**Conclusion 4 — K sensitivity: requalification delay without relapse benefit**

Increasing K from 3 to 8 added 760 ms of mean requalification delay per route
and raised the fallback rate from 38.4% at K = 3 to 40.7% at K = 8, an overall
increase of 2.33 percentage points. It did not reduce matched wrong bypasses.
The evidence requirement controlled how long D waited before restoring
authority; it did not affect how quickly D revoked authority once degradation
began.

---

## Engineering implication

The three simulation series have now mapped the boundary of what the current
Arm D architecture accomplishes.

V1 established that the anti-oscillation gate provides genuine safety value
under the oscillation workload. V2 established that the requalification state
machine enforces structural correctness at the recovery boundary. V3 established
that the existing gate stack, once a route is ACTIVE after promotion, does not
accelerate revocation of unsafe bypass authority relative to ordinary
confidence decay.

The next design problem is not stricter initial requalification. Requiring more
shadow checks before promotion delays authority restoration and raises fallback
cost. V3's sensitivity sweep shows that this cost is real and its safety benefit
in the post-promotion window is zero in this workload.

The next design problem is adding a post-promotion revocation signal or gate
that acts before ordinary confidence decay. Confidence decay under ALPHA = 0.85
is intentionally slow and stable; it tolerates variance without overreacting.
That property is valuable for normal operation but means a degrading route
accumulates several wrong bypasses before confidence crosses T_BYPASS. A gate
that detects early degradation signals — such as a sudden drop in the SMS
admissibility component, a structural cost increase, or a stability score
collapse — and that acts at bypass-decision time rather than waiting for the
moving average to drain, is the architectural gap this series has identified.

That gate design has not been declared or validated. It is the open question
that a future series would need to address with its own pre-declared workload,
its own predeclared verdict boundaries, and its own independent assertion
coverage.
