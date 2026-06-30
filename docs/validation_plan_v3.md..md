# Bounded Routing — v3 Validation Plan
## Recovery Requalification with Post-Authority Relapse

---

## Status

This plan is written before the v3 simulation run. The workload design,
parameter block, metric definitions, verdict boundaries, and required
assertions are declared here and will not be revised after results are
observed.

V1 and V2 files are frozen. V3 does not modify or replace them.

---

## Purpose and scope

V2 established that the requalification state machine is structurally
correct and that aggregate recovery safety is improved under the current
workload. It did not resolve the matched post-requalification safety
comparison because every route that successfully requalified had
route_quality=1.0 for the remainder of the recovery phase. No wrong
bypass was structurally possible on those routes for any arm.

V3 resolves this by introducing a workload where some routes pass fresh
requalification under genuinely admissible conditions and then degrade
afterward. The degradation onset timestamp is fixed in the manifest
before any arm runs. This creates matched post-requalification windows
in which wrong bypasses are structurally possible for the bypass-capable
Arms B, C, and D. The question becomes whether Arm D's full gate
mechanism revokes or reduces unsafe bypass authority sooner than Arms B
and C when a promoted route later becomes unreliable.

V3 does not change the requalification mechanism, the state-machine
rules, or the parameter values inherited from V2. The only additions are
workload structure and the metrics needed to evaluate the new question.

---

## Two questions V3 addresses

**Question 1 — Initial authority restoration**

Did Arm D safely control the decision to restore bypass authority? Did it
require fresh evidence that was genuinely admissible when observed?

The clean observations only establish that the candidate route was
admissible at the time each shadow check was conducted. They do not
establish future safety. This question asks whether the requalification
gate enforced that fresh, current evidence was required before authority
was restored.

**Question 2 — Post-authority revocation speed**

After Arm D restored bypass authority to a route that later degraded,
did Arm D's full gate mechanism — including confidence decay,
depreciation, structural-cost, recovery-state, and anti-oscillation
controls — revoke or reduce that authority sooner than Arms B and C when
the same route became unsafe? This is the primary new question.

These two questions must be reported separately. A result on Question 1
does not substitute for a result on Question 2. The `first_blocking_gate_D`
metric is used to identify which control actually caused the first
authority block. No safety advantage is attributed specifically to the
requalification mechanism unless the observed gate and state history
support that attribution.

---

## Experimental arms

| Arm | Label | Behavior |
|-----|-------|---------|
| A | A_FULL_ANALYSIS | Every task uses full analysis. No learned bypass. |
| B | B_NAIVE_CACHE | Bypass whenever confidence >= T_bypass. No recovery control. |
| C | C_TIMER_BOUND | V1 fixed recovery blackout. Timer-only restoration. |
| D | D_REQUALIFYING | Post-recovery shadow evaluation. Earned requalification. All V2 state-machine rules preserved. |

---

## Route classes

The recovery phase workload contains three route classes. Class
membership is fixed by pattern_id and declared before the simulation
runs. No arm's internal state influences route quality or candidate
conditions at any time.

**Control group — patterns 1 through 4**

Route quality is 1.0 throughout the recovery phase and the post-recovery
window. These routes remain admissible throughout the matched comparison
window for all arms. They confirm that the requalification mechanism does
not lock out genuinely safe routes. If Arm D fails to requalify
control-group routes at K=5, the mechanism is too conservative to be
useful.

**Persistent failure group — pattern 0**

`candidate_admissible` is set deterministically to False for pattern 0
throughout the entire recovery phase. This eliminates the theoretical
possibility that probabilistic sampling at probability 0.1 produces
consecutive admissible results. Arm D must not promote pattern 0.
Assertion A14 verifies this. Arms B and C do not use the requalification
state machine; their behavior on pattern 0 is reported under
full-recovery aggregate metrics but is not part of the matched
post-requalification comparison.

**Borderline relapse group — patterns 5 through 7**

`candidate_admissible` is set deterministically to True during the clean
requalification interval (from the recovery signal to
`degradation_onset_ms`). After `degradation_onset_ms`, candidate
conditions are drawn probabilistically using the route_quality value at
that task's time_ms. The degradation onset timestamp is a fixed manifest
value computed before any arm runs. The environment never delays or
adjusts degradation based on whether or when any arm promoted a route.

---

## Shared task manifest

The manifest is generated once per seed before any arm executes. It
contains one row per task covering the entire simulation. Each row
includes:

```
time_ms
pattern_id
phase
route_quality
candidate_admissible
candidate_latency_ms
candidate_cost
relapse_phase              -- PRE_RECOVERY | CLEAN_REQUALIFY | POST_ONSET | STABLE
route_class                -- CONTROL | PERSISTENT_FAILURE | BORDERLINE_RELAPSE
degradation_onset_ms       -- fixed manifest timestamp; same value for all arms
```

The manifest is saved as `manifest_seed{N}_v3.csv` before any arm runs.
All four arms read the same manifest. No arm receives different candidate
conditions than any other arm. Assertion A1 verifies this.

---

## Candidate conditions during the clean requalification interval

