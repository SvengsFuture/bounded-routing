# ARD, SMS, and Bypass — Component Reference

## Purpose

This document defines the route-state model, confidence update process, and bypass decision sequence used by bounded routing.

Bounded routing is the authority layer for the tetrahedral recovery architecture.

The Adaptive Routing Database stores route-level state.

The Success Measurement System updates historical route confidence.

The Intelligent Bypass Mechanism decides whether a learned route currently has permission to execute.

Live tetrahedral structural state remains separate from route confidence and enters the bypass decision through an independent structural-integrity gate.

## Adaptive Routing Database

### Data Model

Each ARD entry corresponds to one task and route class identified by `S_pat`.

```text
ARD entry:
  s_pat                  : str
  p_opt                  : str
  c_success              : float
  obs_count              : int
  obs_window             : deque
  last_used_ms           : float
  depreciation_state     : str
  depreciation_count     : int
  last_flip_ms           : float
  flip_count             : int
  structural_cost        : float
  recovery_sensitive     : bool
  recovery_state         : str
  authority_state        : str
  structural_record_ref  : optional reference
```

### Field Meanings

| Field | Meaning |
|---|---|
| `s_pat` | Task and route-class identifier |
| `p_opt` | Current learned route identifier |
| `c_success` | Historical route-performance confidence in `[0.0, 1.0]` |
| `obs_count` | Total qualifying route observations |
| `obs_window` | Fixed-size recent route-outcome window |
| `last_used_ms` | Timestamp of the most recent route attempt |
| `depreciation_state` | `ACTIVE`, `WARNED`, `DEPRECATED`, or `RETIRED` |
| `depreciation_count` | Consecutive below-threshold route outcomes |
| `last_flip_ms` | Timestamp of the most recent `p_opt` change |
| `flip_count` | Total route changes |
| `structural_cost` | Current route-level structural cost |
| `recovery_sensitive` | Whether recovery affects this route's authority |
| `recovery_state` | Current recovery or requalification condition |
| `authority_state` | `ACTIVE`, `BLOCKED`, `REQUALIFYING`, or `REVOKED` |
| `structural_record_ref` | Reference to the independent structural observation used by the current decision |

The ARD stores route-level evidence and authority state.

It does not compute tetrahedral structural integrity.

A structural record may be referenced by an ARD entry for traceability, but its contents must remain independently sourced and must not be blended into `c_success`.

## Depreciation and Authority State

### Depreciation State Machine

```text
ACTIVE
  |-- c_success below T_depreciate for N qualifying steps --> WARNED

WARNED
  |-- c_success recovers above T_depreciate              --> ACTIVE
  |-- c_success remains low for M additional steps       --> DEPRECATED

DEPRECATED
  |-- fallback only
  |-- no bypass authority
  |-- may remain fail-closed
  |-- may enter a declared fresh-evidence requalification process

RETIRED
  |-- removed from active ARD use
  |-- future observations require a new route record
```

A deprecated route does not become active merely because old confidence rises or time passes.

Any return to active authority must follow the declared requalification process.

### Authority State

Authority state is separate from depreciation state.

```text
ACTIVE
  route may be considered for bypass

BLOCKED
  one or more current gates prevent bypass

REQUALIFYING
  route is accumulating fresh evidence but cannot bypass

REVOKED
  prior bypass authority has been withdrawn
```

A route may have acceptable historical confidence and still be blocked or revoked.

A route may also remain non-deprecated while requalifying after recovery.

## ARD Write Policy

Only the Success Measurement System writes `c_success`.

No other component may directly increase or decrease route confidence.

Full analysis may propose or replace `p_opt` when a better route is found.

Each `p_opt` change increments `flip_count` and updates `last_flip_ms`.

Recovery logic may change `recovery_state` and `authority_state`.

The structural observer may publish a new structural-integrity record, but it does not modify `c_success`.

The Intelligent Bypass Mechanism reads all required state and produces an allow or fallback decision. It does not rewrite historical evidence to make a route pass.

## Success Measurement System

### Purpose

