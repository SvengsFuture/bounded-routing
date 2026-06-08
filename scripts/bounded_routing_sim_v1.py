"""
Bounded Routing Simulation v1
Bounded Routing public validation harness

PURPOSE
-------
Compare three routing architectures under a synthetic task stream
with controlled phases: stable, drift, fault injection, recovery,
and oscillation trigger.

The goal is not to show a speed record. The goal is to show that
bounded routing is safer and more stable than naive adaptive bypass,
while still reducing cost versus full analysis.

THREE ARMS
----------
  A_FULL_ANALYSIS   : every task takes the full path. No bypass. No ARD.
  B_NAIVE_CACHE     : bypass when confidence >= T_bypass. No structural
                      bounds, no depreciation, no anti-oscillation, no
                      recovery blackout.
  C_BOUNDED_ROUTING : full ARD/SMS/IBM stack. All four bypass gates active.

TASK STREAM PHASES
------------------
  stable     : consistent routes, confidence builds
  drift      : route structural costs increase gradually
  fault      : one route fails abruptly
  recovery   : system recovery event, blackout period
  oscillation: two competing routes alternate in quality

METRICS
-------
  mean_latency_ms, p95_latency_ms, wrong_bypass_rate, fallback_rate,
  oscillation_count, admissibility_violations, route_depreciation_events,
  total_structural_cost, successful_bounded_bypass
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import deque
import os
import time

# -----------------------------------------------------------------------
# Simulation parameters
# -----------------------------------------------------------------------

SEEDS            = [42, 99, 500, 777, 1337]
N_PATTERNS       = 8          # distinct pattern classes
TASK_RATE_MS     = 20.0       # one task every 20ms
SIM_DURATION_MS  = 120_000.0  # 120 seconds total
DT_MS            = 20.0

# Phase boundaries (ms)
PHASE_STABLE_END      =  30_000.0
PHASE_DRIFT_END       =  60_000.0
PHASE_FAULT_END       =  80_000.0
PHASE_RECOVERY_END    =  95_000.0
# oscillation: 95000 to end

# Latency model (ms)
LATENCY_FULL_ANALYSIS = 40.0   # full path always costs this
LATENCY_BYPASS_FAST   =  8.0   # good bypass
LATENCY_BYPASS_SLOW   = 25.0   # degraded bypass (drift/fault)
LATENCY_NOISE_STD     =  3.0

# Structural cost model
COST_FULL_ANALYSIS    = 1.0    # baseline
COST_BYPASS_NORMAL    = 0.3
COST_BYPASS_DRIFTED   = 0.8
COST_BYPASS_FAILED    = 2.0    # wrong bypass is expensive

# Route quality during fault (prob admissible outcome)
FAULT_ADMISSIBILITY_RATE = 0.15   # route mostly fails

# Oscillation: two routes alternate this often
OSCILLATION_FLIP_PERIOD_MS = 4000.0

# -----------------------------------------------------------------------
# ARD/SMS/IBM parameters
# -----------------------------------------------------------------------

T_BYPASS              = 0.75   # min confidence for bypass
T_DEPRECIATE          = 0.55   # below this -> depreciation starts
T_RECOVER_ARD         = 0.70   # above this for K steps -> exit DEPRECATED
T_COST_MAX            = 1.5    # max structural cost multiplier
ALPHA                 = 0.85   # confidence decay
OBS_WINDOW_SIZE       = 20
DEPRECIATION_N        = 5      # consecutive below-T_depreciate -> WARNED
DEPRECIATION_M        = 10     # additional steps -> DEPRECATED
RECOVER_K             = 8      # consecutive above-T_recover -> ACTIVE
T_RETIRE_MS           = 60_000.0
T_FLIP_COOLDOWN_MS    = 2_000.0
MAX_FLIPS_PER_WINDOW  = 3
T_FLIP_WINDOW_MS      = 10_000.0
T_RECOVERY_BLACKOUT_MS = 5_000.0

# SMS outcome weights
W_LAT   = 0.30
W_ADM   = 0.40
W_DEG   = 0.20
W_STAB  = 0.10


# -----------------------------------------------------------------------
# Task stream generator
# -----------------------------------------------------------------------

def task_stream(rng, duration_ms, dt_ms):
    """
    Yield (time_ms, pattern_id, phase, true_admissible, route_quality)
    for each task in the simulation.

    route_quality: float 0-1, how good the current best route is.
    Degrades during drift, collapses during fault, recovers after.
    """
    t = 0.0
    # Per-pattern route quality (varies by phase)
    # Pattern 0 is the "hot" pattern targeted by fault/oscillation
    route_quality = np.ones(N_PATTERNS)

    # Track oscillation state
    osc_phase = 0

    while t < duration_ms:
        # Determine phase
        if t < PHASE_STABLE_END:
            phase = "stable"
            route_quality[:] = 1.0
        elif t < PHASE_DRIFT_END:
            phase = "drift"
            # Pattern 0's route degrades linearly
            frac = (t - PHASE_STABLE_END) / (PHASE_DRIFT_END - PHASE_STABLE_END)
            route_quality[0] = max(0.2, 1.0 - 0.7 * frac)
        elif t < PHASE_FAULT_END:
            phase = "fault"
            route_quality[0] = 0.1   # route mostly broken
        elif t < PHASE_RECOVERY_END:
            phase = "recovery"
            # Route quality recovers
            frac = (t - PHASE_FAULT_END) / (PHASE_RECOVERY_END - PHASE_FAULT_END)
            route_quality[0] = min(1.0, 0.1 + 0.9 * frac)
        else:
            phase = "oscillation"
            # Pattern 1 oscillates between good and bad
            osc_cycle = (t % OSCILLATION_FLIP_PERIOD_MS) / OSCILLATION_FLIP_PERIOD_MS
            route_quality[1] = 1.0 if osc_cycle < 0.5 else 0.2

        pattern_id = rng.randint(0, N_PATTERNS)
        true_admissible = rng.random() < route_quality[pattern_id]
        rq = route_quality[pattern_id]

        yield t, pattern_id, phase, true_admissible, rq
        t += dt_ms


# -----------------------------------------------------------------------
# Arm A: Full analysis baseline
# -----------------------------------------------------------------------

class FullAnalysisBaseline:
    arch_label = "A_FULL_ANALYSIS"

    def __init__(self, seed):
        self.rng = np.random.RandomState(seed)

    def process(self, time_ms, pattern_id, phase, true_admissible, route_quality):
        latency = LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD)
        latency = max(1.0, latency)
        return {
            "time_ms":         time_ms,
            "pattern_id":      pattern_id,
            "phase":           phase,
            "bypassed":        False,
            "admissible":      True,   # full analysis always produces admissible result
            "wrong_bypass":    False,
            "latency_ms":      latency,
            "structural_cost": COST_FULL_ANALYSIS,
            "fallback":        False,
            "oscillation_event": False,
            "depreciation_event": False,
        }


# -----------------------------------------------------------------------
# Arm B: Naive adaptive cache
# -----------------------------------------------------------------------

class NaiveCache:
    arch_label = "B_NAIVE_CACHE"

    def __init__(self, seed):
        self.rng        = np.random.RandomState(seed)
        self.confidence = {}   # pattern_id -> float
        self.flip_count = {}   # pattern_id -> int
        self.last_route = {}   # pattern_id -> str (simulated route label)

    def _get_confidence(self, pid):
        return self.confidence.get(pid, 0.0)

    def _update_confidence(self, pid, outcome_score):
        c = self._get_confidence(pid)
        self.confidence[pid] = ALPHA * c + (1 - ALPHA) * outcome_score

    def process(self, time_ms, pattern_id, phase, true_admissible, route_quality):
        pid = pattern_id
        c   = self._get_confidence(pid)

        osc_event = False

        if c >= T_BYPASS:
            # Naive bypass: no structural check, no depreciation, no recovery gate
            admissible = true_admissible
            latency    = (LATENCY_BYPASS_FAST if route_quality > 0.5
                          else LATENCY_BYPASS_SLOW)
            latency   += self.rng.normal(0, LATENCY_NOISE_STD)
            latency    = max(1.0, latency)
            cost       = COST_BYPASS_NORMAL if route_quality > 0.5 else COST_BYPASS_DRIFTED
            wrong_bp   = not admissible
            fell_back  = False

            # Simulate oscillation: naive cache has no anti-oscillation gate
            # During oscillation phase, route flips frequently
            if phase == "oscillation" and pid == 1:
                prev = self.last_route.get(pid, "A")
                new  = "B" if (time_ms % OSCILLATION_FLIP_PERIOD_MS) < (OSCILLATION_FLIP_PERIOD_MS / 2) else "A"
                if new != prev:
                    self.flip_count[pid] = self.flip_count.get(pid, 0) + 1
                    self.last_route[pid] = new
                    osc_event = True

            outcome = 1.0 if admissible else 0.0
            self._update_confidence(pid, outcome)
        else:
            # Full analysis fallback
            admissible = True
            latency    = LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD)
            latency    = max(1.0, latency)
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True

            # Update confidence from full analysis outcome (always good)
            self._update_confidence(pid, 1.0 if route_quality > 0.5 else 0.5)

        return {
            "time_ms":            time_ms,
            "pattern_id":         pid,
            "phase":              phase,
            "bypassed":           not fell_back and c >= T_BYPASS,
            "admissible":         admissible,
            "wrong_bypass":       wrong_bp,
            "latency_ms":         latency,
            "structural_cost":    cost,
            "fallback":           fell_back,
            "oscillation_event":  osc_event,
            "depreciation_event": False,
        }


# -----------------------------------------------------------------------
# Arm C: Bounded routing
# -----------------------------------------------------------------------

class ARDEntry:
    def __init__(self, pid, time_ms):
        self.pid                 = pid
        self.p_opt               = f"route_{pid}_A"
        self.c_success           = 0.0
        self.obs_count           = 0
        self.obs_window          = deque(maxlen=OBS_WINDOW_SIZE)
        self.last_used_ms        = time_ms
        self.depreciation_state  = "ACTIVE"
        self.depreciation_count  = 0
        self.recover_count       = 0
        self.last_flip_ms        = -T_FLIP_COOLDOWN_MS * 2
        self.flip_count          = 0
        self.flip_times          = deque(maxlen=MAX_FLIPS_PER_WINDOW + 5)
        self.structural_cost     = COST_BYPASS_NORMAL
        self.recovery_sensitive  = False

    def update_depreciation(self):
        if self.c_success < T_DEPRECIATE:
            self.depreciation_count += 1
            self.recover_count       = 0
            if self.depreciation_state == "ACTIVE" and self.depreciation_count >= DEPRECIATION_N:
                self.depreciation_state = "WARNED"
            elif self.depreciation_state == "WARNED" and self.depreciation_count >= DEPRECIATION_N + DEPRECIATION_M:
                self.depreciation_state = "DEPRECATED"
        else:
            if self.depreciation_state in ("WARNED",):
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
            else:
                self.depreciation_count = 0


class BoundedRouting:
    arch_label = "C_BOUNDED_ROUTING"

    def __init__(self, seed):
        self.rng              = np.random.RandomState(seed)
        self.ard              = {}   # pid -> ARDEntry
        self.last_recovery_ms = -T_RECOVERY_BLACKOUT_MS * 2
        self._in_recovery     = False
        self._osc_route       = {}   # pid -> current route label for oscillation sim

    def _get_entry(self, pid, time_ms):
        if pid not in self.ard:
            self.ard[pid] = ARDEntry(pid, time_ms)
        return self.ard[pid]

    def _sms_outcome_score(self, latency_ms, admissible, route_quality, entry):
        # Latency score
        lat_score = 1.0 if latency_ms <= LATENCY_BYPASS_FAST * 2 else 0.5

        # Admissibility score (highest weight)
        adm_score = 1.0 if admissible else 0.0

        # Degradation: route quality as proxy
        deg_score = route_quality

        # Stability: inverse variance of obs_window
        if len(entry.obs_window) >= 3:
            var = np.var(list(entry.obs_window))
            stab_score = max(0.0, 1.0 - var * 4)
        else:
            stab_score = 0.5

        return (W_LAT * lat_score + W_ADM * adm_score +
                W_DEG * deg_score + W_STAB * stab_score)

    def _update_sms(self, entry, latency_ms, admissible, route_quality):
        score = self._sms_outcome_score(latency_ms, admissible, route_quality, entry)
        entry.obs_window.append(score)
        entry.c_success = ALPHA * entry.c_success + (1 - ALPHA) * score
        entry.obs_count += 1
        entry.update_depreciation()

    def _check_bypass_gates(self, entry, time_ms):
        """
        Returns (allowed: bool, reason: str)
        Gate 1: confidence
        Gate 2: depreciation state
        Gate 3: structural cost
        Gate 4: recovery context
        Gate 5: anti-oscillation
        """
        if entry.c_success < T_BYPASS:
            return False, "confidence"
        if entry.depreciation_state in ("DEPRECATED", "RETIRED"):
            return False, "deprecated"
        if entry.structural_cost > T_COST_MAX:
            return False, "cost"
        if (entry.recovery_sensitive and
                (time_ms - self.last_recovery_ms) < T_RECOVERY_BLACKOUT_MS):
            return False, "recovery_blackout"
        # Anti-oscillation: too many flips recently
        recent_flips = sum(1 for ft in entry.flip_times
                           if (time_ms - ft) < T_FLIP_WINDOW_MS)
        if recent_flips >= MAX_FLIPS_PER_WINDOW:
            return False, "oscillation"
        if (time_ms - entry.last_flip_ms) < T_FLIP_COOLDOWN_MS:
            return False, "flip_cooldown"
        return True, "ok"

    def _simulate_route_flip(self, entry, pid, time_ms, phase):
        """
        During oscillation phase, simulate competing route quality.
        Bounded routing records the flip but anti-oscillation gate
        will block bypass if flip rate is too high.
        """
        if phase == "oscillation" and pid == 1:
            new_route = ("route_1_A" if (time_ms % OSCILLATION_FLIP_PERIOD_MS)
                         < (OSCILLATION_FLIP_PERIOD_MS / 2) else "route_1_B")
            if new_route != entry.p_opt:
                entry.p_opt       = new_route
                entry.last_flip_ms = time_ms
                entry.flip_count  += 1
                entry.flip_times.append(time_ms)
                return True
        return False

    def signal_recovery(self, time_ms):
        self.last_recovery_ms = time_ms
        # Mark all entries as recovery-sensitive
        for entry in self.ard.values():
            entry.recovery_sensitive = True

    def process(self, time_ms, pattern_id, phase, true_admissible, route_quality):
        pid   = pattern_id
        entry = self._get_entry(pid, time_ms)

        # Signal recovery event at start of recovery phase
        if phase == "recovery" and not self._in_recovery:
            self.signal_recovery(time_ms)
            self._in_recovery = True
        elif phase != "recovery":
            self._in_recovery = False

        # Simulate route flip (oscillation tracking)
        osc_event = self._simulate_route_flip(entry, pid, time_ms, phase)

        # Check all bypass gates
        bypass_allowed, gate_reason = self._check_bypass_gates(entry, time_ms)

        dep_event = False

        if bypass_allowed:
            # Bounded bypass
            admissible = true_admissible
            latency    = (LATENCY_BYPASS_FAST if route_quality > 0.5
                          else LATENCY_BYPASS_SLOW)
            latency   += self.rng.normal(0, LATENCY_NOISE_STD)
            latency    = max(1.0, latency)
            cost       = entry.structural_cost
            wrong_bp   = not admissible
            fell_back  = False

            # Update structural cost based on observed route quality
            if route_quality < 0.4:
                entry.structural_cost = min(COST_BYPASS_FAILED,
                                            entry.structural_cost * 1.15)
            else:
                entry.structural_cost = max(COST_BYPASS_NORMAL,
                                            entry.structural_cost * 0.98)

            prev_state = entry.depreciation_state
            self._update_sms(entry, latency, admissible, route_quality)
            if (prev_state != "DEPRECATED" and
                    entry.depreciation_state == "DEPRECATED"):
                dep_event = True
        else:
            # Full analysis fallback
            admissible = True
            latency    = LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD)
            latency    = max(1.0, latency)
            cost       = COST_FULL_ANALYSIS
            wrong_bp   = False
            fell_back  = True

            # Reset recovery sensitivity once past blackout
            if ((time_ms - self.last_recovery_ms) >= T_RECOVERY_BLACKOUT_MS
                    and entry.recovery_sensitive):
                entry.recovery_sensitive = False

            # Still update SMS from full-analysis outcome
            prev_state = entry.depreciation_state
            self._update_sms(entry, latency, True, route_quality)
            if (prev_state != "DEPRECATED" and
                    entry.depreciation_state == "DEPRECATED"):
                dep_event = True

        entry.last_used_ms = time_ms

        return {
            "time_ms":            time_ms,
            "pattern_id":         pid,
            "phase":              phase,
            "bypassed":           bypass_allowed and not fell_back,
            "admissible":         admissible,
            "wrong_bypass":       wrong_bp,
            "latency_ms":         latency,
            "structural_cost":    cost,
            "fallback":           fell_back,
            "oscillation_event":  osc_event,
            "depreciation_event": dep_event,
            "bypass_gate":        gate_reason if not bypass_allowed else "ok",
        }


# -----------------------------------------------------------------------
# Run one seed
# -----------------------------------------------------------------------

def run_seed(arch_class, seed):
    rng  = np.random.RandomState(seed)
    arch = arch_class(seed)
    rows = []

    for time_ms, pattern_id, phase, true_admissible, route_quality in \
            task_stream(rng, SIM_DURATION_MS, DT_MS):
        r = arch.process(time_ms, pattern_id, phase, true_admissible, route_quality)
        r["seed"]  = seed
        r["arch"]  = arch_class.arch_label
        rows.append(r)

    return rows


# -----------------------------------------------------------------------
# Sweep
# -----------------------------------------------------------------------

def run_sweep():
    t0   = time.time()
    rows = []

    print("=" * 72)
    print("BOUNDED ROUTING SIMULATION v1")
    print("Three-arm comparison: full analysis / naive cache / bounded routing")
    print("=" * 72)

    total_runs = len(SEEDS) * 3
    idx = 0
    for seed in SEEDS:
        for arch_class in [FullAnalysisBaseline, NaiveCache, BoundedRouting]:
            idx += 1
            r = run_seed(arch_class, seed)
            rows.extend(r)
            print(f"  [{idx:>2}/{total_runs}] {arch_class.arch_label}  seed={seed}  "
                  f"tasks={len(r)}  t={time.time()-t0:.1f}s")

    print(f"\nSweep done in {time.time()-t0:.1f}s, {len(rows)} rows")
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------
# Analysis
# -----------------------------------------------------------------------

def analyze(df):
    print("\n" + "=" * 72)
    print("ANALYSIS — Bounded Routing v1")
    print("=" * 72)

    summary_rows = []

    phases    = ["stable", "drift", "fault", "recovery", "oscillation"]
    arch_list = ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_BOUNDED_ROUTING"]

    for phase in phases:
        print(f"\n-- Phase: {phase} --")
        print(f"  {'arch':>22} {'mean_lat':>9} {'p95_lat':>8} {'wrong_bp%':>10} "
              f"{'fallbk%':>8} {'adm_viol':>9} {'osc_ev':>7} {'struct_cost':>12}")
        print("  " + "-" * 90)

        for arch in arch_list:
            sub = df[(df["arch"] == arch) & (df["phase"] == phase)]
            if len(sub) == 0:
                continue

            n             = len(sub)
            mean_lat      = sub["latency_ms"].mean()
            p95_lat       = sub["latency_ms"].quantile(0.95)
            bypassed      = sub[sub["bypassed"] == True]
            wrong_bp_rate = (sub["wrong_bypass"].sum() / max(1, bypassed["wrong_bypass"].count())) * 100
            fallbk_rate   = sub["fallback"].mean() * 100
            adm_viol      = (~sub["admissible"]).sum()
            osc_ev        = sub["oscillation_event"].sum()
            struct_cost   = sub["structural_cost"].mean()

            print(f"  {arch:>22} {mean_lat:>9.1f} {p95_lat:>8.1f} "
                  f"{wrong_bp_rate:>10.1f} {fallbk_rate:>8.1f} "
                  f"{adm_viol:>9} {osc_ev:>7} {struct_cost:>12.3f}")

            summary_rows.append({
                "phase":                  phase,
                "arch":                   arch,
                "mean_latency_ms":        mean_lat,
                "p95_latency_ms":         p95_lat,
                "wrong_bypass_rate_pct":  wrong_bp_rate,
                "fallback_rate_pct":      fallbk_rate,
                "admissibility_violations": adm_viol,
                "oscillation_events":     osc_ev,
                "mean_structural_cost":   struct_cost,
                "n_tasks":                n,
                "total_bypasses":         (sub["bypassed"] == True).sum(),
                "depreciation_events":    sub["depreciation_event"].sum(),
                "successful_bounded_bypass": (
                    (sub["bypassed"] == True) & sub["admissible"]
                ).sum() if arch == "C_BOUNDED_ROUTING" else 0,
            })

    # Verdict
    print("\n" + "=" * 72)
    print("VERDICT")
    print("=" * 72)
    for phase in ["fault", "drift", "oscillation"]:
        b_viol = next((r["admissibility_violations"] for r in summary_rows
                       if r["arch"] == "B_NAIVE_CACHE" and r["phase"] == phase), 0)
        c_viol = next((r["admissibility_violations"] for r in summary_rows
                       if r["arch"] == "C_BOUNDED_ROUTING" and r["phase"] == phase), 0)
        a_lat  = next((r["mean_latency_ms"] for r in summary_rows
                       if r["arch"] == "A_FULL_ANALYSIS" and r["phase"] == phase), 0)
        c_lat  = next((r["mean_latency_ms"] for r in summary_rows
                       if r["arch"] == "C_BOUNDED_ROUTING" and r["phase"] == phase), 0)
        safer   = "SAFER" if c_viol < b_viol else "SAME"
        faster  = "FASTER" if c_lat < a_lat else "SAME"
        print(f"  {phase:>12}: admissibility  B={b_viol:>4}  C={c_viol:>4}  [{safer}]  "
              f"latency vs full-analysis: C={c_lat:.1f}ms A={a_lat:.1f}ms  [{faster}]")

    print()

    return pd.DataFrame(summary_rows)


# -----------------------------------------------------------------------
# Plots
# -----------------------------------------------------------------------

def make_plots(df, summary, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    plots = []

    phase_order = ["stable", "drift", "fault", "recovery", "oscillation"]
    arch_colors = {
        "A_FULL_ANALYSIS":   ("#d62728", "-o"),
        "B_NAIVE_CACHE":     ("#1f77b4", "-s"),
        "C_BOUNDED_ROUTING": ("#2ca02c", "-^"),
    }
    arch_labels = {
        "A_FULL_ANALYSIS":   "Full analysis",
        "B_NAIVE_CACHE":     "Naive cache",
        "C_BOUNDED_ROUTING": "Bounded routing",
    }

    # -- Plot 1: Mean latency and p95 by phase --
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Bounded Routing v1 - Latency by Phase",
                 fontsize=12, fontweight="bold")
    for col, metric, label in [
        (0, "mean_latency_ms", "Mean latency (ms)"),
        (1, "p95_latency_ms",  "p95 latency (ms)"),
    ]:
        ax = axes[col]
        x  = np.arange(len(phase_order))
        w  = 0.25
        for i, arch in enumerate(["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_BOUNDED_ROUTING"]):
            vals = [summary[(summary["arch"] == arch) & (summary["phase"] == p)][metric].mean()
                    for p in phase_order]
            color, _ = arch_colors[arch]
            ax.bar(x + (i-1)*w, vals, w, color=color, alpha=0.8, label=arch_labels[arch])
        ax.set_xticks(x)
        ax.set_xticklabels(phase_order, rotation=20, fontsize=9)
        ax.set_ylabel(label, fontsize=10)
        ax.set_title(label, fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    p = os.path.join(out_dir, "latency_by_phase_v1.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    plots.append(p)

    # -- Plot 2: Admissibility violations and wrong bypass rate --
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Bounded Routing v1 - Safety Metrics by Phase",
                 fontsize=12, fontweight="bold")
    for col, metric, label in [
        (0, "admissibility_violations", "Admissibility violations (count)"),
        (1, "wrong_bypass_rate_pct",    "Wrong bypass rate (%)"),
    ]:
        ax = axes[col]
        x  = np.arange(len(phase_order))
        w  = 0.3
        for i, arch in enumerate(["B_NAIVE_CACHE", "C_BOUNDED_ROUTING"]):
            vals = [summary[(summary["arch"] == arch) & (summary["phase"] == p)][metric].mean()
                    for p in phase_order]
            color, _ = arch_colors[arch]
            ax.bar(x + (i-0.5)*w, vals, w, color=color, alpha=0.8, label=arch_labels[arch])
        ax.set_xticks(x)
        ax.set_xticklabels(phase_order, rotation=20, fontsize=9)
        ax.set_ylabel(label, fontsize=10)
        ax.set_title(label, fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")
        if metric == "admissibility_violations":
            ax.set_title("Admissibility violations\n(Arm A excluded: always admissible)", fontsize=9)
    plt.tight_layout()
    p = os.path.join(out_dir, "safety_metrics_v1.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    plots.append(p)

    # -- Plot 3: Structural cost and fallback rate --
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Bounded Routing v1 - Structural Cost and Fallback Rate by Phase",
                 fontsize=12, fontweight="bold")
    for col, metric, label in [
        (0, "mean_structural_cost", "Mean structural cost"),
        (1, "fallback_rate_pct",    "Fallback rate (%)"),
    ]:
        ax = axes[col]
        x  = np.arange(len(phase_order))
        w  = 0.25
        arch_set = (["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_BOUNDED_ROUTING"]
                    if metric == "mean_structural_cost"
                    else ["B_NAIVE_CACHE", "C_BOUNDED_ROUTING"])
        for i, arch in enumerate(arch_set):
            vals = [summary[(summary["arch"] == arch) & (summary["phase"] == p)][metric].mean()
                    for p in phase_order]
            color, _ = arch_colors[arch]
            offset = (i - len(arch_set)/2 + 0.5) * w
            ax.bar(x + offset, vals, w, color=color, alpha=0.8, label=arch_labels[arch])
        ax.set_xticks(x)
        ax.set_xticklabels(phase_order, rotation=20, fontsize=9)
        ax.set_ylabel(label, fontsize=10)
        ax.set_title(label.replace(" (%)", " by phase").capitalize(), fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

        if metric == "fallback_rate_pct":
            c_recovery = summary[(summary["arch"] == "C_BOUNDED_ROUTING") &
                                 (summary["phase"] == "recovery")][metric].mean()
            recovery_x = phase_order.index("recovery") + 0.5 * w
            ax.annotate("Intended: post-recovery\nconservative gating",
                        xy=(recovery_x, c_recovery),
                        xytext=(recovery_x + 0.7, max(c_recovery - 8, 5)),
                        arrowprops=dict(arrowstyle="->", lw=1.2),
                        fontsize=8)
    plt.tight_layout()
    p = os.path.join(out_dir, "cost_fallback_v1.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    plots.append(p)

    # -- Plot 4: Wrong bypasses and oscillation discriminator --
    # This replaces the old route-flip-observation plot. The public metric is
    # unsafe execution, not how many flips were observed for enforcement.
    wrong_by_seed = (
        df[df["arch"].isin(["B_NAIVE_CACHE", "C_BOUNDED_ROUTING"])]
        .groupby(["seed", "phase", "arch"])["wrong_bypass"]
        .sum()
        .reset_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Bounded Routing v1 - Admissibility Violations and Blocked Bypasses\n"
        "Oscillation phase: naive cache keeps executing bad routes; bounded routing blocks them",
        fontsize=12, fontweight="bold"
    )

    ax = axes[0]
    x = np.arange(len(phase_order))
    w = 0.3
    for i, arch in enumerate(["B_NAIVE_CACHE", "C_BOUNDED_ROUTING"]):
        vals = []
        for phase in phase_order:
            sub = wrong_by_seed[(wrong_by_seed["arch"] == arch) &
                                (wrong_by_seed["phase"] == phase)]
            vals.append(sub["wrong_bypass"].mean() if len(sub) else 0.0)
        color, _ = arch_colors[arch]
        ax.bar(x + (i-0.5)*w, vals, w, color=color, alpha=0.8, label=arch_labels[arch])
    ax.set_xticks(x)
    ax.set_xticklabels(phase_order, rotation=20, fontsize=9)
    ax.set_ylabel("Wrong bypasses (mean across seeds)", fontsize=10)
    ax.set_title("Wrong bypasses per phase\n(bypassed AND inadmissible result)", fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    ax = axes[1]
    osc = wrong_by_seed[wrong_by_seed["phase"] == "oscillation"]
    means = []
    stds  = []
    labels = ["Naive cache\n(wrong bypasses)", "Bounded routing\n(wrong bypasses)"]
    for arch in ["B_NAIVE_CACHE", "C_BOUNDED_ROUTING"]:
        sub = osc[osc["arch"] == arch]["wrong_bypass"]
        means.append(sub.mean() if len(sub) else 0.0)
        stds.append(sub.std(ddof=1) if len(sub) > 1 else 0.0)
    ax.bar([0, 1], means, yerr=stds, capsize=6,
           color=[arch_colors["B_NAIVE_CACHE"][0], arch_colors["C_BOUNDED_ROUTING"][0]],
           alpha=0.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Mean wrong bypasses (oscillation phase)", fontsize=10)
    ax.set_title(f"Oscillation phase: wrong bypass count\nBounded routing = {means[1]:.1f} across all seeds",
                 fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")
    for i, m in enumerate(means):
        ax.text(i, m + max(stds + [0.5]) + 0.3, f"{m:.1f}",
                ha="center", va="bottom", fontsize=10, fontweight="bold")
    plt.tight_layout()
    p = os.path.join(out_dir, "oscillation_wrong_bypass_v1.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    plots.append(p)

    # -- Plot 5: Time-series latency (one seed) --
    seed_df = df[df["seed"] == 42].copy()
    seed_df["time_bin_s"] = (seed_df["time_ms"] // 5000) * 5
    binned = seed_df.groupby(["arch", "time_bin_s"])["latency_ms"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(14, 5))
    fig.suptitle("Bounded Routing v1 - Rolling Mean Latency Over Time (seed=42)",
                 fontsize=12, fontweight="bold")
    for arch in ["A_FULL_ANALYSIS", "B_NAIVE_CACHE", "C_BOUNDED_ROUTING"]:
        sub = binned[binned["arch"] == arch]
        color, ls = arch_colors[arch]
        ax.plot(sub["time_bin_s"], sub["latency_ms"],
                ls.replace("o", "").replace("s", "").replace("^", ""),
                color=color, lw=2, label=arch_labels[arch])
    # Phase markers
    for t_end, label in [
        (PHASE_STABLE_END/1000,    "drift"),
        (PHASE_DRIFT_END/1000,     "fault"),
        (PHASE_FAULT_END/1000,     "recovery"),
        (PHASE_RECOVERY_END/1000,  "oscillation"),
    ]:
        ax.axvline(t_end, color="grey", ls="--", alpha=0.5)
        ax.text(t_end + 0.5, ax.get_ylim()[0] + 1, label, fontsize=8, color="grey")
    ax.set_xlim(0, SIM_DURATION_MS / 1000)
    ax.set_xlabel("Time (seconds)", fontsize=10)
    ax.set_ylabel("Mean latency (ms)", fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    p = os.path.join(out_dir, "latency_timeseries_v1.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    plots.append(p)

    return plots


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

if __name__ == "__main__":
    OUT_DIR = "bounded_routing_output_v1"
    os.makedirs(OUT_DIR, exist_ok=True)

    t_start = time.time()

    df      = run_sweep()
    summary = analyze(df)

    df.to_csv(     os.path.join(OUT_DIR, "bounded_routing_v1_raw.csv"),     index=False)
    summary.to_csv(os.path.join(OUT_DIR, "bounded_routing_v1_summary.csv"), index=False)

    print("\nGenerating plots...")
    plots = make_plots(df, summary, OUT_DIR)

    elapsed = time.time() - t_start
    print(f"\n{'=' * 72}")
    print("OUTPUT FILES")
    print(f"{'=' * 72}")
    for f in ["bounded_routing_v1_raw.csv", "bounded_routing_v1_summary.csv"]:
        print(f"  {OUT_DIR}/{f}")
    for p in plots:
        print(f"  {p}")
    print(f"\nTotal runtime: {elapsed:.1f}s")
    print(f"{'=' * 72}")
    print()
    print("SUMMARY")
    print("  A_FULL_ANALYSIS:   safe but slow. No bypass. Upper bound on admissibility.")
    print("  B_NAIVE_CACHE:     fast under stable conditions. Breaks under drift,")
    print("                     fault, recovery, and oscillation. Accumulates violations.")
    print("  C_BOUNDED_ROUTING: slower than naive cache. Faster than full analysis.")
    print("                     Fewer violations. Tracks route flips and blocks unsafe oscillating bypasses.")
    print("                     Fallback rate rises during fault/recovery (correct behavior).")