For control-group patterns (1–4) and borderline relapse patterns (5–7)
during the clean requalification interval (recovery signal to
`degradation_onset_ms`), each manifest row must satisfy:

```
candidate_admissible  = True
candidate_cost        = COST_BYPASS_NORMAL  (0.3)
candidate_latency_ms  within [LATENCY_BYPASS_FAST - LATENCY_NOISE_STD,
                               LATENCY_BYPASS_FAST + LATENCY_NOISE_STD * 2]
                      (within [5.0, 14.0] ms given LATENCY_BYPASS_FAST = 8.0,
                       LATENCY_NOISE_STD = 3.0)
```

The latency bound ensures the latency component of the SMS outcome score
is computed in the fast-latency band. Combined with
`candidate_admissible = True` and `route_quality = Q_REQUALIFY_HIGH` or
1.0, the resulting shadow SMS score for each clean observation must be at
least T_bypass = 0.75. Assertion A15 verifies that every clean-interval
shadow observation recorded by Arm D meets this floor.

For pattern 0 throughout recovery: `candidate_admissible = False`
deterministically, as declared above.

For all other phases and patterns: `candidate_admissible` is drawn
probabilistically using route_quality as the Bernoulli parameter,
`candidate_cost` drawn from the V2 cost model, and `candidate_latency_ms`
drawn with Gaussian noise around the appropriate base latency.

---

## Manifest coverage requirement

Because the declared sensitivity sweep includes K_REQUALIFY values of 3,
5, and 8, and because sensitivity results can change the final verdict
(see Step 3 of the Verdict boundaries section), the manifest must provide
adequate observation opportunity for the largest declared K value, not
only for the primary K value.

Before any arm runs, the manifest must be verified to contain at least

```
max(K_REQUALIFY_SWEEP) = 8
```

task observations for each control-group and borderline relapse pattern
during its clean requalification interval. Specifically, for each
(seed, pattern_id) pair in those classes, the count of manifest rows with
`phase == recovery` and `time_ms < degradation_onset_ms` and
`pattern_id == pid` must be >= 8.

This requirement guarantees adequate manifest opportunity for K=3, K=5,
and K=8 alike. Using only K_REQUALIFY_PRIMARY=5 as the coverage minimum
would be insufficient for the K=8 sensitivity run, since a route instance
with exactly 5 or 6 clean-interval observations could satisfy K=5
promotion but could never satisfy K=8 promotion regardless of route
quality, making the K=8 sensitivity result an artifact of manifest
construction rather than a property of the mechanism.

If any (seed, pattern_id) pair fails this requirement, the run must halt
with a workload-construction error before any arm executes. This is not
a mechanism failure and must not be recorded as an ineligible route
instance. The parameter block or simulation duration must be revised
until the coverage requirement is satisfied.

Assertion A16 performs this check.

---

## Admissibility generation summary

| Context | Method |
|---------|--------|
| Pattern 0, recovery phase | Deterministically False |
| Patterns 1–4, recovery phase | Deterministically True |
| Patterns 5–7, clean requalification interval | Deterministically True |
| Patterns 5–7, post-onset window | Probabilistic, Bernoulli(route_quality) |
| All patterns, stable / drift / fault / oscillation phases | Probabilistic, Bernoulli(route_quality), V2 behavior |

Deterministically True means the manifest field is set to True
unconditionally. It is a workload construction choice, not a claim about
the route being objectively safe.

---

## Route quality schedule

Route quality is a deterministic function of time_ms, pattern_id, and
seed. It does not depend on any arm's current state.

**Stable phase** (all patterns): route_quality = 1.0

**Drift phase** (pattern 0 only): linear decline from 1.0 to 0.2

**Fault phase** (pattern 0 only): route_quality = 0.1

**Recovery phase — clean requalification interval**

From the recovery signal to `degradation_onset_ms`:

- Pattern 0: route_quality = 0.1 (admissibility overridden to False)
- Patterns 1–4 (control): route_quality = 1.0
- Patterns 5–7 (borderline relapse): route_quality = Q_REQUALIFY_HIGH = 0.92

**Recovery phase — post-onset window**

After `degradation_onset_ms`, route quality for the borderline relapse
group follows each pattern's declared degradation profile:

- Pattern 5: linear decline from Q_REQUALIFY_HIGH to Q_RELAPSE_FLOOR_5
  over T_RELAPSE_RAMP_MS milliseconds beginning at `degradation_onset_ms`.
  Q_RELAPSE_FLOOR_5 = 0.25. T_RELAPSE_RAMP_MS = 4,000 ms.

- Pattern 6: route_quality = Q_REQUALIFY_HIGH until `degradation_onset_ms`,
  then drops immediately to Q_RELAPSE_FLOOR_6 = 0.15 and remains there.

- Pattern 7: oscillates between Q_OSC_HIGH and Q_OSC_LOW on a period of
  T_OSC_PERIOD_MS = 3,000 ms beginning at `degradation_onset_ms`. Each
  cycle begins in the **high state** (Q_OSC_HIGH = 0.90) for the first
  1,500 ms, then transitions to the **low state** (Q_OSC_LOW = 0.20) for
  the remaining 1,500 ms. The high-state half and the low-state half are
  each exactly T_OSC_PERIOD_MS / 2 in duration. The phase of each cycle
  is determined entirely by elapsed time since `degradation_onset_ms` and
  does not vary by any other condition.