The Success Measurement System records how well a route has performed over time.

It answers:

How successful has this route been?

It does not answer:

Is the tetrahedral substrate structurally intact at this moment?

### Outcome Scoring

After a qualifying route observation, SMS computes an `outcome_score` in `[0.0, 1.0]`.

```text
outcome_score =
    w_lat  * latency_score
  + w_adm  * admissibility_score
  + w_deg  * degradation_score
  + w_stab * stability_score
```

The v1 simulation used:

```text
w_lat  = 0.30
w_adm  = 0.40
w_deg  = 0.20
w_stab = 0.10
```

Admissibility carries the highest weight because an inadmissible route result is more serious than an ordinary performance shortfall.

These weights are simulation parameters, not universal constants.

### Confidence Update

```text
c_success_new =
    alpha * c_success_old
  + (1 - alpha) * outcome_score
```

The v1 simulation used:

```text
alpha = 0.85
```

A higher `alpha` produces slower confidence movement.

A lower `alpha` responds faster to new outcomes but may increase sensitivity to noise and oscillation.

The v3 result showed that slow scalar confidence decay was not sufficient to provide early post-promotion revocation under the tested relapse workload.

### Stability Score

The stability score is derived from variation in recent route outcomes stored in `obs_window`.

High variation lowers the score.

This penalizes a route that alternates between good and bad outcomes even when its average confidence remains above the bypass threshold.

The stability score remains a route-performance measure.

It is not a substitute for live tetrahedral shape integrity.

## Tetrahedral Structural-Integrity Record

The tetrahedral substrate provides a separate structural record.

A valid record should contain at least:

```text
Structural integrity record:
  source_id              : str
  observer_type          : str
  timestamp_ms           : float
  structural_epoch       : str or int
  scope_type             : str
  scope_id               : str
  fact_state             : structured evidence
  logic_state            : structured evidence
  coherence_state        : structured evidence
  coordinator_result     : structured evidence
  shape_integrity        : scalar, enum, or bounded record
  verification_status    : str
```

The exact schema remains a design task.

The record must preserve enough evidence to inspect or replay how the structural conclusion was reached.

A single scalar may be exposed to the bypass gate, but the underlying role-separated or geometric evidence must not be discarded.

### Structural Record Admissibility

A structural record is usable only when:

- its source is authorized
- its timestamp is fresh
- its structural epoch matches the active substrate
- its scope applies to the route or system being evaluated
- its integrity can be verified
- its structural condition remains inside the declared bound

If any of these conditions fails, structural authority is absent.

The router must fall back to full analysis.

A previous valid structural record cannot preserve authority indefinitely.

## Intelligent Bypass Mechanism

### Decision Sequence

```text
task arrives
  |
  +--> PRE produces S_pat
  |
  +--> ARD lookup(S_pat)
         |
         +-- not found or RETIRED
         |     --> full analysis
         |
         +-- found
               |
               +--> gate 1: sufficient route history?
               |       NO --> full analysis
               |
               +--> gate 2: c_success >= T_bypass?
               |       NO --> full analysis
               |
               +--> gate 3: depreciation state permits?
               |       NO --> full analysis
               |
               +--> gate 4: structural_cost <= T_cost?
               |       NO --> full analysis
               |
               +--> gate 5: recovery and authority state permit?
               |       NO --> full analysis
               |
               +--> gate 6: anti-oscillation state permits?
               |       NO --> full analysis
               |
               +--> gate 7: structural record authorized?
               |       NO --> full analysis
               |
               +--> gate 8: structural record fresh?
               |       NO --> full analysis
               |
               +--> gate 9: structural epoch matches?
               |       NO --> full analysis
               |
               +--> gate 10: structural scope applies?
               |       NO --> full analysis
               |
               +--> gate 11: shape integrity inside bound?
                       NO --> full analysis
                       YES --> bounded bypass along P_opt
```

After execution, SMS records the qualifying route outcome and ARD state is updated where applicable.

No individual gate may override a failure in another required gate.

High confidence cannot override invalid structural state.

Valid structural state cannot override a deprecated route.

