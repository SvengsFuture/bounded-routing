# Bounded Routing — Simulation Verdict

**Series:** v1 initial harness and v2 recovery requalification
**Current overall verdict:** PARTIAL SUPPORT

The simulation series tests whether learned routes should be allowed to bypass full analysis while operating conditions remain inside declared bounds. It also tests what happens when those conditions degrade, oscillate, or recover after disruption.

The results support bounded bypass authority as a useful control mechanism. They do not establish that bounded routing is always safer, always faster, or optimal under every workload.

# v1 — Initial Harness

v1 used three arms across stable, drift, fault, recovery, and oscillation phases.

| Arm | Label             | Description                                                                                                                           |
| --- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| A   | A_FULL_ANALYSIS   | Every task takes the full analysis path. No bypass.                                                                                   |
| B   | B_NAIVE_CACHE     | Bypass occurs when confidence exceeds the threshold. No structural bounds, depreciation, anti-oscillation gate, or recovery blackout. |
| C   | C_BOUNDED_ROUTING | Bypass requires the full ARD, SMS, and IBM gate stack to remain admissible.                                                           |

## Stable Phase

All three arms behaved normally. Arms B and C built usable bypass routes. Arm C was more conservative, with approximately 7.5 percent fallback compared with 4.8 percent for Arm B.

No admissibility violations occurred.

Average latency was approximately 40 milliseconds for Arm A, 9.6 milliseconds for Arm B, and 10.5 milliseconds for Arm C.

## Drift Phase

Route quality for pattern 0 degraded gradually from 1.0 to 0.2.

Arm B accumulated 114 admissibility violations. Arm C accumulated 101.

The separation was modest because confidence decay caused both arms to fall back. The structural-cost gate was not a strong discriminator in this configuration.

## Fault Phase

Route quality collapsed to 0.1.

Both Arms B and C depleted confidence and returned to full analysis. Neither arm recorded an admissibility violation during this phase.

This phase did not strongly distinguish bounded routing from ordinary confidence decay. The failure was severe enough that both systems recognized it quickly.

## Recovery Phase

Arm C used a fixed 5,000 millisecond blackout for recovery-sensitive routes.

Fallback increased to approximately 36.3 percent for Arm C, compared with 7.1 percent for Arm B. This shows that the recovery gate correctly forced more work through full analysis.

Arm B recorded 33 admissibility violations. Arm C recorded 31.

Arm C performed fewer bypasses, but its wrong-bypass rate was not lower. The recovery phase therefore supported conservative fallback behavior, but it did not establish a clean per-bypass safety advantage.

## Oscillation Phase

Two competing routes alternated quality every four seconds.

This produced the clearest v1 separation.

Arm B recorded 64 admissibility violations. Arm C recorded zero.

The naive cache repeatedly entered the bad route while confidence remained high. The bounded arm blocked bypass during anti-oscillation cooldown periods.

The wrong-bypass rate was approximately 1.1 percent for Arm B and 0 percent for Arm C.

## v1 Verdict

| Claim                                                                                  | Result                    |
| -------------------------------------------------------------------------------------- | ------------------------- |
| Bounded routing reduces violations during route oscillation                            | SUPPORTED                 |
| Bounded routing can be faster than full analysis                                       | SUPPORTED                 |
| The anti-oscillation gate prevents repeated wrong bypasses in the oscillation scenario | SUPPORTED                 |
| The recovery blackout correctly increases fallback                                     | SUPPORTED                 |
| Bounded routing is always safer than a naive cache                                     | NOT SUPPORTED             |
| Bounded routing eliminates all wrong bypasses                                          | NOT CLAIMED AND NOT SHOWN |

v1 validated the anti-oscillation mechanism. The fixed recovery blackout produced conservative behavior, but it did not show a clear safety advantage.

# v2 — Recovery Requalification

v2 replaced timer-only restoration with earned route requalification.

A recovery event removes bypass authority. The current task goes through full analysis. The candidate learned route is then evaluated in shadow on that same task.

Shadow evidence applies only to future bypass authority.

A route cannot regain authority using confidence or history from before recovery. It must build fresh post-recovery evidence.

Deprecated routes remain deprecated.

## v2 Arms

| Arm | Label           | Description                                                                         |
| --- | --------------- | ----------------------------------------------------------------------------------- |
| A   | A_FULL_ANALYSIS | Every task uses full analysis.                                                      |
| B   | B_NAIVE_CACHE   | Learned routes resume bypass without recovery-specific requalification.             |
| C   | C_TIMER_BOUND   | Bypass is blocked for a fixed recovery interval and then restored by time.          |
| D   | D_REQUALIFYING  | Bypass authority is removed and must be earned again through fresh shadow evidence. |

## Requalification Rule

The primary v2 test used `K=5`.

A route had to complete five consecutive admissible shadow checks and reach fresh confidence of at least 0.75 before returning to active bypass.

A failed shadow check reset the consecutive count and reduced fresh confidence.

Sustained fresh confidence below 0.55 could move a route into the deprecated state.

## Primary v2 Results