**Oscillation phase** (pattern 1 only): unchanged from V2.

---

## Degradation onset timestamps

`degradation_onset_ms` is a fixed per-seed manifest value:

```
degradation_onset_ms = PHASE_FAULT_END + T_REQUALIFY_WINDOW_MS + seed_relapse_offset_ms
```

where T_REQUALIFY_WINDOW_MS = 5,000 ms and the per-seed offsets are:

| Seed | seed_relapse_offset_ms | degradation_onset_ms |
|------|------------------------|----------------------|
| 42 | 0 | 85,000 |
| 99 | 500 | 85,500 |
| 500 | 1,000 | 86,000 |
| 777 | 1,500 | 86,500 |
| 1337 | 2,000 | 87,000 |

These offsets ensure that no single timing value controls the aggregate
result. The five values are explicitly enumerated in the parameter block
and stored in the manifest. The formula `(seed % 5) * 500` does not
produce five distinct values for the declared seed set and must not be
used.

---

## Eligibility rule for primary matched comparison

A (seed, pattern_id) route instance in the borderline relapse group is
**eligible** for the primary matched comparison if and only if Arm D
promoted that route to ACTIVE at a time satisfying
`requalified_at_ms < degradation_onset_ms` for that seed.

A16 guarantees that every borderline relapse pattern received at least
`max(K_REQUALIFY_SWEEP) = 8` clean-interval observations before any arm
ran, which is sufficient coverage for K=3, K=5, and K=8 alike. Insufficient
manifest coverage therefore cannot be the reason a route fails to promote
during a completed run at any declared K value. If a borderline route
does not promote before degradation onset despite valid manifest
coverage, that route instance is ineligible. The reason for non-promotion
must be identified from the actual state history, confidence history, and
gate results for that (seed, pattern_id) instance, and reported in
`bounded_routing_v3_per_route_instance.csv` under `ineligibility_reason`.

The aggregate metric `eligible_borderline_instance_count` counts the
number of (seed, pattern_id) borderline relapse route instances that
satisfy the eligibility condition. This count determines which verdict
branch is entered; see the Verdict boundaries section.

Ineligible instances are reported separately and do not contribute to
verdict counts. The ineligibility rule is applied to route instances; it
does not affect how Arms B and C are evaluated.

Assertion A11 verifies that for every eligible route instance, Arm D's
recorded `requalified_at_ms` satisfies `requalified_at_ms < degradation_onset_ms`.

---

## Phase timing

| Phase | Start (ms) | End (ms) |
|-------|-----------|---------|
| Stable | 0 | 30,000 |
| Drift | 30,000 | 60,000 |
| Fault | 60,000 | 80,000 |
| Recovery | 80,000 | 110,000 |
| Oscillation | 110,000 | 120,000 |

V3 extends the recovery phase from 95,000 ms (V2) to 110,000 ms. This
provides time for both the clean requalification interval and a
meaningful post-onset observation window. The oscillation phase is
preserved unchanged.

---

## V3 parameter block

Parameters inherited from V2 are listed with their exact verified values.
New V3 parameters are marked **[V3 addition]**.

| Parameter | Value | Source |
|-----------|-------|--------|
| T_bypass | 0.75 | V2 |
| T_depreciate | 0.55 | V2 |
| T_recover_ARD | 0.70 | V2 |
| T_cost_max | 1.5 | V2 |
| alpha | 0.85 | V2 |
| obs_window_size | 20 | V2 |
| depreciation_N | 5 | V2 |
| depreciation_M | 10 | V2 |
| recover_K | 8 | V2 |
| T_retire_ms | 60,000 | V2 |
| T_flip_cooldown_ms | 2,000 | V2 |
| MAX_FLIPS_PER_WINDOW | 3 | V2 |
| T_flip_window_ms | 10,000 | V2 |
| T_recovery_blackout_ms | 5,000 | V2 (Arm C only) |
| K_REQUALIFY_PRIMARY | 5 | V2 |
| K_REQUALIFY_SWEEP | 3, 5, 8 | V2 |
| W_LAT | 0.30 | V2 |
| W_ADM | 0.40 | V2 |
| W_DEG | 0.20 | V2 |
| W_STAB | 0.10 | V2 |
| COST_BYPASS_NORMAL | 0.3 | V2 |
| COST_BYPASS_DRIFTED | 0.8 | V2 |
| COST_FULL_ANALYSIS | 1.0 | V2 |
| LATENCY_FULL_ANALYSIS | 40.0 ms | V2 |
| LATENCY_BYPASS_FAST | 8.0 ms | V2 |
| LATENCY_BYPASS_SLOW | 25.0 ms | V2 |
| LATENCY_NOISE_STD | 3.0 ms | V2 |
| SEEDS | 42, 99, 500, 777, 1337 | V2 |
| N_PATTERNS | 8 | V2 |
| DT_MS | 20 | V2 |
| Q_REQUALIFY_HIGH | 0.92 | **[V3 addition]** |
| Q_RELAPSE_FLOOR_5 | 0.25 | **[V3 addition]** |
| Q_RELAPSE_FLOOR_6 | 0.15 | **[V3 addition]** |
| T_REQUALIFY_WINDOW_MS | 5,000 ms | **[V3 addition]** |
| T_RELAPSE_RAMP_MS | 4,000 ms | **[V3 addition]** |
| T_OSC_PERIOD_MS | 3,000 ms | **[V3 addition]** |
| Q_OSC_HIGH | 0.90 | **[V3 addition]** |
| Q_OSC_LOW | 0.20 | **[V3 addition]** |
| seed_relapse_offset_ms (seed=42) | 0 | **[V3 addition]** |
| seed_relapse_offset_ms (seed=99) | 500 | **[V3 addition]** |
| seed_relapse_offset_ms (seed=500) | 1,000 | **[V3 addition]** |
| seed_relapse_offset_ms (seed=777) | 1,500 | **[V3 addition]** |
| seed_relapse_offset_ms (seed=1337) | 2,000 | **[V3 addition]** |
| MANIFEST_COVERAGE_MIN_OBS | max(K_REQUALIFY_SWEEP) = 8 | **[V3 addition]** |