Elapsed time cannot override required fresh requalification evidence.

## Anti-Oscillation Gate

Bypass is blocked when either condition is true:

```text
current_time_ms - last_flip_ms < T_flip_cooldown_ms
```

or:

```text
recent_flip_count >= MAX_FLIPS_PER_WINDOW
```

Recent flips are counted inside `T_flip_window_ms`.

This prevents rapid alternation between routes that retain misleading confidence.

The v1 oscillation workload produced the clearest supported result in the simulation series.

The naive cache recorded 64 wrong bypasses.

The bounded-routing arm recorded zero.

## Recovery and Requalification Gate

A recovery event removes bypass authority from affected routes.

The current task goes through full analysis.

A candidate route may be evaluated in shadow on that task, but the result applies only to future authority.

Pre-recovery confidence does not count as fresh evidence.

A route in `REQUALIFYING` cannot bypass.

Promotion requires the declared number of consecutive admissible shadow checks and the declared fresh-confidence threshold.

A failed check may reset the consecutive count and reduce fresh confidence.

A persistent-failure route may become deprecated and remain fail-closed.

The v2 primary workload used:

```text
K = 5
fresh confidence threshold = 0.75
```

Those values are simulation settings, not universal requirements.

The v3 sensitivity test showed that increasing `K` from 3 to 5 to 8 delayed restoration and increased fallback without reducing post-promotion wrong bypasses in the tested relapse workload.

## Why the Structural Gate Remains Independent

The route-confidence score records historical route performance.

The structural-integrity record describes the current condition of the tetrahedral substrate.

Blending both into one score would destroy the distinction between history and live structure.

A high confidence average could conceal a fresh structural failure.

A low confidence average could also obscure whether the route itself failed or whether the substrate changed.

Keeping the signals separate makes the decision auditable.

The system can record whether authority was denied because of confidence, depreciation, recovery, oscillation, structural cost, freshness, epoch mismatch, scope mismatch, or actual shape deformation.

That distinction is necessary for both recovery and replay.

## Simulation Parameter Reference

The values below describe the v1 flat harness unless otherwise stated.

| Parameter | Default | Meaning |
|---|---:|---|
| `T_bypass` | 0.75 | Minimum historical route confidence for bypass |
| `T_depreciate` | 0.55 | Confidence below which depreciation begins |
| `T_recover` | 0.70 | Earlier flat-harness recovery threshold |
| `T_cost` | 1.5 | Maximum route-level structural cost multiplier |
| `alpha` | 0.85 | Confidence decay factor |
| `obs_window_size` | 20 | Number of recent route outcomes tracked |
| `depreciation_N` | 5 | Qualifying low outcomes before warning |
| `depreciation_M` | 10 | Additional low outcomes before deprecation |
| `recover_K` | 8 | Earlier flat-harness recovery count |
| `T_retire_ms` | 60000 | Inactivity period before retirement |
| `T_flip_cooldown_ms` | 2000 | Minimum time between route flips |
| `MAX_FLIPS_PER_WINDOW` | 3 | Maximum allowed flips in the flip window |
| `T_flip_window_ms` | 10000 | Window used to count route flips |
| `T_recovery_blackout_ms` | 5000 | V1 fixed recovery blackout |

The v2 and v3 requalification tests used separate fresh-evidence rules and sensitivity values.

The tetrahedral structural-record threshold, freshness interval, epoch rules, and scope model have not yet been frozen.

## Current Evidence Boundary

V1 supports anti-oscillation gating under the tested oscillation workload.

V2 supports removal of stale bypass authority, fresh-evidence requalification, and fail-closed handling of persistent-failure routes.

V3 does not support the claim that the current flat Arm D gate stack revokes unsafe post-promotion authority faster than simpler comparison arms.

In all 15 eligible v3 borderline instances, confidence was the first blocking gate.

The next mechanism to define and test is the independent tetrahedral structural-integrity gate.

That work must preserve role-separated evidence, provenance, freshness, epoch integrity, and scope without folding structural condition into `c_success`.
