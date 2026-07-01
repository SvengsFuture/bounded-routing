# Bounded Routing — Simulation Verdict

**Series:** v1 initial harness, v2 recovery requalification, and v3 post-authority relapse  
**Current overall verdict:** PARTIAL SUPPORT

The simulation series tests whether learned routes should be allowed to bypass full analysis while operating conditions remain inside declared bounds. It also tests what happens when those conditions drift, oscillate, recover after disruption, and degrade again after bypass authority has been restored.

The results support bounded bypass authority as a useful control mechanism. They do not establish that bounded routing is always safer, always faster, or optimal under every workload.

The series now separates three different findings.

V1 tested bounded routing under drift, fault, recovery, and oscillation.

V2 tested whether stale route authority could be removed and earned back through fresh evidence.

V3 tested whether the full requalifying gate stack could revoke unsafe authority faster than simpler controls after a restored route degraded again.

---

## v1 — Initial Harness

V1 used three arms across stable, drift, fault, recovery, and oscillation phases.

| Arm | Label | Description |
|---|---|---|
| A | A_FULL_ANALYSIS | Every task takes the full analysis path. No bypass. |
| B | B_NAIVE_CACHE | Bypass occurs when confidence exceeds the threshold. No structural bounds, depreciation, anti-oscillation gate, or recovery blackout. |
| C | C_BOUNDED_ROUTING | Bypass requires the full ARD, SMS, and IBM gate stack to remain admissible. |

### Stable phase

All three arms behaved normally. Arms B and C built usable bypass routes. Arm C was more conservative, with approximately 7.5 percent fallback compared with 4.8 percent for Arm B.

No admissibility violations occurred.

Average latency was approximately 40 milliseconds for Arm A, 9.6 milliseconds for Arm B, and 10.5 milliseconds for Arm C.

### Drift phase

Route quality for pattern 0 degraded gradually from 1.0 to 0.2.

Arm B accumulated 114 admissibility violations. Arm C accumulated 101.

The separation was modest because confidence decay caused both arms to fall back. The structural-cost gate was not a strong discriminator in this configuration.

### Fault phase

Route quality collapsed to 0.1.

Both Arms B and C depleted confidence and returned to full analysis. Neither arm recorded an admissibility violation during this phase.

This phase did not strongly distinguish bounded routing from ordinary confidence decay. The failure was severe enough that both systems recognized it quickly.

### Recovery phase

Arm C used a fixed 5,000 millisecond blackout for recovery-sensitive routes.

Fallback increased to approximately 36.3 percent for Arm C, compared with 7.1 percent for Arm B. This shows that the recovery gate correctly forced more work through full analysis.

Arm B recorded 33 admissibility violations. Arm C recorded 31.

Arm C performed fewer bypasses, but its wrong-bypass rate was not lower. The recovery phase therefore supported conservative fallback behavior, but it did not establish a clean per-bypass safety advantage.

### Oscillation phase

Two competing routes alternated quality every four seconds.

This produced the clearest v1 separation.

Arm B recorded 64 admissibility violations. Arm C recorded zero.

The naive cache repeatedly entered the bad route while confidence remained high. The bounded arm blocked bypass during anti-oscillation cooldown periods.

The wrong-bypass rate was approximately 1.1 percent for Arm B and 0 percent for Arm C.

### v1 verdict

| Claim | Result |
|---|---|
| Bounded routing reduces violations during route oscillation | SUPPORTED |
| Bounded routing can be faster than full analysis | SUPPORTED |
| The anti-oscillation gate prevents repeated wrong bypasses in the oscillation scenario | SUPPORTED |
| The recovery blackout correctly increases fallback | SUPPORTED |
| Bounded routing is always safer than a naive cache | NOT SUPPORTED |
| Bounded routing eliminates all wrong bypasses | NOT CLAIMED AND NOT SHOWN |

V1 validated the anti-oscillation mechanism. The fixed recovery blackout produced conservative behavior, but it did not show a general recovery safety advantage.

---

## v2 — Recovery Requalification

V2 replaced timer-only restoration with earned route requalification.

