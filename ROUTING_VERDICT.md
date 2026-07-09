# Bounded Routing Simulation Verdict

Series: V1 initial harness, V2 recovery requalification, V3 post-authority relapse, V4 shape-integrity gate, Scar Layer V1, Cellular Shedding V1, Lineage Inheritance V1, and Prospective Filtering V1.

Current overall verdict: PARTIAL SUPPORT.

The simulation series tests whether learned routes should be allowed to bypass full analysis while operating conditions remain inside declared bounds. It also tests what happens when those conditions drift, oscillate, recover after disruption, degrade again after bypass authority has been restored, fail under live structural conditions, require local structural removal after a cell loses authority, require bounded constraint inheritance when a replacement child cell is introduced, and require candidate screening before promotion.

The results support bounded bypass authority as a useful control mechanism. They do not establish that bounded routing is always safer, always faster, or optimal under every workload.

The series now separates eight findings.

V1 tested bounded routing under drift, fault, recovery, and oscillation.

V2 tested whether stale route authority could be removed and earned back through fresh evidence.

V3 tested whether the full requalifying gate stack could revoke unsafe authority faster than simpler controls after a restored route degraded again.

V4 tested whether an independent tetrahedral shape-integrity gate could revoke unsafe bypass authority earlier than the inherited flat gate under a frozen matched structural-deformation workload.

Scar Layer V1 tested whether a minimal rejected-configuration registry could write, match, elevate, and retire scars only under declared authority and evidence rules.

Cellular Shedding V1 tested whether a damaged local cell could be removed from active authority while preserving the correct route-authority boundary, scar boundary, replacement boundary, and load-transfer escalation boundary.

Lineage Inheritance V1 tested whether a replacement child cell could inherit compact constraints from a parent context without inheriting active authority, bypass permission, full history, parent route confidence, or parent shape integrity.

Prospective Filtering V1 tested whether a candidate replacement, reconstruction, route, child cell, or local structural configuration could be screened before promotion without receiving active authority or bypass permission from the filter itself.

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

```text
B_NAIVE_CACHE wrong bypasses: 35
C_TIMER_BOUND wrong bypasses: 33
D_REQUALIFYING wrong bypasses: 0

B_NAIVE_CACHE fallback rate: approximately 7.4 percent
C_TIMER_BOUND fallback rate: approximately 36.3 percent
D_REQUALIFYING fallback rate: approximately 17.23 percent
```

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

```text
B_NAIVE_CACHE wrong bypasses:           105
C_TIMER_BOUND wrong bypasses:           123
D_REQUALIFYING wrong bypasses:          126

B_NAIVE_CACHE actual wrong-bypass rate: 12.04 percent
C_TIMER_BOUND actual wrong-bypass rate: 25.41 percent
D_REQUALIFYING actual wrong-bypass rate:13.86 percent
```

Arm D executed 909 matched bypasses. Its result was therefore not caused by permanent suppression or avoidance of exposure.

Arm D did not record fewer wrong bypasses than both comparison arms.

For all 15 eligible borderline route instances, the first Arm D gate to block bypass after degradation onset was the confidence gate. Depreciation, structural cost, anti-oscillation, and cooldown did not fire first in any eligible instance.

The extra Arm D gates were present and operational, but they did not provide an earlier revocation signal in this workload. The router relied on ordinary confidence decay.

V3 does not support the stronger claim that the flat Arm D gate stack revokes unsafe post-promotion authority faster than simpler comparison arms. It does not invalidate earned requalification, fail-closed deprecation, or the V1 anti-oscillation result.

V3 identified the need for an independent structural signal.

## V4 Shape-Integrity Gate

V4 tested the mechanism that V3 left unresolved.

V3 showed that route-level scalar confidence was too slow to serve as the only post-promotion degradation detector. V4 added an independent tetrahedral structural signal as a conjunctive authority gate.

