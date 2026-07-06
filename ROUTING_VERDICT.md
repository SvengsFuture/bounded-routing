# Bounded Routing Simulation Verdict

Series: V1 initial harness, V2 recovery requalification, V3 post-authority relapse, V4 shape-integrity gate, and Scar Layer V1.

Current overall verdict: PARTIAL SUPPORT.

The simulation series tests whether learned routes should be allowed to bypass full analysis while operating conditions remain inside declared bounds. It also tests what happens when those conditions drift, oscillate, recover after disruption, degrade again after bypass authority has been restored, and fail under live structural conditions.

The results support bounded bypass authority as a useful control mechanism. They do not establish that bounded routing is always safer, always faster, or optimal under every workload.

The series now separates five findings.

V1 tested bounded routing under drift, fault, recovery, and oscillation.

V2 tested whether stale route authority could be removed and earned back through fresh evidence.

V3 tested whether the full requalifying gate stack could revoke unsafe authority faster than simpler controls after a restored route degraded again.

V4 tested whether an independent tetrahedral shape-integrity gate could revoke unsafe bypass authority earlier than the inherited flat gate under a frozen matched structural-deformation workload.

Scar Layer V1 tested whether a minimal rejected-configuration registry could write, match, elevate, and retire scars only under declared authority and evidence rules.

## V1 Initial Harness

V1 used three arms across stable, drift, fault, recovery, and oscillation phases.

Arm A was full analysis. Every task took the full analysis path and no bypass was allowed.

Arm B was the naive cache. Bypass occurred when confidence exceeded the threshold, without structural bounds, depreciation, anti-oscillation control, or recovery blackout.

Arm C was bounded routing. Bypass required the full ARD, SMS, and IBM gate stack to remain admissible.

The clearest V1 separation occurred during route oscillation. Two competing routes alternated quality every four seconds. Arm B recorded 64 admissibility violations. Arm C recorded zero.

The naive cache repeatedly entered the bad route while confidence remained high. The bounded arm blocked bypass during anti-oscillation cooldown periods.

V1 supports the anti-oscillation mechanism under the tested oscillation workload. It does not prove that bounded routing is always safer than a naive cache. The fixed recovery blackout produced conservative fallback behavior, but it did not show a general recovery safety advantage.

## V2 Recovery Requalification

V2 replaced timer-only restoration with earned route requalification.

A recovery event removes bypass authority. The current task goes through full analysis. The candidate learned route is then evaluated in shadow on that same task. Shadow evidence applies only to future bypass authority.

A route cannot regain authority using confidence or history from before recovery. It must build fresh post-recovery evidence.

Deprecated routes remain fail-closed.

The primary V2 test used K=5. A route had to complete five consecutive admissible shadow checks and reach fresh confidence of at least 0.75 before returning to active bypass.

The primary V2 result was:

B_NAIVE_CACHE wrong bypasses: 35.

C_TIMER_BOUND wrong bypasses: 33.

D_REQUALIFYING wrong bypasses: 0.

B_NAIVE_CACHE fallback rate: approximately 7.4 percent.

C_TIMER_BOUND fallback rate: approximately 36.3 percent.

D_REQUALIFYING fallback rate: approximately 17.23 percent.

Arm D eliminated wrong bypasses during the measured V2 recovery workload. It did not remain permanently locked in fallback. Thirty-five route instances earned bypass authority back. Five route instances remained deprecated.

The mean time required to requalify an eligible route was approximately 816 milliseconds.

The V2 sensitivity test showed the expected tradeoff. K=3 restored bypass sooner and lowered fallback, but allowed 15 wrong bypasses. K=5 and K=8 produced zero wrong bypasses in the V2 workload, but increased fallback and delayed restoration.

V2 supports stale-authority removal, earned restoration through fresh evidence, and fail-closed handling of persistent-failure routes. It does not prove that the selected thresholds are optimal.

## V3 Post-Authority Relapse

V3 introduced three borderline relapse patterns that could requalify cleanly and then degrade after authority was restored.

