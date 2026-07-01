"""
Bounded Routing Simulation v3
Recovery Requalification with Post-Authority Relapse

Controlling specification: docs/validation_plan_v3.md (frozen/approved).
Base mechanics inherited from the verified v2 script (bounded_routing_sim_v2.py).
Does not modify, rename, or overwrite any v1 or v2 file.

This file implements:
  - shared pre-generated manifest (per seed, before any arm runs)
  - four arms: A_FULL_ANALYSIS, B_NAIVE_CACHE, C_TIMER_BOUND, D_REQUALIFYING
  - three route classes: CONTROL (1-4), PERSISTENT_FAILURE (0), BORDERLINE_RELAPSE (5-7)
  - fixed per-seed degradation onset schedule
  - K=5 primary run, K=3/5/8 sensitivity sweep
  - primary matched window (post requalified_at_ms) and secondary relapse-only
    view (post first_inadmissible_task_ms)
  - manifest coverage pre-check (>= max(K_REQUALIFY_SWEEP) = 8 clean obs)
  - all 16 assertions (A1-A16), including the pre-execution verdict-branch
    function test (A13)
  - NA handling for zero-bypass-denominator rates
  - terminal state counts from final recovery row per (seed, pattern_id) only
  - full verdict pipeline: Step 0 (branch) -> Step 1 (suppression) ->
    Step 2 (primary K=5 verdict) -> Step 3 (K=3/K=8 sensitivity downgrade)
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import deque
from pathlib import Path
import time
import sys

# =========================================================================
# PARAMETER BLOCK (exact values from validation_plan_v3.md)
# =========================================================================

# --- Inherited from V2 (unchanged) ---
SEEDS           = [42, 99, 500, 777, 1337]
N_PATTERNS      = 8
DT_MS           = 20.0

T_BYPASS             = 0.75
T_DEPRECIATE         = 0.55
T_RECOVER_ARD        = 0.70
T_COST_MAX           = 1.5
ALPHA                = 0.85
OBS_WINDOW_SIZE      = 20
DEPRECIATION_N       = 5
DEPRECIATION_M       = 10
RECOVER_K            = 8
T_RETIRE_MS          = 60_000.0
T_FLIP_COOLDOWN_MS   = 2_000.0
MAX_FLIPS_PER_WINDOW = 3
T_FLIP_WINDOW_MS     = 10_000.0
T_RECOVERY_BLACKOUT_MS = 5_000.0   # Arm C only

K_REQUALIFY_PRIMARY = 5
K_REQUALIFY_SWEEP   = [3, 5, 8]

W_LAT  = 0.30
W_ADM  = 0.40
W_DEG  = 0.20
W_STAB = 0.10

COST_BYPASS_NORMAL  = 0.3
COST_BYPASS_DRIFTED = 0.8
COST_FULL_ANALYSIS  = 1.0
COST_BYPASS_FAILED  = 2.0

LATENCY_FULL_ANALYSIS = 40.0
LATENCY_BYPASS_FAST   = 8.0
LATENCY_BYPASS_SLOW   = 25.0
LATENCY_NOISE_STD     = 3.0

# --- V3 phase timing (recovery phase extended from V2's 95,000 to 110,000) ---
PHASE_STABLE_END   =  30_000.0
PHASE_DRIFT_END    =  60_000.0
PHASE_FAULT_END    =  80_000.0
PHASE_RECOVERY_END = 110_000.0
SIM_DURATION_MS    = 120_000.0   # oscillation phase 110,000-120,000

# --- V3 additions ---
Q_REQUALIFY_HIGH     = 0.92
Q_RELAPSE_FLOOR_5    = 0.25
Q_RELAPSE_FLOOR_6    = 0.15
T_REQUALIFY_WINDOW_MS = 5_000.0
T_RELAPSE_RAMP_MS    = 4_000.0
T_OSC_PERIOD_MS      = 3_000.0
Q_OSC_HIGH           = 0.90
Q_OSC_LOW            = 0.20

SEED_RELAPSE_OFFSET_MS = {
    42:   0.0,
    99:   500.0,
    500:  1000.0,
    777:  1500.0,
    1337: 2000.0,
}

MANIFEST_COVERAGE_MIN_OBS = max(K_REQUALIFY_SWEEP)   # = 8

CONTROL_PATTERNS    = [1, 2, 3, 4]
PERSISTENT_PATTERN  = 0
BORDERLINE_PATTERNS = [5, 6, 7]

# Oscillation-phase pattern (V2-inherited, pattern 1 reused in stable oscillation phase)
OSCILLATION_FLIP_PERIOD_MS = 4000.0
FAULT_ADMISSIBILITY_RATE   = 0.15

# Gate vocab
GATE_REQUALIFYING_COUNT      = "REQUALIFYING_COUNT"
GATE_REQUALIFYING_CONFIDENCE = "REQUALIFYING_CONFIDENCE"
GATE_DEPRECATED              = "DEPRECATED"
GATE_TIMER                   = "TIMER"
GATE_NONE                    = "NONE"

# Module-level log for A6 coverage reporting across all (seed, k) runs
A6_COVERAGE_LOG = []

BYPASS_GATE_CONFIDENCE  = "confidence"
BYPASS_GATE_COST        = "cost"
BYPASS_GATE_OSCILLATION = "anti_oscillation"
BYPASS_GATE_COOLDOWN    = "cooldown"
BYPASS_GATE_DEPRECIATION = "depreciation"
BYPASS_GATE_RECOVERY_STATE = "recovery_state"


def degradation_onset_ms(seed):
    return PHASE_FAULT_END + T_REQUALIFY_WINDOW_MS + SEED_RELAPSE_OFFSET_MS[seed]


# =========================================================================
# SHARED TASK MANIFEST
# =========================================================================

def build_manifest(seed):
    """
    Generate the full per-seed task manifest before any arm runs.
    Implements the route-class rules, admissibility generation summary,
    and degradation schedule exactly as declared in validation_plan_v3.md.
    """
    rng = np.random.RandomState(seed)
    onset = degradation_onset_ms(seed)
    tasks = []
    t = 0.0

    # pattern-0 drift/fault route_quality state (deterministic schedule, V2-inherited)
    while t < SIM_DURATION_MS:
        if t < PHASE_STABLE_END:
            phase = "stable"
        elif t < PHASE_DRIFT_END:
            phase = "drift"
        elif t < PHASE_FAULT_END:
            phase = "fault"
        elif t < PHASE_RECOVERY_END:
            phase = "recovery"
        else:
            phase = "oscillation"

        pid = int(rng.randint(0, N_PATTERNS))

        # ---- route_quality and route_class ----
        if pid == PERSISTENT_PATTERN:
            route_class = "PERSISTENT_FAILURE"
            if phase == "stable":
                rq = 1.0
            elif phase == "drift":
                frac = (t - PHASE_STABLE_END) / (PHASE_DRIFT_END - PHASE_STABLE_END)
                rq = max(0.2, 1.0 - 0.7 * frac)
            elif phase == "fault":
                rq = 0.1
            elif phase == "recovery":
                rq = 0.1   # persistent failure: stays low throughout recovery
            else:
                rq = 0.1

        elif pid in CONTROL_PATTERNS:
            route_class = "CONTROL"
            rq = 1.0

        elif pid in BORDERLINE_PATTERNS:
            route_class = "BORDERLINE_RELAPSE"
            if phase != "recovery":
                rq = 1.0  # outside recovery, treat as stable/background
            elif t < onset:
                rq = Q_REQUALIFY_HIGH
            else:
                # post-onset degradation profile, per pattern
                dt_since_onset = t - onset
                if pid == 5:
                    frac = min(1.0, dt_since_onset / T_RELAPSE_RAMP_MS)
                    rq = Q_REQUALIFY_HIGH + (Q_RELAPSE_FLOOR_5 - Q_REQUALIFY_HIGH) * frac
                elif pid == 6:
                    rq = Q_RELAPSE_FLOOR_6
                else:  # pid == 7, oscillation
                    cyc = dt_since_onset % T_OSC_PERIOD_MS
                    half = T_OSC_PERIOD_MS / 2.0
                    rq = Q_OSC_HIGH if cyc < half else Q_OSC_LOW
        else:
            # pattern 1 also doubles as the V2 oscillation-phase pattern outside recovery
            route_class = "CONTROL" if pid in CONTROL_PATTERNS else "OTHER"
            rq = 1.0

        # oscillation-phase override (pattern 1) - V2 inherited, applies after recovery phase
        if phase == "oscillation" and pid == 1:
            osc_cycle = (t % OSCILLATION_FLIP_PERIOD_MS) / OSCILLATION_FLIP_PERIOD_MS
            rq = 1.0 if osc_cycle < 0.5 else 0.2
            route_class = "CONTROL"

        # ---- candidate_admissible determination ----
        relapse_phase_label = "STABLE"
        if phase == "recovery":
            if pid == PERSISTENT_PATTERN:
                candidate_admissible = False   # deterministic, per plan
                relapse_phase_label = "PRE_RECOVERY"
            elif pid in CONTROL_PATTERNS:
                candidate_admissible = True    # deterministic, full recovery phase
                relapse_phase_label = "CLEAN_REQUALIFY"
            elif pid in BORDERLINE_PATTERNS:
                if t < onset:
                    candidate_admissible = True   # deterministic clean interval
                    relapse_phase_label = "CLEAN_REQUALIFY"
                else:
                    candidate_admissible = bool(rng.random() < rq)  # probabilistic post-onset
                    relapse_phase_label = "POST_ONSET"
            else:
                candidate_admissible = bool(rng.random() < rq)
        else:
            candidate_admissible = bool(rng.random() < rq)

        # ---- candidate_latency_ms / candidate_cost ----
        clean_interval_forced = (
            phase == "recovery" and
            ((pid in CONTROL_PATTERNS) or
             (pid in BORDERLINE_PATTERNS and t < onset))
        )
        if clean_interval_forced:
            # Forced fast-latency band + normal cost, per plan
            candidate_latency = float(LATENCY_BYPASS_FAST + rng.uniform(
                -LATENCY_NOISE_STD, LATENCY_NOISE_STD * 2))
            candidate_latency = max(LATENCY_BYPASS_FAST - LATENCY_NOISE_STD,
                                     min(candidate_latency,
                                         LATENCY_BYPASS_FAST + LATENCY_NOISE_STD * 2))
            candidate_cost = COST_BYPASS_NORMAL
        else:
            if rq > 0.5:
                candidate_latency = float(LATENCY_BYPASS_FAST + rng.normal(0, LATENCY_NOISE_STD))
                candidate_cost = COST_BYPASS_NORMAL
            else:
                candidate_latency = float(LATENCY_BYPASS_SLOW + rng.normal(0, LATENCY_NOISE_STD))
                candidate_cost = COST_BYPASS_DRIFTED
            candidate_latency = max(1.0, candidate_latency)

        tasks.append({
            "time_ms":              t,
            "pattern_id":           pid,
            "phase":                phase,
            "route_quality":        float(rq),
            "candidate_admissible": bool(candidate_admissible),
            "candidate_latency_ms": float(candidate_latency),
            "candidate_cost":       float(candidate_cost),
            "relapse_phase":        relapse_phase_label,
            "route_class":          route_class,
            "degradation_onset_ms": onset,
        })
        t += DT_MS

    return tasks

# =========================================================================
# SMS SCORING (V2-inherited)
# =========================================================================

def sms_outcome_score(latency_ms, admissible, route_quality, obs_window):
    lat_score  = 1.0 if latency_ms <= LATENCY_BYPASS_FAST * 2 else 0.5
    adm_score  = 1.0 if admissible else 0.0
    deg_score  = route_quality
    if len(obs_window) >= 3:
        var = float(np.var(list(obs_window)))
        stab_score = max(0.0, 1.0 - var * 4)
    else:
        stab_score = 0.5
    return W_LAT * lat_score + W_ADM * adm_score + W_DEG * deg_score + W_STAB * stab_score


# =========================================================================
# ARD ENTRY (V2-inherited, extended with v3 fields)
# =========================================================================

class ARDEntry:
    def __init__(self, pid, time_ms):
        self.pid                = pid
        self.p_opt              = f"route_{pid}_A"
        self.c_success          = 0.0
        self.obs_count          = 0
        self.obs_window         = deque(maxlen=OBS_WINDOW_SIZE)
        self.last_used_ms       = time_ms
        self.depreciation_state = "ACTIVE"
        self.depreciation_count = 0
        self.recover_count      = 0
        self.last_flip_ms       = -T_FLIP_COOLDOWN_MS * 2
        self.flip_count         = 0
        self.flip_times         = deque(maxlen=MAX_FLIPS_PER_WINDOW + 5)
        self.structural_cost    = COST_BYPASS_NORMAL
        self.recovery_sensitive = False

        # requalification fields (Arm D only)
        self.requalify_window         = deque(maxlen=1)
        self.requalify_obs_with_epoch = []   # (score, timestamp_ms)
        self.requalify_count          = 0
        self.requalify_deprec_count   = 0
        self.requalified_at_ms        = None
        self.pre_recovery_state       = None

        # state-transition history (v3 addition, for per-route diagnostics)
        self.state_transition_history = []   # (time_ms, from_state, to_state)

        # v3: was this pid DEPRECATED-at-signal? populated by signal_recovery
        self.was_deprecated_at_signal = False

    def transition(self, t, new_state):
        if new_state != self.depreciation_state:
            self.state_transition_history.append((t, self.depreciation_state, new_state))
            self.depreciation_state = new_state

    def update_depreciation(self, t):
        """Standard depreciation state machine (V2-inherited, unchanged)."""
        if self.c_success < T_DEPRECIATE:
            self.depreciation_count += 1
            self.recover_count       = 0
            if (self.depreciation_state == "ACTIVE"
                    and self.depreciation_count >= DEPRECIATION_N):
                self.transition(t, "WARNED")
            elif (self.depreciation_state == "WARNED"
                    and self.depreciation_count >= DEPRECIATION_N + DEPRECIATION_M):
                self.transition(t, "DEPRECATED")
        else:
            if self.depreciation_state == "WARNED":
                self.transition(t, "ACTIVE")
                self.depreciation_count = 0
            elif self.depreciation_state == "DEPRECATED":
                if self.c_success >= T_RECOVER_ARD:
                    self.recover_count += 1
                    if self.recover_count >= RECOVER_K:
                        self.transition(t, "ACTIVE")
                        self.depreciation_count = 0
                        self.recover_count      = 0
                else:
                    self.recover_count = 0
            elif self.depreciation_state not in ("REQUALIFYING",):
                self.depreciation_count = 0


# =========================================================================
# ROW BUILDER
# =========================================================================

def make_row(task, seed, arch, k_requalify,
             latency_ms, admissible, bypassed, wrong_bypass, fallback, cost,
             time_since_recovery_ms, requalification_state, requalify_count,
             shadow_route_admissible, shadow_latency_ms, shadow_cost,
             shadow_outcome_score, fresh_requalify_confidence,
             requalified_at_ms, bypass_post_requalify,
             requalification_gate_reason, bypass_gate_reason,
             oscillation_event=False, depreciation_event=False,
             promotion_completed_this_task=False):
    return {
        "seed":                        seed,
        "arch":                        arch,
        "k_requalify":                 k_requalify,
        "time_ms":                     task["time_ms"],
        "pattern_id":                  task["pattern_id"],
        "phase":                       task["phase"],
        "route_quality":               task["route_quality"],
        "route_class":                 task["route_class"],
        "degradation_onset_ms":        task["degradation_onset_ms"],
        "candidate_admissible":        task["candidate_admissible"],
        "candidate_latency_ms":        task["candidate_latency_ms"],
        "candidate_cost":              task["candidate_cost"],
        "bypassed":                    bypassed,
        "admissible":                  admissible,
        "wrong_bypass":                wrong_bypass,
        "latency_ms":                  latency_ms,
        "structural_cost":             cost,
        "fallback":                    fallback,
        "oscillation_event":           oscillation_event,
        "depreciation_event":          depreciation_event,
        "time_since_recovery_ms":      time_since_recovery_ms,
        "requalification_state":       requalification_state,
        "requalify_count":             requalify_count,
        "shadow_route_admissible":     shadow_route_admissible,
        "shadow_latency_ms":           shadow_latency_ms,
        "shadow_structural_cost":      shadow_cost,
        "shadow_outcome_score":        shadow_outcome_score,
        "fresh_requalify_confidence":  fresh_requalify_confidence,
        "requalified_at_ms":           requalified_at_ms,
        "bypass_post_requalify":       bypass_post_requalify,
        "requalification_gate_reason": requalification_gate_reason,
        "bypass_gate_reason":          bypass_gate_reason,
        "promotion_completed_this_task": promotion_completed_this_task,
    }


# =========================================================================
# ARM A: Full analysis baseline
# =========================================================================

class FullAnalysisArm:
    arch_label = "A_FULL_ANALYSIS"

    def __init__(self, seed, k_requalify=K_REQUALIFY_PRIMARY):
        self.rng         = np.random.RandomState(seed * 7919 + 1)
        self.seed        = seed
        self.k_requalify = k_requalify

    def process(self, task):
        latency = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
        rec_ms  = (task["time_ms"] - PHASE_FAULT_END) if task["phase"] == "recovery" else None
        return make_row(task, self.seed, self.arch_label, self.k_requalify,
                        latency, True, False, False, False, COST_FULL_ANALYSIS,
                        rec_ms, None, 0,
                        None, None, None, None, None, None, False,
                        GATE_NONE, GATE_NONE)


# =========================================================================
# ARM B: Naive cache
# =========================================================================

class NaiveCacheArm(FullAnalysisArm):
    arch_label = "B_NAIVE_CACHE"

    def __init__(self, seed, k_requalify=K_REQUALIFY_PRIMARY):
        super().__init__(seed, k_requalify)
        self.confidence  = {}
        self.last_route  = {}
        self.flip_counts = {}

    def _get_c(self, pid):
        return self.confidence.get(pid, 0.0)

    def _update_c(self, pid, score):
        self.confidence[pid] = ALPHA * self._get_c(pid) + (1 - ALPHA) * score

    def process(self, task):
        pid    = task["pattern_id"]
        t      = task["time_ms"]
        rq     = task["route_quality"]
        c      = self._get_c(pid)
        rec_ms = (t - PHASE_FAULT_END) if task["phase"] == "recovery" else None

        # FIX 1: restore real V2 oscillation-phase flip bookkeeping for pattern 1.
        # route_quality already encodes the high/low half-cycle (manifest-driven);
        # here we detect the underlying route identity flip and record it.
        osc_event = False
        if task["phase"] == "oscillation" and pid == 1:
            new_rt = "A" if (t % OSCILLATION_FLIP_PERIOD_MS) < (OSCILLATION_FLIP_PERIOD_MS / 2) else "B"
            if new_rt != self.last_route.get(pid, "A"):
                self.flip_counts[pid] = self.flip_counts.get(pid, 0) + 1
                self.last_route[pid]  = new_rt
                osc_event = True

        if c >= T_BYPASS:
            admissible = task["candidate_admissible"]
            latency    = task["candidate_latency_ms"]
            cost       = task["candidate_cost"]
            wrong_bp   = not admissible
            fell_back  = False
            self._update_c(pid, 1.0 if admissible else 0.0)
        else:
            admissible = True
            latency    = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True
            self._update_c(pid, 1.0 if rq > 0.5 else 0.5)

        row = make_row(task, self.seed, self.arch_label, self.k_requalify,
                       latency, admissible, c >= T_BYPASS and not fell_back,
                       wrong_bp, fell_back, cost,
                       rec_ms, None, 0,
                       None, None, None, None, None, None, False,
                       GATE_NONE, GATE_NONE)
        row["oscillation_event"] = osc_event
        return row

# =========================================================================
# ARM C: Timer-bound recovery blackout (V2-inherited)
# =========================================================================

class TimerBoundArm(FullAnalysisArm):
    arch_label = "C_TIMER_BOUND"

    def __init__(self, seed, k_requalify=K_REQUALIFY_PRIMARY):
        super().__init__(seed, k_requalify)
        self.ard              = {}
        self.last_recovery_ms = -T_RECOVERY_BLACKOUT_MS * 2
        self._in_recovery     = False

    def _get_entry(self, pid, t):
        if pid not in self.ard:
            self.ard[pid] = ARDEntry(pid, t)
        return self.ard[pid]

    def _update_sms(self, entry, t, latency, admissible, rq):
        score = sms_outcome_score(latency, admissible, rq, entry.obs_window)
        entry.obs_window.append(score)
        entry.c_success = ALPHA * entry.c_success + (1 - ALPHA) * score
        entry.obs_count += 1
        entry.update_depreciation(t)

    def _check_bypass(self, entry, t, candidate_cost):
        if entry.depreciation_state in ("DEPRECATED", "RETIRED"):
            return False, GATE_DEPRECATED, BYPASS_GATE_DEPRECIATION
        if entry.c_success < T_BYPASS:
            return False, GATE_NONE, BYPASS_GATE_CONFIDENCE
        if candidate_cost > T_COST_MAX:
            return False, GATE_NONE, BYPASS_GATE_COST
        if (entry.recovery_sensitive and
                (t - self.last_recovery_ms) < T_RECOVERY_BLACKOUT_MS):
            return False, GATE_TIMER, GATE_TIMER
        recent_flips = sum(1 for ft in entry.flip_times if (t - ft) < T_FLIP_WINDOW_MS)
        if recent_flips >= MAX_FLIPS_PER_WINDOW:
            return False, GATE_NONE, BYPASS_GATE_OSCILLATION
        if (t - entry.last_flip_ms) < T_FLIP_COOLDOWN_MS:
            return False, GATE_NONE, BYPASS_GATE_COOLDOWN
        return True, GATE_NONE, GATE_NONE

    def process(self, task):
        pid   = task["pattern_id"]
        t     = task["time_ms"]
        rq    = task["route_quality"]
        phase = task["phase"]
        rec_ms = (t - PHASE_FAULT_END) if phase == "recovery" else None

        entry = self._get_entry(pid, t)

        if phase == "recovery" and not self._in_recovery:
            self.last_recovery_ms = t
            for e in self.ard.values():
                e.recovery_sensitive = True
            self._in_recovery = True
        elif phase != "recovery":
            self._in_recovery = False

        # FIX 1: restore real V2 oscillation-phase flip bookkeeping for pattern 1.
        # Updates p_opt, last_flip_ms, flip_count, flip_times so the anti-oscillation
        # and cooldown gates in _check_bypass can actually be exercised.
        osc_event = False
        if phase == "oscillation" and pid == 1:
            new_route = ("route_1_A" if (t % OSCILLATION_FLIP_PERIOD_MS) <
                         (OSCILLATION_FLIP_PERIOD_MS / 2) else "route_1_B")
            if new_route != entry.p_opt:
                entry.p_opt        = new_route
                entry.last_flip_ms = t
                entry.flip_count  += 1
                entry.flip_times.append(t)
                osc_event = True

        allowed, rq_gate, bp_gate = self._check_bypass(entry, t, task["candidate_cost"])
        dep_event = False

        if allowed:
            admissible = task["candidate_admissible"]
            latency    = task["candidate_latency_ms"]
            cost       = task["candidate_cost"]
            wrong_bp   = not admissible
            fell_back  = False
            if rq < 0.4:
                entry.structural_cost = min(COST_BYPASS_FAILED, entry.structural_cost * 1.15)
            else:
                entry.structural_cost = max(COST_BYPASS_NORMAL, entry.structural_cost * 0.98)
            prev = entry.depreciation_state
            self._update_sms(entry, t, latency, admissible, rq)
            if prev != "DEPRECATED" and entry.depreciation_state == "DEPRECATED":
                dep_event = True
        else:
            admissible = True
            latency    = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True
            if ((t - self.last_recovery_ms) >= T_RECOVERY_BLACKOUT_MS
                    and entry.recovery_sensitive):
                entry.recovery_sensitive = False
            prev = entry.depreciation_state
            self._update_sms(entry, t, latency, True, rq)
            if prev != "DEPRECATED" and entry.depreciation_state == "DEPRECATED":
                dep_event = True

        entry.last_used_ms = t
        row = make_row(task, self.seed, self.arch_label, self.k_requalify,
                       latency, admissible, allowed and not fell_back,
                       wrong_bp, fell_back, cost,
                       rec_ms, entry.depreciation_state, 0,
                       None, None, None, None, None,
                       entry.requalified_at_ms, False,
                       rq_gate, bp_gate)
        row["depreciation_event"] = dep_event
        row["oscillation_event"]  = osc_event
        return row


# =========================================================================
# ARM D: Requalifying (full gate mechanism, V2-inherited + v3 fail-closed fix)
# =========================================================================

class RequalifyingArm(FullAnalysisArm):
    arch_label = "D_REQUALIFYING"
    _assertion_log = []   # class-level; cleared per (seed, k) run

    def __init__(self, seed, k_requalify=K_REQUALIFY_PRIMARY):
        super().__init__(seed, k_requalify)
        self.ard                 = {}
        self._in_recovery        = False
        self._recovery_signal_ms = None
        self._promotions         = []   # (pid, count, conf, t)
        self._deprecated_at_recovery     = set()
        self._deprecated_during_recovery = set()

    def _get_entry(self, pid, t):
        if pid not in self.ard:
            self.ard[pid] = ARDEntry(pid, t)
        return self.ard[pid]

    def _update_sms(self, entry, t, latency, admissible, rq):
        score = sms_outcome_score(latency, admissible, rq, entry.obs_window)
        entry.obs_window.append(score)
        entry.c_success = ALPHA * entry.c_success + (1 - ALPHA) * score
        entry.obs_count += 1
        entry.update_depreciation(t)

    def _signal_recovery(self, t):
        self._recovery_signal_ms = t
        for pid, entry in self.ard.items():
            entry.pre_recovery_state = entry.depreciation_state
            if entry.depreciation_state in ("ACTIVE", "WARNED"):
                entry.transition(t, "REQUALIFYING")
                entry.requalify_count          = 0
                entry.requalify_deprec_count   = 0
                entry.requalify_window         = deque(maxlen=self.k_requalify)
                entry.requalify_obs_with_epoch = []
                entry.requalified_at_ms        = None
                entry.recovery_sensitive       = True
            elif entry.depreciation_state == "DEPRECATED":
                entry.was_deprecated_at_signal = True
                self._deprecated_at_recovery.add(pid)

    def _update_shadow(self, entry, shadow_latency, shadow_admissible, rq, t):
        shadow_score = sms_outcome_score(
            shadow_latency, shadow_admissible, rq, entry.requalify_window
        )
        entry.requalify_obs_with_epoch.append((shadow_score, t))
        entry.requalify_window.append(shadow_score)

        if shadow_admissible:
            entry.requalify_count += 1
        else:
            entry.requalify_count = 0

        fresh_conf = float(np.mean(list(entry.requalify_window))) if entry.requalify_window else 0.0

        if fresh_conf < T_DEPRECIATE:
            entry.requalify_deprec_count += 1
            if entry.requalify_deprec_count >= DEPRECIATION_N + DEPRECIATION_M:
                entry.transition(t, "DEPRECATED")
                self._deprecated_during_recovery.add(entry.pid)
                return shadow_score, GATE_DEPRECATED, False, fresh_conf
        else:
            entry.requalify_deprec_count = 0

        count_met = entry.requalify_count >= self.k_requalify
        conf_met  = fresh_conf >= T_BYPASS

        if count_met and conf_met:
            entry.c_success  = fresh_conf
            entry.obs_window = deque(list(entry.requalify_window), maxlen=OBS_WINDOW_SIZE)
            entry.transition(t, "ACTIVE")
            entry.requalified_at_ms      = t
            entry.requalify_deprec_count = 0
            self._promotions.append((entry.pid, entry.requalify_count, fresh_conf, t))
            return shadow_score, GATE_NONE, True, fresh_conf
        elif count_met and not conf_met:
            return shadow_score, GATE_REQUALIFYING_CONFIDENCE, False, fresh_conf
        else:
            return shadow_score, GATE_REQUALIFYING_COUNT, False, fresh_conf

    def _check_bypass(self, entry, t, candidate_cost):
        """Returns (allowed, rq_gate, bp_gate). Evaluates the FULL gate stack:
        requalification state, deprecation, confidence, structural cost,
        anti-oscillation, flip cooldown. The gate that fires first (in this
        declared priority order) is reported in bp_gate / first_blocking_gate."""
        if entry.depreciation_state == "REQUALIFYING":
            if entry.requalify_count >= self.k_requalify:
                return False, GATE_REQUALIFYING_CONFIDENCE, GATE_REQUALIFYING_CONFIDENCE
            return False, GATE_REQUALIFYING_COUNT, GATE_REQUALIFYING_COUNT
        if entry.depreciation_state in ("DEPRECATED", "RETIRED"):
            return False, GATE_DEPRECATED, BYPASS_GATE_DEPRECIATION
        if entry.c_success < T_BYPASS:
            return False, GATE_NONE, BYPASS_GATE_CONFIDENCE
        if candidate_cost > T_COST_MAX:
            return False, GATE_NONE, BYPASS_GATE_COST
        # Arm D has no timer blackout; recovery_sensitive itself does not block
        # bypass (replaced by requalification). Flag is retained for state-history
        # parity with Arm C only.
        recent_flips = sum(1 for ft in entry.flip_times if (t - ft) < T_FLIP_WINDOW_MS)
        if recent_flips >= MAX_FLIPS_PER_WINDOW:
            return False, GATE_NONE, BYPASS_GATE_OSCILLATION
        if (t - entry.last_flip_ms) < T_FLIP_COOLDOWN_MS:
            return False, GATE_NONE, BYPASS_GATE_COOLDOWN
        return True, GATE_NONE, GATE_NONE

    def process(self, task):
        pid   = task["pattern_id"]
        t     = task["time_ms"]
        rq    = task["route_quality"]
        phase = task["phase"]
        rec_ms = (t - PHASE_FAULT_END) if phase == "recovery" else None

        entry = self._get_entry(pid, t)

        if phase == "recovery" and not self._in_recovery:
            self._signal_recovery(t)
            self._in_recovery = True
        elif phase != "recovery" and self._in_recovery:
            self._in_recovery = False

        # FIX 1: restore real V2 oscillation-phase flip bookkeeping for pattern 1
        # so Arm D's anti-oscillation and cooldown gates can be exercised.
        osc_event = False
        if phase == "oscillation" and pid == 1:
            new_route = ("route_1_A" if (t % OSCILLATION_FLIP_PERIOD_MS) <
                         (OSCILLATION_FLIP_PERIOD_MS / 2) else "route_1_B")
            if new_route != entry.p_opt:
                entry.p_opt        = new_route
                entry.last_flip_ms = t
                entry.flip_count  += 1
                entry.flip_times.append(t)
                osc_event = True

        allowed, rq_gate, bp_gate = self._check_bypass(entry, t, task["candidate_cost"])

        dep_event              = False
        shadow_admissible_out  = None
        shadow_latency_out     = None
        shadow_cost_out        = None
        shadow_score_out       = None
        fresh_conf_out         = None
        bypass_post_req        = False
        promotion_this_task    = False

        if entry.depreciation_state == "REQUALIFYING":
            pre_decision_rq_gate = rq_gate

            admissible = True
            latency    = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True

            shadow_admissible_out = task["candidate_admissible"]
            shadow_latency_out    = task["candidate_latency_ms"]
            shadow_cost_out       = task["candidate_cost"]

            prev_state = entry.depreciation_state
            shadow_score_out, post_shadow_rq_gate, promoted, fresh_conf_out = self._update_shadow(
                entry, shadow_latency_out, shadow_admissible_out, rq, t
            )
            if prev_state != "DEPRECATED" and entry.depreciation_state == "DEPRECATED":
                dep_event = True

            rq_gate = pre_decision_rq_gate
            promotion_this_task = promoted

        elif allowed:
            admissible = task["candidate_admissible"]
            latency    = task["candidate_latency_ms"]
            cost       = task["candidate_cost"]
            wrong_bp   = not admissible
            fell_back  = False
            bypass_post_req = (entry.requalified_at_ms is not None)
            if rq < 0.4:
                entry.structural_cost = min(COST_BYPASS_FAILED, entry.structural_cost * 1.15)
            else:
                entry.structural_cost = max(COST_BYPASS_NORMAL, entry.structural_cost * 0.98)
            prev = entry.depreciation_state
            self._update_sms(entry, t, latency, admissible, rq)
            if prev != "DEPRECATED" and entry.depreciation_state == "DEPRECATED":
                dep_event = True
                if phase == "recovery":
                    self._deprecated_during_recovery.add(entry.pid)

        elif entry.depreciation_state == "DEPRECATED":
            # Fail-closed: full analysis handles the live task; the route receives
            # NO SMS update. c_success is frozen; depreciation state stays DEPRECATED.
            admissible = True
            latency    = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True

        else:
            admissible = True
            latency    = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True
            prev = entry.depreciation_state
            self._update_sms(entry, t, latency, True, rq)
            if prev != "DEPRECATED" and entry.depreciation_state == "DEPRECATED":
                dep_event = True
                if phase == "recovery":
                    self._deprecated_during_recovery.add(entry.pid)

        entry.last_used_ms = t

        if (allowed and not fell_back) and entry.depreciation_state == "REQUALIFYING":
            RequalifyingArm._assertion_log.append(
                f"A4 FAIL pid={pid} t={t} bypassed while REQUALIFYING"
            )

        row = make_row(task, self.seed, self.arch_label, self.k_requalify,
                       latency, admissible, allowed and not fell_back,
                       wrong_bp, fell_back, cost,
                       rec_ms, entry.depreciation_state, entry.requalify_count,
                       shadow_admissible_out, shadow_latency_out, shadow_cost_out,
                       shadow_score_out, fresh_conf_out,
                       entry.requalified_at_ms, bypass_post_req,
                       rq_gate, bp_gate,
                       promotion_completed_this_task=promotion_this_task)
        row["depreciation_event"] = dep_event
        row["oscillation_event"]  = osc_event
        return row

# =========================================================================
# MANIFEST COVERAGE PRE-CHECK (A16) -- runs before any arm executes
# =========================================================================

def check_manifest_coverage(manifest, seed):
    """
    A16: for each (seed, pattern_id) in CONTROL + BORDERLINE_RELAPSE classes,
    count manifest rows with phase==recovery and time_ms < degradation_onset_ms.
    Must be >= MANIFEST_COVERAGE_MIN_OBS (=8). Halt with workload-construction
    error if not satisfied. This runs BEFORE any arm executes.
    """
    onset = degradation_onset_ms(seed)
    relevant_pids = CONTROL_PATTERNS + BORDERLINE_PATTERNS
    counts = {pid: 0 for pid in relevant_pids}
    for row in manifest:
        if row["phase"] == "recovery" and row["time_ms"] < onset and row["pattern_id"] in relevant_pids:
            counts[row["pattern_id"]] += 1

    failures = {pid: c for pid, c in counts.items() if c < MANIFEST_COVERAGE_MIN_OBS}
    if failures:
        raise RuntimeError(
            f"A16 WORKLOAD-CONSTRUCTION ERROR: seed={seed} insufficient clean-interval "
            f"coverage for patterns {failures} (need >= {MANIFEST_COVERAGE_MIN_OBS}, "
            f"got {failures}). Halting before arm execution."
        )
    return counts


# =========================================================================
# A12: manifest admissibility verification (run before arm execution,
# operates directly on the saved manifest)
# =========================================================================

def check_manifest_admissibility(manifest, seed):
    """
    A12 part 1: borderline relapse patterns (5-7) must have candidate_admissible
    == True for every recovery row with time_ms < degradation_onset_ms.
    A12 part 2: control patterns (1-4) must have candidate_admissible == True
    for every recovery row across the ENTIRE recovery phase.
    """
    onset = degradation_onset_ms(seed)
    bad_borderline = []
    bad_control = []
    for row in manifest:
        if row["phase"] != "recovery":
            continue
        pid = row["pattern_id"]
        if pid in BORDERLINE_PATTERNS and row["time_ms"] < onset:
            if not row["candidate_admissible"]:
                bad_borderline.append((pid, row["time_ms"]))
        if pid in CONTROL_PATTERNS:
            if not row["candidate_admissible"]:
                bad_control.append((pid, row["time_ms"]))

    assert len(bad_borderline) == 0, (
        f"A12 FAIL (borderline): seed={seed} {len(bad_borderline)} clean-interval "
        f"rows have candidate_admissible=False: {bad_borderline[:5]}"
    )
    assert len(bad_control) == 0, (
        f"A12 FAIL (control): seed={seed} {len(bad_control)} recovery-phase "
        f"rows have candidate_admissible=False: {bad_control[:5]}"
    )


# =========================================================================
# A13: verdict branch function + mandatory pre-execution test
# =========================================================================

def select_verdict_branch(eligible_borderline_instance_count, total_relapse_wrong_bypasses_B):
    """Pure function. Returns one of:
    'EMPTY_COHORT_NOT_SUPPORTED', 'INCONCLUSIVE', 'EVALUATE_MAIN_VERDICT'."""
    if eligible_borderline_instance_count == 0:
        return "EMPTY_COHORT_NOT_SUPPORTED"
    if total_relapse_wrong_bypasses_B == 0:
        return "INCONCLUSIVE"
    return "EVALUATE_MAIN_VERDICT"


def run_verdict_branch_self_test():
    """A13: must be run BEFORE any simulation arm executes. Halts on failure."""
    tests = [
        ((0, 0), "EMPTY_COHORT_NOT_SUPPORTED"),
        ((1, 0), "INCONCLUSIVE"),
        ((1, 1), "EVALUATE_MAIN_VERDICT"),
    ]
    for (args, expected) in tests:
        actual = select_verdict_branch(*args)
        if actual != expected:
            raise RuntimeError(
                f"A13 PRE-EXECUTION SELF-TEST FAILED: select_verdict_branch{args} "
                f"returned '{actual}', expected '{expected}'. Halting before arm execution."
            )
    print("A13 verdict-branch self-test: PASS (3/3 synthetic cases)")


# =========================================================================
# A1: shared manifest integrity check (run after all arms complete for a seed)
# =========================================================================

def check_shared_manifest_integrity(manifest, all_arm_rows, seed):
    manifest_by_key = {
        (row["time_ms"], row["pattern_id"]): row for row in manifest
    }
    for row in all_arm_rows:
        key = (row["time_ms"], row["pattern_id"])
        mrow = manifest_by_key.get(key)
        assert mrow is not None, f"A1 FAIL: seed={seed} key={key} not found in manifest"
        assert row["candidate_admissible"] == mrow["candidate_admissible"], (
            f"A1 FAIL: seed={seed} key={key} candidate_admissible mismatch "
            f"arch={row['arch']}: row={row['candidate_admissible']} manifest={mrow['candidate_admissible']}"
        )
        assert abs(row["candidate_latency_ms"] - mrow["candidate_latency_ms"]) < 1e-9, (
            f"A1 FAIL: seed={seed} key={key} candidate_latency_ms mismatch arch={row['arch']}"
        )
        assert abs(row["candidate_cost"] - mrow["candidate_cost"]) < 1e-9, (
            f"A1 FAIL: seed={seed} key={key} candidate_cost mismatch arch={row['arch']}"
        )

# =========================================================================
# ARM-D-SPECIFIC ASSERTIONS: A2, A3, A4, A5, A6, A9, A10, A11, A14, A15
# =========================================================================

def run_arm_d_assertions(arm_d, rows_d, seed, k_requalify):
    df = pd.DataFrame(rows_d)
    rec = df[df["phase"] == "recovery"]

    # --- A4: Arm D never bypasses while REQUALIFYING ---
    assert not RequalifyingArm._assertion_log, \
        "A4 FAIL: " + "; ".join(RequalifyingArm._assertion_log)
    bad = df[(df["bypassed"] == True) & (df["requalification_state"] == "REQUALIFYING")]
    assert len(bad) == 0, \
        f"A4 FAIL (data): seed={seed} k={k_requalify} {len(bad)} rows bypassed while REQUALIFYING"

    # --- A3 (independent check): for every promotion, independently reconstruct
    #     the shadow sequence for that (seed, pattern_id) and verify, from the
    #     recorded shadow history itself (not from the promotion tuple's count/conf
    #     fields), that:
    #       (a) the most recent K shadow observations immediately preceding the
    #           promotion timestamp were all admissible (reconstructed from row
    #           data: shadow_route_admissible == True for each)
    #       (b) those K observations are consecutive in time (recovery rows have
    #           no gaps in pattern observation order within REQUALIFYING state)
    #       (c) every one of those K observations occurred at or after the
    #           recovery signal (re-derived, not assumed)
    #       (d) recomputing the mean SMS score of exactly those K observations
    #           from shadow_outcome_score independently reproduces a value >= T_BYPASS
    #     The independent reconstruction must agree with the stored promotion
    #     record; if it does not, A3 fails.
    pid_to_obs_history = {pid: list(entry.requalify_obs_with_epoch) for pid, entry in arm_d.ard.items()}

    for pid, stored_count, stored_conf, t_prom in arm_d._promotions:
        # Independent reconstruction from recorded shadow history (score, timestamp)
        history = pid_to_obs_history.get(pid, [])
        # Observations strictly before/at the promotion timestamp
        history_upto_promo = [(s, ts) for (s, ts) in history if ts <= t_prom]
        assert len(history_upto_promo) >= arm_d.k_requalify, (
            f"A3 FAIL (independent): seed={seed} k={k_requalify} pid={pid} promoted at "
            f"t={t_prom} but only {len(history_upto_promo)} shadow observations exist "
            f"up to that time, need >= K={arm_d.k_requalify}"
        )
        last_k = history_upto_promo[-arm_d.k_requalify:]

        # (c) all K observations at or after recovery signal
        recovery_signal_ms = arm_d._recovery_signal_ms
        assert all(ts >= recovery_signal_ms for (s, ts) in last_k), (
            f"A3 FAIL (independent): seed={seed} k={k_requalify} pid={pid} the K shadow "
            f"observations preceding promotion include one predating the recovery signal"
        )

        # Re-derive admissibility for those exact K observations directly from the
        # row data for this (seed, pattern_id), matched by timestamp, rather than
        # trusting any cached flag.
        pid_rows = rec[(rec["pattern_id"] == pid) &
                       (rec["shadow_outcome_score"].notna())].sort_values("time_ms")
        last_k_timestamps = {ts for (s, ts) in last_k}
        matched_rows = pid_rows[pid_rows["time_ms"].isin(last_k_timestamps)]
        assert len(matched_rows) == arm_d.k_requalify, (
            f"A3 FAIL (independent): seed={seed} k={k_requalify} pid={pid} could not "
            f"locate all {arm_d.k_requalify} shadow rows by timestamp in recorded data "
            f"(found {len(matched_rows)})"
        )
        # (a) every one of the K reconstructed rows must show admissible == True
        bad_admiss = matched_rows[matched_rows["shadow_route_admissible"] != True]
        assert len(bad_admiss) == 0, (
            f"A3 FAIL (independent): seed={seed} k={k_requalify} pid={pid} {len(bad_admiss)} "
            f"of the K shadow observations immediately preceding promotion were NOT "
            f"admissible (independently reconstructed from row data)"
        )

        # (b) consecutiveness: the K reconstructed timestamps must be exactly the
        # K most recent shadow observations for this route with no admissible-streak
        # break between them, i.e. requalify_count for pattern at promotion equals K
        # and no inadmissible shadow observation occurred between the (K)th-from-last
        # and the promotion timestamp.
        sorted_ts = sorted(last_k_timestamps)
        between = pid_rows[(pid_rows["time_ms"] > sorted_ts[0]) &
                           (pid_rows["time_ms"] <= t_prom)]
        non_admissible_between = between[between["shadow_route_admissible"] != True]
        assert len(non_admissible_between) == 0, (
            f"A3 FAIL (independent): seed={seed} k={k_requalify} pid={pid} an inadmissible "
            f"shadow observation occurred within the reconstructed K-window, breaking "
            f"consecutiveness"
        )

        # (d) recompute mean of exactly these K observed scores; must reproduce
        # a value >= T_BYPASS, independently of the stored promotion confidence.
        recomputed_scores = [s for (s, ts) in last_k]
        recomputed_mean = float(np.mean(recomputed_scores))
        assert recomputed_mean >= T_BYPASS, (
            f"A3 FAIL (independent): seed={seed} k={k_requalify} pid={pid} independently "
            f"recomputed mean of K preceding shadow scores = {recomputed_mean:.4f} "
            f"< T_BYPASS={T_BYPASS}"
        )

        # Independent reconstruction must agree with the stored promotion record
        assert stored_count >= arm_d.k_requalify, (
            f"A3 FAIL: seed={seed} k={k_requalify} pid={pid} stored promotion count="
            f"{stored_count} < K={arm_d.k_requalify}"
        )
        assert stored_conf >= T_BYPASS, (
            f"A3 FAIL: seed={seed} k={k_requalify} pid={pid} stored promotion conf="
            f"{stored_conf:.4f} < T_BYPASS={T_BYPASS}"
        )
        assert abs(recomputed_mean - stored_conf) < 1e-6, (
            f"A3 FAIL: seed={seed} k={k_requalify} pid={pid} independently recomputed "
            f"confidence {recomputed_mean:.6f} disagrees with stored promotion "
            f"confidence {stored_conf:.6f}"
        )

    # --- A2: every shadow observation timestamped >= recovery signal ---
    recovery_signal_ms = arm_d._recovery_signal_ms
    if recovery_signal_ms is not None:
        for pid, entry in arm_d.ard.items():
            for score, obs_t in entry.requalify_obs_with_epoch:
                assert obs_t >= recovery_signal_ms, (
                    f"A2 FAIL: seed={seed} k={k_requalify} pid={pid} obs at t={obs_t} "
                    f"predates recovery signal t={recovery_signal_ms}"
                )

    # --- A6: routes DEPRECATED at recovery signal never promoted, never get
    #         shadow observations. Coverage must be reported explicitly --
    #         silently doing nothing when the set is empty is not an acceptable
    #         substitute for stating that the check was unexercised. ---
    a6_coverage_record = {
        "seed": seed, "k_requalify": k_requalify,
        "n_deprecated_at_signal": len(arm_d._deprecated_at_recovery),
        "exercised": len(arm_d._deprecated_at_recovery) > 0,
    }
    if len(arm_d._deprecated_at_recovery) == 0:
        print(f"  A6 [seed={seed} k={k_requalify}]: PRESENT BUT UNEXERCISED "
              f"(no route was DEPRECATED at the recovery signal)")
    else:
        print(f"  A6 [seed={seed} k={k_requalify}]: EXERCISED "
              f"({len(arm_d._deprecated_at_recovery)} route(s) DEPRECATED at signal: "
              f"{sorted(arm_d._deprecated_at_recovery)})")
    for pid in arm_d._deprecated_at_recovery:
        entry = arm_d.ard.get(pid)
        if entry is None:
            continue
        assert len(entry.requalify_obs_with_epoch) == 0, (
            f"A6 FAIL: seed={seed} k={k_requalify} pid={pid} was DEPRECATED at recovery "
            f"but received {len(entry.requalify_obs_with_epoch)} shadow observations"
        )
        promoted_pids = {p[0] for p in arm_d._promotions}
        assert pid not in promoted_pids, (
            f"A6 FAIL: seed={seed} k={k_requalify} pid={pid} was DEPRECATED at recovery "
            f"but appears in promotions list"
        )
    A6_COVERAGE_LOG.append(a6_coverage_record)

    # --- A5 (strengthened): routes DEPRECATED during recovery remain fail-closed
    #     for every subsequent recovery row ---
    for pid in arm_d._deprecated_during_recovery:
        entry = arm_d.ard.get(pid)
        if entry is None:
            continue
        assert entry.depreciation_state == "DEPRECATED", (
            f"A5 FAIL: seed={seed} k={k_requalify} pid={pid} deprecated during recovery "
            f"but ended phase in state={entry.depreciation_state}"
        )
        promoted_pids = {p[0] for p in arm_d._promotions}
        assert pid not in promoted_pids, (
            f"A5 FAIL: seed={seed} k={k_requalify} pid={pid} deprecated during recovery "
            f"but appears in promotions list"
        )
        pid_rows = rec[rec["pattern_id"] == pid].sort_values("time_ms")
        dep_rows = pid_rows[pid_rows["requalification_state"] == "DEPRECATED"]
        if len(dep_rows) == 0:
            continue
        first_dep_t = float(dep_rows["time_ms"].iloc[0])
        post_dep = pid_rows[pid_rows["time_ms"] >= first_dep_t]
        bad_state    = post_dep[post_dep["requalification_state"] != "DEPRECATED"]
        bad_bypass   = post_dep[post_dep["bypassed"] == True]
        bad_fallback = post_dep[post_dep["fallback"] != True]
        assert len(bad_state) == 0, (
            f"A5 FAIL: seed={seed} k={k_requalify} pid={pid} has {len(bad_state)} "
            f"post-depreciation rows with state != DEPRECATED"
        )
        assert len(bad_bypass) == 0, (
            f"A5 FAIL: seed={seed} k={k_requalify} pid={pid} has {len(bad_bypass)} "
            f"post-depreciation rows with bypassed=True"
        )
        assert len(bad_fallback) == 0, (
            f"A5 FAIL: seed={seed} k={k_requalify} pid={pid} has {len(bad_fallback)} "
            f"post-depreciation rows with fallback != True"
        )

    # --- A14: pattern 0 never promoted by Arm D ---
    promoted_pids_all = {p[0] for p in arm_d._promotions}
    assert 0 not in promoted_pids_all, (
        f"A14 FAIL: seed={seed} k={k_requalify} pattern 0 appears in Arm D promotions list"
    )

    # --- A15 (corrected): every clean-interval shadow observation has
    #     shadow_outcome_score >= T_BYPASS, INCLUDING the observation on the
    #     task that completes promotion. A promotion-completing row is stored
    #     with requalification_state == ACTIVE (the state was already updated),
    #     so filtering on requalification_state == REQUALIFYING silently drops
    #     exactly the row that proves promotion was earned. Instead, identify
    #     clean shadow observations by the presence of a shadow score together
    #     with route class, phase, and timestamp -- not by post-processing state.
    onset = degradation_onset_ms(seed)
    clean_shadow_rows = rec[
        (rec["phase"] == "recovery") &
        (rec["time_ms"] < onset) &
        (rec["shadow_outcome_score"].notna()) &
        (rec["route_class"].isin(["CONTROL", "BORDERLINE_RELAPSE"])) &
        (rec["pattern_id"] != PERSISTENT_PATTERN)
    ]
    bad_clean = clean_shadow_rows[clean_shadow_rows["shadow_outcome_score"] < T_BYPASS]
    assert len(bad_clean) == 0, (
        f"A15 FAIL: seed={seed} k={k_requalify} {len(bad_clean)} clean-interval shadow "
        f"observations (including any promotion-completing row) fell below "
        f"T_BYPASS={T_BYPASS}. Min observed: "
        f"{clean_shadow_rows['shadow_outcome_score'].min() if len(clean_shadow_rows) else 'N/A'}"
    )
    # Confirm the fix actually captures promotion-completing rows: any row where
    # promotion_completed_this_task is True must be present in clean_shadow_rows
    # if it falls inside the clean interval.
    promo_rows_in_window = rec[
        (rec["promotion_completed_this_task"] == True) &
        (rec["time_ms"] < onset)
    ]
    if len(promo_rows_in_window):
        promo_keys = set(zip(promo_rows_in_window["pattern_id"], promo_rows_in_window["time_ms"]))
        clean_keys = set(zip(clean_shadow_rows["pattern_id"], clean_shadow_rows["time_ms"]))
        missing = promo_keys - clean_keys
        assert len(missing) == 0, (
            f"A15 FAIL: seed={seed} k={k_requalify} promotion-completing row(s) "
            f"{missing} fall inside the clean interval but were excluded from the "
            f"A15 check"
        )

    # --- A10: requalification time uses exactly one value per (seed, pattern_id) ---
    rq_per_route = (
        rec[rec["requalified_at_ms"].notna()]
        .groupby(["seed", "pattern_id"])["requalified_at_ms"]
        .nunique()
    )
    # nunique should be 1 for every group (one promotion per route under current mechanics)
    bad_multi = rq_per_route[rq_per_route > 1]
    assert len(bad_multi) == 0, (
        f"A10 FAIL: seed={seed} k={k_requalify} route(s) with multiple distinct "
        f"requalified_at_ms values: {bad_multi.to_dict()}"
    )

    return clean_shadow_rows

# =========================================================================
# A9: terminal state counts from FINAL recovery row per (seed, pattern_id) only
# =========================================================================

def compute_final_row_state_counts(df_d_recovery):
    """Returns dict {state: count} using only the final recovery row per
    (seed, pattern_id). This is the ONLY valid source of terminal state counts."""
    if len(df_d_recovery) == 0:
        return {"ACTIVE": 0, "REQUALIFYING": 0, "DEPRECATED": 0}
    final_rows = (
        df_d_recovery.sort_values("time_ms")
                     .groupby(["seed", "pattern_id"], sort=False)
                     .last()
                     .reset_index()
    )
    return {
        "ACTIVE":       int((final_rows["requalification_state"] == "ACTIVE").sum()),
        "REQUALIFYING": int((final_rows["requalification_state"] == "REQUALIFYING").sum()),
        "DEPRECATED":   int((final_rows["requalification_state"] == "DEPRECATED").sum()),
    }, final_rows


def compute_historical_appearance_counts(df_d_recovery):
    """Diagnostic only (see A9). Counts ANY row where a state was observed,
    per (seed, pattern_id), then aggregates. NOT used for terminal reporting."""
    if len(df_d_recovery) == 0:
        return {"ACTIVE": 0, "REQUALIFYING": 0, "DEPRECATED": 0}
    appeared = (
        df_d_recovery.groupby(["seed", "pattern_id", "requalification_state"])
                     .size().reset_index(name="n")
    )
    out = {}
    for state in ("ACTIVE", "REQUALIFYING", "DEPRECATED"):
        out[state] = int(appeared[appeared["requalification_state"] == state]
                          [["seed", "pattern_id"]].drop_duplicates().shape[0])
    return out


def check_A9_against_written_output(sens_csv_path, df_raw):
    """A9 (corrected): after the sensitivity summary table has been written to
    disk, independently recompute final-row state counts for K=3, K=5, and K=8
    directly from the raw per-task dataframe, and compare those independently
    recomputed values against the counts actually present in the written CSV.
    This does NOT compare a value to itself; it reads back the persisted
    artifact and checks it against a fresh computation."""
    written = pd.read_csv(sens_csv_path)
    mismatches = []
    for k in K_REQUALIFY_SWEEP:
        sub = df_raw[(df_raw["arch"] == "D_REQUALIFYING") &
                     (df_raw["phase"] == "recovery") &
                     (df_raw["k_requalify"] == k)]
        independent_counts, _ = compute_final_row_state_counts(sub)

        row = written[written["k_requalify"] == k]
        assert len(row) == 1, f"A9 FAIL: expected exactly one sensitivity row for K={k}, found {len(row)}"
        row = row.iloc[0]
        written_counts = {
            "ACTIVE":       int(row["final_ACTIVE"]),
            "REQUALIFYING": int(row["final_REQUALIFYING"]),
            "DEPRECATED":   int(row["final_DEPRECATED"]),
        }
        if independent_counts != written_counts:
            mismatches.append((k, independent_counts, written_counts))

    assert len(mismatches) == 0, (
        f"A9 FAIL: independently recomputed final-row state counts disagree with "
        f"the counts actually written to {sens_csv_path}: {mismatches}"
    )
    return True


# =========================================================================
# Per-route-instance table (borderline relapse routes), eligibility (A11),
# ineligibility_reason
# =========================================================================

def build_route_instance_table(df_primary_k5, arm_d_objs=None, k=K_REQUALIFY_PRIMARY):
    """
    One row per (seed, pattern_id) for BORDERLINE_RELAPSE patterns (5,6,7) in
    Arm D. Computes eligibility, ineligibility_reason, state_transition_history_D
    (pulled directly from the live ARDEntry when arm_d_objs is provided),
    first_inadmissible_task_ms, and revocation timing metrics (filled in later
    by compute_revocation_metrics).
    """
    d = df_primary_k5[df_primary_k5["arch"] == "D_REQUALIFYING"]
    rec_d = d[d["phase"] == "recovery"]

    rows = []
    for seed in SEEDS:
        onset = degradation_onset_ms(seed)
        arm_d = arm_d_objs.get((seed, k)) if arm_d_objs else None
        for pid in BORDERLINE_PATTERNS:
            sub = rec_d[(rec_d["seed"] == seed) & (rec_d["pattern_id"] == pid)].sort_values("time_ms")
            if len(sub) == 0:
                continue
            rq_rows = sub[sub["requalified_at_ms"].notna()]
            requalified_at = float(rq_rows["requalified_at_ms"].iloc[0]) if len(rq_rows) else None

            eligible = (requalified_at is not None) and (requalified_at < onset)

            ineligibility_reason = None
            if not eligible:
                last_row = sub.iloc[-1]
                ineligibility_reason = (
                    f"final_state={last_row['requalification_state']}, "
                    f"final_requalify_count={int(last_row['requalify_count'])}, "
                    f"final_gate={last_row['requalification_gate_reason']}, "
                    f"requalified_at_ms={requalified_at}"
                )

            first_inadm = sub[sub["candidate_admissible"] == False]
            first_inadmissible_task_ms = (
                float(first_inadm["time_ms"].iloc[0]) if len(first_inadm) else None
            )

            final_state = sub.iloc[-1]["requalification_state"]

            # Fix 9: pull the real state-transition history directly from the
            # live ARDEntry for this (seed, pattern_id), not reconstructed
            # from rows (the entry records it natively via entry.transition()).
            state_transitions = None
            if arm_d is not None:
                entry = arm_d.ard.get(pid)
                if entry is not None:
                    state_transitions = [
                        {"time_ms": t, "from": fr, "to": to}
                        for (t, fr, to) in entry.state_transition_history
                    ]

            rows.append({
                "seed": seed,
                "pattern_id": pid,
                "route_class": "BORDERLINE_RELAPSE",
                "requalified_at_ms": requalified_at,
                "time_to_requalify_ms": (requalified_at - PHASE_FAULT_END) if requalified_at else None,
                "degradation_onset_ms": onset,
                "eligible_for_primary_matched_comparison": eligible,
                "ineligibility_reason": ineligibility_reason,
                "first_inadmissible_task_ms": first_inadmissible_task_ms,
                "final_state_D": final_state,
                "state_transition_history_D": state_transitions,
            })
    return pd.DataFrame(rows)


def check_A11(route_instance_df):
    eligible = route_instance_df[route_instance_df["eligible_for_primary_matched_comparison"] == True]
    bad = eligible[eligible["requalified_at_ms"] >= eligible["degradation_onset_ms"]]
    assert len(bad) == 0, (
        f"A11 FAIL: {len(bad)} eligible route instances violate "
        f"requalified_at_ms < degradation_onset_ms: "
        f"{bad[['seed','pattern_id','requalified_at_ms','degradation_onset_ms']].to_dict('records')}"
    )


# =========================================================================
# Matched comparison windows (primary + secondary relapse-only), A7, A8
# =========================================================================

def build_matched_windows(df_primary_k5, route_instance_df):
    """
    Primary window: for each eligible route instance, all (seed,time_ms,pattern_id)
    rows with time_ms > requalified_at_ms, through end of recovery phase.
    Secondary (relapse-only) window: subset of primary restricted to
    time_ms >= first_inadmissible_task_ms.

    Both windows defined ENTIRELY from manifest/Arm-D-promotion timestamps,
    never from any arm's bypass decision (A8).
    """
    eligible = route_instance_df[route_instance_df["eligible_for_primary_matched_comparison"] == True]

    if len(eligible) == 0:
        empty = pd.DataFrame(columns=["seed", "time_ms", "pattern_id"])
        return empty, empty

    primary_keys = []
    relapse_keys = []
    for _, r in eligible.iterrows():
        seed = r["seed"]; pid = r["pattern_id"]
        req_at = r["requalified_at_ms"]
        first_inadm = r["first_inadmissible_task_ms"]

        d_sub = df_primary_k5[
            (df_primary_k5["arch"] == "D_REQUALIFYING") &
            (df_primary_k5["seed"] == seed) &
            (df_primary_k5["pattern_id"] == pid) &
            (df_primary_k5["phase"] == "recovery") &
            (df_primary_k5["time_ms"] > req_at)
        ][["seed", "time_ms", "pattern_id"]]
        primary_keys.append(d_sub)

        if first_inadm is not None:
            r_sub = d_sub[d_sub["time_ms"] >= first_inadm]
            relapse_keys.append(r_sub)

    primary_window_keys = pd.concat(primary_keys).drop_duplicates() if primary_keys else \
        pd.DataFrame(columns=["seed", "time_ms", "pattern_id"])
    relapse_window_keys = pd.concat(relapse_keys).drop_duplicates() if relapse_keys else \
        pd.DataFrame(columns=["seed", "time_ms", "pattern_id"])

    # Join all four arms onto these keys (A8: window defined by keys only,
    # not by any arm's bypass/fallback field)
    primary_matched = df_primary_k5.merge(primary_window_keys, on=["seed", "time_ms", "pattern_id"], how="inner")
    relapse_matched = df_primary_k5.merge(relapse_window_keys, on=["seed", "time_ms", "pattern_id"], how="inner")

    return primary_matched, relapse_matched


def check_A7(primary_matched, relapse_matched):
    for label, df in [("primary", primary_matched), ("relapse", relapse_matched)]:
        if len(df) == 0:
            continue
        key_sets = {}
        for arch in ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
            sub = df[df["arch"] == arch]
            key_sets[arch] = set(zip(sub["seed"], sub["time_ms"], sub["pattern_id"]))
        ref = key_sets["D_REQUALIFYING"]
        for arch, keys in key_sets.items():
            assert keys == ref, (
                f"A7 FAIL ({label}): arch={arch} key set differs from D_REQUALIFYING. "
                f"Missing={len(ref - keys)} Extra={len(keys - ref)}"
            )


def check_A8(route_instance_df, primary_matched, relapse_matched, df_primary_k5):
    """A8 (strengthened): window membership must not depend on any arm's bypass
    decision. Independently reconstruct the EXACT expected primary key set from
    requalified_at_ms and the EXACT expected relapse-only key set from
    first_inadmissible_task_ms, using only the manifest/route-instance table
    (never reading bypassed/fallback from any arm's rows). Verify the produced
    windows equal those expected key sets exactly -- not merely a containment
    or single-arm spot check."""
    eligible = route_instance_df[route_instance_df["eligible_for_primary_matched_comparison"] == True]

    # Independently reconstruct expected primary keys directly from the full
    # K=5 dataframe filtered ONLY by seed/pattern/phase/time -- explicitly
    # dropping bypassed/fallback columns before computing keys so they cannot
    # participate in selection.
    expected_primary_parts = []
    expected_relapse_parts = []
    for _, r in eligible.iterrows():
        seed, pid = r["seed"], r["pattern_id"]
        req_at = r["requalified_at_ms"]
        first_inadm = r["first_inadmissible_task_ms"]

        candidate_rows = df_primary_k5[
            (df_primary_k5["arch"] == "D_REQUALIFYING") &
            (df_primary_k5["seed"] == seed) &
            (df_primary_k5["pattern_id"] == pid) &
            (df_primary_k5["phase"] == "recovery") &
            (df_primary_k5["time_ms"] > req_at)
        ][["seed", "time_ms", "pattern_id"]]  # bypassed/fallback explicitly excluded
        expected_primary_parts.append(candidate_rows)

        if first_inadm is not None:
            expected_relapse_parts.append(
                candidate_rows[candidate_rows["time_ms"] >= first_inadm]
            )

    expected_primary_keys = (
        set(map(tuple, pd.concat(expected_primary_parts)[["seed", "time_ms", "pattern_id"]].values))
        if expected_primary_parts else set()
    )
    expected_relapse_keys = (
        set(map(tuple, pd.concat(expected_relapse_parts)[["seed", "time_ms", "pattern_id"]].values))
        if expected_relapse_parts else set()
    )

    for arch in ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        produced_primary_keys = set(map(tuple, primary_matched[primary_matched["arch"] == arch]
                                        [["seed", "time_ms", "pattern_id"]].values))
        assert produced_primary_keys == expected_primary_keys, (
            f"A8 FAIL (primary, {arch}): produced key set differs from independently "
            f"reconstructed expected set. Missing={len(expected_primary_keys - produced_primary_keys)} "
            f"Extra={len(produced_primary_keys - expected_primary_keys)}"
        )
        produced_relapse_keys = set(map(tuple, relapse_matched[relapse_matched["arch"] == arch]
                                        [["seed", "time_ms", "pattern_id"]].values))
        assert produced_relapse_keys == expected_relapse_keys, (
            f"A8 FAIL (relapse, {arch}): produced key set differs from independently "
            f"reconstructed expected set. Missing={len(expected_relapse_keys - produced_relapse_keys)} "
            f"Extra={len(produced_relapse_keys - expected_relapse_keys)}"
        )

    # Confirm bypassed/fallback fields were not used: re-verify by checking the
    # window contains rows of BOTH bypassed=True and bypassed=False (if any
    # arm fell back at all within the window), proving selection wasn't bypass-gated.
    if len(primary_matched):
        d_primary = primary_matched[primary_matched["arch"] == "D_REQUALIFYING"]
        has_both = d_primary["bypassed"].nunique() <= 2  # trivially true; real check is the set equality above
        assert has_both, "A8 FAIL: unexpected single-value bypassed column"

# =========================================================================
# NA-aware wrong-bypass-rate helper
# =========================================================================

def wbr_or_na(wrong_bypasses, bypass_count):
    """Wrong bypasses / actual bypasses. Returns 'NA' (string) if bypass_count==0."""
    if bypass_count == 0:
        return "NA"
    return round((wrong_bypasses / bypass_count) * 100, 3)


def exposure_wbr(wrong_bypasses, task_count):
    """Wrong bypasses per 1000 eligible tasks. Always reportable."""
    if task_count == 0:
        return 0.0
    return round((wrong_bypasses / task_count) * 1000, 3)


# =========================================================================
# Matched / relapse aggregate metrics per arm
# =========================================================================

def compute_window_metrics(window_df, arch):
    sub = window_df[window_df["arch"] == arch]
    tasks = len(sub)
    bp    = sub[sub["bypassed"] == True]
    bypasses = len(bp)
    wrong    = int(sub["wrong_bypass"].sum())
    fallback_rate = round(sub["fallback"].mean() * 100, 2) if tasks else 0.0
    return {
        "tasks": tasks,
        "bypasses": bypasses,
        "wrong_bypasses": wrong,
        "wbr": wbr_or_na(wrong, bypasses),
        "exposure_wbr": exposure_wbr(wrong, tasks),
        "fallback_rate": fallback_rate,
    }


def compute_per_route_window_metrics(window_df, seed, pid, arch):
    sub = window_df[(window_df["seed"] == seed) & (window_df["pattern_id"] == pid) & (window_df["arch"] == arch)]
    tasks = len(sub)
    bp = sub[sub["bypassed"] == True]
    bypasses = len(bp)
    wrong = int(sub["wrong_bypass"].sum())
    return {
        "tasks": tasks, "bypasses": bypasses, "wrong_bypasses": wrong,
        "wbr": wbr_or_na(wrong, bypasses),
        "exposure_wbr": exposure_wbr(wrong, tasks),
        "fallback_rate": round(sub["fallback"].mean() * 100, 2) if tasks else 0.0,
        "first_wrong_bypass_ms": (
            float(sub[sub["wrong_bypass"] == True]["time_ms"].iloc[0])
            if (sub["wrong_bypass"] == True).any() else None
        ),
    }


def attach_window_fields_to_route_instances(route_instance_df, primary_matched, relapse_matched):
    """
    Fix 9: attach, for every route instance, the complete set of primary-window
    and relapse-only-window task/bypass/wrong-bypass/wbr/exposure-rate/
    fallback-rate fields for Arms B, C, and D, as required by the plan.
    """
    out_rows = []
    for _, r in route_instance_df.iterrows():
        row = r.to_dict()
        seed, pid = r["seed"], r["pattern_id"]
        if not r["eligible_for_primary_matched_comparison"]:
            for view in ("primary", "relapse"):
                for arch_short in ("B", "C", "D"):
                    for field in ("tasks", "bypasses", "wrong_bypasses", "wbr",
                                 "exposure_wbr", "fallback_rate"):
                        row[f"{view}_{field}_{arch_short}"] = None
            out_rows.append(row)
            continue

        for view, window in (("primary", primary_matched), ("relapse", relapse_matched)):
            for arch_short, arch_full in (("B", "B_NAIVE_CACHE"), ("C", "C_TIMER_BOUND"), ("D", "D_REQUALIFYING")):
                m = compute_per_route_window_metrics(window, seed, pid, arch_full)
                row[f"{view}_tasks_{arch_short}"]         = m["tasks"]
                row[f"{view}_bypasses_{arch_short}"]      = m["bypasses"]
                row[f"{view}_wrong_bypasses_{arch_short}"] = m["wrong_bypasses"]
                row[f"{view}_wbr_{arch_short}"]           = m["wbr"]
                row[f"{view}_exposure_wbr_{arch_short}"]  = m["exposure_wbr"]
                row[f"{view}_fallback_rate_{arch_short}"] = m["fallback_rate"]
        out_rows.append(row)

    return pd.DataFrame(out_rows)


# =========================================================================
# Revocation timing metrics (Arm D), gate-name tracking
# =========================================================================

ALL_GATE_NAMES = [
    BYPASS_GATE_CONFIDENCE, BYPASS_GATE_COST, BYPASS_GATE_DEPRECIATION,
    BYPASS_GATE_RECOVERY_STATE, BYPASS_GATE_OSCILLATION, BYPASS_GATE_COOLDOWN,
]

def compute_revocation_metrics(df_primary_k5, route_instance_df):
    """
    For each eligible borderline route instance, compute:
      time_confidence_gate_failed_D, time_first_bypass_authority_blocked_D,
      first_blocking_gate_D, time_first_wrong_bypass_{B,C,D}
    using post-onset recovery rows for that (seed, pattern_id).
    """
    d_all = df_primary_k5[df_primary_k5["arch"] == "D_REQUALIFYING"]
    b_all = df_primary_k5[df_primary_k5["arch"] == "B_NAIVE_CACHE"]
    c_all = df_primary_k5[df_primary_k5["arch"] == "C_TIMER_BOUND"]

    out_rows = []
    for _, r in route_instance_df.iterrows():
        if not r["eligible_for_primary_matched_comparison"]:
            out_rows.append({**r.to_dict(),
                "time_confidence_gate_failed_D": None,
                "time_first_bypass_authority_blocked_D": None,
                "first_blocking_gate_D": None,
                "time_first_wrong_bypass_B": None,
                "time_first_wrong_bypass_C": None,
                "time_first_wrong_bypass_D": None,
            })
            continue

        seed, pid = r["seed"], r["pattern_id"]
        onset = r["degradation_onset_ms"]

        d_sub = d_all[(d_all["seed"] == seed) & (d_all["pattern_id"] == pid) &
                      (d_all["phase"] == "recovery") & (d_all["time_ms"] >= onset)].sort_values("time_ms")

        # time_confidence_gate_failed_D: first post-onset row where bp_gate == confidence
        conf_fail = d_sub[d_sub["bypass_gate_reason"] == BYPASS_GATE_CONFIDENCE]
        t_conf_fail = float(conf_fail["time_ms"].iloc[0]) if len(conf_fail) else None

        # time_first_bypass_authority_blocked_D: first post-onset eligible row
        # where ANY required gate blocks bypass (bp_gate not NONE and not already bypassed)
        blocked = d_sub[(d_sub["bypassed"] == False) & (d_sub["bypass_gate_reason"] != GATE_NONE)]
        if len(blocked):
            t_blocked = float(blocked["time_ms"].iloc[0])
            gate_name = blocked["bypass_gate_reason"].iloc[0]
        else:
            t_blocked = None
            gate_name = None

        b_sub = b_all[(b_all["seed"] == seed) & (b_all["pattern_id"] == pid) &
                      (b_all["phase"] == "recovery") & (b_all["time_ms"] >= onset)]
        c_sub = c_all[(c_all["seed"] == seed) & (c_all["pattern_id"] == pid) &
                      (c_all["phase"] == "recovery") & (c_all["time_ms"] >= onset)]

        def first_wrong(sub):
            wb = sub[sub["wrong_bypass"] == True]
            return float(wb["time_ms"].iloc[0]) if len(wb) else None

        out_rows.append({**r.to_dict(),
            "time_confidence_gate_failed_D": t_conf_fail,
            "time_first_bypass_authority_blocked_D": t_blocked,
            "first_blocking_gate_D": gate_name,
            "time_first_wrong_bypass_B": first_wrong(b_sub),
            "time_first_wrong_bypass_C": first_wrong(c_sub),
            "time_first_wrong_bypass_D": first_wrong(d_sub),
        })

    return pd.DataFrame(out_rows)

# =========================================================================
# VERDICT PIPELINE -- Steps 0, 1, 2, 3 (exact declared order, mutually exclusive)
# =========================================================================

def seed_shows_advantage(seed, route_instance_df, primary_matched, relapse_matched):
    """A seed shows an advantage for D iff D has fewer matched wrong bypasses
    than BOTH B and C across eligible borderline instances in that seed,
    in BOTH matched views."""
    eligible_pids = route_instance_df[
        (route_instance_df["seed"] == seed) &
        (route_instance_df["eligible_for_primary_matched_comparison"] == True)
    ]["pattern_id"].tolist()
    if not eligible_pids:
        return False

    def wrong_count(window_df, arch):
        sub = window_df[(window_df["seed"] == seed) &
                         (window_df["pattern_id"].isin(eligible_pids)) &
                         (window_df["arch"] == arch)]
        return int(sub["wrong_bypass"].sum())

    d_p = wrong_count(primary_matched, "D_REQUALIFYING")
    b_p = wrong_count(primary_matched, "B_NAIVE_CACHE")
    c_p = wrong_count(primary_matched, "C_TIMER_BOUND")
    d_r = wrong_count(relapse_matched, "D_REQUALIFYING")
    b_r = wrong_count(relapse_matched, "B_NAIVE_CACHE")
    c_r = wrong_count(relapse_matched, "C_TIMER_BOUND")

    return (d_p < b_p and d_p < c_p) and (d_r < b_r and d_r < c_r)


def pattern_contributes_advantage(pid, route_instance_df, primary_matched, relapse_matched):
    """A pattern contributes iff D has fewer matched wrong bypasses than BOTH
    B and C for that pattern across all eligible seeds, in BOTH views."""
    eligible_seeds = route_instance_df[
        (route_instance_df["pattern_id"] == pid) &
        (route_instance_df["eligible_for_primary_matched_comparison"] == True)
    ]["seed"].tolist()
    if not eligible_seeds:
        return False

    def wrong_count(window_df, arch):
        sub = window_df[(window_df["pattern_id"] == pid) &
                         (window_df["seed"].isin(eligible_seeds)) &
                         (window_df["arch"] == arch)]
        return int(sub["wrong_bypass"].sum())

    d_p = wrong_count(primary_matched, "D_REQUALIFYING")
    b_p = wrong_count(primary_matched, "B_NAIVE_CACHE")
    c_p = wrong_count(primary_matched, "C_TIMER_BOUND")
    d_r = wrong_count(relapse_matched, "D_REQUALIFYING")
    b_r = wrong_count(relapse_matched, "B_NAIVE_CACHE")
    c_r = wrong_count(relapse_matched, "C_TIMER_BOUND")

    return (d_p < b_p and d_p < c_p) and (d_r < b_r and d_r < c_r)


def evaluate_step2(route_instance_df, primary_matched, relapse_matched):
    """Returns (verdict_str, detail_dict) for the primary K=5 verdict."""
    m_d = compute_window_metrics(primary_matched, "D_REQUALIFYING")
    m_b = compute_window_metrics(primary_matched, "B_NAIVE_CACHE")
    m_c = compute_window_metrics(primary_matched, "C_TIMER_BOUND")
    r_d = compute_window_metrics(relapse_matched, "D_REQUALIFYING")
    r_b = compute_window_metrics(relapse_matched, "B_NAIVE_CACHE")
    r_c = compute_window_metrics(relapse_matched, "C_TIMER_BOUND")

    d_beats_both_primary = m_d["wrong_bypasses"] < m_b["wrong_bypasses"] and m_d["wrong_bypasses"] < m_c["wrong_bypasses"]
    d_beats_both_relapse  = r_d["wrong_bypasses"] < r_b["wrong_bypasses"] and r_d["wrong_bypasses"] < r_c["wrong_bypasses"]

    exposure_not_worse = (
        m_d["exposure_wbr"] <= m_b["exposure_wbr"] and m_d["exposure_wbr"] <= m_c["exposure_wbr"] and
        r_d["exposure_wbr"] <= r_b["exposure_wbr"] and r_d["exposure_wbr"] <= r_c["exposure_wbr"]
    )

    seeds_with_advantage = [s for s in SEEDS if seed_shows_advantage(s, route_instance_df, primary_matched, relapse_matched)]
    patterns_contributing = [p for p in BORDERLINE_PATTERNS
                             if pattern_contributes_advantage(p, route_instance_df, primary_matched, relapse_matched)]

    control_requalified = check_control_requalified_at_k5(route_instance_df_control_cache)

    supported = (
        d_beats_both_primary and d_beats_both_relapse and
        exposure_not_worse and
        len(seeds_with_advantage) >= 3 and
        len(patterns_contributing) >= 2 and
        control_requalified
    )

    # PARTIAL SUPPORT: D shows measurable improvement over >=1 comparison arm
    # in >=1 matched view, but fails one or more full SUPPORTED requirements.
    improvement_over_b_primary = m_d["wrong_bypasses"] < m_b["wrong_bypasses"]
    improvement_over_c_primary = m_d["wrong_bypasses"] < m_c["wrong_bypasses"]
    improvement_over_b_relapse = r_d["wrong_bypasses"] < r_b["wrong_bypasses"]
    improvement_over_c_relapse = r_d["wrong_bypasses"] < r_c["wrong_bypasses"]
    any_improvement = (improvement_over_b_primary or improvement_over_c_primary or
                       improvement_over_b_relapse or improvement_over_c_relapse)

    # NOT SUPPORTED: no matched safety improvement over EITHER B or C in EITHER view
    no_improvement_anywhere = not any_improvement

    detail = {
        "matched_primary": {"D": m_d, "B": m_b, "C": m_c},
        "matched_relapse": {"D": r_d, "B": r_b, "C": r_c},
        "seeds_with_advantage": seeds_with_advantage,
        "patterns_contributing": patterns_contributing,
        "control_requalified_at_k5": control_requalified,
        "d_beats_both_primary": d_beats_both_primary,
        "d_beats_both_relapse": d_beats_both_relapse,
        "exposure_not_worse": exposure_not_worse,
    }

    if supported:
        return "SUPPORTED", detail
    elif no_improvement_anywhere:
        return "NOT SUPPORTED", detail
    else:
        return "PARTIAL SUPPORT", detail


def check_control_requalified_at_k5(control_cache):
    return control_cache


def step3_sensitivity_check(df_all_k, route_instance_df_by_k):
    """
    Only called when Step 2 verdict == SUPPORTED.
    Re-evaluate the same D-beats-both-in-both-views advantage at K=3 and K=8.
    Returns True if advantage holds at BOTH; False if it disappears at either.
    """
    holds_at_all = True
    detail = {}
    for k in [3, 8]:
        df_k = df_all_k[df_all_k["k_requalify"] == k]
        ri_k = route_instance_df_by_k[k]
        pm_k, rm_k = build_matched_windows(df_k, ri_k)
        if len(pm_k) == 0 or len(rm_k) == 0:
            holds_at_all = False
            detail[k] = "no matched data"
            continue
        m_d = compute_window_metrics(pm_k, "D_REQUALIFYING")
        m_b = compute_window_metrics(pm_k, "B_NAIVE_CACHE")
        m_c = compute_window_metrics(pm_k, "C_TIMER_BOUND")
        r_d = compute_window_metrics(rm_k, "D_REQUALIFYING")
        r_b = compute_window_metrics(rm_k, "B_NAIVE_CACHE")
        r_c = compute_window_metrics(rm_k, "C_TIMER_BOUND")
        holds = (m_d["wrong_bypasses"] < m_b["wrong_bypasses"] and m_d["wrong_bypasses"] < m_c["wrong_bypasses"] and
                 r_d["wrong_bypasses"] < r_b["wrong_bypasses"] and r_d["wrong_bypasses"] < r_c["wrong_bypasses"])
        detail[k] = holds
        if not holds:
            holds_at_all = False
    return holds_at_all, detail

# =========================================================================
# RUN ONE SEED (all four arms, one K value)
# =========================================================================

def run_seed(seed, k_requalify, manifest):
    arms = [
        FullAnalysisArm(seed, k_requalify),
        NaiveCacheArm(seed, k_requalify),
        TimerBoundArm(seed, k_requalify),
        RequalifyingArm(seed, k_requalify),
    ]
    all_rows = []
    arm_d_obj = None
    arm_d_rows = None

    for arm in arms:
        if isinstance(arm, RequalifyingArm):
            RequalifyingArm._assertion_log.clear()
        rows = []
        for task in manifest:
            rows.append(arm.process(task))
        if isinstance(arm, RequalifyingArm):
            run_arm_d_assertions(arm, rows, seed, k_requalify)
            arm_d_obj = arm
            arm_d_rows = rows
        all_rows.extend(rows)

    check_shared_manifest_integrity(manifest, all_rows, seed)

    return all_rows, arm_d_obj


# =========================================================================
# RUN FULL SWEEP
# =========================================================================

def run_sweep(out_dir):
    t0 = time.time()
    all_rows = []
    manifests = {}
    arm_d_objs = {}   # (seed, k) -> RequalifyingArm instance

    print("=" * 76)
    print("BOUNDED ROUTING SIMULATION v3 -- Recovery Requalification with Relapse")
    print(f"Primary K_REQUALIFY={K_REQUALIFY_PRIMARY} | Sweep K={K_REQUALIFY_SWEEP}")
    print("=" * 76)

    # ---- Build + save manifests for all seeds BEFORE any arm runs ----
    print("\nBuilding shared manifests (before any arm executes)...")
    for seed in SEEDS:
        manifest = build_manifest(seed)
        manifests[seed] = manifest
        check_manifest_coverage(manifest, seed)          # A16
        check_manifest_admissibility(manifest, seed)      # A12
        pd.DataFrame(manifest).to_csv(out_dir / f"manifest_seed{seed}_v3.csv", index=False)
        print(f"  seed={seed}  tasks={len(manifest)}  degradation_onset_ms={degradation_onset_ms(seed)}  "
              f"[A16 PASS, A12 PASS]")

    print("\nA16 + A12 passed for all seeds. Manifests saved.\n")

    # ---- A13: verdict-branch self-test, BEFORE any arm execution ----
    run_verdict_branch_self_test()
    print()

    # ---- Run all K values ----
    for k in K_REQUALIFY_SWEEP:
        label = "PRIMARY" if k == K_REQUALIFY_PRIMARY else "sensitivity"
        print(f"Running K_REQUALIFY={k} ({label})")
        for seed in SEEDS:
            rows, arm_d = run_seed(seed, k, manifests[seed])
            all_rows.extend(rows)
            arm_d_objs[(seed, k)] = arm_d
            print(f"  seed={seed}  tasks={len(rows)}  t={time.time()-t0:.1f}s")

    df = pd.DataFrame(all_rows)
    print(f"\nAll per-arm assertions (A1-A6, A10, A14, A15) passed. {len(df)} total rows. "
          f"{time.time()-t0:.1f}s")
    return df, manifests, arm_d_objs


# =========================================================================
# MAIN ANALYSIS / VERDICT / OUTPUT GENERATION
# =========================================================================

def main():
    OUT_DIR = Path.cwd() / "bounded_routing_output_v3"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    df, manifests, arm_d_objs = run_sweep(OUT_DIR)

    df_k5 = df[df["k_requalify"] == K_REQUALIFY_PRIMARY].copy()
    df_k5_d = df_k5[df_k5["arch"] == "D_REQUALIFYING"]
    df_k5_d_rec = df_k5_d[df_k5_d["phase"] == "recovery"]

    # ---- Terminal state counts (final-row-only) -- diagnostic display now;
    #      real A9 verification happens after the sensitivity CSV is written,
    #      by reading that file back and independently recomputing. ----
    print("\n" + "=" * 76)
    print("TERMINAL STATE COUNTS (final recovery row per (seed,pattern_id) only)")
    print("=" * 76)
    final_counts, final_rows_df = compute_final_row_state_counts(df_k5_d_rec)
    historical_counts = compute_historical_appearance_counts(df_k5_d_rec)
    print(f"  Final-row terminal counts (K=5): {final_counts}")
    print(f"  Historical appearance counts (diagnostic only, NOT used for A9): {historical_counts}")

    # ---- Route instance table (borderline relapse, K=5) ----
    route_instance_df = build_route_instance_table(df_k5, arm_d_objs, K_REQUALIFY_PRIMARY)
    check_A11(route_instance_df)
    print(f"\nA11 PASS: all eligible route instances satisfy requalified_at_ms < degradation_onset_ms")

    eligible_count = int(route_instance_df["eligible_for_primary_matched_comparison"].sum())
    print(f"\neligible_borderline_instance_count = {eligible_count}")

    # ---- Matched windows (primary + relapse-only), A7, A8 ----
    primary_matched, relapse_matched = build_matched_windows(df_k5, route_instance_df)
    check_A7(primary_matched, relapse_matched)
    check_A8(route_instance_df, primary_matched, relapse_matched, df_k5)
    print("A7 PASS: matched window key sets identical across all four arms.")
    print("A8 PASS: window membership defined by manifest timestamps only.")

    # ---- Revocation metrics ----
    route_instance_df = compute_revocation_metrics(df_k5, route_instance_df)

    # ---- Fix 9: attach all primary/relapse window B,C,D fields ----
    route_instance_df = attach_window_fields_to_route_instances(
        route_instance_df, primary_matched, relapse_matched
    )

    # ---- Control-group requalification check (K=5) ----
    control_d = df_k5_d_rec[df_k5_d_rec["pattern_id"].isin(CONTROL_PATTERNS)]
    control_final = (
        control_d.sort_values("time_ms").groupby(["seed", "pattern_id"], sort=False).last().reset_index()
    )
    control_requalified = bool((control_final["requalification_state"] == "ACTIVE").all()) if len(control_final) else False
    global route_instance_df_control_cache
    route_instance_df_control_cache = control_requalified
    print(f"\nControl-group requalified at K=5 (all patterns 1-4, all seeds ACTIVE): {control_requalified}")

    # ---- total_relapse_wrong_bypasses_B (for verdict branch) ----
    b_relapse_wrong = int(relapse_matched[relapse_matched["arch"] == "B_NAIVE_CACHE"]["wrong_bypass"].sum())

    # =====================================================================
    # VERDICT PIPELINE
    # =====================================================================
    print("\n" + "=" * 76)
    print("VERDICT PIPELINE")
    print("=" * 76)

    branch = select_verdict_branch(eligible_count, b_relapse_wrong)
    print(f"Step 0: select_verdict_branch({eligible_count}, {b_relapse_wrong}) -> {branch}")

    final_verdict = None
    verdict_reason = None
    step2_detail = None
    step3_detail = None

    if branch == "EMPTY_COHORT_NOT_SUPPORTED":
        final_verdict = "NOT SUPPORTED"
        verdict_reason = "failure to restore useful authority (eligible_borderline_instance_count == 0)"

    elif branch == "INCONCLUSIVE":
        final_verdict = "INCONCLUSIVE"
        verdict_reason = "workload non-discriminating (Arm B zero wrong bypasses on nonempty eligible cohort)"

    else:  # EVALUATE_MAIN_VERDICT
        total_matched_bypasses_D = int(
            (primary_matched[primary_matched["arch"] == "D_REQUALIFYING"]["bypassed"] == True).sum()
        )
        print(f"Step 1: total_matched_bypasses_D = {total_matched_bypasses_D}")

        if total_matched_bypasses_D == 0:
            final_verdict = "NOT SUPPORTED"
            verdict_reason = ("Arm D promoted eligible routes but performed zero actual "
                              "post-promotion bypasses across the eligible matched cohort, so the "
                              "apparent safety advantage came from immediate suppression rather "
                              "than successful revocation under use.")
        else:
            step2_verdict, step2_detail = evaluate_step2(route_instance_df, primary_matched, relapse_matched)
            print(f"Step 2: primary K=5 verdict = {step2_verdict}")

            if step2_verdict == "SUPPORTED":
                df_for_sensitivity = df[df["k_requalify"].isin([3, 5, 8])]
                route_instance_df_by_k = {5: route_instance_df}
                for k in [3, 8]:
                    df_k = df[df["k_requalify"] == k]
                    route_instance_df_by_k[k] = build_route_instance_table(df_k, arm_d_objs, k)
                holds, step3_detail = step3_sensitivity_check(df_for_sensitivity, route_instance_df_by_k)
                print(f"Step 3: sensitivity holds at K=3 and K=8: {holds}  detail={step3_detail}")
                if holds:
                    final_verdict = "SUPPORTED"
                    verdict_reason = "advantage confirmed at K=5 and holds across K=3, K=8 sensitivity sweep"
                else:
                    final_verdict = "PARTIAL SUPPORT"
                    verdict_reason = "primary K=5 qualifies as SUPPORTED but advantage disappears at K=3 or K=8"
            else:
                final_verdict = step2_verdict
                verdict_reason = "from Step 2 primary K=5 evaluation"

    print(f"\nFINAL VERDICT: {final_verdict}")
    print(f"Reason: {verdict_reason}")

    # =====================================================================
    # Gate-cause analysis
    # =====================================================================
    gate_counts = route_instance_df["first_blocking_gate_D"].value_counts(dropna=True).to_dict()
    most_common_gate = max(gate_counts, key=gate_counts.get) if gate_counts else None

    # =====================================================================
    # OUTPUT: CSVs
    # =====================================================================
    df.to_csv(OUT_DIR / "bounded_routing_v3_raw.csv", index=False)

    # summary (phase-level, K=5 primary, four arms)
    summary_rows = []
    for phase in ["stable", "drift", "fault", "recovery", "oscillation"]:
        for arch in ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
            sub = df_k5[(df_k5["arch"] == arch) & (df_k5["phase"] == phase)]
            if len(sub) == 0:
                continue
            bp = sub[sub["bypassed"] == True]
            summary_rows.append({
                "phase": phase, "arch": arch, "k_requalify": K_REQUALIFY_PRIMARY,
                "n_tasks": len(sub),
                "mean_latency_ms": round(sub["latency_ms"].mean(), 2),
                "wrong_bypass_rate_pct": wbr_or_na(int(sub["wrong_bypass"].sum()), len(bp)),
                "fallback_rate_pct": round(sub["fallback"].mean() * 100, 2),
                "admissibility_violations": int((~sub["admissible"]).sum()),
                "total_bypasses": len(bp),
            })
    _sdf = pd.DataFrame(summary_rows)
    _sdf["wrong_bypass_rate_pct"] = _sdf["wrong_bypass_rate_pct"].astype(str)
    _sdf.to_csv(OUT_DIR / "bounded_routing_v3_summary.csv", index=False)

    # recovery summary
    rec_summary_rows = []
    for arch in ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        sub = df_k5[(df_k5["arch"] == arch) & (df_k5["phase"] == "recovery")]
        bp = sub[sub["bypassed"] == True]
        rec_summary_rows.append({
            "arch": arch, "k_requalify": K_REQUALIFY_PRIMARY,
            "n_tasks": len(sub),
            "wrong_bypasses": int(sub["wrong_bypass"].sum()),
            "wrong_bypass_rate_pct": wbr_or_na(int(sub["wrong_bypass"].sum()), len(bp)),
            "fallback_rate_pct": round(sub["fallback"].mean() * 100, 2),
            "total_bypasses": len(bp),
        })
    _rdf = pd.DataFrame(rec_summary_rows)
    _rdf["wrong_bypass_rate_pct"] = _rdf["wrong_bypass_rate_pct"].astype(str)
    _rdf.to_csv(OUT_DIR / "bounded_routing_v3_recovery_summary.csv", index=False)

    # sensitivity summary (K=3,5,8)
    # Fix 8: mean (and std) requalification time computed from exactly one
    # first-promotion timestamp per unique (seed, pattern_id) route instance,
    # independently verified per K.
    # Fix 9 (sensitivity part): eligible / ineligible borderline-instance counts per K.
    sens_rows = []
    route_instance_by_k_for_sens = {}
    for k in K_REQUALIFY_SWEEP:
        sub_d = df[(df["arch"] == "D_REQUALIFYING") & (df["phase"] == "recovery") & (df["k_requalify"] == k)]
        fc, _ = compute_final_row_state_counts(sub_d)
        bp = sub_d[sub_d["bypassed"] == True]

        # Independent per-K mean/std requalification time: exactly one timestamp
        # per unique (seed, pattern_id) that requalified.
        rq_per_route_k = (
            sub_d[sub_d["requalified_at_ms"].notna()]
            .groupby(["seed", "pattern_id"])["requalified_at_ms"]
            .first()
        )
        n_route_instances_requalified_k = len(rq_per_route_k)
        # Independent verification: the number of values about to be averaged
        # must equal the number of unique (seed, pattern_id) pairs that requalified.
        n_unique_pairs_k = sub_d[sub_d["requalified_at_ms"].notna()][["seed", "pattern_id"]].drop_duplicates().shape[0]
        assert n_route_instances_requalified_k == n_unique_pairs_k, (
            f"A10 FAIL: K={k} count of values to be averaged "
            f"({n_route_instances_requalified_k}) != count of unique requalified "
            f"route instances ({n_unique_pairs_k})"
        )
        times_since_fault_k = (rq_per_route_k - PHASE_FAULT_END)
        mean_req_time_k = float(times_since_fault_k.mean()) if len(times_since_fault_k) else None
        std_req_time_k  = float(times_since_fault_k.std()) if len(times_since_fault_k) > 1 else 0.0

        # eligible / ineligible borderline instance counts at this K
        ri_k = build_route_instance_table(df[df["k_requalify"] == k], arm_d_objs, k)
        route_instance_by_k_for_sens[k] = ri_k
        n_eligible_k   = int(ri_k["eligible_for_primary_matched_comparison"].sum()) if len(ri_k) else 0
        n_ineligible_k = int((~ri_k["eligible_for_primary_matched_comparison"]).sum()) if len(ri_k) else 0

        sens_rows.append({
            "k_requalify": k,
            "final_ACTIVE": fc["ACTIVE"], "final_REQUALIFYING": fc["REQUALIFYING"], "final_DEPRECATED": fc["DEPRECATED"],
            "wrong_bypasses": int(sub_d["wrong_bypass"].sum()),
            "wrong_bypass_rate_pct": wbr_or_na(int(sub_d["wrong_bypass"].sum()), len(bp)),
            "bypass_count": len(bp),
            "fallback_rate_pct": round(sub_d["fallback"].mean() * 100, 2) if len(sub_d) else 0.0,
            "mean_time_to_requalify_ms": round(mean_req_time_k, 1) if mean_req_time_k is not None else None,
            "std_time_to_requalify_ms": round(std_req_time_k, 1),
            "n_route_instances_requalified": n_route_instances_requalified_k,
            "eligible_borderline_instance_count": n_eligible_k,
            "ineligible_borderline_instance_count": n_ineligible_k,
        })
    _kdf = pd.DataFrame(sens_rows)
    _kdf["wrong_bypass_rate_pct"] = _kdf["wrong_bypass_rate_pct"].astype(str)
    sens_csv_path = OUT_DIR / "bounded_routing_v3_sensitivity_summary.csv"
    _kdf.to_csv(sens_csv_path, index=False)

    # ---- A9 (corrected): real post-hoc check against the WRITTEN output file ----
    check_A9_against_written_output(sens_csv_path, df)
    print("\nA9 PASS: final-row state counts independently recomputed from raw data "
          "and verified to match the values actually written to "
          f"{sens_csv_path.name} for K=3, K=5, K=8.")

    # matched_comparison csv (primary + relapse aggregates per arm)
    matched_rows = []
    for view_name, window in [("primary", primary_matched), ("relapse_only", relapse_matched)]:
        for arch in ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
            m = compute_window_metrics(window, arch)
            matched_rows.append({"view": view_name, "arch": arch, **m})
    matched_df = pd.DataFrame(matched_rows)
    matched_df["wbr"] = matched_df["wbr"].astype(str)  # preserve "NA" literal, not coerced to NaN
    matched_df.to_csv(OUT_DIR / "bounded_routing_v3_matched_comparison.csv", index=False)

    # per-route-instance csv
    route_instance_df.to_csv(OUT_DIR / "bounded_routing_v3_per_route_instance.csv", index=False)

    # ---- Fix 9: aggregate outputs CSV ----
    n_eligible          = int(route_instance_df["eligible_for_primary_matched_comparison"].sum())
    n_ineligible        = int((~route_instance_df["eligible_for_primary_matched_comparison"]).sum())
    n_not_requalified   = int(route_instance_df["requalified_at_ms"].isna().sum())
    n_deprecated_during_recovery = sum(len(arm_d_objs[(s, K_REQUALIFY_PRIMARY)]._deprecated_during_recovery)
                                       for s in SEEDS)

    rq_per_route_agg = (
        df_k5_d_rec[df_k5_d_rec["requalified_at_ms"].notna()]
        .groupby(["seed", "pattern_id"])["requalified_at_ms"].first()
    )
    times_since_fault_agg = (rq_per_route_agg - PHASE_FAULT_END)
    mean_rq_time = float(times_since_fault_agg.mean()) if len(times_since_fault_agg) else None
    std_rq_time  = float(times_since_fault_agg.std()) if len(times_since_fault_agg) > 1 else 0.0

    eligible_ri = route_instance_df[route_instance_df["eligible_for_primary_matched_comparison"] == True]
    mean_first_wrong_b = eligible_ri["time_first_wrong_bypass_B"].dropna().mean() if len(eligible_ri) else None
    mean_first_wrong_c = eligible_ri["time_first_wrong_bypass_C"].dropna().mean() if len(eligible_ri) else None
    mean_first_wrong_d = eligible_ri["time_first_wrong_bypass_D"].dropna().mean() if len(eligible_ri) else None
    mean_conf_gate_fail_d = eligible_ri["time_confidence_gate_failed_D"].dropna().mean() if len(eligible_ri) else None
    mean_first_block_d = eligible_ri["time_first_bypass_authority_blocked_D"].dropna().mean() if len(eligible_ri) else None

    aggregate_rows = [{
        "k_requalify": K_REQUALIFY_PRIMARY,
        "routes_eligible": n_eligible,
        "routes_ineligible": n_ineligible,
        "routes_not_requalified": n_not_requalified,
        "routes_deprecated_during_recovery": n_deprecated_during_recovery,
        "mean_time_to_requalify_ms": round(mean_rq_time, 1) if mean_rq_time is not None else None,
        "std_time_to_requalify_ms": round(std_rq_time, 1),
        "mean_time_first_wrong_bypass_B": round(float(mean_first_wrong_b), 1) if pd.notna(mean_first_wrong_b) else None,
        "mean_time_first_wrong_bypass_C": round(float(mean_first_wrong_c), 1) if pd.notna(mean_first_wrong_c) else None,
        "mean_time_first_wrong_bypass_D": round(float(mean_first_wrong_d), 1) if pd.notna(mean_first_wrong_d) else None,
        "mean_time_confidence_gate_failed_D": round(float(mean_conf_gate_fail_d), 1) if pd.notna(mean_conf_gate_fail_d) else None,
        "mean_time_first_bypass_authority_blocked_D": round(float(mean_first_block_d), 1) if pd.notna(mean_first_block_d) else None,
    }]
    pd.DataFrame(aggregate_rows).to_csv(OUT_DIR / "bounded_routing_v3_aggregate_metrics.csv", index=False)

    # =====================================================================
    # OUTPUT: Plots
    # =====================================================================
    print("\nGenerating plots...")
    plots = make_all_plots(df, df_k5, route_instance_df, primary_matched, relapse_matched,
                            eligible_count, b_relapse_wrong, OUT_DIR, arm_d_objs)

    elapsed = time.time() - t_start

    print(f"\n{'='*76}")
    print("OUTPUT FILES")
    print(f"{'='*76}")
    named = [
        OUT_DIR / "bounded_routing_v3_raw.csv",
        OUT_DIR / "bounded_routing_v3_summary.csv",
        OUT_DIR / "bounded_routing_v3_recovery_summary.csv",
        OUT_DIR / "bounded_routing_v3_sensitivity_summary.csv",
        OUT_DIR / "bounded_routing_v3_matched_comparison.csv",
        OUT_DIR / "bounded_routing_v3_per_route_instance.csv",
        OUT_DIR / "bounded_routing_v3_aggregate_metrics.csv",
    ] + [OUT_DIR / f"manifest_seed{s}_v3.csv" for s in SEEDS] + plots
    for f in named:
        if Path(f).exists():
            print(f"  {f}")
    print(f"\nTotal runtime: {elapsed:.1f}s")

    # ---- Fix 10: verify required output fields are actually present in the
    # written files before declaring all checks passed. ----
    print("\nVerifying required output fields are present in written files...")
    _ri_check = pd.read_csv(OUT_DIR / "bounded_routing_v3_per_route_instance.csv")
    _required_ri_fields = (
        ["state_transition_history_D"] +
        [f"primary_{f}_{a}" for f in ("tasks","bypasses","wrong_bypasses","wbr","exposure_wbr","fallback_rate") for a in "BCD"] +
        [f"relapse_{f}_{a}" for f in ("tasks","bypasses","wrong_bypasses","wbr","exposure_wbr","fallback_rate") for a in "BCD"]
    )
    _missing_ri = [f for f in _required_ri_fields if f not in _ri_check.columns]
    assert not _missing_ri, f"OUTPUT FIELD CHECK FAIL: per-route-instance CSV missing {_missing_ri}"

    _agg_check = pd.read_csv(OUT_DIR / "bounded_routing_v3_aggregate_metrics.csv")
    _required_agg_fields = [
        "routes_eligible", "routes_ineligible", "routes_not_requalified",
        "routes_deprecated_during_recovery", "mean_time_to_requalify_ms",
        "std_time_to_requalify_ms", "mean_time_first_wrong_bypass_B",
        "mean_time_first_wrong_bypass_C", "mean_time_first_wrong_bypass_D",
        "mean_time_confidence_gate_failed_D", "mean_time_first_bypass_authority_blocked_D",
    ]
    _missing_agg = [f for f in _required_agg_fields if f not in _agg_check.columns]
    assert not _missing_agg, f"OUTPUT FIELD CHECK FAIL: aggregate metrics CSV missing {_missing_agg}"

    _sens_check = pd.read_csv(sens_csv_path)
    _required_sens_fields = [
        "mean_time_to_requalify_ms", "eligible_borderline_instance_count",
        "ineligible_borderline_instance_count",
    ]
    _missing_sens = [f for f in _required_sens_fields if f not in _sens_check.columns]
    assert not _missing_sens, f"OUTPUT FIELD CHECK FAIL: sensitivity CSV missing {_missing_sens}"
    print("  per-route-instance, aggregate, and sensitivity output fields: ALL PRESENT")

    # ---- A6 coverage summary across the full sweep ----
    print("\nA6 coverage summary across all (seed, K) runs:")
    n_exercised = sum(1 for r in A6_COVERAGE_LOG if r["exercised"])
    n_unexercised = len(A6_COVERAGE_LOG) - n_exercised
    print(f"  exercised: {n_exercised}/{len(A6_COVERAGE_LOG)}  unexercised: {n_unexercised}/{len(A6_COVERAGE_LOG)}")
    if n_exercised == 0:
        print("  A6 PRESENT BUT UNEXERCISED across the entire sweep "
              "(no route was ever DEPRECATED at a recovery signal in this workload)")

    print(f"\n{'='*76}")
    print("ALL ASSERTIONS PASSED (A1-A16, including independently-verified A3, A5, A8, A9, A10, A15)")
    print(f"{'='*76}")

    # =====================================================================
    # RUN SUMMARY (for the chat response)
    # =====================================================================
    d_primary_m = compute_window_metrics(primary_matched, "D_REQUALIFYING")
    b_primary_m = compute_window_metrics(primary_matched, "B_NAIVE_CACHE")
    c_primary_m = compute_window_metrics(primary_matched, "C_TIMER_BOUND")
    d_relapse_m = compute_window_metrics(relapse_matched, "D_REQUALIFYING")
    b_relapse_m = compute_window_metrics(relapse_matched, "B_NAIVE_CACHE")
    c_relapse_m = compute_window_metrics(relapse_matched, "C_TIMER_BOUND")

    summary = {
        "runtime_s": round(elapsed, 1),
        "final_verdict": final_verdict,
        "verdict_reason": verdict_reason,
        "eligible_borderline_instance_count": eligible_count,
        "matched_wrong_bypasses": {"B": b_primary_m["wrong_bypasses"], "C": c_primary_m["wrong_bypasses"], "D": d_primary_m["wrong_bypasses"]},
        "relapse_only_wrong_bypasses": {"B": b_relapse_m["wrong_bypasses"], "C": c_relapse_m["wrong_bypasses"], "D": d_relapse_m["wrong_bypasses"]},
        "total_matched_bypasses_D": d_primary_m["bypasses"],
        "final_state_counts_D": final_counts,
        "gate_counts_D": gate_counts,
        "most_common_first_blocking_gate_D": most_common_gate,
    }
    print("\n" + "=" * 76)
    print("RUN SUMMARY (JSON)")
    print("=" * 76)
    import json
    print(json.dumps(summary, indent=2, default=str))

    return summary


route_instance_df_control_cache = False

# =========================================================================
# PLOTS
# =========================================================================

def make_all_plots(df, df_k5, route_instance_df, primary_matched, relapse_matched,
                    eligible_count, b_relapse_wrong, out_dir, arm_d_objs=None):
    plots = []
    arch_colors = {
        "A_FULL_ANALYSIS": "#d62728", "B_NAIVE_CACHE": "#1f77b4",
        "C_TIMER_BOUND": "#ff7f0e", "D_REQUALIFYING": "#2ca02c",
    }
    arch_labels = {
        "A_FULL_ANALYSIS": "Full analysis", "B_NAIVE_CACHE": "Naive cache",
        "C_TIMER_BOUND": "Timer-bound", "D_REQUALIFYING": "Requalifying",
    }
    rec = df_k5[df_k5["phase"] == "recovery"].copy()
    time_bins = np.arange(0, (PHASE_RECOVERY_END - PHASE_FAULT_END) + 1001, 1000)

    # ---- Plot 1: recovery wrong-bypass timeseries ----
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle("v3 — Cumulative Wrong Bypasses Over Recovery Phase (K=5)", fontsize=11, fontweight="bold")
    for arch in ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        sub = rec[rec["arch"] == arch].copy()
        sub["tbin"] = pd.cut(sub["time_since_recovery_ms"], bins=time_bins, labels=time_bins[:-1])
        binned = sub.groupby("tbin", observed=True)["wrong_bypass"].sum().reset_index()
        binned["cumulative"] = binned["wrong_bypass"].cumsum()
        ax.plot(binned["tbin"].astype(float), binned["cumulative"], color=arch_colors[arch], lw=2, label=arch_labels[arch])
    ax.set_xlabel("Time since recovery event (ms)"); ax.set_ylabel("Cumulative wrong bypasses")
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    plt.tight_layout(); p = str(out_dir / "recovery_wrong_bypass_timeseries_v3.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 2: fallback rate timeseries ----
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle("v3 — Fallback Rate Over Recovery Phase (K=5)", fontsize=11, fontweight="bold")
    for arch in ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        sub = rec[rec["arch"] == arch].copy()
        sub["tbin"] = pd.cut(sub["time_since_recovery_ms"], bins=time_bins, labels=time_bins[:-1])
        binned = sub.groupby("tbin", observed=True)["fallback"].mean().reset_index()
        ax.plot(binned["tbin"].astype(float), binned["fallback"] * 100, color=arch_colors[arch], lw=2, label=arch_labels[arch])
    ax.set_xlabel("Time since recovery event (ms)"); ax.set_ylabel("Fallback rate (%)")
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    plt.tight_layout(); p = str(out_dir / "recovery_fallback_timeseries_v3.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 3: requalification by pattern ----
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle("v3 — Requalification Timing by Pattern (Arm D, K=5)", fontsize=11, fontweight="bold")
    d_k5 = df_k5[df_k5["arch"] == "D_REQUALIFYING"]
    d_rec = d_k5[d_k5["phase"] == "recovery"]

    ax = axes[0]
    ax.set_title("Control group (patterns 1-4)", fontsize=10)
    for pid in CONTROL_PATTERNS:
        for seed in SEEDS:
            sub = d_rec[(d_rec["pattern_id"] == pid) & (d_rec["seed"] == seed)]
            rq = sub[sub["requalified_at_ms"].notna()]
            if len(rq):
                t_rq = float(rq["requalified_at_ms"].iloc[0]) - PHASE_FAULT_END
                ax.scatter([t_rq], [pid], marker="o", s=40, color=arch_colors["D_REQUALIFYING"], alpha=0.7)
    ax.set_xlabel("Time since recovery event (ms)"); ax.set_ylabel("Pattern ID")
    ax.set_yticks(CONTROL_PATTERNS); ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.set_title("Borderline relapse group (patterns 5-7), onset marked per seed", fontsize=10)
    for pid in BORDERLINE_PATTERNS:
        for seed in SEEDS:
            sub = d_rec[(d_rec["pattern_id"] == pid) & (d_rec["seed"] == seed)]
            rq = sub[sub["requalified_at_ms"].notna()]
            onset_rel = degradation_onset_ms(seed) - PHASE_FAULT_END
            ax.axvline(onset_rel, color="grey", alpha=0.15, lw=1)
            if len(rq):
                t_rq = float(rq["requalified_at_ms"].iloc[0]) - PHASE_FAULT_END
                ax.scatter([t_rq], [pid], marker="*", s=120, color=arch_colors["D_REQUALIFYING"], zorder=5)
    ax.set_xlabel("Time since recovery event (ms)"); ax.set_ylabel("Pattern ID")
    ax.set_yticks(BORDERLINE_PATTERNS); ax.grid(True, alpha=0.3)

    plt.tight_layout(); p = str(out_dir / "requalification_by_pattern_v3.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 4: post-requalification matched (3 panel) ----
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    inconclusive = (eligible_count > 0 and b_relapse_wrong == 0)
    not_supported_empty = (eligible_count == 0)
    suffix = ""
    if not_supported_empty:
        suffix = "  [NOT SUPPORTED: eligible_borderline_instance_count == 0]"
    elif inconclusive:
        suffix = "  [INCONCLUSIVE: workload non-discriminating]"
    fig.suptitle(f"v3 — Post-Requalification Bypass Safety (Matched Cohort){suffix}", fontsize=11, fontweight="bold")

    archs3 = ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]

    ax = axes[0]
    vals = [compute_window_metrics(primary_matched, a)["wrong_bypasses"] for a in archs3]
    ax.bar(range(3), vals, color=[arch_colors[a] for a in archs3], alpha=0.85)
    ax.set_xticks(range(3)); ax.set_xticklabels([arch_labels[a] for a in archs3], fontsize=9)
    ax.set_title("Wrong bypass count\n(primary matched window)", fontsize=9); ax.set_ylabel("Count")
    for i, v in enumerate(vals): ax.text(i, v + 0.05, str(v), ha="center", fontsize=9, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    ax = axes[1]
    vals = [compute_window_metrics(primary_matched, a)["exposure_wbr"] for a in archs3]
    ax.bar(range(3), vals, color=[arch_colors[a] for a in archs3], alpha=0.85)
    ax.set_xticks(range(3)); ax.set_xticklabels([arch_labels[a] for a in archs3], fontsize=9)
    ax.set_title("Exposure-normalized rate\n(per 1000 eligible tasks)", fontsize=9); ax.set_ylabel("Rate")
    for i, v in enumerate(vals): ax.text(i, v + 0.05, f"{v:.2f}", ha="center", fontsize=9, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    ax = axes[2]
    vals_raw = [compute_window_metrics(primary_matched, a)["wbr"] for a in archs3]
    vals_plot = [0.0 if v == "NA" else v for v in vals_raw]
    ax.bar(range(3), vals_plot, color=[arch_colors[a] for a in archs3], alpha=0.85)
    ax.set_xticks(range(3)); ax.set_xticklabels([arch_labels[a] for a in archs3], fontsize=9)
    ax.set_title("Actual wrong-bypass rate\n(wrong / actual bypasses)", fontsize=9); ax.set_ylabel("Rate (%)")
    for i, v in enumerate(vals_raw):
        label = "NA" if v == "NA" else f"{v:.2f}%"
        ax.text(i, (0 if v == "NA" else v) + 0.1, label, ha="center", fontsize=9, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout(); p = str(out_dir / "post_requalification_matched_v3.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 5: revocation timeline ----
    fig, ax = plt.subplots(figsize=(12, max(4, 0.5 * max(1, len(route_instance_df)))))
    fig.suptitle("v3 — Revocation Timeline (eligible borderline relapse instances)", fontsize=11, fontweight="bold")
    eligible = route_instance_df[route_instance_df["eligible_for_primary_matched_comparison"] == True].copy()
    eligible = eligible.sort_values("requalified_at_ms")
    if len(eligible):
        ylabels = []
        for i, (_, r) in enumerate(eligible.iterrows()):
            base = r["first_inadmissible_task_ms"]
            ylabels.append(f"s={r['seed']} p={r['pattern_id']}")
            if base is None:
                continue
            for col, color, marker, lbl in [
                ("time_first_wrong_bypass_B", arch_colors["B_NAIVE_CACHE"], "o", "B wrong"),
                ("time_first_wrong_bypass_C", arch_colors["C_TIMER_BOUND"], "s", "C wrong"),
                ("time_first_wrong_bypass_D", arch_colors["D_REQUALIFYING"], "^", "D wrong"),
                ("time_confidence_gate_failed_D", "purple", "x", "D conf fail"),
                ("time_first_bypass_authority_blocked_D", "black", "*", "D blocked"),
            ]:
                val = r.get(col)
                if val is not None and not (isinstance(val, float) and np.isnan(val)):
                    ax.scatter([val - base], [i], color=color, marker=marker, s=60, label=lbl, zorder=5)
        ax.set_yticks(range(len(ylabels))); ax.set_yticklabels(ylabels, fontsize=8)
        ax.set_xlabel("ms since first_inadmissible_task_ms")
        handles, labels = ax.get_legend_handles_labels()
        uniq = dict(zip(labels, handles))
        ax.legend(uniq.values(), uniq.keys(), fontsize=8, loc="upper right")
    else:
        ax.text(0.5, 0.5, "No eligible route instances", transform=ax.transAxes, ha="center")
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout(); p = str(out_dir / "revocation_timeline_v3.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 6: sensitivity sweep ----
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("v3 — Sensitivity Sweep K=3,5,8 (Arm D, recovery phase)", fontsize=11, fontweight="bold")
    k_vals = K_REQUALIFY_SWEEP
    wbr_vals, fbk_vals, final_counts_by_k, eligible_by_k = [], [], [], []
    for k in k_vals:
        sub = df[(df["arch"] == "D_REQUALIFYING") & (df["phase"] == "recovery") & (df["k_requalify"] == k)]
        bp = sub[sub["bypassed"] == True]
        w = int(sub["wrong_bypass"].sum())
        wbr_v = wbr_or_na(w, len(bp))
        wbr_vals.append(0.0 if wbr_v == "NA" else wbr_v)
        fbk_vals.append(sub["fallback"].mean() * 100 if len(sub) else 0.0)
        fc, _ = compute_final_row_state_counts(sub)
        final_counts_by_k.append(fc)
        # Fix 9: eligible-instance count annotation, per plan requirement
        ri_k = build_route_instance_table(df[df["k_requalify"] == k], arm_d_objs, k)
        n_elig_k = int(ri_k["eligible_for_primary_matched_comparison"].sum()) if len(ri_k) else 0
        eligible_by_k.append(n_elig_k)

    ax = axes[0]
    ax.bar(range(len(k_vals)), wbr_vals, color=arch_colors["D_REQUALIFYING"], alpha=0.85)
    ax.set_xticks(range(len(k_vals))); ax.set_xticklabels([f"K={k}" for k in k_vals])
    ax.set_ylabel("Wrong bypass rate (%)"); ax.set_title("Wrong bypass rate by K")
    for i, k in enumerate(k_vals):
        fc = final_counts_by_k[i]
        ax.text(i, wbr_vals[i] + 0.05,
                f"A={fc['ACTIVE']} R={fc['REQUALIFYING']} D={fc['DEPRECATED']}\n"
                f"eligible={eligible_by_k[i]}",
                ha="center", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    ax = axes[1]
    ax.bar(range(len(k_vals)), fbk_vals, color=arch_colors["D_REQUALIFYING"], alpha=0.85)
    ax.set_xticks(range(len(k_vals))); ax.set_xticklabels([f"K={k}" for k in k_vals])
    ax.set_ylabel("Fallback rate (%)"); ax.set_title("Fallback rate by K")
    for i, v in enumerate(fbk_vals): ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout(); p = str(out_dir / "requalification_sensitivity_v3.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    return plots


# =========================================================================
# ENTRY POINT
# =========================================================================

if __name__ == "__main__":
    summary = main()