The V4 shape gate did not replace `C_success`. It did not blend structural state into route confidence. It did not repair or reinterpret the route score.

It acted as a separate authority condition. A learned route could bypass only when both the ordinary route gates and the independent shape-integrity gate were admissible.

The V4 comparison was:

```text
V4-C: flat bounded routing without the shape-integrity gate
V4-D: bounded routing with independent tetrahedral shape-integrity gate
```

The primary comparison changed only one authority variable: whether the independent shape-integrity gate was consumed.

The primary V4 result was:

```text
Final verdict: SUPPORTED
Assertions: 26 of 26 passed
Eligible matched instances: 105
V4-C matched wrong bypasses: 404
V4-D matched wrong bypasses: 14
Wrong-bypass reduction: 96.53 percent
Earlier revocation fraction: 100 percent
Median revocation lead: 1860 milliseconds
Clean suppression check: passed
```

This result supports the narrow claim that live structural evidence can revoke unsafe bypass authority earlier than the inherited flat route gate under the frozen matched structural-deformation workload.

It also supports the separation of route confidence and structural condition.

V4 does not prove the complete tetrahedral architecture. It does not prove production reliability. It does not prove threshold optimality. It does not prove route-specific deployment scope.

V4 changes the architecture boundary after V3. The unresolved issue is no longer whether an independent structural signal can be tested at all. Under the frozen V4 workload, it can. The remaining questions are scope, threshold selection, production instrumentation, route-specific applicability, and integration with downstream recovery behavior.

## Scar Layer V1 Rejected Configuration Registry

The scar layer was added after the shape-gate work.

A scar is a compact rejected-configuration record. It says that a structural configuration had authority, later failed under valid evidence, and should not be promoted again as-is.

The governing rule is simple:

```text
Only betrayed authority creates a scar.
```

The scar layer does not diagnose why a configuration failed. It is not semantic memory. It is not a full history. It is not cellular shedding. It is not lineage inheritance. It is not prospective filtering. It is not fuzzy matching. It is not an extra-proof protocol.

The frozen scar validation tested geometry-only fingerprinting, write boundary, cheap failure exclusion, non-admitted candidate exclusion, invalid evidence exclusion, hard scar behavior, soft scar behavior, restoration scar behavior, failure-count increment rules, elevation threshold, retirement rule, and isolation from `shape_integrity` and `C_success`.

The declared constants were:

```text
K_SOFT_PERSIST = 3
T_SCAR_ELEVATE = 3
T_SCAR_RETIRE_SUCCESS_CYCLES = 5
```

The primary scar result was:

```text
Final verdict: SUPPORTED
Assertions: 30 of 30 passed
Runtime: 0.98 seconds
stderr: empty
```

The scar layer validated that scars can be written only for betrayed authority, matched by exact geometry-only fingerprint, elevated only after the declared threshold, and retired only after declared successful cycles.

The scar result supports a narrow registry primitive. It does not define how damaged structure is cut away, how new structure is grown back, or how a regenerated cell inherits a compact rejected-configuration list.

## Cellular Shedding V1 Local Removal

Cellular Shedding V1 was added after the scar-layer work.

A shed cell is a damaged local structural unit removed from active authority after failure. The cell may remain available for inspection or replay, but it cannot support bypass authority.

The governing rule is simple:

```text
Do not preserve failed authority through continuity of form.
```

A structure that looks like the old cell is not trusted merely because it occupies the same position. It must earn authority again under current evidence.

The frozen cellular shedding validation tested dependent-route revocation, independent-route preservation, uncertain-scope fail-closed behavior, invalid-evidence exclusion, betrayed-authority scar writing, cheap retry exclusion, non-admitted candidate exclusion, hard scar reconstruction blocking, soft and restoration scar extra-proof routing, replacement-cell requalification, load-transfer success, load-transfer failure, and replay-log coverage.

The primary cellular shedding result was:

