# ARD, SMS, and Bypass — Component Reference

## Adaptive Routing Database (ARD)

### Data model

Each entry in ARD corresponds to one pattern class S_pat.

```
ARD entry:
  s_pat               : str       -- pattern signature
  p_opt               : str       -- current best route identifier
  c_success           : float     -- confidence in [0.0, 1.0]
  obs_count           : int       -- total observations
  obs_window          : deque     -- recent outcome window (fixed size)
  last_used_ms        : float     -- timestamp of last bypass attempt
  depreciation_state  : str       -- ACTIVE | WARNED | DEPRECATED | RETIRED
  depreciation_count  : int       -- consecutive below-threshold outcomes
  last_flip_ms        : float     -- timestamp of last P_opt change
  flip_count          : int       -- total route changes
  structural_cost     : float     -- estimated cost of P_opt
  recovery_sensitive  : bool      -- flag: do not bypass post-recovery
```

### Depreciation state machine

```
ACTIVE
  |-- C_success < T_depreciate for N consecutive windows --> WARNED
WARNED
  |-- C_success recovers above T_depreciate                --> ACTIVE
  |-- C_success stays below T_depreciate for M more steps  --> DEPRECATED
DEPRECATED
  |-- Fallback only. No bypass allowed.
  |-- If C_success recovers above T_recover for K steps    --> ACTIVE
  |-- If entry not updated for T_retire window             --> RETIRED
RETIRED
  |-- Removed from ARD. Next observation re-initializes.
```

Parameters T_depreciate, N, M, T_recover, K, T_retire are configurable.
Defaults in the v1 simulation are documented in bounded_routing_sim_v1.py.

### ARD write policy

Only SMS writes C_success. No other component modifies confidence.
P_opt is updated by full-analysis when a better route is found.
Each P_opt update increments flip_count and records last_flip_ms.

---

## Success Measurement System (SMS)

### Outcome scoring

After each task completes (bypass or full analysis), SMS computes
an outcome_score in [0.0, 1.0]:

```
outcome_score = w_lat  * latency_score(t_actual, t_expected)
              + w_adm  * admissibility_score(result)
              + w_deg  * degradation_score(quality)
              + w_stab * stability_score(recent_history)
```

Default weights (v1 simulation):
  w_lat  = 0.30
  w_adm  = 0.40
  w_deg  = 0.20
  w_stab = 0.10

Admissibility carries the highest weight because an inadmissible
result is a structural failure, not a performance shortfall.

### Confidence update

```
C_success_new = alpha * C_success_old + (1 - alpha) * outcome_score
```

alpha = 0.85 default (slow decay, stable confidence).
Lower alpha = faster response to outcome changes, more oscillation risk.

### Stability score

stability_score is derived from the variance of recent outcome scores
in obs_window. High variance -> low stability score. This penalizes
routes that are sometimes good and sometimes bad, even if mean
confidence remains above T_bypass.

---

## Intelligent Bypass Mechanism (IBM)

### Decision sequence

```
task arrives
  |
  +--> PRE: produce S_pat
  |
  +--> ARD lookup(S_pat)
         |
         +-- not found or RETIRED/DEPRECATED
         |     --> full analysis path
         |
         +-- found, ACTIVE or WARNED
               |
               +--> gate 1: C_success >= T_bypass?          NO --> full analysis
               +--> gate 2: structural_cost <= T_cost?       NO --> full analysis
               +--> gate 3: recovery_context OK?             NO --> full analysis
               +--> gate 4: anti-oscillation OK?             NO --> full analysis
               |
               all pass
               |
               +--> bounded bypass: delegate along P_opt
               +--> SMS records outcome
               +--> ARD updated
```

### Anti-oscillation gate

Bypass is blocked if either condition is true:
(current_time_ms - last_flip_ms) < T_flip_cooldown
OR
the number of flips in the last T_flip_window is greater than or equal to MAX_FLIPS_PER_WINDOW.

This prevents the system from rapidly alternating between two routes
that both have borderline confidence.

### Recovery context gate

If the system has experienced a recovery event within T_recovery_blackout
milliseconds, bypass is blocked for any entry with recovery_sensitive=True.

recovery_sensitive is set True for any route that was established during
a period when system topology or load was abnormal.

---

## Parameter table (v1 simulation defaults)

| Parameter | Default | Meaning |
|-----------|---------|---------|
| T_bypass | 0.75 | min confidence for bypass |
| T_depreciate | 0.55 | confidence below which depreciation begins |
| T_recover | 0.70 | confidence required to exit DEPRECATED |
| T_cost | 1.5 | max structural cost multiplier for bypass |
| alpha | 0.85 | confidence decay factor |
| obs_window_size | 20 | recent outcomes tracked |
| depreciation_N | 5 | consecutive below-T_depreciate before WARNED |
| depreciation_M | 10 | additional steps before DEPRECATED |
| recover_K | 8 | consecutive above-T_recover to exit DEPRECATED |
| T_retire_ms | 60000 | inactivity window before RETIRED |
| T_flip_cooldown_ms | 2000 | min ms between route flips |
| MAX_FLIPS_PER_WINDOW | 3 | max flips in T_flip_window |
| T_flip_window_ms | 10000 | window for flip count |
| T_recovery_blackout_ms | 5000 | bypass blackout after recovery event |