No V2 mechanism parameter is changed in value. The recovery phase end
time moves from 95,000 ms to 110,000 ms; this is a workload extension,
not a change to any routing parameter.

---

## Why this workload is discriminating

The V2 limitation was that route_quality for successfully requalifying
patterns remained 1.0 after promotion, making wrong bypass impossible on
those routes regardless of which arm executed them. The matched
comparison had no variance to measure.

V3 creates variance by causing route quality to degrade at a fixed
manifest timestamp after the clean requalification interval closes. The
degradation onset is identical for all arms. Whether that degradation
produces wrong bypasses depends on how quickly each arm detects the
deterioration and revokes or withholds bypass authority.

Arm B detects degradation only through confidence decay. With alpha=0.85,
each inadmissible bypass decays confidence incrementally. Arm B may
accumulate wrong bypasses before its confidence falls below T_bypass=0.75.

Arm C detects degradation the same way as B for routes outside the
recovery blackout window. By the time degradation onset occurs, the
recovery blackout (5,000 ms) has typically expired. Arm C behaves
similarly to B during the post-onset window for most route instances.

Arm D's full gate mechanism — confidence decay, depreciation,
structural-cost gate, recovery-state gate, and anti-oscillation gate —
applies to routes that are ACTIVE after promotion. The requalification
mechanism applied during recovery; standard ARD machinery applies
afterward. The `first_blocking_gate_D` metric identifies which specific
control caused the first bypass block after degradation onset. No
attribution is made in advance about which gate will dominate or whether
D will outperform B and C.

The INCONCLUSIVE condition — a nonempty eligible cohort and zero wrong
bypasses in Arm B — must be detected automatically. It indicates workload
failure requiring parameter revision, not a verdict on the mechanism.

---

## Matched post-requalification comparison

### Primary matched window

For each eligible (seed, pattern_id) borderline relapse route instance,
the primary matched comparison window begins at the first manifest task
with time_ms strictly greater than Arm D's `requalified_at_ms` for that
route instance. It ends at the end of the recovery phase.

For the same (seed, time_ms, pattern_id) rows in that window, all four
arms are observed. Every row in the window is included regardless of what
any arm did on that row. Arm A provides a structural check. Arms B, C,
and D are the comparison arms.

The window is defined entirely by Arm D's `requalified_at_ms`. It is not
defined by any arm's bypass or fallback decision.

### Secondary relapse-only view

A second view begins at the first manifest task for each eligible route
instance where `candidate_admissible == False` — the first task where
the degraded route would produce a wrong bypass if executed. This
timestamp is derived from the manifest, not from any arm's state.

The secondary view uses the same (seed, time_ms, pattern_id) keys as the
primary window restricted to tasks at or after the first inadmissible
manifest row for that route instance. All arms are joined on identical
keys. Assertion A7 covers both views.

The secondary view isolates the revocation-speed question from the
initial post-promotion safe period. Both views are reported. Both are
required for the full verdict.

---

## Zero-denominator reporting

For any metric defined as wrong bypasses divided by actual bypasses: if
the bypass count for that arm in that window is zero, report the rate as
`NA`. Do not report 0.00% when an arm performed zero bypasses, as this
conflates a zero bypass count with a zero wrong-bypass rate. Always
report the raw bypass count alongside the rate so the NA condition is
unambiguous.

For exposure-normalized rates (wrong bypasses per 1,000 eligible tasks):
the denominator is the count of eligible matched tasks, which is
independent of any arm's bypass decision and will not be zero for any
eligible route instance. These rates are always reportable.

---

## Required metrics

### Per route instance (seed × pattern_id)