```text
Final verdict: SUPPORTED
Assertions: 22 of 22 passed
Document integrity: OK
Script filename: cellular_shedding_sim_v1_REVIEWED.py
```

The run record verified the frozen document hashes:

```text
Specification SHA-256: 8aaf925877d5bde60826a4a7ae3075d6177afaf41151e9d3a185bd4a1a27f512
Validation plan SHA-256: 4c073e5cdef9cd1e1812088bbf490775a658900cf790d87d632c049a4d821ae4
```

Cellular Shedding V1 supports the narrow claim that a local failed cell can be removed from active authority while preserving the correct authority boundary, scar boundary, replacement boundary, and load-transfer escalation boundary under the frozen synthetic harness.

It does not validate lineage inheritance. It does not validate fuzzy scar matching. It does not validate prospective filtering. It does not validate production recovery. It does not validate a full extra-proof protocol. It does not prove that every structural failure is locally shed-able. It does not prove uninterrupted service. It does not prove production reliability.

## Lineage Inheritance V1 Constraint Inheritance

Lineage Inheritance V1 was added after cellular shedding.

A lineage packet is the compact constraint record passed from parent context into child context after a failed cell has been shed, quarantined, retired, or replaced.

The governing rule is simple:

```text
Inherit constraints, not authority.
```

A replacement child cell may inherit compact constraints. It may not inherit active authority, bypass permission, full history, parent route confidence, or parent shape integrity.

The frozen lineage validation tested hard scar inheritance, soft scar inheritance, restoration scar inheritance, no-scar-match behavior, active-authority contamination, route-confidence contamination, shape-integrity contamination, full-history rejection, stale packet rejection, epoch mismatch rejection, unknown-scope rejection, narrower proven overlap, no direct ACTIVE state, partial requalification failure, post-authority child failure, repeated contaminated-source recording without source escalation, and non-mutation isolation checks.

The declared constants were:

```text
REQUALIFICATION_THRESHOLD = 5
PARTIAL_REQUALIFICATION_PROGRESS = 3
SCOPE_OVERLAP_MODEL = explicit boolean scope_overlap_proven field
```

The primary lineage result was:

```text
Final verdict: SUPPORTED
Assertions: 32 of 32 passed
Document integrity: OK
Script filename: lineage_inheritance_sim_v1_REVIEWED.py
```

The run record verified the frozen document hashes:

```text
Specification SHA-256: 7aa05bf40a2a787f79e5eed9a7f7d3e1aca3baa83dd2be576ba1ef17458f8ebe
Validation plan SHA-256: 1f02a1fc94b419799b2ee88e26b6d69f2dd1bdeb026fc558c655ad9a57ffa803
```

Lineage Inheritance V1 supports the narrow claim that a replacement child cell can inherit compact constraints from a parent context without inheriting active authority, bypass permission, full history, parent route confidence, or parent shape integrity under the frozen synthetic harness.

It does not validate fuzzy scar matching. It does not validate prospective filtering. It does not validate source-level escalation for repeated contaminated packets. It does not validate production recovery. It does not validate a full extra-proof protocol. It does not prove that every child cell is safe. It does not prove that all damaged cells can be replaced. It does not prove that lineage packets are sufficient for all recovery cases. It does not prove production reliability.

## Prospective Filtering V1 Pre-Promotion Screening

Prospective Filtering V1 was added after lineage inheritance.

A prospective filter is a pre-promotion screening operation applied to a candidate replacement, reconstruction, route, child cell, or local structural configuration.

The governing rule is simple:

```text
Filter before promotion, not after failure.
```

A candidate may be rejected as-is.

A candidate may be required to provide extra proof.

A candidate may be quarantined when evidence, provenance, epoch, scope, lineage dependency, or contamination is invalid.

A candidate may pass to requalification.

The filter may not grant active authority.

The filter may not grant bypass permission.