The degradation schedule was generated in shared deterministic manifests before any arm ran. All four arms saw the same candidate admissibility, latency, cost, route class, and degradation timing on the same tasks.

The primary question was whether Arm D's full gate stack revoked unsafe post-promotion bypass authority faster than the simpler Arms B and C.

All 15 borderline route instances, consisting of patterns 5, 6, and 7 across five seeds, requalified before their degradation onset.

The primary matched result was:

B_NAIVE_CACHE wrong bypasses: 105.

C_TIMER_BOUND wrong bypasses: 123.

D_REQUALIFYING wrong bypasses: 126.

B_NAIVE_CACHE actual wrong-bypass rate: 12.04 percent.

C_TIMER_BOUND actual wrong-bypass rate: 25.41 percent.

D_REQUALIFYING actual wrong-bypass rate: 13.86 percent.

Arm D executed 909 matched bypasses. Its result was therefore not caused by permanent suppression or avoidance of exposure.

Arm D did not record fewer wrong bypasses than both comparison arms.

For all 15 eligible borderline route instances, the first Arm D gate to block bypass after degradation onset was the confidence gate. Depreciation, structural cost, anti-oscillation, and cooldown did not fire first in any eligible instance.

The extra Arm D gates were present and operational, but they did not provide an earlier revocation signal in this workload. The router relied on ordinary confidence decay.

V3 does not support the stronger claim that the flat Arm D gate stack revokes unsafe post-promotion authority faster than simpler comparison arms. It does not invalidate earned requalification, fail-closed deprecation, or the V1 anti-oscillation result.

V3 identified the need for an independent structural signal.

## V4 Shape-Integrity Gate

V4 tested the mechanism that V3 left unresolved.

V3 showed that route-level scalar confidence was too slow to serve as the only post-promotion degradation detector. V4 added an independent tetrahedral structural signal as a conjunctive authority gate.

The V4 shape gate did not replace C_success. It did not blend structural state into route confidence. It did not repair or reinterpret the route score.

It acted as a separate authority condition. A learned route could bypass only when both the ordinary route gates and the independent shape-integrity gate were admissible.

The V4 comparison was:

V4-C: flat bounded routing without the shape-integrity gate.

V4-D: bounded routing with independent tetrahedral shape-integrity gate.

The primary comparison changed only one authority variable: whether the independent shape-integrity gate was consumed.

The primary V4 result was:

Final verdict: SUPPORTED.

Assertions: 26 of 26 passed.

Eligible matched instances: 105.

V4-C matched wrong bypasses: 404.

V4-D matched wrong bypasses: 14.

Wrong-bypass reduction: 96.53 percent.

Earlier revocation fraction: 100 percent.

Median revocation lead: 1860 milliseconds.

Clean suppression check: passed.

This result supports the narrow claim that live structural evidence can revoke unsafe bypass authority earlier than the inherited flat route gate under the frozen matched structural-deformation workload.

It also supports the separation of route confidence and structural condition.

V4 does not prove the complete tetrahedral architecture. It does not prove production reliability. It does not prove threshold optimality. It does not prove route-specific deployment scope.

V4 changes the architecture boundary after V3. The unresolved issue is no longer whether an independent structural signal can be tested at all. Under the frozen V4 workload, it can. The remaining questions are scope, threshold selection, production instrumentation, route-specific applicability, and integration with downstream recovery behavior.

## Scar Layer V1 Rejected Configuration Registry

The scar layer was added after the shape-gate work.

A scar is a compact rejected-configuration record. It says that a structural configuration had authority, later failed under valid evidence, and should not be promoted again as-is.

The governing rule is simple:

Only betrayed authority creates a scar.

The scar layer does not diagnose why a configuration failed. It is not semantic memory. It is not a full history. It is not cellular shedding. It is not lineage inheritance. It is not prospective filtering. It is not fuzzy matching. It is not an extra-proof protocol.

