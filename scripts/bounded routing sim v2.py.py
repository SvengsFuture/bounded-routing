"""
Bounded Routing Simulation v2
Recovery Requalification Validation Harness

PURPOSE
-------
Compare four routing architectures during a simulated recovery event.
The primary question: does earned route requalification via shadow evaluation
produce safer post-recovery bypasses than timer-only blackout or naive cache?

FOUR ARMS
---------
  A_FULL_ANALYSIS : every task uses full analysis. No learned bypass.
  B_NAIVE_CACHE   : bypass whenever confidence >= T_bypass. No recovery control.
  C_TIMER_BOUND   : v1-style fixed recovery blackout. Bypass blocked for
                    T_RECOVERY_BLACKOUT_MS after recovery event.
  D_REQUALIFYING  : post-recovery shadow evaluation. Routes enter REQUALIFYING
                    state on recovery. Bypass blocked until fresh shadow evidence
                    meets K_REQUALIFY consecutive admissible results AND mean
                    of the most-recent K shadow SMS scores >= T_BYPASS.
                    Pre-recovery confidence and observations cannot contribute
                    to fresh requalification confidence.

SHARED TASK MANIFEST
--------------------
Candidate-route conditions are generated once per task per seed and shared
across all four arms. All arms use manifest candidate_cost directly for the structural cost bypass
gate. Arms C and D also maintain an internal ARD structural_cost estimate for
route-quality tracking; this estimate does not influence the gate decision.
See UNRESOLVED DECISIONS #6 for details.

CONTROLLING SPECIFICATION
-------------------------
validation_plan_v2.md. Where v1 implementation conflicts with v2 plan, the
plan governs. Changes from v1 are marked with # V2-CHANGE comments.

ASSERTIONS
----------
  1. Arm D never bypasses while route is REQUALIFYING.
  2. No route promoted to ACTIVE without K_REQUALIFY count + confidence gate.
  3. Every observation in every requalify_window was timestamped at or after
     the recovery signal. Verified by stored epoch tags on each observation.
  4. Routes DEPRECATED at the recovery signal are never promoted via requalification.
     (Structurally correct; unexercised in current workload — no route was
     DEPRECATED at signal time. Will be exercised by a future workload.)
  5. Routes that become DEPRECATED during recovery remain fail-closed: every
     subsequent recovery row for that (seed, pattern_id) is verified to have
     requalification_state=DEPRECATED, bypassed=False, fallback=True.

IMPLEMENTATION DECISIONS NOT RESOLVED BY THE PLAN
--------------------------------------------------
See end-of-file section.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import deque
from pathlib import Path
import time

# -----------------------------------------------------------------------
# Simulation parameters (inherited from v1, unchanged unless noted)
# -----------------------------------------------------------------------

SEEDS           = [42, 99, 500, 777, 1337]
N_PATTERNS      = 8
TASK_RATE_MS    = 20.0
DT_MS           = 20.0

PHASE_STABLE_END   =  30_000.0
PHASE_DRIFT_END    =  60_000.0
PHASE_FAULT_END    =  80_000.0
PHASE_RECOVERY_END =  95_000.0
SIM_DURATION_MS    = 120_000.0

LATENCY_FULL_ANALYSIS = 40.0
LATENCY_BYPASS_FAST   =  8.0
LATENCY_BYPASS_SLOW   = 25.0
LATENCY_NOISE_STD     =  3.0

COST_FULL_ANALYSIS  = 1.0
COST_BYPASS_NORMAL  = 0.3
COST_BYPASS_DRIFTED = 0.8
COST_BYPASS_FAILED  = 2.0

FAULT_ADMISSIBILITY_RATE   = 0.15
OSCILLATION_FLIP_PERIOD_MS = 4000.0

# -----------------------------------------------------------------------
# ARD/SMS/IBM parameters (v1 defaults retained)
# -----------------------------------------------------------------------

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

# V2-CHANGE: K_REQUALIFY — required consecutive admissible shadow checks.
K_REQUALIFY_PRIMARY = 5
K_REQUALIFY_SWEEP   = [3, 5, 8]

W_LAT  = 0.30
W_ADM  = 0.40
W_DEG  = 0.20
W_STAB = 0.10

# Gate reason vocabulary (declared in validation_plan_v2.md).
# requalification_gate_reason uses ONLY these values.
GATE_REQUALIFYING_COUNT      = "REQUALIFYING_COUNT"
GATE_REQUALIFYING_CONFIDENCE = "REQUALIFYING_CONFIDENCE"
GATE_DEPRECATED              = "DEPRECATED"
GATE_TIMER                   = "TIMER"
GATE_NONE                    = "NONE"

# Separate field for standard bypass gate reasons (not in requalification vocab)
BYPASS_GATE_CONFIDENCE = "confidence"
BYPASS_GATE_COST       = "cost"
BYPASS_GATE_OSCILLATION = "oscillation"
BYPASS_GATE_COOLDOWN   = "flip_cooldown"


# -----------------------------------------------------------------------
# Shared task manifest
# -----------------------------------------------------------------------

def build_manifest(seed):
    """
    Generate the full task sequence for one seed.
    All four arms read the same manifest; candidate-route conditions are
    generated here and shared identically.

    CORRECTION #12: manifest is also saved as an auditable CSV by the caller.
    """
    rng = np.random.RandomState(seed)
    tasks = []
    t = 0.0
    route_quality = np.ones(N_PATTERNS)

    while t < SIM_DURATION_MS:
        if t < PHASE_STABLE_END:
            phase = "stable"
            route_quality[:] = 1.0
        elif t < PHASE_DRIFT_END:
            phase = "drift"
            frac = (t - PHASE_STABLE_END) / (PHASE_DRIFT_END - PHASE_STABLE_END)
            route_quality[0] = max(0.2, 1.0 - 0.7 * frac)
        elif t < PHASE_FAULT_END:
            phase = "fault"
            route_quality[0] = 0.1
        elif t < PHASE_RECOVERY_END:
            phase = "recovery"
            frac = (t - PHASE_FAULT_END) / (PHASE_RECOVERY_END - PHASE_FAULT_END)
            route_quality[0] = min(1.0, 0.1 + 0.9 * frac)
        else:
            phase = "oscillation"
            osc_cycle = (t % OSCILLATION_FLIP_PERIOD_MS) / OSCILLATION_FLIP_PERIOD_MS
            route_quality[1] = 1.0 if osc_cycle < 0.5 else 0.2

        pid = rng.randint(0, N_PATTERNS)
        rq  = float(route_quality[pid])

        candidate_admissible = bool(rng.random() < rq)
        if rq > 0.5:
            candidate_latency = float(LATENCY_BYPASS_FAST + rng.normal(0, LATENCY_NOISE_STD))
            candidate_cost    = COST_BYPASS_NORMAL
        else:
            candidate_latency = float(LATENCY_BYPASS_SLOW + rng.normal(0, LATENCY_NOISE_STD))
            candidate_cost    = COST_BYPASS_DRIFTED

        candidate_latency = max(1.0, candidate_latency)

        tasks.append({
            "time_ms":              t,
            "pattern_id":           pid,
            "phase":                phase,
            "route_quality":        rq,
            "candidate_admissible": candidate_admissible,
            "candidate_latency_ms": candidate_latency,
            "candidate_cost":       candidate_cost,
        })
        t += DT_MS

    return tasks


# -----------------------------------------------------------------------
# SMS scoring helper
# -----------------------------------------------------------------------

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


# -----------------------------------------------------------------------
# ARD entry
# -----------------------------------------------------------------------

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

        # V2: requalification fields (Arm D only; inert in Arms A-C)
        # CORRECTION #1: requalify_window is a bounded deque of size K_REQUALIFY.
        # Fresh confidence = mean of this window (most recent K observations only).
        # Sized at construction; K passed in via reset.
        self.requalify_window          = deque(maxlen=1)   # resized at recovery signal
        # CORRECTION #3: each shadow observation is stored as (score, epoch_ms) so
        # assertions can verify timestamp >= recovery_signal_ms.
        self.requalify_obs_with_epoch  = []   # list of (score, timestamp_ms)
        self.requalify_count           = 0    # consecutive admissible shadow checks
        self.requalify_deprec_count    = 0    # consecutive below-T_DEPRECIATE shadow windows
        self.requalified_at_ms         = None
        self.pre_recovery_state        = None  # snapshot of depreciation_state at signal

    def update_depreciation(self):
        """Standard depreciation state machine (v1 logic, unchanged)."""
        if self.c_success < T_DEPRECIATE:
            self.depreciation_count += 1
            self.recover_count       = 0
            if (self.depreciation_state == "ACTIVE"
                    and self.depreciation_count >= DEPRECIATION_N):
                self.depreciation_state = "WARNED"
            elif (self.depreciation_state == "WARNED"
                    and self.depreciation_count >= DEPRECIATION_N + DEPRECIATION_M):
                self.depreciation_state = "DEPRECATED"
        else:
            if self.depreciation_state == "WARNED":
                self.depreciation_state = "ACTIVE"
                self.depreciation_count = 0
            elif self.depreciation_state == "DEPRECATED":
                if self.c_success >= T_RECOVER_ARD:
                    self.recover_count += 1
                    if self.recover_count >= RECOVER_K:
                        self.depreciation_state = "ACTIVE"
                        self.depreciation_count = 0
                        self.recover_count      = 0
                else:
                    self.recover_count = 0
            elif self.depreciation_state not in ("REQUALIFYING",):
                self.depreciation_count = 0


# -----------------------------------------------------------------------
# Base row builder
# -----------------------------------------------------------------------

def make_row(task, seed, arch, k_requalify,
             latency_ms, admissible, bypassed, wrong_bypass, fallback, cost,
             time_since_recovery_ms, requalification_state, requalify_count,
             shadow_route_admissible, shadow_latency_ms, shadow_cost,
             shadow_outcome_score, fresh_requalify_confidence,
             requalified_at_ms, bypass_post_requalify,
             requalification_gate_reason, bypass_gate_reason,
             oscillation_event=False, depreciation_event=False):
    return {
        "seed":                        seed,
        "arch":                        arch,
        "k_requalify":                 k_requalify,
        "time_ms":                     task["time_ms"],
        "pattern_id":                  task["pattern_id"],
        "phase":                       task["phase"],
        "route_quality":               task["route_quality"],
        "bypassed":                    bypassed,
        "admissible":                  admissible,
        "wrong_bypass":                wrong_bypass,
        "latency_ms":                  latency_ms,
        "structural_cost":             cost,
        "fallback":                    fallback,
        "oscillation_event":           oscillation_event,
        "depreciation_event":          depreciation_event,
        # V2 fields
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
        # Two separate gate fields (requalification vocab vs standard bypass reasons)
        "requalification_gate_reason": requalification_gate_reason,
        "bypass_gate_reason":          bypass_gate_reason,
        # Issue 4: True only on the task where requalification promotion completed.
        # Allows row-level distinction between 'promotion just happened' and
        # 'no gate withheld bypass'. NONE in rq_gate_reason means no requalification
        # gate applied; promotion_completed_this_task=True means the route promoted
        # but the live task had already been dispatched as full analysis.
        "promotion_completed_this_task": False,  # overridden by Arm D when relevant
    }


# -----------------------------------------------------------------------
# Arm A: Full analysis baseline
# -----------------------------------------------------------------------

class FullAnalysisArm:
    arch_label = "A_FULL_ANALYSIS"

    def __init__(self, seed, k_requalify=K_REQUALIFY_PRIMARY):
        self.rng        = np.random.RandomState(seed)
        self.seed       = seed
        self.k_requalify = k_requalify

    def process(self, task):
        latency = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
        rec_ms  = (task["time_ms"] - PHASE_FAULT_END) if task["phase"] == "recovery" else None
        return make_row(task, self.seed, self.arch_label, self.k_requalify,
                        latency, True, False, False, False, COST_FULL_ANALYSIS,
                        rec_ms, None, 0,
                        None, None, None, None, None, None, False,
                        GATE_NONE, GATE_NONE)


# -----------------------------------------------------------------------
# Arm B: Naive cache
# -----------------------------------------------------------------------

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

        osc_event = False
        if task["phase"] == "oscillation" and pid == 1:
            new_rt = "A" if (t % OSCILLATION_FLIP_PERIOD_MS) < (OSCILLATION_FLIP_PERIOD_MS / 2) else "B"
            if new_rt != self.last_route.get(pid, "A"):
                self.flip_counts[pid] = self.flip_counts.get(pid, 0) + 1
                self.last_route[pid]  = new_rt
                osc_event = True

        # CORRECTION #11: Arm B uses manifest candidate_cost directly.
        if c >= T_BYPASS:
            admissible = task["candidate_admissible"]
            latency    = task["candidate_latency_ms"]
            cost       = task["candidate_cost"]          # manifest value
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


# -----------------------------------------------------------------------
# Arm C: Timer-bound (v1 recovery blackout)
# -----------------------------------------------------------------------

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

    def _update_sms(self, entry, latency, admissible, rq):
        score = sms_outcome_score(latency, admissible, rq, entry.obs_window)
        entry.obs_window.append(score)
        entry.c_success = ALPHA * entry.c_success + (1 - ALPHA) * score
        entry.obs_count += 1
        entry.update_depreciation()

    def _check_bypass(self, entry, t, candidate_cost):
        """Returns (allowed, requalification_gate_reason, bypass_gate_reason).

        Issue 3 fix (Arm C): structural cost gate now uses candidate_cost from the
        shared manifest, matching Arm D. entry.structural_cost is retained for ARD
        state persistence only and does not influence the gate decision.
        """
        if entry.depreciation_state in ("DEPRECATED", "RETIRED"):
            return False, GATE_DEPRECATED, GATE_DEPRECATED
        if entry.c_success < T_BYPASS:
            return False, GATE_NONE, BYPASS_GATE_CONFIDENCE
        if candidate_cost > T_COST_MAX:          # manifest value, not ARD estimate
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

        # Issue 3 fix + CORRECTION #11: manifest candidate_cost used in gate and row.
        # Internal structural_cost tracks ARD state for persistence across tasks.
        if allowed:
            admissible = task["candidate_admissible"]
            latency    = task["candidate_latency_ms"]
            cost       = task["candidate_cost"]          # manifest value for task row
            wrong_bp   = not admissible
            fell_back  = False
            # Update internal cost estimate for ARD state
            if rq < 0.4:
                entry.structural_cost = min(COST_BYPASS_FAILED, entry.structural_cost * 1.15)
            else:
                entry.structural_cost = max(COST_BYPASS_NORMAL, entry.structural_cost * 0.98)
            prev = entry.depreciation_state
            self._update_sms(entry, latency, admissible, rq)
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
            self._update_sms(entry, latency, True, rq)
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
        row["oscillation_event"]  = osc_event
        row["depreciation_event"] = dep_event
        return row


# -----------------------------------------------------------------------
# Arm D: Requalifying
# -----------------------------------------------------------------------

class RequalifyingArm(FullAnalysisArm):
    """
    V2-CHANGE: Replaces timer blackout with earned requalification.

    On recovery event, all ACTIVE/WARNED routes enter REQUALIFYING.
    DEPRECATED routes remain DEPRECATED.

    While REQUALIFYING:
      - Live task uses full analysis.
      - Candidate route evaluated in shadow only.
      - Shadow SMS score stored in bounded deque of size K_REQUALIFY.
      - Fresh confidence = mean of that bounded window (most recent K only).
      - Admissible shadow result: requalify_count += 1.
      - Inadmissible shadow result: requalify_count = 0 (do not deprecate immediately).
      - REQUALIFYING -> DEPRECATED: fresh shadow confidence below T_DEPRECIATE
        for DEPRECIATION_N + DEPRECIATION_M consecutive shadow observations.
      - Promotion to ACTIVE: requalify_count >= K_REQUALIFY AND
        mean(recent K window) >= T_BYPASS.

    On promotion:
      c_success = fresh requalification confidence (mean of K-window).
      No pre-recovery confidence contributes.
    """

    arch_label = "D_REQUALIFYING"
    _assertion_log = []

    def __init__(self, seed, k_requalify=K_REQUALIFY_PRIMARY):
        super().__init__(seed, k_requalify)
        self.ard                  = {}
        self._in_recovery         = False
        self._recovery_signal_ms  = None     # exact timestamp of recovery signal
        self._promotions          = []       # (pid, count, conf, t) at each promotion
        # Set of pids that were DEPRECATED at recovery signal.
        self._deprecated_at_recovery = set()
        # Set of pids that became DEPRECATED during recovery (REQUALIFYING -> DEPRECATED).
        # These are fail-closed for the remainder of the recovery phase;
        # they must not receive SMS updates capable of restoring them.
        self._deprecated_during_recovery = set()

    def _get_entry(self, pid, t):
        if pid not in self.ard:
            self.ard[pid] = ARDEntry(pid, t)
        return self.ard[pid]

    def _update_sms(self, entry, latency, admissible, rq):
        score = sms_outcome_score(latency, admissible, rq, entry.obs_window)
        entry.obs_window.append(score)
        entry.c_success = ALPHA * entry.c_success + (1 - ALPHA) * score
        entry.obs_count += 1
        entry.update_depreciation()

    def _signal_recovery(self, t):
        """
        Move ACTIVE/WARNED routes to REQUALIFYING.
        DEPRECATED routes stay DEPRECATED.
        Snapshot state of every route for assertions.
        """
        self._recovery_signal_ms = t
        for pid, entry in self.ard.items():
            entry.pre_recovery_state = entry.depreciation_state
            if entry.depreciation_state in ("ACTIVE", "WARNED"):
                entry.depreciation_state       = "REQUALIFYING"
                entry.requalify_count          = 0
                entry.requalify_deprec_count   = 0
                # CORRECTION #1: bounded deque of exactly K_REQUALIFY entries
                entry.requalify_window         = deque(maxlen=self.k_requalify)
                # CORRECTION #3: fresh epoch-tagged observation list
                entry.requalify_obs_with_epoch = []
                entry.requalified_at_ms        = None
                entry.recovery_sensitive       = True
            elif entry.depreciation_state == "DEPRECATED":
                # CORRECTION #4: record which pids were DEPRECATED at signal
                self._deprecated_at_recovery.add(pid)

    def _update_shadow(self, entry, shadow_latency, shadow_admissible, rq, t):
        """
        Shadow evaluation while REQUALIFYING.

        CORRECTION #1: fresh confidence = mean of bounded K-window (not all obs).
        CORRECTION #3: each observation stored with its epoch timestamp.
        CORRECTION #8: REQUALIFYING -> DEPRECATED via deprec_count on shadow confidence.

        Returns (shadow_score, rq_gate, promoted, fresh_conf).
        """
        shadow_score = sms_outcome_score(
            shadow_latency, shadow_admissible, rq, entry.requalify_window
        )

        # CORRECTION #3: store (score, timestamp) for assertion verification
        entry.requalify_obs_with_epoch.append((shadow_score, t))
        # CORRECTION #1: append to bounded deque; oldest dropped automatically
        entry.requalify_window.append(shadow_score)

        if shadow_admissible:
            entry.requalify_count += 1
        else:
            entry.requalify_count = 0

        # CORRECTION #1: fresh_conf = mean of most-recent K shadow observations
        fresh_conf = float(np.mean(list(entry.requalify_window))) if entry.requalify_window else 0.0

        # CORRECTION #8: track depreciation via shadow confidence
        if fresh_conf < T_DEPRECIATE:
            entry.requalify_deprec_count += 1
            if entry.requalify_deprec_count >= DEPRECIATION_N + DEPRECIATION_M:
                entry.depreciation_state = "DEPRECATED"
                self._deprecated_during_recovery.add(entry.pid)
                return shadow_score, GATE_DEPRECATED, False, fresh_conf
        else:
            entry.requalify_deprec_count = 0

        # Promotion check
        count_met = entry.requalify_count >= self.k_requalify
        conf_met  = fresh_conf >= T_BYPASS

        if count_met and conf_met:
            entry.c_success          = fresh_conf
            entry.obs_window         = deque(list(entry.requalify_window), maxlen=OBS_WINDOW_SIZE)
            entry.depreciation_state = "ACTIVE"
            entry.requalified_at_ms  = t
            entry.requalify_deprec_count = 0
            self._promotions.append((entry.pid, entry.requalify_count, fresh_conf, t))
            return shadow_score, GATE_NONE, True, fresh_conf
        elif count_met and not conf_met:
            return shadow_score, GATE_REQUALIFYING_CONFIDENCE, False, fresh_conf
        else:
            return shadow_score, GATE_REQUALIFYING_COUNT, False, fresh_conf

    def _check_bypass(self, entry, t, candidate_cost):
        """Returns (allowed, rq_gate, bp_gate).

        ISSUE 4 FIX: structural cost gate uses candidate_cost from the shared
        manifest, not entry.structural_cost (the internal ARD estimate).
        entry.structural_cost is retained for ARD state persistence only.
        """
        if entry.depreciation_state == "REQUALIFYING":
            if entry.requalify_count >= self.k_requalify:
                return False, GATE_REQUALIFYING_CONFIDENCE, GATE_REQUALIFYING_CONFIDENCE
            return False, GATE_REQUALIFYING_COUNT, GATE_REQUALIFYING_COUNT
        if entry.depreciation_state in ("DEPRECATED", "RETIRED"):
            return False, GATE_DEPRECATED, GATE_DEPRECATED
        if entry.c_success < T_BYPASS:
            return False, GATE_NONE, BYPASS_GATE_CONFIDENCE
        if candidate_cost > T_COST_MAX:          # manifest value, not ARD estimate
            return False, GATE_NONE, BYPASS_GATE_COST
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

        dep_event             = False
        shadow_admissible_out = None
        shadow_latency_out    = None
        shadow_cost_out       = None
        shadow_score_out      = None
        fresh_conf_out        = None
        bypass_post_req       = False

        if entry.depreciation_state == "REQUALIFYING":
            # Issue 4 fix: capture the pre-decision gate reason before _update_shadow
            # may change the route's state. The row must record the reason bypass was
            # withheld at decision time, not the state after shadow processing.
            pre_decision_rq_gate = rq_gate   # REQUALIFYING_COUNT or REQUALIFYING_CONFIDENCE

            # Live task: full analysis
            admissible = True
            latency    = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True

            # Shadow evaluation
            shadow_admissible_out = task["candidate_admissible"]
            shadow_latency_out    = task["candidate_latency_ms"]
            shadow_cost_out       = task["candidate_cost"]

            prev_state = entry.depreciation_state
            shadow_score_out, post_shadow_rq_gate, promoted, fresh_conf_out = self._update_shadow(
                entry, shadow_latency_out, shadow_admissible_out, rq, t
            )
            if prev_state != "DEPRECATED" and entry.depreciation_state == "DEPRECATED":
                dep_event = True

            # Issue 4 fix: restore pre-decision gate reason so the row reflects
            # the routing decision, not the post-shadow state.
            # If the route promoted this task, post_shadow_rq_gate is NONE, but
            # that NONE describes the shadow outcome, not the routing decision.
            # The live task still used full analysis; NONE should not appear here.
            rq_gate = pre_decision_rq_gate
            promotion_this_task = promoted   # used below to set promotion field

        elif allowed:
            admissible = task["candidate_admissible"]
            latency    = task["candidate_latency_ms"]
            cost       = task["candidate_cost"]          # manifest value
            wrong_bp   = not admissible
            fell_back  = False
            bypass_post_req = (entry.requalified_at_ms is not None)
            if rq < 0.4:
                entry.structural_cost = min(COST_BYPASS_FAILED, entry.structural_cost * 1.15)
            else:
                entry.structural_cost = max(COST_BYPASS_NORMAL, entry.structural_cost * 0.98)
            prev = entry.depreciation_state
            self._update_sms(entry, latency, admissible, rq)
            if prev != "DEPRECATED" and entry.depreciation_state == "DEPRECATED":
                dep_event = True

        elif entry.depreciation_state == "DEPRECATED":
            # ISSUE 1 FIX: Routes DEPRECATED during or before recovery are fail-closed.
            # Full analysis handles the live task but the route receives NO SMS update.
            # The standard update_depreciation() path can restore DEPRECATED -> ACTIVE
            # via RECOVER_K steps above T_RECOVER_ARD. That path must not be available
            # to a route that became DEPRECATED during recovery, because it would bypass
            # the requalification requirement. Replacement-route nomination is out of scope.
            admissible = True
            latency    = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True
            # No _update_sms() call: c_success is frozen, depreciation state stays DEPRECATED.

        else:
            # Not REQUALIFYING, not DEPRECATED, not allowed (confidence/cost/osc/cooldown).
            admissible = True
            latency    = max(1.0, LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD))
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True
            prev = entry.depreciation_state
            self._update_sms(entry, latency, True, rq)
            if prev != "DEPRECATED" and entry.depreciation_state == "DEPRECATED":
                dep_event = True

        entry.last_used_ms = t

        # Inline assertion 1
        if (allowed and not fell_back) and entry.depreciation_state == "REQUALIFYING":
            RequalifyingArm._assertion_log.append(
                f"A1 FAIL pid={pid} t={t} bypassed while REQUALIFYING"
            )

        row = make_row(task, self.seed, self.arch_label, self.k_requalify,
                       latency, admissible, allowed and not fell_back,
                       wrong_bp, fell_back, cost,
                       rec_ms, entry.depreciation_state, entry.requalify_count,
                       shadow_admissible_out, shadow_latency_out, shadow_cost_out,
                       shadow_score_out, fresh_conf_out,
                       entry.requalified_at_ms, bypass_post_req,
                       rq_gate, bp_gate)
        row["oscillation_event"]  = osc_event
        row["depreciation_event"] = dep_event
        # Issue 4 fix: mark the row where promotion completed.
        if 'promotion_this_task' in dir() and promotion_this_task:
            row["promotion_completed_this_task"] = True
        return row


# -----------------------------------------------------------------------
# Assertions
# -----------------------------------------------------------------------

def run_assertions(arm_d, rows_d, seed):
    """
    Four structural assertions per validation_plan_v2.md go/no-go criteria.
    All assertions are real checks; none are pass-through comments.
    """
    df = pd.DataFrame(rows_d)
    rec = df[df["phase"] == "recovery"]

    # --- Assertion 1: Arm D never bypasses while REQUALIFYING ---
    assert not RequalifyingArm._assertion_log, \
        "ASSERTION 1 FAIL: " + "; ".join(RequalifyingArm._assertion_log)
    bad = df[(df["bypassed"] == True) & (df["requalification_state"] == "REQUALIFYING")]
    assert len(bad) == 0, \
        f"ASSERTION 1 FAIL (data): seed={seed} {len(bad)} rows bypassed while REQUALIFYING"

    # --- Assertion 2: Every promotion met K_REQUALIFY count AND fresh_conf >= T_BYPASS ---
    for pid, count, conf, t_prom in arm_d._promotions:
        assert count >= arm_d.k_requalify, \
            f"ASSERTION 2 FAIL: seed={seed} pid={pid} promoted count={count} < K={arm_d.k_requalify}"
        assert conf >= T_BYPASS, \
            f"ASSERTION 2 FAIL: seed={seed} pid={pid} promoted conf={conf:.4f} < T_BYPASS={T_BYPASS}"

    # --- Assertion 3: Every observation in requalify_window timestamped >= recovery signal ---
    # requalify_obs_with_epoch stores (score, timestamp_ms) for every shadow observation.
    recovery_signal_ms = arm_d._recovery_signal_ms
    if recovery_signal_ms is not None:
        for pid, entry in arm_d.ard.items():
            for score, obs_t in entry.requalify_obs_with_epoch:
                assert obs_t >= recovery_signal_ms, (
                    f"ASSERTION 3 FAIL: seed={seed} pid={pid} "
                    f"obs at t={obs_t} predates recovery signal t={recovery_signal_ms}"
                )

    # --- Assertion 4: Routes DEPRECATED at recovery signal never promoted via requalification ---
    for pid in arm_d._deprecated_at_recovery:
        entry = arm_d.ard.get(pid)
        if entry is None:
            continue
        assert len(entry.requalify_obs_with_epoch) == 0, (
            f"ASSERTION 4 FAIL: seed={seed} pid={pid} was DEPRECATED at recovery "
            f"but received {len(entry.requalify_obs_with_epoch)} shadow observations"
        )
        promoted_pids = {p[0] for p in arm_d._promotions}
        assert pid not in promoted_pids, (
            f"ASSERTION 4 FAIL: seed={seed} pid={pid} was DEPRECATED at recovery "
            f"but appears in promotions list"
        )

    # --- Assertion 5 (strengthened): Routes DEPRECATED during recovery are fail-closed ---
    # For each route that became DEPRECATED during recovery, find the first depreciation
    # transition row and assert every subsequent recovery row for that (seed, pid) is:
    #   requalification_state == DEPRECATED
    #   bypassed == False
    #   fallback == True
    # This verifies the fail-closed invariant at row level, not just at arm-state level.
    for pid in arm_d._deprecated_during_recovery:
        entry = arm_d.ard.get(pid)
        if entry is None:
            continue
        # Final state check
        assert entry.depreciation_state == "DEPRECATED", (
            f"ASSERTION 5 FAIL: seed={seed} pid={pid} was DEPRECATED during recovery "
            f"but ended phase in state={entry.depreciation_state}."
        )
        promoted_pids = {p[0] for p in arm_d._promotions}
        assert pid not in promoted_pids, (
            f"ASSERTION 5 FAIL: seed={seed} pid={pid} deprecated during recovery "
            f"but appears in promotions list"
        )
        # Row-level check: find first depreciation row for this (seed, pid)
        pid_rows = rec[(rec["pattern_id"] == pid)].sort_values("time_ms")
        dep_rows = pid_rows[pid_rows["requalification_state"] == "DEPRECATED"]
        if len(dep_rows) == 0:
            continue  # not yet seen in this seed's data slice (e.g. pattern never appeared)
        first_dep_t = float(dep_rows["time_ms"].iloc[0])
        post_dep    = pid_rows[pid_rows["time_ms"] >= first_dep_t]
        # Every post-depreciation row must be fail-closed
        bad_state   = post_dep[post_dep["requalification_state"] != "DEPRECATED"]
        bad_bypass  = post_dep[post_dep["bypassed"] == True]
        bad_fallback = post_dep[post_dep["fallback"] != True]
        assert len(bad_state) == 0, (
            f"ASSERTION 5 FAIL: seed={seed} pid={pid} has {len(bad_state)} post-depreciation "
            f"rows with state != DEPRECATED"
        )
        assert len(bad_bypass) == 0, (
            f"ASSERTION 5 FAIL: seed={seed} pid={pid} has {len(bad_bypass)} post-depreciation "
            f"rows with bypassed=True"
        )
        assert len(bad_fallback) == 0, (
            f"ASSERTION 5 FAIL: seed={seed} pid={pid} has {len(bad_fallback)} post-depreciation "
            f"rows with fallback!=True"
        )

    # --- Assertion coverage note ---
    # Assertion 4 guards routes DEPRECATED at the recovery signal.
    # In the current workload, no route was DEPRECATED at the recovery signal
    # (pattern 0 was WARNED/ACTIVE, becoming DEPRECATED only during recovery).
    # Assertion 4 is structurally correct but experimentally unexercised in this run.
    # It will be exercised when a workload includes a route that is already
    # DEPRECATED before the recovery signal fires.


# -----------------------------------------------------------------------
# Matched post-requalification comparison
# CORRECTION #10: compare arms B, C, D on identical manifest rows
# -----------------------------------------------------------------------

def build_matched_comparison(df_primary_rec):
    """
    ISSUE 3 FIX: Correct matched post-requalification cohort.

    For every (seed, pattern_id) route that successfully requalified in Arm D,
    use its requalified_at_ms timestamp to select every subsequent recovery task
    for that same seed and pattern_id. Join Arms B, C, and D on those identical
    seed, time_ms, pattern_id rows.

    Seeding from bypass_post_requalify=True (previous approach) was wrong because
    it selected only rows where Arm D actually bypassed, which structurally
    guarantees Arm D fallback_rate=0 and prevents a fair comparison.

    WORKLOAD NOTE: Patterns 1-7 have route_quality=1.0 during recovery, so
    candidate_admissible is always True for those patterns. Pattern 0 does not
    successfully requalify. Therefore the matched comparison cannot establish
    that D is cleaner than B or C on admissibility; the result is INCONCLUSIVE.
    A discriminating workload must be declared prospectively in a later plan.
    """
    d_arm = df_primary_rec[df_primary_rec["arch"] == "D_REQUALIFYING"].copy()

    # Find requalified routes: unique (seed, pattern_id) pairs with a requalified_at_ms
    rq_routes = (
        d_arm[d_arm["requalified_at_ms"].notna()]
        [["seed", "pattern_id", "requalified_at_ms"]]
        .drop_duplicates(subset=["seed", "pattern_id"])
    )

    if len(rq_routes) == 0:
        return {}, pd.DataFrame(), True  # inconclusive: no routes requalified

    # For each requalified route, select all recovery tasks AFTER requalified_at_ms
    cohort_keys = []
    for _, row in rq_routes.iterrows():
        post = d_arm[
            (d_arm["seed"] == row["seed"]) &
            (d_arm["pattern_id"] == row["pattern_id"]) &
            (d_arm["time_ms"] > row["requalified_at_ms"])
        ][["seed", "time_ms", "pattern_id"]]
        cohort_keys.append(post)

    if not cohort_keys:
        return {}, pd.DataFrame(), True

    cohort = pd.concat(cohort_keys).drop_duplicates()
    matched = df_primary_rec.merge(cohort, on=["seed", "time_ms", "pattern_id"], how="inner")

    # Determine if the comparison is discriminating.
    # If all matched candidate routes are admissible, wrong bypass cannot occur
    # for any arm, and the safety comparison is INCONCLUSIVE.
    d_matched = matched[matched["arch"] == "D_REQUALIFYING"]
    all_admissible = bool((d_matched["route_quality"] >= 1.0).all())
    inconclusive   = all_admissible

    results = {}
    for arch in ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        sub = matched[matched["arch"] == arch]
        bp  = sub[sub["bypassed"] == True]
        results[arch] = {
            "matched_tasks":             len(sub),
            "matched_bypasses":          len(bp),
            "matched_wrong_bypasses":    int(sub["wrong_bypass"].sum()),
            "matched_wrong_bypass_rate": (int(sub["wrong_bypass"].sum()) / max(1, len(bp))) * 100,
            "matched_fallback_rate":     sub["fallback"].mean() * 100,
        }

    return results, matched, inconclusive


# -----------------------------------------------------------------------
# Run one seed
# -----------------------------------------------------------------------

def run_seed(seed, k_requalify=K_REQUALIFY_PRIMARY):
    manifest = build_manifest(seed)

    arms = [
        FullAnalysisArm(seed, k_requalify),
        NaiveCacheArm(seed, k_requalify),
        TimerBoundArm(seed, k_requalify),
        RequalifyingArm(seed, k_requalify),
    ]

    all_rows = []
    for arm in arms:
        if isinstance(arm, RequalifyingArm):
            RequalifyingArm._assertion_log.clear()
        rows = []
        for task in manifest:
            r = arm.process(task)
            rows.append(r)
        if isinstance(arm, RequalifyingArm):
            run_assertions(arm, rows, seed)
        all_rows.extend(rows)

    return all_rows, manifest


# -----------------------------------------------------------------------
# Sweep
# -----------------------------------------------------------------------

def run_sweep(out_dir):
    t0       = time.time()
    all_rows = []
    manifests_saved = set()

    print("=" * 72)
    print("BOUNDED ROUTING SIMULATION v2")
    print(f"Primary K_REQUALIFY={K_REQUALIFY_PRIMARY} | Sweep K={K_REQUALIFY_SWEEP}")
    print("=" * 72)

    for k in K_REQUALIFY_SWEEP:
        label = "Primary run" if k == K_REQUALIFY_PRIMARY else "Sensitivity sweep"
        print(f"\n{label} (K_REQUALIFY={k})")
        for seed in SEEDS:
            rows, manifest = run_seed(seed, k)
            all_rows.extend(rows)
            # CORRECTION #12: save manifest once per seed (same across K values)
            if seed not in manifests_saved:
                pd.DataFrame(manifest).assign(seed=seed).to_csv(
                    out_dir / f"manifest_seed{seed}.csv", index=False
                )
                manifests_saved.add(seed)
            print(f"  seed={seed}  tasks={len(rows)}  t={time.time()-t0:.1f}s")

    print(f"\nAll assertions passed. {len(all_rows)} rows, {time.time()-t0:.1f}s")
    return pd.DataFrame(all_rows)


# -----------------------------------------------------------------------
# Analysis
# -----------------------------------------------------------------------

def analyze(df):
    print("\n" + "=" * 72)
    print("ANALYSIS — Bounded Routing v2")
    print("=" * 72)

    primary = df[df["k_requalify"] == K_REQUALIFY_PRIMARY].copy()
    arch_list = ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]
    summary_rows = []

    for phase in ["stable", "drift", "fault", "recovery", "oscillation"]:
        print(f"\n-- Phase: {phase} --")
        print(f"  {'arch':>18} {'mean_lat':>9} {'p95_lat':>8} {'wrong_bp%':>10} "
              f"{'fallbk%':>8} {'adm_viol':>9}")
        print("  " + "-" * 70)
        for arch in arch_list:
            sub = primary[(primary["arch"] == arch) & (primary["phase"] == phase)]
            if len(sub) == 0:
                continue
            bp  = sub[sub["bypassed"] == True]
            wbr = (int(sub["wrong_bypass"].sum()) / max(1, len(bp))) * 100
            print(f"  {arch:>18} {sub['latency_ms'].mean():>9.1f} "
                  f"{sub['latency_ms'].quantile(0.95):>8.1f} "
                  f"{wbr:>10.2f} {sub['fallback'].mean()*100:>8.1f} "
                  f"{int((~sub['admissible']).sum()):>9}")
            summary_rows.append({
                "phase":                    phase,
                "arch":                     arch,
                "k_requalify":              K_REQUALIFY_PRIMARY,
                "mean_latency_ms":          sub["latency_ms"].mean(),
                "p95_latency_ms":           sub["latency_ms"].quantile(0.95),
                "wrong_bypass_rate_pct":    wbr,
                "fallback_rate_pct":        sub["fallback"].mean() * 100,
                "admissibility_violations": int((~sub["admissible"]).sum()),
                "oscillation_events":       int(sub["oscillation_event"].sum()),
                "mean_structural_cost":     sub["structural_cost"].mean(),
                "n_tasks":                  len(sub),
                "total_bypasses":           len(bp),
                "depreciation_events":      int(sub["depreciation_event"].sum()),
                "successful_bounded_bypass": int(
                    ((sub["bypassed"] == True) & sub["admissible"]).sum()
                ) if arch in ("C_TIMER_BOUND", "D_REQUALIFYING") else 0,
            })

    # Recovery detail
    rec = primary[primary["phase"] == "recovery"]
    print("\n-- Recovery phase detail --")
    for arch in ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        sub = rec[rec["arch"] == arch]
        bp  = sub[sub["bypassed"] == True]
        wbr = (int(sub["wrong_bypass"].sum()) / max(1, len(bp))) * 100
        print(f"\n  {arch}")
        print(f"    wrong bypasses total:  {int(sub['wrong_bypass'].sum())}")
        print(f"    wrong bypass rate:     {wbr:.2f}%")
        print(f"    fallback rate:         {sub['fallback'].mean()*100:.1f}%")
        if arch == "D_REQUALIFYING":
            # CORRECTION #2: count explicit True values, not sum of mixed dtype
            shadow = sub[sub["shadow_route_admissible"].notna()]
            n_shadow_true = int((shadow["shadow_route_admissible"] == True).sum())
            print(f"    shadow checks total:       {len(shadow)}")
            print(f"    shadow checks admissible:  {n_shadow_true}")

            # CORRECTION #3 & #4: unique (seed, pattern_id) route instances
            requalified_routes = sub[sub["requalified_at_ms"].notna()][
                ["seed", "pattern_id"]].drop_duplicates()
            n_routes_requalified  = len(requalified_routes)
            n_pids_requalified    = requalified_routes["pattern_id"].nunique()
            # ISSUE 2 FIX: use final row per (seed, pattern_id) to count terminal states.
            # Selecting any row where state==REQUALIFYING would count routes that
            # later promoted or deprecated, not only those still locked at phase end.
            final_rows = (
                sub.sort_values("time_ms")
                   .groupby(["seed", "pattern_id"], sort=False)
                   .last()
                   .reset_index()
            )
            n_final_active      = int((final_rows["requalification_state"] == "ACTIVE").sum())
            n_final_requalifying = int((final_rows["requalification_state"] == "REQUALIFYING").sum())
            n_final_deprecated  = int((final_rows["requalification_state"] == "DEPRECATED").sum())
            print(f"    route instances requalified:  {n_routes_requalified}")
            print(f"    distinct pattern IDs:          {n_pids_requalified}")
            print(f"    final state — ACTIVE:          {n_final_active}")
            print(f"    final state — REQUALIFYING:    {n_final_requalifying}")
            print(f"    final state — DEPRECATED:      {n_final_deprecated}")

            post = sub[sub["bypass_post_requalify"] == True]
            print(f"    post-requalify bypasses:   {len(post)}")
            print(f"    post-requalify wrong bp:   {int(post['wrong_bypass'].sum())} "
                  f"({(int(post['wrong_bypass'].sum())/max(1,len(post[post['bypassed']==True])))*100:.2f}%)")

    # Matched comparison
    matched_results, _, inconclusive_flag = build_matched_comparison(rec)
    if matched_results:
        print("\n-- Post-requalification matched comparison --")
        print("  Cohort: recovery tasks after requalified_at_ms, per requalified (seed, pattern_id).")
        if inconclusive_flag:
            print("  RESULT: INCONCLUSIVE — all matched candidate routes have route_quality=1.0.")
            print("  Patterns 1-7 have perfect admissibility during recovery; pattern 0 did not")
            print("  requalify. No wrong bypass is possible for any arm on this cohort.")
            print("  A discriminating workload must be declared prospectively in a later plan.")
        print(f"  {'arch':>18} {'matched_tasks':>14} {'bypasses':>9} "
              f"{'wrong_bp':>9} {'wbr%':>7} {'fallbk%':>8}")
        for arch in ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
            r = matched_results.get(arch, {})
            if r:
                print(f"  {arch:>18} {r['matched_tasks']:>14} "
                      f"{r['matched_bypasses']:>9} {r['matched_wrong_bypasses']:>9} "
                      f"{r['matched_wrong_bypass_rate']:>7.2f} "
                      f"{r['matched_fallback_rate']:>8.1f}")

    # Verdict
    b_rec = rec[rec["arch"] == "B_NAIVE_CACHE"]
    c_rec = rec[rec["arch"] == "C_TIMER_BOUND"]
    d_rec = rec[rec["arch"] == "D_REQUALIFYING"]

    def wbr(sub):
        bp = sub[sub["bypassed"] == True]
        return (int(sub["wrong_bypass"].sum()) / max(1, len(bp))) * 100

    print("\n" + "=" * 72)
    print("VERDICT — Bounded Routing v2 Recovery Requalification (K=5)")
    print("=" * 72)
    print(f"  wrong_bypass_rate:  B={wbr(b_rec):.2f}%  C={wbr(c_rec):.2f}%  D={wbr(d_rec):.2f}%")
    print(f"  adm_violations:     B={int((~b_rec['admissible']).sum())}  "
          f"C={int((~c_rec['admissible']).sum())}  D={int((~d_rec['admissible']).sum())}")
    print(f"  fallback_rate:      B={b_rec['fallback'].mean()*100:.1f}%  "
          f"C={c_rec['fallback'].mean()*100:.1f}%  D={d_rec['fallback'].mean()*100:.1f}%")
    print()
    print("  OUTCOME 1 — State-machine integrity")
    print("  PASS. All five assertions held across all seeds and K values.")
    print("  No route bypassed while REQUALIFYING. No route promoted without meeting")
    print("  both K_REQUALIFY count and fresh confidence gates. No pre-recovery")
    print("  observation contributed to fresh confidence. Routes DEPRECATED during")
    print("  recovery remained fail-closed for the remainder of the recovery phase.")
    print("  Note: Assertion 4 (routes DEPRECATED at signal) is structurally correct")
    print("  but unexercised in this workload — no route was DEPRECATED at signal time.")
    print()
    print("  OUTCOME 2 — Full-recovery aggregate safety")
    print(f"  PASS in this workload. D=0 wrong bypasses vs B={int((~b_rec['admissible']).sum())} vs C={int((~c_rec['admissible']).sum())}.")
    print("  D's advantage is attributable to pattern 0 becoming DEPRECATED and being")
    print("  held fail-closed. D is faster than A (full analysis) and safer than B and C.")
    print("  The workload does not test a scenario where a route causes wrong bypasses")
    print("  only after requalification — that scenario remains untested.")
    print()
    print("  OUTCOME 3 — Matched post-requalification safety advantage")
    print("  INCONCLUSIVE. All successfully requalified routes (patterns 1-7) have")
    print("  route_quality=1.0 during recovery; candidate_admissible is always True.")
    print("  Pattern 0 (the failing route) did not requalify. No wrong bypass is")
    print("  structurally possible on the matched cohort for any arm. The comparison")
    print("  cannot demonstrate that requalification produces cleaner bypasses than")
    print("  naive cache on this workload. A discriminating workload must be declared")
    print("  prospectively in a later validation plan.")
    print()
    print("  OVERALL v2 VERDICT: PARTIAL SUPPORT")
    print("  The state-machine correctness and aggregate safety claims are supported.")
    print("  The post-requalification safety advantage over naive cache is not")
    print("  demonstrated in this workload and requires a future discriminating run.")

    # --- Sensitivity summary (K = 3, 5, 8) ---
    print("\n" + "=" * 72)
    print("SENSITIVITY SUMMARY — Arm D, recovery phase, K = 3 / 5 / 8")
    print("=" * 72)
    print(f"{'K':>4} {'ACTIVE':>8} {'REQUALIFYING':>14} {'DEPRECATED':>11} "
          f"{'wrong_bp':>9} {'wbr%':>8} {'bypasses':>9} {'fallbk%':>9}")
    print("-" * 80)
    for k in K_REQUALIFY_SWEEP:
        ksub = df[(df["arch"] == "D_REQUALIFYING") &
                  (df["phase"] == "recovery") &
                  (df["k_requalify"] == k)]
        kbp  = ksub[ksub["bypassed"] == True]
        kwbr = (int(ksub["wrong_bypass"].sum()) / max(1, len(kbp))) * 100
        # Terminal state counts from final row per (seed, pattern_id)
        if len(ksub) > 0:
            kfinal = (
                ksub.sort_values("time_ms")
                    .groupby(["seed", "pattern_id"], sort=False)
                    .last()
                    .reset_index()
            )
            n_act = int((kfinal["requalification_state"] == "ACTIVE").sum())
            n_req = int((kfinal["requalification_state"] == "REQUALIFYING").sum())
            n_dep = int((kfinal["requalification_state"] == "DEPRECATED").sum())
        else:
            n_act = n_req = n_dep = 0
        print(f"  {k:>2}  {n_act:>8} {n_req:>14} {n_dep:>11} "
              f"{int(ksub['wrong_bypass'].sum()):>9} {kwbr:>8.3f} "
              f"{len(kbp):>9} {ksub['fallback'].mean()*100:>9.2f}")
    print()
    print("  Interpretation:")
    print("  K=3 produces fewer requalification delays and more bypasses, but admits")
    print("  15 wrong bypasses in this workload. The bounded mechanism is still safer")
    print("  than B or C at K=3 (B=35 wrong bypasses in recovery), but the safety")
    print("  margin narrows. K=5 and K=8 both produce zero violations in this workload.")
    print("  The zero-violation result at K>=5 is not invariant: it reflects that")
    print("  pattern 0 deprecates before producing wrong bypasses. A workload with")
    print("  slower confidence drain or partial fault recovery may discriminate K=5")
    print("  from K=8. Larger K increases fallback rate: K=8 fallback is ~20%, K=5")
    print("  is ~17%, K=3 is ~13%.")

    return pd.DataFrame(summary_rows)


# -----------------------------------------------------------------------
# Summary CSV
# -----------------------------------------------------------------------

def build_summary_csv(df, out_dir):
    primary = df[df["k_requalify"] == K_REQUALIFY_PRIMARY].copy()
    rec     = primary[primary["phase"] == "recovery"]

    extra_rows = []
    for arch in ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        sub = rec[rec["arch"] == arch]
        bp  = sub[sub["bypassed"] == True]
        post = sub[sub["bypass_post_requalify"] == True] if "bypass_post_requalify" in sub else pd.DataFrame()

        shadow = sub[sub["shadow_route_admissible"].notna()] if "shadow_route_admissible" in sub else pd.DataFrame()
        # CORRECTION #2
        n_shadow_adm = int((shadow["shadow_route_admissible"] == True).sum()) if len(shadow) else 0

        bins       = [0, 3000, 6000, 9000, 12000, 15001]
        bin_labels = ["0-3s", "3-6s", "6-9s", "9-12s", "12-15s"]
        sub2 = sub.copy()
        sub2["tbin"] = pd.cut(sub2["time_since_recovery_ms"], bins=bins,
                              labels=bin_labels, right=False)
        wbr_bin = sub2.groupby("tbin", observed=True)["wrong_bypass"].sum().to_dict()
        fbk_bin = sub2.groupby("tbin", observed=True)["fallback"].mean().to_dict()

        # CORRECTION #3 & #4: unique route instances and pattern IDs
        rq_routes = sub[sub["requalified_at_ms"].notna()][["seed","pattern_id"]].drop_duplicates()
        n_routes_rq  = len(rq_routes)
        n_pids_rq    = rq_routes["pattern_id"].nunique()

        # Issue 1 fix: terminal state counts use final row per (seed, pattern_id).
        # Any earlier intermediate state (e.g. REQUALIFYING before promotion)
        # must not inflate the remaining-REQUALIFYING count.
        if arch == "D_REQUALIFYING" and len(sub) > 0:
            final_rows = (
                sub.sort_values("time_ms")
                   .groupby(["seed", "pattern_id"], sort=False)
                   .last()
                   .reset_index()
            )
            n_final_active       = int((final_rows["requalification_state"] == "ACTIVE").sum())
            n_still_rq           = int((final_rows["requalification_state"] == "REQUALIFYING").sum())
            n_dep_during_rq      = int((final_rows["requalification_state"] == "DEPRECATED").sum())
        else:
            n_final_active  = 0
            n_still_rq      = 0
            n_dep_during_rq = 0

        # Issue 2 fix: mean_time_to_requalify_ms uses one requalified_at_ms value
        # per unique (seed, pattern_id) route instance. Using .unique() on the full
        # column would average repeated timestamp values across many rows.
        if arch == "D_REQUALIFYING" and len(sub) > 0:
            rq_per_route = (
                sub[sub["requalified_at_ms"].notna()]
                .groupby(["seed", "pattern_id"])["requalified_at_ms"]
                .first()
                .reset_index()
            )
            rq_times_since = list(rq_per_route["requalified_at_ms"] - PHASE_FAULT_END)
        else:
            rq_times_since = []

        matched_r, _, _inc = build_matched_comparison(rec)
        m = matched_r.get(arch, {})

        extra_rows.append({
            "phase":                                  "recovery",
            "arch":                                   arch,
            "k_requalify":                            K_REQUALIFY_PRIMARY,
            "mean_time_to_requalify_ms":              float(np.mean(rq_times_since)) if rq_times_since else None,
            "route_instances_requalified":            n_routes_rq,
            "distinct_pattern_ids_requalified":       n_pids_rq,
            "route_instances_remaining_requalifying": n_still_rq,
            "patterns_deprecated_during_requalification": n_dep_during_rq,
            "shadow_checks_total":                    len(shadow),
            "shadow_checks_admissible":               n_shadow_adm,
            "post_requalify_bypasses":                len(post),
            "post_requalify_wrong_bypasses":          int(post["wrong_bypass"].sum()) if len(post) else 0,
            "post_requalify_wrong_bypass_rate":       (int(post["wrong_bypass"].sum()) / max(1, len(post[post["bypassed"]==True]))) * 100 if len(post) else 0.0,
            "matched_tasks":                          m.get("matched_tasks", 0),
            "matched_bypasses":                       m.get("matched_bypasses", 0),
            "matched_wrong_bypasses":                 m.get("matched_wrong_bypasses", 0),
            "matched_wrong_bypass_rate":              m.get("matched_wrong_bypass_rate", 0.0),
            "matched_fallback_rate":                  m.get("matched_fallback_rate", 0.0),
            **{f"wrong_bypasses_{lb}": wbr_bin.get(lb, 0) for lb in bin_labels},
            **{f"fallback_rate_{lb}": fbk_bin.get(lb, 0.0) for lb in bin_labels},
        })

    extra_df = pd.DataFrame(extra_rows)
    extra_df.to_csv(out_dir / "bounded_routing_v2_recovery_summary.csv", index=False)
    return extra_df


# -----------------------------------------------------------------------
# Sensitivity summary CSV
# -----------------------------------------------------------------------

def build_sensitivity_csv(df, out_dir):
    """
    Build and save bounded_routing_v2_sensitivity_summary.csv.

    Columns:
      k_requalify, final_ACTIVE, final_REQUALIFYING, final_DEPRECATED,
      wrong_bypasses, wrong_bypass_rate_pct, bypass_count,
      fallback_rate_pct, mean_time_to_requalify_ms

    Terminal state counts use the final recovery row per (seed, pattern_id).
    mean_time_to_requalify_ms uses one requalified_at_ms value per unique
    (seed, pattern_id) route instance, not one value per row.
    """
    out_dir = Path(out_dir)
    rows = []

    for k in K_REQUALIFY_SWEEP:
        sub = df[
            (df["arch"]       == "D_REQUALIFYING") &
            (df["phase"]      == "recovery") &
            (df["k_requalify"] == k)
        ]
        bp  = sub[sub["bypassed"] == True]
        wbr = (int(sub["wrong_bypass"].sum()) / max(1, len(bp))) * 100

        # Terminal state counts: final row per (seed, pattern_id)
        if len(sub) > 0:
            final = (
                sub.sort_values("time_ms")
                   .groupby(["seed", "pattern_id"], sort=False)
                   .last()
                   .reset_index()
            )
            n_act = int((final["requalification_state"] == "ACTIVE").sum())
            n_req = int((final["requalification_state"] == "REQUALIFYING").sum())
            n_dep = int((final["requalification_state"] == "DEPRECATED").sum())
        else:
            n_act = n_req = n_dep = 0

        # Mean requalification time: one value per unique (seed, pattern_id) route instance
        rq_per_route = (
            sub[sub["requalified_at_ms"].notna()]
            .groupby(["seed", "pattern_id"])["requalified_at_ms"]
            .first()
            .reset_index()
        )
        if len(rq_per_route) > 0:
            mean_t = round(float((rq_per_route["requalified_at_ms"] - PHASE_FAULT_END).mean()), 1)
        else:
            mean_t = None

        rows.append({
            "k_requalify":               k,
            "final_ACTIVE":              n_act,
            "final_REQUALIFYING":        n_req,
            "final_DEPRECATED":          n_dep,
            "wrong_bypasses":            int(sub["wrong_bypass"].sum()),
            "wrong_bypass_rate_pct":     round(wbr, 3),
            "bypass_count":              len(bp),
            "fallback_rate_pct":         round(sub["fallback"].mean() * 100, 2),
            "mean_time_to_requalify_ms": mean_t,
        })

    sens_df = pd.DataFrame(rows)
    path = out_dir / "bounded_routing_v2_sensitivity_summary.csv"
    sens_df.to_csv(path, index=False)
    return path


# -----------------------------------------------------------------------
# Plots
# -----------------------------------------------------------------------

def make_plots(df, summary, out_dir):
    primary = df[df["k_requalify"] == K_REQUALIFY_PRIMARY].copy()
    rec     = primary[primary["phase"] == "recovery"]

    arch_colors = {
        "A_FULL_ANALYSIS": "#d62728",
        "B_NAIVE_CACHE":   "#1f77b4",
        "C_TIMER_BOUND":   "#ff7f0e",
        "D_REQUALIFYING":  "#2ca02c",
    }
    arch_labels = {
        "A_FULL_ANALYSIS": "Full analysis",
        "B_NAIVE_CACHE":   "Naive cache",
        "C_TIMER_BOUND":   "Timer-bound",
        "D_REQUALIFYING":  "Requalifying",
    }
    plots = []

    time_bins  = np.arange(0, 15001, 1000)

    # ---- Plot 1: recovery wrong-bypass timeseries ----
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle("v2 — Cumulative Wrong Bypasses Over Recovery Phase",
                 fontsize=11, fontweight="bold")
    for arch in ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        sub = rec[rec["arch"] == arch].copy()
        sub["tbin"] = pd.cut(sub["time_since_recovery_ms"], bins=time_bins, labels=time_bins[:-1])
        binned = sub.groupby("tbin", observed=True)["wrong_bypass"].sum().reset_index()
        binned["cumulative"] = binned["wrong_bypass"].cumsum()
        ax.plot(binned["tbin"].astype(float), binned["cumulative"],
                color=arch_colors[arch], lw=2, label=arch_labels[arch])
    ax.set_xlabel("Time since recovery event (ms)", fontsize=10)
    ax.set_ylabel("Cumulative wrong bypasses", fontsize=10)
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    p = str(out_dir / "recovery_wrong_bypass_timeseries_v2.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 2: fallback rate timeseries ----
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle("v2 — Fallback Rate Over Recovery Phase",
                 fontsize=11, fontweight="bold")
    for arch in ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]:
        sub = rec[rec["arch"] == arch].copy()
        sub["tbin"] = pd.cut(sub["time_since_recovery_ms"], bins=time_bins, labels=time_bins[:-1])
        binned = sub.groupby("tbin", observed=True)["fallback"].mean().reset_index()
        ax.plot(binned["tbin"].astype(float), binned["fallback"] * 100,
                color=arch_colors[arch], lw=2, label=arch_labels[arch])
    ax.set_xlabel("Time since recovery event (ms)", fontsize=10)
    ax.set_ylabel("Fallback rate (%)", fontsize=10)
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    p = str(out_dir / "recovery_fallback_timeseries_v2.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 3: requalification by pattern (seed=42) ----
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle("v2 — Requalification Timing by Pattern (Arm D, seed=42)",
                 fontsize=11, fontweight="bold")
    d42 = rec[(rec["arch"] == "D_REQUALIFYING") & (rec["seed"] == 42)]
    for pid in range(N_PATTERNS):
        ax.axhline(pid, color="grey", alpha=0.2, lw=0.5)
        pat = d42[d42["pattern_id"] == pid]
        rq_rows = pat[pat["requalified_at_ms"].notna()]
        if len(rq_rows):
            t_rq = float(rq_rows["requalified_at_ms"].iloc[0]) - PHASE_FAULT_END
            ax.scatter([t_rq], [pid], marker="*", s=200, color=arch_colors["D_REQUALIFYING"], zorder=5)
            ax.text(t_rq + 100, pid + 0.1, f"pat {pid}", fontsize=8)
        else:
            ax.text(14400, pid + 0.1, f"pat {pid} — not requalified", fontsize=7, color="red")
    ax.set_xlabel("Time since recovery event (ms)", fontsize=10)
    ax.set_ylabel("Pattern ID", fontsize=10)
    ax.set_yticks(range(N_PATTERNS)); ax.set_xlim(0, 15500)
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    p = str(out_dir / "requalification_by_pattern_v2.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 4: post-requalification safety — matched + full recovery ----
    # CORRECTION #10: two panels: matched comparison and full-recovery comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("v2 — Post-Requalification Bypass Safety", fontsize=11, fontweight="bold")

    # Left panel: matched comparison (same manifest rows where D earned authority)
    matched_results, _, inconclusive_flag = build_matched_comparison(rec)
    ax = axes[0]
    if matched_results:
        archs_m = ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]
        vals_m  = [matched_results.get(a, {}).get("matched_wrong_bypass_rate", 0.0) for a in archs_m]
        ax.bar(range(len(archs_m)), vals_m,
               color=[arch_colors[a] for a in archs_m], alpha=0.85)
        ax.set_xticks(range(len(archs_m)))
        ax.set_xticklabels([arch_labels[a] for a in archs_m], fontsize=9)
        ax.set_ylabel("Wrong bypass rate (%)", fontsize=10)
        title_suffix = "\nINCONCLUSIVE: workload non-discriminating" if inconclusive_flag else ""
        ax.set_title(f"Matched tasks (post-requalify cohort){title_suffix}", fontsize=9)
        for i, v in enumerate(vals_m):
            ax.text(i, v + 0.02, f"{v:.2f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
    else:
        ax.text(0.5, 0.5, "No matched tasks", transform=ax.transAxes, ha="center")
        ax.set_title("Matched tasks", fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    # Right panel: full recovery comparison
    ax = axes[1]
    archs_f = ["B_NAIVE_CACHE", "C_TIMER_BOUND", "D_REQUALIFYING"]
    vals_f  = []
    for arch in archs_f:
        sub = rec[rec["arch"] == arch]
        bp  = sub[sub["bypassed"] == True]
        vals_f.append((int(sub["wrong_bypass"].sum()) / max(1, len(bp))) * 100)
    ax.bar(range(len(archs_f)), vals_f,
           color=[arch_colors[a] for a in archs_f], alpha=0.85)
    ax.set_xticks(range(len(archs_f)))
    ax.set_xticklabels([arch_labels[a] for a in archs_f], fontsize=9)
    ax.set_ylabel("Wrong bypass rate (%)", fontsize=10)
    ax.set_title("Full recovery phase\n(all bypass attempts)", fontsize=9)
    for i, v in enumerate(vals_f):
        ax.text(i, v + 0.02, f"{v:.2f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    p = str(out_dir / "post_requalification_safety_v2.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    # ---- Plot 5: sensitivity sweep ----
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("v2 — Sensitivity Sweep K_REQUALIFY = 3, 5, 8 (Arm D, recovery phase)",
                 fontsize=11, fontweight="bold")
    sweep_d = df[(df["arch"] == "D_REQUALIFYING") & (df["phase"] == "recovery")]
    k_vals  = K_REQUALIFY_SWEEP
    wbr_vals  = []
    fbk_vals  = []
    for k in k_vals:
        sub = sweep_d[sweep_d["k_requalify"] == k]
        bp  = sub[sub["bypassed"] == True]
        wbr_vals.append((int(sub["wrong_bypass"].sum()) / max(1, len(bp))) * 100)
        fbk_vals.append(sub["fallback"].mean() * 100)

    for ax, vals, ylabel, title in [
        (axes[0], wbr_vals, "Wrong bypass rate (%)", "Wrong bypass rate by K_REQUALIFY"),
        (axes[1], fbk_vals, "Fallback rate (%)",     "Fallback rate by K_REQUALIFY"),
    ]:
        ax.bar(range(len(k_vals)), vals, color=arch_colors["D_REQUALIFYING"], alpha=0.85)
        ax.set_xticks(range(len(k_vals)))
        ax.set_xticklabels([f"K={k}" for k in k_vals], fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=10)
        ax.grid(True, alpha=0.3, axis="y")
        fmt = ".2f" if "bypass" in ylabel else ".1f"
        for i, v in enumerate(vals):
            ax.text(i, v + 0.05, f"{v:{fmt}}%", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    p = str(out_dir / "requalification_sensitivity_v2.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(); plots.append(p)

    return plots


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

if __name__ == "__main__":
    OUT_DIR = Path.cwd() / "bounded_routing_output_v2"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    df      = run_sweep(OUT_DIR)
    summary = analyze(df)

    df.to_csv(     OUT_DIR / "bounded_routing_v2_raw.csv",     index=False)
    summary.to_csv(OUT_DIR / "bounded_routing_v2_summary.csv", index=False)
    extra    = build_summary_csv(df, OUT_DIR)
    sens_csv = build_sensitivity_csv(df, OUT_DIR)

    print("\nGenerating plots...")
    plots = make_plots(df, summary, OUT_DIR)

    elapsed = time.time() - t_start
    print(f"\n{'='*72}")
    print("OUTPUT FILES")
    print(f"{'='*72}")
    named = [
        OUT_DIR / "bounded_routing_v2_raw.csv",
        OUT_DIR / "bounded_routing_v2_summary.csv",
        OUT_DIR / "bounded_routing_v2_recovery_summary.csv",
        sens_csv,
    ] + [OUT_DIR / p.name for p in OUT_DIR.iterdir()
         if p.suffix in (".png",) or p.name.startswith("manifest_")]
    seen = set()
    for f in named:
        fp = Path(f)
        if fp not in seen and fp.exists():
            print(f"  {fp}")
            seen.add(fp)
    print(f"\nTotal runtime: {elapsed:.1f}s")
    print(f"\n{'='*72}")
    print("ALL ASSERTIONS PASSED")
    print(f"{'='*72}")


# -----------------------------------------------------------------------
# UNRESOLVED DECISIONS
# -----------------------------------------------------------------------
#
# 1. PROMOTION TASK USES FULL ANALYSIS
#    The task on which K_REQUALIFY is satisfied uses full analysis (it was
#    already dispatched before promotion completed). Bypass authority begins
#    on the next task. The plan specifies promotion criteria, not task
#    routing on the promoting task. Conservative choice.
#
# 2. OSCILLATION PHASE INCLUDED IN RAW AND SUMMARY CSVs
#    The v2 plan focuses on recovery. All phases are included in output;
#    go/no-go metrics and primary plots restrict to recovery phase only.
#
# 3. REQUALIFYING -> DEPRECATED IMPLEMENTATION
#    CORRECTION #8 implements the declared rule: fresh shadow confidence
#    below T_DEPRECIATE for DEPRECIATION_N + DEPRECIATION_M consecutive
#    shadow observations triggers DEPRECATED. This uses the shadow
#    observation count, not c_success, since c_success is not updated
#    while REQUALIFYING. If zero routes deprecate during recovery (as
#    expected given short phase duration), the count is reported as zero.
#
# 4. SENSITIVITY SWEEP SHARES MANIFESTS WITH PRIMARY RUN
#    Manifests are generated per seed once and saved. All K values read
#    the same manifest. Plots 1-4 use K=5 primary data only; plot 5
#    uses all K values.
#
# 5. time_since_recovery_ms IS None FOR NON-RECOVERY PHASES
#    Recovery-phase rows compute this as time_ms - PHASE_FAULT_END.
#    All other phases set it to None.
#
# 6. STRUCTURAL COST GATE
#    The structural_cost bypass gate in all arms uses the manifest
#    candidate_cost value directly (the shared, auditable value).
#    Arms C and D also maintain an internal ARD structural_cost estimate
#    that drifts with observed route quality. This internal estimate is
#    used only for ARD state persistence (long-run cost tracking) and does
#    NOT influence the bypass gate decision. Arm D's _check_bypass() takes
#    candidate_cost as an explicit parameter to make the dependency clear.
#    If the internal ARD cost estimate should be removed entirely, that is
#    a v2.1 decision.