The frozen prospective-filtering validation tested hard scar matching, soft scar matching, restoration scar matching, no-scar-match behavior, active-authority contamination, bypass-permission contamination, route-confidence contamination, parent-shape-integrity contamination, full-history contamination, stale evidence, invalid provenance, epoch mismatch, unknown scope, narrower proven overlap, no-lineage candidate handling, invalid-lineage dependency, hard inherited lineage constraint, soft inherited lineage constraint, contamination precedence, isolation checks, repeated contaminated-source recording without source escalation, and event-log coverage.

The declared constants were:

```text
SCOPE_OVERLAP_MODEL = explicit boolean scope_overlap_proven field
FILTER_DECISION_PRECEDENCE = evidence, provenance, epoch, scope, contamination, hard scar, soft/restoration scar, lineage constraint, no-match pass
SCAR_MATCH_MODEL = exact fingerprint only
EXTRA_PROOF_PROTOCOL = not implemented; REQUIRE_EXTRA_PROOF is a routing state only
SOURCE_ESCALATION = not implemented; repeated contamination is recorded only
```

The primary prospective-filtering result was:

```text
Final verdict: SUPPORTED
Assertions: 37 of 37 passed
Document integrity: OK
Script filename: prospective_filtering_sim_v1_REVIEWED.py
```

The run record verified the frozen document hashes:

```text
Specification SHA-256: 01c7dda142d63aebc1f739c35b0ea23e15ac91c578f9593cdedcd903a33fc3b0
Validation plan SHA-256: 58ffccde8d5f96e7330f1d3e62ad6745909ef94a70db18b2be750aa3c5342e5c
```

Prospective Filtering V1 supports the narrow claim that a candidate can be screened before promotion without receiving active authority or bypass permission from the filter itself under the frozen synthetic harness.

It does not validate fuzzy scar matching. It does not validate a full extra-proof protocol. It does not validate source-level escalation for repeated contaminated packets. It does not validate production recovery. It does not prove that every unsafe candidate can be detected before requalification. It does not prove that every safe candidate can be admitted. It does not prove that a clean filter result is authority. It does not prove production reliability.

## Tetrahedral Architecture Boundary

The architecture now separates eight responsibilities.

`S_pat` identifies the task and route class.

`C_success` records historical route performance.

`shape_integrity` represents the current authorized structural condition of the tetrahedral substrate.

The shape gate consumes live structural state as an independent bypass-authority condition.

The scar layer records rejected structural configurations after betrayed authority.

The cellular shedding layer removes damaged local structure from active authority and prevents failed authority from continuing through position, history, or reconstruction.

The lineage inheritance layer transfers compact constraints into a replacement child cell path without transferring active authority.

The prospective filtering layer consumes scars, lineage constraints, candidate evidence, scope, provenance, epoch, and contamination checks before promotion without granting authority.

The router must preserve the distinction among task identity, historical route performance, current structural condition, rejected-configuration memory, local structural removal, constraint inheritance, and pre-promotion filtering.

Structural state must come from the tetrahedral coordinator or another authorized structural observer. It must carry source, timestamp, epoch, and applicable scope.

Missing, stale, unverifiable, epoch-mismatched, or inapplicable structural state cannot preserve bypass authority.

Structural condition must remain an independent gate and must not be blended into the SMS moving average.

Scar matching must remain a separate registry operation and must not mutate `shape_integrity` or `C_success`.

Shedding must remain a separate recovery action and must not be treated as route scoring, scar matching, automatic lineage inheritance, or prospective filtering.

Lineage inheritance must remain a separate constraint-transfer action and must not be treated as authority transfer, bypass permission, full history replay, route-confidence inheritance, shape-integrity inheritance, or prospective filtering.

Prospective filtering must remain a separate pre-promotion screening action and must not be treated as active authority, bypass permission, automatic safety, fuzzy matching, full extra-proof behavior, or source-level escalation.