A recovery event removes bypass authority. The current task goes through full analysis. The candidate learned route is then evaluated in shadow on that same task.

Shadow evidence applies only to future bypass authority.

A route cannot regain authority using confidence or history from before recovery. It must build fresh post-recovery evidence.

Deprecated routes remain fail-closed.

### v2 arms

| Arm | Label | Description |
|---|---|---|
| A | A_FULL_ANALYSIS | Every task uses full analysis. |
| B | B_NAIVE_CACHE | Learned routes resume bypass without recovery-specific requalification. |
| C | C_TIMER_BOUND | Bypass is blocked for a fixed recovery interval and then restored by time. |
| D | D_REQUALIFYING | Bypass authority is removed and must be earned again through fresh shadow evidence. |

### Requalification rule

The primary v2 test used K=5.

A route had to complete five consecutive admissible shadow checks and reach fresh confidence of at least 0.75 before returning to active bypass.

A failed shadow check reset the consecutive count and reduced fresh confidence.

Sustained fresh confidence below 0.55 could move a route into the deprecated state.

### Primary v2 results

| Arm | Wrong bypasses | Wrong-bypass rate | Fallback rate |
|---|---:|---:|---:|
| B_NAIVE_CACHE | 35 | approximately 1.01% | approximately 7.4% |
| C_TIMER_BOUND | 33 | approximately 1.38% | approximately 36.3% |
| D_REQUALIFYING | 0 | 0% | approximately 17.23% |

Arm D eliminated wrong bypasses during the measured v2 recovery workload.

It did not remain permanently locked in fallback. Thirty-five route instances earned bypass authority back.

Five route instances remained deprecated.

| State | Route instances |
|---|---:|
| ACTIVE | 35 |
| REQUALIFYING | 0 |
| DEPRECATED | 5 |

The mean time required to requalify an eligible route was approximately 816 milliseconds.

Patterns 1 through 7 successfully requalified across the five seeds. Pattern 0 failed the fresh checks, became deprecated, and remained fail-closed.

### Sensitivity results

The requalification requirement was also tested at K=3, K=5, and K=8.

| K | Active | Requalifying | Deprecated | Wrong bypasses | Wrong-bypass rate | Bypasses | Fallback rate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 37 | 0 | 3 | 15 | approximately 0.462% | 3246 | approximately 13.44% |
| 5 | 35 | 0 | 5 | 0 | 0% | 3104 | approximately 17.23% |
| 8 | 35 | 0 | 5 | 0 | 0% | 2999 | approximately 20.03% |

The sensitivity test showed the expected tradeoff.

A smaller evidence requirement restored bypass sooner and lowered fallback, but allowed wrong bypasses.

Larger evidence requirements were safer in the v2 workload, but increased fallback and delayed route restoration.

### v2 verdict

| Claim | Result |
|---|---|
| Recovery removes stale bypass authority | SUPPORTED |
| Pre-recovery confidence cannot silently restore authority | SUPPORTED |
| Eligible routes can earn authority back using fresh evidence | SUPPORTED |
| Failed routes can remain fail-closed | SUPPORTED |
| The requalifying arm eliminated wrong bypasses in the primary v2 recovery workload | SUPPORTED |
| The requalifying arm remained permanently stuck in fallback | NOT SUPPORTED |
| K=5 and K=8 were safer than K=3 in the v2 workload | SUPPORTED |
| Requalified routes were proven safer than the same routes under every competing arm | INCONCLUSIVE |
| The selected thresholds are optimal | NOT SHOWN |

### Why the v2 matched comparison was inconclusive

The successfully requalified patterns were patterns 1 through 7.

Those routes had perfect route quality during the modeled recovery phase. Once they requalified, they were not exposed to a condition that could produce a wrong bypass.

Pattern 0 was the failing route, but it did not requalify.

The matched post-requalification cohort therefore could not distinguish the arms. The routes that came back were clean, and the route that could have failed stayed shut down.

This did not invalidate the requalification mechanism. It limited the strength of the claim that could be made from the v2 workload.

V3 was created to address that limitation.

---

## v3 — Post-Authority Relapse