```
requalified_at_ms
time_to_requalify_ms                    -- requalified_at_ms - recovery_signal_ms
route_class                             -- CONTROL | PERSISTENT_FAILURE | BORDERLINE_RELAPSE
eligible_for_primary_matched_comparison -- True if requalified_at_ms < degradation_onset_ms
ineligibility_reason                    -- if not eligible: gate name, confidence level,
                                        --   and state at degradation_onset_ms derived from
                                        --   actual state history, confidence history, and
                                        --   gate results; None if eligible
degradation_onset_ms                    -- from manifest; same for all arms
first_inadmissible_task_ms              -- first task where candidate_admissible == False
final_state_D                           -- ACTIVE | REQUALIFYING | DEPRECATED
state_transition_history_D              -- ordered list of (time_ms, from_state, to_state)

-- Primary matched window (all eligible tasks after requalified_at_ms)
matched_window_tasks
matched_window_bypasses_B
matched_window_bypasses_C
matched_window_bypasses_D
matched_wrong_bypasses_B
matched_wrong_bypasses_C
matched_wrong_bypasses_D
matched_wbr_B                           -- wrong bypasses / matched_window_bypasses_B;
                                        --   NA if matched_window_bypasses_B == 0
matched_wbr_C                           -- NA if matched_window_bypasses_C == 0
matched_wbr_D                           -- NA if matched_window_bypasses_D == 0
matched_exposure_wbr_B                  -- wrong bypasses / matched_window_tasks * 1000
matched_exposure_wbr_C
matched_exposure_wbr_D
matched_fallback_rate_B
matched_fallback_rate_C
matched_fallback_rate_D

-- Secondary relapse-only view (eligible tasks from first_inadmissible_task_ms onward)
relapse_window_tasks
relapse_window_bypasses_B
relapse_window_bypasses_C
relapse_window_bypasses_D
relapse_wrong_bypasses_B
relapse_wrong_bypasses_C
relapse_wrong_bypasses_D
relapse_wbr_B                           -- NA if relapse_window_bypasses_B == 0
relapse_wbr_C                           -- NA if relapse_window_bypasses_C == 0
relapse_wbr_D                           -- NA if relapse_window_bypasses_D == 0
relapse_exposure_wbr_B                  -- wrong bypasses / relapse_window_tasks * 1000
relapse_exposure_wbr_C
relapse_exposure_wbr_D

-- Revocation timing (Arm D)
time_confidence_gate_failed_D           -- first post-onset task where c_success < T_bypass;
                                        --   None if confidence never drops below T_bypass
                                        --   in the post-onset window
time_first_bypass_authority_blocked_D   -- first post-onset eligible task where any required
                                        --   bypass gate prevents execution;
                                        --   None if bypass is never blocked in the window
first_blocking_gate_D                   -- gate name at time_first_bypass_authority_blocked_D;
                                        --   one of: confidence | cost | depreciation |
                                        --   recovery_state | anti_oscillation | cooldown;
                                        --   None if time_first_bypass_authority_blocked_D
                                        --   is None
time_first_wrong_bypass_B               -- None if zero wrong bypasses in window
time_first_wrong_bypass_C               -- None if zero wrong bypasses in window
time_first_wrong_bypass_D               -- None if zero wrong bypasses in window
```

### Aggregate (across all seeds, per pattern_id and per route_class)

```
eligible_borderline_instance_count
routes_ineligible
routes_not_requalified
routes_deprecated_during_recovery

mean_time_to_requalify_ms
std_time_to_requalify_ms

total_matched_tasks
total_matched_bypasses_B
total_matched_bypasses_C
total_matched_bypasses_D
total_matched_wrong_bypasses_B
total_matched_wrong_bypasses_C
total_matched_wrong_bypasses_D
aggregate_matched_wbr_B                 -- NA if total_matched_bypasses_B == 0
aggregate_matched_wbr_C                 -- NA if total_matched_bypasses_C == 0
aggregate_matched_wbr_D                 -- NA if total_matched_bypasses_D == 0
aggregate_exposure_wbr_B
aggregate_exposure_wbr_C
aggregate_exposure_wbr_D

total_relapse_tasks
total_relapse_bypasses_B
total_relapse_bypasses_C
total_relapse_bypasses_D
total_relapse_wrong_bypasses_B
total_relapse_wrong_bypasses_C
total_relapse_wrong_bypasses_D
aggregate_relapse_wbr_B                 -- NA if total_relapse_bypasses_B == 0
aggregate_relapse_wbr_C                 -- NA if total_relapse_bypasses_C == 0
aggregate_relapse_wbr_D                 -- NA if total_relapse_bypasses_D == 0
aggregate_relapse_exposure_wbr_B
aggregate_relapse_exposure_wbr_C
aggregate_relapse_exposure_wbr_D

mean_time_first_wrong_bypass_B
mean_time_first_wrong_bypass_C
mean_time_first_wrong_bypass_D
mean_time_confidence_gate_failed_D
mean_time_first_bypass_authority_blocked_D

-- Diagnostic only, not used for terminal state reporting (see A9)
historical_state_appearance_counts      -- count of rows where each state was ever observed,
                                        --   per (seed, pattern_id); reported for diagnostics
                                        --   only and expected to differ from final_row_state_counts
```

### Full-recovery phase

All V2 per-phase metrics preserved. Reported separately from matched
comparison metrics.

### Sensitivity sweep (K = 3, 5, 8)