## Overall Series Verdict

The honest overall verdict remains PARTIAL SUPPORT.

V1 supports anti-oscillation control under the tested oscillation workload.

V2 supports removal of stale authority, earned requalification through fresh shadow evidence, and fail-closed handling of persistent-failure routes.

V3 does not support the stronger claim that the flat Arm D gate stack revokes unsafe post-promotion authority faster than simpler controls.

V4 supports the narrow claim that an independent tetrahedral shape-integrity gate can revoke unsafe bypass authority earlier than the inherited flat gate under the frozen matched structural-deformation workload.

Scar Layer V1 supports the narrow claim that a rejected-configuration scar registry can write, match, elevate, and retire scars under declared authority and evidence rules.

Cellular Shedding V1 supports the narrow claim that a local failed cell can be removed from active authority while preserving the correct authority boundary, scar boundary, replacement boundary, and load-transfer escalation boundary under the frozen synthetic harness.

Lineage Inheritance V1 supports the narrow claim that a replacement child cell can inherit compact constraints without inheriting active authority, bypass permission, full history, parent route confidence, or parent shape integrity under the frozen synthetic harness.

Prospective Filtering V1 supports the narrow claim that a candidate can be screened before promotion without receiving active authority or bypass permission from the filter itself under the frozen synthetic harness.

The series supports bounded authority around learned routing, but not a general claim of superior safety across all workloads.

The strongest architectural result is that bypass authority can be treated as temporary, conditional, revocable, structurally gated, capable of leaving behind compact rejected-configuration records after betrayed authority, capable of removing damaged local structure from active authority, capable of passing forward compact constraints without automatically preserving failed authority, and capable of screening a candidate before promotion without granting authority.

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

It does not prove lineage inheritance beyond the frozen synthetic harness.

It does not prove prospective filtering beyond the frozen synthetic harness.

It does not prove fuzzy scar matching.

It does not prove extra-proof recovery behavior.

It does not prove source-level escalation for repeated contaminated packets.

It does not prove that the system knows why a structural configuration failed.

It does not prove that every structural failure can be locally shed.

It does not prove that every child cell is safe.

It does not prove that all damaged cells can be replaced.

It does not prove that every unsafe candidate can be detected before requalification.

It does not prove that every safe candidate can be admitted.

It does not prove that a clean filter result is authority.

It does not prove uninterrupted service during shedding or reconstruction.

## Series Status

V1 is preserved as the initial bounded-routing harness.

V2 is preserved as the first recovery requalification test.

V3 is preserved as the matched post-authority relapse test.

V4 is preserved as the independent shape-integrity gate test.

Scar Layer V1 is preserved as the rejected-configuration registry test.

Cellular Shedding V1 is preserved as the local structural-removal test.

Lineage Inheritance V1 is preserved as the constraint-inheritance test.

Prospective Filtering V1 is preserved as the pre-promotion screening test.

The current executable scar checkpoint is:

```text
scripts/rejected_configuration_scar_sim_v1_REVIEWED.py
```

The current frozen scar result record is:

```text
docs/REJECTED_CONFIGURATION_SCAR_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md
```

The current executable shedding checkpoint is:

```text
scripts/cellular_shedding_sim_v1_REVIEWED.py
```

The current frozen shedding result record is:

```text
docs/CELLULAR_SHEDDING_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md
```

The current executable lineage checkpoint is:

```text
scripts/lineage_inheritance_sim_v1_REVIEWED.py
```

The current frozen lineage result record is:

```text
docs/LINEAGE_INHERITANCE_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md
```

The current executable prospective-filtering checkpoint is:

```text
scripts/prospective_filtering_sim_v1_REVIEWED.py
```

The current frozen prospective-filtering result record is:

```text
docs/PROSPECTIVE_FILTERING_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md
```

The current architectural checkpoint is prospective filtering. The next repository work is review and cleanup, not another architecture layer.