V3 introduced three borderline relapse patterns that could requalify cleanly and then degrade after authority was restored.

The degradation schedule was generated in shared deterministic manifests before any arm ran. All four arms saw the same candidate admissibility, latency, cost, route class, and degradation timing on the same tasks.

The primary question was whether Arm D's full gate stack revoked unsafe post-promotion bypass authority faster than the simpler Arms B and C.

### Matched cohort

All 15 borderline route instances, consisting of patterns 5, 6, and 7 across five seeds, requalified before their degradation onset.

The primary matched window began after each route's Arm D promotion timestamp and continued through the end of recovery.

The relapse-only view began at the first inadmissible manifest task for each eligible route instance.

Both windows used identical task keys across all four arms and were constructed without using any arm's bypass or fallback decisions.

### Primary matched results

| Arm | Wrong bypasses | Actual wrong-bypass rate | Exposure-normalized rate |
|---|---:|---:|---:|
| B_NAIVE_CACHE | 105 | 12.04% | 37.95 per 1,000 tasks |
| C_TIMER_BOUND | 123 | 25.41% | 44.45 per 1,000 tasks |
| D_REQUALIFYING | 126 | 13.86% | 45.54 per 1,000 tasks |

Arm D executed 909 matched bypasses. Its result was therefore not caused by permanent suppression or avoidance of exposure.

Arm D did not record fewer wrong bypasses than both comparison arms. It recorded 126, compared with 105 for Arm B and 123 for Arm C.

### Relapse-only results

| Arm | Wrong bypasses | Actual wrong-bypass rate | Exposure-normalized rate |
|---|---:|---:|---:|
| B_NAIVE_CACHE | 105 | 37.50% | 48.28 per 1,000 tasks |
| C_TIMER_BOUND | 123 | 39.68% | 56.55 per 1,000 tasks |
| D_REQUALIFYING | 126 | 39.75% | 57.93 per 1,000 tasks |

The wrong-bypass counts were unchanged in the relapse-only view because all wrong bypasses occurred after degradation had begun.

Arm D again did not outperform both comparison arms.

### Gate observations

For all 15 eligible borderline route instances, the first Arm D gate to block bypass after degradation onset was the confidence gate.

Depreciation, structural cost, anti-oscillation, and cooldown did not fire first in any eligible instance.

The extra Arm D gates were present and operational, but they did not provide an earlier revocation signal in this workload.

The router therefore relied on ordinary confidence decay, governed by the same ALPHA value and threshold used by the simpler comparison mechanisms.

### v3 sensitivity results

| K | Active | Requalifying | Deprecated | Wrong bypasses | Wrong-bypass rate | Fallback rate |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 35 | 0 | 5 | 126 | 2.73% | 38.4% |
| 5 | 35 | 0 | 5 | 126 | 2.77% | 39.3% |
| 8 | 35 | 0 | 5 | 126 | 2.84% | 40.7% |

All 15 borderline instances were eligible at K=3, K=5, and K=8.

Mean requalification time increased from approximately 394 milliseconds at K=3, to 709 milliseconds at K=5, to 1,154 milliseconds at K=8.

Fallback increased from 38.4 percent to 40.7 percent.

Wrong bypasses remained fixed at 126.

Increasing the evidence requirement delayed restoration and increased fallback cost, but did not improve post-promotion relapse safety.

### v3 assertion coverage

Assertions A1 through A16 passed.

The run verified shared-manifest integrity, post-recovery evidence isolation, independent promotion reconstruction, no bypass while requalifying, fail-closed deprecation behavior, matched key identity, matched-window independence, final-state accounting, requalification timing, eligibility ordering, admissibility construction, verdict-branch behavior, pattern 0 non-promotion, clean-interval SMS floors, and manifest coverage.

A6 was present but unexercised because no route was already deprecated at the moment the recovery signal fired.

### v3 verdict