Terminal state counts (ACTIVE, REQUALIFYING, DEPRECATED) per K value,
computed from the final recovery row per (seed, pattern_id). Wrong
bypasses, wrong-bypass rate (NA if zero bypasses), bypass count, fallback
rate, and mean requalification time per K value. Eligible and ineligible
route instance counts reported per K value.

---

## Required plots

```
recovery_wrong_bypass_timeseries_v3.png
    Cumulative wrong bypasses over recovery phase, all four arms.

recovery_fallback_timeseries_v3.png
    Fallback rate over recovery phase, all four arms.

requalification_by_pattern_v3.png
    Per-pattern requalification timing across seeds. One point per eligible
    (seed, pattern_id). Separate panels for control group and borderline
    relapse group. Degradation onset timestamps marked per seed.

post_requalification_matched_v3.png
    Three-panel comparison using only eligible matched post-promotion window.
    Left: wrong bypass count by arm and route class.
    Center: exposure-normalized wrong-bypass rate (wrong bypasses per 1,000
    eligible tasks).
    Right: actual wrong-bypass rate (wrong bypasses / actual bypasses);
    cells with zero bypass count annotated NA.
    Annotated INCONCLUSIVE at figure level if eligible_borderline_instance_count > 0
    and Arm B accumulates zero wrong bypasses on the eligible borderline
    relapse cohort. Annotated NOT SUPPORTED if
    eligible_borderline_instance_count == 0.

revocation_timeline_v3.png
    For each eligible (seed, pattern_id) borderline relapse instance:
    time from first_inadmissible_task_ms to time_first_wrong_bypass for B, C, D;
    time to time_confidence_gate_failed_D;
    time to time_first_bypass_authority_blocked_D with gate name annotated.
    One row per route instance sorted by requalification time.

requalification_sensitivity_v3.png
    K = 3, 5, 8. Wrong bypass rate (NA annotated where bypass count is zero)
    and fallback rate panels. Terminal state counts and eligible instance
    counts annotated on bars.
```

---

## Required assertions

All assertions must be real checks that can fail the run or produce
explicit diagnostic output. No assertion may be replaced by a comment or
a pass statement.

**A1 — Shared manifest integrity**
For every (seed, time_ms, pattern_id) triplet, the candidate_admissible,
candidate_latency_ms, and candidate_cost values recorded in each arm's
output rows must match the saved manifest exactly. Fail if any arm
received different candidate conditions.

**A2 — No pre-recovery contribution to fresh confidence**
Every shadow observation in every entry's requalify_obs_with_epoch list
must carry a timestamp >= recovery_signal_ms for that seed. Fail if any
observation predates the signal.

**A3 — Promotion gate integrity**
Every promotion to ACTIVE must be preceded by at least K_REQUALIFY
consecutive admissible shadow checks and fresh confidence >= T_bypass.
Fail if any promotion record violates either condition.

**A4 — No bypass while REQUALIFYING**
No row for Arm D may have bypassed=True and requalification_state=
REQUALIFYING simultaneously. Fail if any such row exists.

**A5 — Deprecated routes remain deprecated (fail-closed)**
For every (seed, pattern_id) route that entered DEPRECATED state during
recovery, every subsequent recovery row must have
requalification_state=DEPRECATED, bypassed=False, and fallback=True.
Fail if any subsequent row violates any of these conditions.

**A6 — Pre-recovery DEPRECATED routes not promoted**
Routes whose depreciation_state was DEPRECATED at the recovery signal
must not appear in the promotions list and must not receive shadow
observations. Coverage of this assertion must be reported explicitly:
if no route was DEPRECATED at signal time, state that A6 is structurally
present but unexercised in this run.

**A7 — Matched window key identity**
The set of (seed, time_ms, pattern_id) keys in both the primary matched
window and the secondary relapse-only view must be identical across all
four arms after joining. Fail if any arm is missing a key or carries an
extra key in either comparison.

**A8 — Window not conditioned on bypass decision**
The primary matched window must be defined entirely by Arm D's
requalified_at_ms timestamp. The secondary relapse-only view must be
defined entirely by first_inadmissible_task_ms from the manifest. Fail
if any row is included or excluded based on any arm's bypass or fallback
decision.

**A9 — Terminal state counts match final-row computation exactly**
Terminal state counts (ACTIVE, REQUALIFYING, DEPRECATED) reported in any
summary or sensitivity output must satisfy:

```
reported_terminal_state_counts == final_row_state_counts
```

where `final_row_state_counts` are computed using only the final recovery
row for each unique (seed, pattern_id) route instance. Fail if the
reported terminal counts differ from this computation by any amount.

Historical state appearance counts — the count of rows where a given
state was ever observed for a (seed, pattern_id) instance across the
full recovery phase — may be computed and reported separately for
diagnostic purposes only. Historical appearance counts are expected to
differ from final-row counts whenever a route transitions through more
than one state during recovery (for example, REQUALIFYING then ACTIVE).
This assertion must never compare historical appearance counts to
final-row counts and must never expect them to be equal.