| Arm            | Wrong bypasses |   Wrong-bypass rate |        Fallback rate |
| -------------- | -------------: | ------------------: | -------------------: |
| B_NAIVE_CACHE  |             35 | approximately 1.01% |   approximately 7.4% |
| C_TIMER_BOUND  |             33 | approximately 1.38% |  approximately 36.3% |
| D_REQUALIFYING |              0 |                  0% | approximately 17.23% |

Arm D eliminated wrong bypasses during the measured recovery workload.

It did not remain permanently locked in fallback. Thirty-five route instances earned bypass authority back.

Five route instances remained deprecated.

The final Arm D route states were:

| State        | Route instances |
| ------------ | --------------: |
| ACTIVE       |              35 |
| REQUALIFYING |               0 |
| DEPRECATED   |               5 |

The mean time required to requalify an eligible route was approximately 816 milliseconds.

Patterns 1 through 7 successfully requalified across the five seeds. Pattern 0 failed the fresh checks, became deprecated, and remained fail-closed.

## Sensitivity Results

The requalification requirement was also tested at `K=3`, `K=5`, and `K=8`.

|  K | Active | Requalifying | Deprecated | Wrong bypasses |    Wrong-bypass rate | Bypasses |        Fallback rate |
| -: | -----: | -----------: | ---------: | -------------: | -------------------: | -------: | -------------------: |
|  3 |     37 |            0 |          3 |             15 | approximately 0.462% |     3246 | approximately 13.44% |
|  5 |     35 |            0 |          5 |              0 |                   0% |     3104 | approximately 17.23% |
|  8 |     35 |            0 |          5 |              0 |                   0% |     2999 | approximately 20.03% |

The sensitivity test shows the expected tradeoff.

A smaller evidence requirement restores bypass sooner and lowers fallback, but it allowed wrong bypasses.

Larger evidence requirements were safer in this workload, but they increased fallback and delayed route restoration.

## v2 Verdict

| Claim                                                                               | Result        |
| ----------------------------------------------------------------------------------- | ------------- |
| Recovery removes stale bypass authority                                             | SUPPORTED     |
| Pre-recovery confidence cannot silently restore authority                           | SUPPORTED     |
| Eligible routes can earn authority back using fresh evidence                        | SUPPORTED     |
| Failed routes can remain fail-closed                                                | SUPPORTED     |
| The requalifying arm eliminated wrong bypasses in the primary recovery workload     | SUPPORTED     |
| The requalifying arm remained permanently stuck in fallback                         | NOT SUPPORTED |
| `K=5` and `K=8` were safer than `K=3` in this workload                              | SUPPORTED     |
| Requalified routes were proven safer than the same routes under every competing arm | INCONCLUSIVE  |
| The selected thresholds are optimal                                                 | NOT SHOWN     |

## Why the Matched Post-Requalification Comparison Is Inconclusive

The successfully requalified patterns were patterns 1 through 7.

Those routes had perfect route quality during the modeled recovery phase. Once they requalified, they were not exposed to a condition that could produce a wrong bypass.

Pattern 0 was the failing route, but it did not requalify.

This means the matched post-requalification cohort could not distinguish the arms. The routes that came back were clean, and the route that could have failed stayed shut down.

This does not invalidate the requalification mechanism. It limits the strength of the claim that can be made from this workload.

A future test needs borderline routes that sometimes pass requalification and later become inadmissible. That would create a genuine matched safety comparison after authority is restored.

# Overall Series Verdict

The series supports the use of bounded authority around learned routing.

v1 showed that anti-oscillation controls can prevent repeated wrong bypasses when confidence alone remains misleadingly high.

v2 showed that bypass authority can be removed after recovery and earned back using fresh evidence rather than restored through elapsed time or stale confidence.

The strongest v2 result is not merely that Arm D made zero wrong bypasses. The stronger architectural result is that the system distinguished between routes that could regain authority and routes that should remain shut down.

The mechanism worked as designed:

Recovery removed authority.

Full analysis handled live work while authority was absent.

Fresh shadow evidence governed future promotion.

Successful routes returned to active use.

Failed routes remained deprecated.

The cost was increased fallback. That cost is the safety tax paid for refusing to treat earlier confidence as permanent execution authority.

The honest overall verdict is **PARTIAL SUPPORT**.

The state machine and recovery controls are supported. Aggregate recovery safety is supported in the tested workload. A general post-requalification safety advantage remains unproven.

# What the Simulation Does Not Prove

The simulation does not prove real-world latency.

It does not prove that the selected thresholds are optimal.

It does not prove that bounded routing outperforms every possible adaptive routing method.

It does not prove the correctness of the incoming pattern signature, which is treated as given.

It does not prove that every successfully requalified route will remain safe under later degradation.

It does not establish a general safety advantage across all workloads.

# Series Status

v1 is preserved as the initial bounded-routing harness.

v2 is the first recovery requalification test.

The v2 state-machine integrity checks passed. The primary recovery workload produced zero wrong bypasses in the requalifying arm while still allowing qualified routes to regain authority.

The repository therefore contains a working checkpoint with an honest partial-support verdict.

The next useful experiment is a harder post-requalification workload containing borderline routes that can earn authority and later become unsafe.