| Claim | Result |
|---|---|
| Earned requalification remains structurally correct | SUPPORTED |
| Persistent-failure routes remain fail-closed | SUPPORTED |
| Eligible routes regain authority using fresh evidence | SUPPORTED |
| Arm D performs real post-promotion bypasses | SUPPORTED |
| Arm D revokes unsafe post-promotion authority faster than both simpler comparison arms | NOT SUPPORTED |
| Increasing K improves post-promotion relapse safety | NOT SUPPORTED |
| The extra gate stack acted before confidence decay | NOT SUPPORTED |
| The selected v3 thresholds are optimal | NOT SHOWN |

The pre-declared v3 verdict was NOT SUPPORTED.

That verdict applies specifically to the stronger claim that Arm D's full gate stack provides an earlier post-promotion revocation advantage under the v3 relapse workload.

It does not invalidate earned requalification, fail-closed deprecation, or the anti-oscillation result from v1.

---

## Tetrahedral Architecture Boundary

V3 tested the router in a flat harness.

No live Fact, Logic, or Coherence signals participated in the bypass decision. No tetrahedral coordinator produced a structural integrity observation. Route quality was encoded directly in the manifest, and the router was required to infer degradation through route-level scalar evidence.

The v3 result therefore does not test whether deformation of the tetrahedral substrate can provide an earlier revocation signal.

The project-level architecture principle is now:

**Bounded routing is the authority layer for the tetrahedral recovery architecture. It grants, maintains, and revokes route authority based on route-level evidence and the continuing structural integrity of the tetrahedral substrate beneath it.**

The tetrahedral layer produces role-separated structural state.

The routing layer governs bypass authority.

The recovery layer reconstructs the structure when its invariants fail.

The router must preserve the distinction among task identity, historical route performance, and current structural condition.

`S_pat` identifies the task and route class.

`C_success` records historical route performance.

`shape_integrity` represents the current authorized structural condition of the tetrahedral substrate.

Structural state must come from the tetrahedral coordinator or another authorized structural observer. It must carry source, timestamp, epoch, and applicable scope.

Missing, stale, unverifiable, epoch-mismatched, or inapplicable structural state cannot preserve bypass authority.

Structural condition must remain an independent gate and must not be blended into the SMS moving average.

The v3 NOT SUPPORTED verdict remains unchanged. Future tetrahedral routing work will test a different mechanism: whether live role-separated or coordinator-derived structural deformation can revoke route authority before ordinary confidence decay detects the problem.

---

## Overall Series Verdict

The honest overall verdict remains PARTIAL SUPPORT.

V1 supports anti-oscillation control under the tested oscillation workload.

V2 supports removal of stale authority, earned requalification through fresh shadow evidence, and fail-closed handling of persistent-failure routes.

V3 does not support the stronger claim that the current flat Arm D gate stack revokes unsafe post-promotion authority faster than simpler controls.

The series supports bounded authority around learned routing, but not a general claim of superior safety across all workloads.

The strongest architectural result is that bypass authority can be treated as temporary, conditional, and revocable rather than as a permanent consequence of earlier confidence.

The clearest current limitation is that route-level scalar confidence is too slow to serve as the sole post-promotion degradation detector.

The next design problem is not stricter initial requalification. It is defining a live tetrahedral deformation signal that remains independent of route confidence and can participate directly in the bypass decision.

---

## What the Simulation Series Does Not Prove

The series does not prove real-world latency.

It does not prove that the selected thresholds are optimal.

It does not prove that bounded routing outperforms every possible adaptive routing method.

It does not prove the correctness of the incoming task-pattern signature, which is treated as given.

It does not prove that every successfully requalified route will remain safe under later degradation.

It does not establish a general safety advantage across all workloads.

It does not yet prove that tetrahedral deformation provides an earlier revocation signal.

It does not yet define or validate a shape-integrity formula, threshold, freshness interval, route scope, or coordinator schema.

---

## Series Status

V1 is preserved as the initial bounded-routing harness.

V2 is preserved as the first recovery requalification test.

V3 is preserved as the matched post-authority relapse test.

The v3 script, manifests, data, plots, assertions, final run record, and result document form the current executable checkpoint.

The tetrahedral routing principle records the architectural boundary for future work.

The next step is an architecture-level definition of candidate tetrahedral deformation measures before any v4 simulation is written.