**A10 — Requalification time calculation**
mean_time_to_requalify_ms must be computed from exactly one
requalified_at_ms value per unique (seed, pattern_id) route instance.
Fail if the count of values averaged differs from the count of distinct
(seed, pattern_id) pairs that requalified.

**A11 — Eligibility timestamp ordering**
For every borderline relapse route instance marked eligible for the
primary matched comparison, assert that
`requalified_at_ms < degradation_onset_ms` for that seed. Fail if any
eligible instance violates this ordering. Report ineligible instances
separately without failing the run for ineligible instances.

**A12 — Manifest admissibility during the recovery phase**
This assertion has two parts:

For borderline relapse patterns (5–7), assert that
`candidate_admissible == True` in the saved manifest for every recovery
task with time_ms < degradation_onset_ms for that seed. Fail if any such
row contains False.

For control patterns (1–4), assert that `candidate_admissible == True`
in the saved manifest for every recovery task across the entire recovery
phase (time_ms from recovery signal through PHASE_RECOVERY_END), not
merely before degradation_onset_ms. Control patterns have no degradation
onset and must remain admissible for the full recovery phase. Fail if any
such row contains False.

**A13 — Verdict branch function tested before arm execution**
A pure function

```
select_verdict_branch(eligible_borderline_instance_count, total_relapse_wrong_bypasses_B)
```

must be implemented and must return one of three values:
`EMPTY_COHORT_NOT_SUPPORTED`, `INCONCLUSIVE`, or `EVALUATE_MAIN_VERDICT`.

Before any simulation arm runs, the function must be tested against these
three synthetic inputs:

| Input (eligible_count, B_wrong_bypasses) | Required return value |
|---|---|
| (0, 0) | EMPTY_COHORT_NOT_SUPPORTED |
| (1, 0) | INCONCLUSIVE |
| (1, 1) | EVALUATE_MAIN_VERDICT |

If any of the three test cases returns the wrong value, the run must halt
before any arm executes. This is a pre-execution gate, not a post-hoc
check.

The actual simulation verdict must call this same tested function with
the real computed values of `eligible_borderline_instance_count` and
`total_relapse_wrong_bypasses_B`. The verdict pipeline must not implement
parallel or duplicate branching logic outside this function. No comment
or pass-through assertion may substitute for this requirement.

**A14 — Pattern 0 never promoted by Arm D**
Assert that pattern 0 does not appear in Arm D's promotions list for any
seed. Fail if any promotion record contains pattern_id == 0.

**A15 — Clean-interval shadow SMS floor**
For every shadow observation recorded by Arm D during the clean
requalification interval (time_ms < degradation_onset_ms, phase ==
recovery, route in REQUALIFYING state), assert that the
shadow_outcome_score recorded in that observation is >= T_bypass = 0.75.
Fail if any clean-interval shadow observation falls below this floor.

**A16 — Manifest coverage before arms run**
Before any arm executes, verify that for each (seed, pattern_id) pair in
the control group and borderline relapse group, the count of manifest
rows with phase == recovery and time_ms < degradation_onset_ms and
pattern_id == pid is >= max(K_REQUALIFY_SWEEP) = 8. If any pair fails
this requirement, halt with a workload-construction error. Do not proceed
to arm execution. This threshold guarantees adequate manifest opportunity
for the K=3, K=5, and K=8 sensitivity runs alike; using only
K_REQUALIFY_PRIMARY=5 as the coverage minimum would be insufficient for
K=8 and would make the K=8 sensitivity result an artifact of manifest
construction.

---

## Verdict boundaries

These boundaries are declared before the simulation runs and will not be
adjusted after results are observed. Exactly one verdict is produced per
run. The evaluation order below is exhaustive and the branches are
mutually exclusive.

### Step 0 — Branch selection (A13)

Compute `eligible_borderline_instance_count` and
`total_relapse_wrong_bypasses_B`, then call
`select_verdict_branch(eligible_borderline_instance_count, total_relapse_wrong_bypasses_B)`.

- Return value `EMPTY_COHORT_NOT_SUPPORTED` → final verdict is
  **NOT SUPPORTED**, reason: failure to restore useful authority.
  Skip Steps 1–3. Generate all output files.
- Return value `INCONCLUSIVE` → final verdict is **INCONCLUSIVE —
  workload non-discriminating**. Skip Steps 1–3. Generate all output
  files. The parameter block must be revised in V3.1.
- Return value `EVALUATE_MAIN_VERDICT` → proceed to Step 1.

### Step 1 — Suppression check

Determine `total_matched_bypasses_D` across the eligible borderline
cohort (primary matched window). If this count is zero, the final verdict
is **NOT SUPPORTED**, reason: Arm D promoted eligible routes but
performed zero actual post-promotion bypasses across the eligible matched
cohort, so the apparent safety advantage came from immediate suppression
rather than successful revocation under use. Skip Steps 2–3.

If `total_matched_bypasses_D` is greater than zero, proceed to Step 2.

### Step 2 — Primary K=5 verdict

For verdict purposes, the following operational definitions apply:

A **seed counts as showing an advantage for Arm D** if and only if Arm D
has fewer matched wrong bypasses than both Arm B and Arm C across all
eligible borderline route instances in that seed.