The frozen scar validation tested geometry-only fingerprinting, write boundary, cheap failure exclusion, non-admitted candidate exclusion, invalid evidence exclusion, hard scar behavior, soft scar behavior, restoration scar behavior, failure-count increment rules, elevation threshold, retirement rule, and isolation from shape_integrity and C_success.

The declared constants were:

K_SOFT_PERSIST equals 3.

T_SCAR_ELEVATE equals 3.

T_SCAR_RETIRE_SUCCESS_CYCLES equals 5.

The primary scar result was:

Final verdict: SUPPORTED.

Assertions: 30 of 30 passed.

Runtime: 0.98 seconds.

stderr: empty.

The scar layer validated that scars can be written only for betrayed authority, matched by exact geometry-only fingerprint, elevated only after the declared threshold, and retired only after declared successful cycles.

The scar result supports a narrow registry primitive. It does not yet define how damaged structure is cut away, how new structure is grown back, or how a regenerated cell inherits a compact rejected-configuration list.

## Tetrahedral Architecture Boundary

The architecture now separates five responsibilities.

S_pat identifies the task and route class.

C_success records historical route performance.

shape_integrity represents the current authorized structural condition of the tetrahedral substrate.

The shape gate consumes live structural state as an independent bypass-authority condition.

The scar layer records rejected structural configurations after betrayed authority.

The router must preserve the distinction among task identity, historical route performance, current structural condition, and rejected-configuration memory.

Structural state must come from the tetrahedral coordinator or another authorized structural observer. It must carry source, timestamp, epoch, and applicable scope.

Missing, stale, unverifiable, epoch-mismatched, or inapplicable structural state cannot preserve bypass authority.

Structural condition must remain an independent gate and must not be blended into the SMS moving average.

Scar matching must remain a separate registry operation and must not mutate shape_integrity or C_success.

## Overall Series Verdict

The honest overall verdict remains PARTIAL SUPPORT.

V1 supports anti-oscillation control under the tested oscillation workload.

V2 supports removal of stale authority, earned requalification through fresh shadow evidence, and fail-closed handling of persistent-failure routes.

V3 does not support the stronger claim that the flat Arm D gate stack revokes unsafe post-promotion authority faster than simpler controls.

V4 supports the narrow claim that an independent tetrahedral shape-integrity gate can revoke unsafe bypass authority earlier than the inherited flat gate under the frozen matched structural-deformation workload.

Scar Layer V1 supports the narrow claim that a rejected-configuration scar registry can write, match, elevate, and retire scars under declared authority and evidence rules.

The series supports bounded authority around learned routing, but not a general claim of superior safety across all workloads.

The strongest architectural result is that bypass authority can be treated as temporary, conditional, revocable, structurally gated, and capable of leaving behind compact rejected-configuration records after betrayed authority.

## What the Simulation Series Does Not Prove

The series does not prove real-world latency.

It does not prove that the selected thresholds are optimal.

It does not prove that bounded routing outperforms every possible adaptive routing method.

It does not prove the correctness of the incoming task-pattern signature, which is treated as given.

It does not prove that every successfully requalified route will remain safe under later degradation.

It does not establish a general safety advantage across all workloads.

It does not prove production reliability.

It does not prove the complete tetrahedral architecture.

It does not prove that GLOBAL scope is the correct deployment scope.

It does not prove cellular shedding.

It does not prove lineage inheritance.

It does not prove prospective filtering.

It does not prove fuzzy scar matching.

It does not prove extra-proof recovery behavior.

It does not prove that the system knows why a structural configuration failed.

## Series Status

V1 is preserved as the initial bounded-routing harness.

V2 is preserved as the first recovery requalification test.

V3 is preserved as the matched post-authority relapse test.

V4 is preserved as the independent shape-integrity gate test.

Scar Layer V1 is preserved as the rejected-configuration registry test.

The current executable scar checkpoint is scripts/rejected_configuration_scar_sim_v1_REVIEWED.py.

The current frozen scar result record is docs/REJECTED_CONFIGURATION_SCAR_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md.

The next architectural work is cellular shedding, followed by lineage inheritance.