A **borderline pattern counts as contributing to the advantage** if and
only if Arm D has fewer matched wrong bypasses than both Arm B and Arm C
for that pattern across all eligible seeds.

**SUPPORTED** requires all of the following:
- Arm D produces fewer matched post-requalification wrong bypasses than
  both Arm B and Arm C across all eligible borderline relapse instances,
  in both the primary matched window and the secondary relapse-only view.
- Arm D's exposure-normalized wrong-bypass rate is not worse than B or C
  in either view.
- The advantage appears in at least three of the five seeds using the
  seed advantage definition above.
- At least two of the three borderline patterns (5, 6, 7) contribute to
  the advantage using the pattern contribution definition above.
- Control-group routes (patterns 1–4) requalify in Arm D at K=5.

**PARTIAL SUPPORT** applies when Arm D shows a measurable improvement
over at least one comparison arm in at least one matched view, but fails
one or more of the full SUPPORTED requirements.

**NOT SUPPORTED** applies when Arm D shows no matched safety improvement
over either Arm B or Arm C in either the primary matched window or the
secondary relapse-only view.

This produces a provisional K=5 verdict of SUPPORTED, PARTIAL SUPPORT, or
NOT SUPPORTED. Proceed to Step 3 only if the provisional verdict is
SUPPORTED.

### Step 3 — Sensitivity downgrade check (K=3 and K=8 robustness)

This step applies only when Step 2 produced a provisional SUPPORTED
verdict. If the provisional verdict from Step 2 is PARTIAL SUPPORT or
NOT SUPPORTED, Step 3 is skipped and that verdict is final.

If the provisional verdict is SUPPORTED, evaluate whether the same
advantage (Arm D fewer matched wrong bypasses than both B and C, in
both matched views) also holds at K=3 and at K=8 using the same seed and
pattern definitions as Step 2, applied to the K=3 and K=8 sensitivity
runs.

- If the advantage holds at both K=3 and K=8: final verdict is
  **SUPPORTED**.
- If the advantage disappears at K=3 or at K=8 (or both): final verdict
  is downgraded to **PARTIAL SUPPORT**, reason: primary K=5 result
  qualifies as SUPPORTED but is sensitive to the K_REQUALIFY value and
  does not hold across the declared sensitivity sweep.

This sensitivity condition is evaluated only after a SUPPORTED verdict
has been provisionally assigned in Step 2. It does not overlap with or
substitute for the PARTIAL SUPPORT conditions in Step 2; it is a
distinct downgrade path applied only to the SUPPORTED branch.

### Summary of decision order

```
Step 0: select_verdict_branch(...)
  -> EMPTY_COHORT_NOT_SUPPORTED -> NOT SUPPORTED (done)
  -> INCONCLUSIVE               -> INCONCLUSIVE (done)
  -> EVALUATE_MAIN_VERDICT      -> continue to Step 1

Step 1: total_matched_bypasses_D == 0?
  -> yes -> NOT SUPPORTED (suppression) (done)
  -> no  -> continue to Step 2

Step 2: apply SUPPORTED / PARTIAL SUPPORT / NOT SUPPORTED criteria
  -> PARTIAL SUPPORT -> done
  -> NOT SUPPORTED    -> done
  -> SUPPORTED        -> continue to Step 3

Step 3: K=3 and K=8 robustness check (only reached if Step 2 = SUPPORTED)
  -> advantage holds at both K=3 and K=8 -> SUPPORTED (final)
  -> advantage disappears at K=3 or K=8  -> PARTIAL SUPPORT (final)
```

Exactly one verdict value is produced by this process for any run.

---

## What V3 does not test

- Real-world latency, throughput, or hardware behavior.
- Optimal values for any routing parameter.
- Behavior under simultaneous faults in multiple patterns.
- The PRE pattern signature, which is treated as given.
- Replacement-route nomination for deprecated routes. This remains
  deferred.
- Any scenario outside the declared recovery phase structure.

---

## Output files

```
bounded_routing_v3_raw.csv
bounded_routing_v3_summary.csv
bounded_routing_v3_recovery_summary.csv
bounded_routing_v3_sensitivity_summary.csv
bounded_routing_v3_matched_comparison.csv
bounded_routing_v3_per_route_instance.csv
manifest_seed{N}_v3.csv              (one per seed, saved before arms run)
recovery_wrong_bypass_timeseries_v3.png
recovery_fallback_timeseries_v3.png
requalification_by_pattern_v3.png
post_requalification_matched_v3.png
revocation_timeline_v3.png
requalification_sensitivity_v3.png
```

---

## Series continuity

V1: initial three-arm harness. Oscillation phase is the primary
discriminator.

V2: four-arm harness with earned requalification. State-machine
integrity confirmed. Aggregate recovery safety confirmed in this workload.
Matched post-requalification comparison inconclusive — workload
non-discriminating because all successfully requalifying patterns had
perfect admissibility throughout the recovery phase.

V3: same four arms. Discriminating workload with borderline relapse group.
Degradation onset fixed in manifest before any arm runs. Primary new
question: does Arm D's full gate mechanism revoke post-promotion authority
faster than Arms B and C when a route it promoted later degrades?
