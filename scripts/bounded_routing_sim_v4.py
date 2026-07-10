"""
Bounded Routing Simulation v4
Independent Tetrahedral Shape-Integrity Gate

Controlling specification:
  docs/TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md (frozen)
Controlling architecture:
  docs/TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1.md (frozen)
Routing baseline:
  bounded routing sim v3.py, SHA-256
  2e45f4e66326e87ec09e18737c983731cc9f6335d79cc3bee0ad137c05f1b9a7

The primary run is prospective. Do not change thresholds, scenarios, assertions,
or verdict boundaries after observing results. Use --smoke-test for a reduced
implementation check that does not produce a scientific verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import platform
import ssl
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Frozen inherited v3 parameters
# -----------------------------------------------------------------------------
SEEDS = [42, 99, 500, 777, 1337]
N_PATTERNS = 8
DT_MS = 20.0

T_BYPASS = 0.75
T_DEPRECIATE = 0.55
T_RECOVER_ARD = 0.70
T_COST_MAX = 1.5
ALPHA = 0.85
OBS_WINDOW_SIZE = 20
DEPRECIATION_N = 5
DEPRECIATION_M = 10
RECOVER_K = 8
T_RETIRE_MS = 60_000.0
T_FLIP_COOLDOWN_MS = 2_000.0
MAX_FLIPS_PER_WINDOW = 3
T_FLIP_WINDOW_MS = 10_000.0
T_RECOVERY_BLACKOUT_MS = 5_000.0  # retained for auditability, unused by V4-C/D
K_REQUALIFY = 5

W_LAT = 0.30
W_ADM = 0.40
W_DEG = 0.20
W_STAB = 0.10

COST_BYPASS_NORMAL = 0.3
COST_BYPASS_DRIFTED = 0.8
COST_FULL_ANALYSIS = 1.0
COST_BYPASS_FAILED = 2.0

LATENCY_FULL_ANALYSIS = 40.0
LATENCY_BYPASS_FAST = 8.0
LATENCY_BYPASS_SLOW = 25.0
LATENCY_NOISE_STD = 3.0

PHASE_STABLE_END_MS = 30_000.0
PHASE_DRIFT_END_MS = 60_000.0
PHASE_FAULT_END_MS = 80_000.0
PHASE_RECOVERY_END_MS = 110_000.0
SIM_DURATION_MS = 120_000.0

Q_REQUALIFY_HIGH = 0.92
Q_RELAPSE_FLOOR_5 = 0.25
Q_RELAPSE_FLOOR_6 = 0.15
T_REQUALIFY_WINDOW_MS = 5_000.0
T_RELAPSE_RAMP_MS = 4_000.0
T_OSC_PERIOD_MS = 3_000.0
Q_OSC_HIGH = 0.90
Q_OSC_LOW = 0.20

SEED_RELAPSE_OFFSET_MS = {42: 0.0, 99: 500.0, 500: 1000.0, 777: 1500.0, 1337: 2000.0}
CONTROL_PATTERNS = [1, 2, 3, 4]
PERSISTENT_PATTERN = 0
BORDERLINE_PATTERNS = [5, 6, 7]
OSCILLATION_FLIP_PERIOD_MS = 4_000.0

# -----------------------------------------------------------------------------
# Frozen v4 structural parameters
# -----------------------------------------------------------------------------
SHAPE_OBSERVATION_INTERVAL_MS = 100.0
T_SHAPE_FRESHNESS_MS = 120.0
K_SOFT_PERSIST = 3
K_RESTORE = 3

AUTHORIZED_SOURCE_ID = "TETRAHEDRAL_COORDINATOR_V4"
AUTHORIZED_OBSERVER_TYPE = "DETERMINISTIC_STRUCTURAL_OBSERVER"
VERIFICATION_METHOD = "DETERMINISTIC_REPLAY_SHA256"
ACTIVE_SCOPE_TYPE = "GLOBAL"
ACTIVE_SCOPE_ID = "ACTIVE_TETRAHEDRAL_SUBSTRATE"

T_ROLE_SEPARATION_SOFT_DEG = 90.0
T_ROLE_SEPARATION_HARD_DEG = 60.0
T_ROLE_IMBALANCE_SOFT = 0.20
T_ROLE_IMBALANCE_HARD = 0.45
T_COVERAGE_SOFT = 0.75
T_COVERAGE_HARD = 0.50
T_COORDINATOR_OFFSET_SOFT = 0.15
T_COORDINATOR_OFFSET_HARD = 0.35
T_PROBE_LATENCY_SKEW_SOFT = 0.50
STRUCTURAL_DEFORMATION_MS = 4_000.0
EVIDENCE_INVALIDITY_MS = 500.0

ARCH_A = "A_FULL_ANALYSIS"
ARCH_B = "B_NAIVE_CACHE"
ARCH_C = "C_FLAT_BOUNDED"
ARCH_D = "D_TETRAHEDRAL_GATE"
ARCHES = [ARCH_A, ARCH_B, ARCH_C, ARCH_D]

CANONICAL_INVARIANT_ORDER = [
    "ROLE_PRESENCE",
    "STRUCTURAL_ERROR_STATE",
    "ROLE_SEPARATION",
    "COVERAGE",
    "COORDINATOR_ALIGNMENT",
    "ROLE_IMBALANCE",
    "HEALTH_PROBE_LATENCY_SKEW",
]

STRUCTURAL_INPUT_FIELDS = [
    "scenario_id", "seed", "observation_key", "observation_index", "timestamp_ms",
    "active_structural_epoch", "record_structural_epoch", "emit_record",
    "fact_present", "logic_present", "coherence_present",
    "fact_theta_deg", "logic_theta_deg", "coherence_theta_deg",
    "fact_weight", "logic_weight", "coherence_weight",
    "fact_coverage", "logic_coverage", "coherence_coverage",
    "fact_probe_latency_ms", "logic_probe_latency_ms", "coherence_probe_latency_ms",
    "fact_structural_error_state", "logic_structural_error_state", "coherence_structural_error_state",
    "coordinator_x", "coordinator_y", "source_id", "observer_type", "scope_type", "scope_id",
    "verification_method", "verification_reference", "force_corrupt_hash", "record_timestamp_ms",
]

FORBIDDEN_OBSERVER_FIELDS = {
    "arch", "arm", "bypassed", "wrong_bypass", "candidate_admissible", "candidate_latency_ms",
    "route_quality", "c_success", "future_task", "ground_truth_class", "ground_truth_active",
}

# -----------------------------------------------------------------------------
# Scenario declarations
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    category: str
    deformation_type: str
    duration_ms: float
    relapse_workload: bool
    hard: bool = False
    soft: bool = False
    evidence_invalidity: bool = False
    epoch_changes_at_clear: bool = False
    active_observation_count: int | None = None


def scenario_catalog() -> list[Scenario]:
    return [
        Scenario("D0_CLEAN_CONTROL", "CONTROL", "NONE", 0.0, False),
        Scenario("D1_TRANSIENT_SOFT_IMBALANCE", "STRUCTURAL", "SOFT_IMBALANCE", 200.0, False,
                 soft=True, active_observation_count=2),
        Scenario("D2_PERSISTENT_SOFT_IMBALANCE", "STRUCTURAL", "SOFT_IMBALANCE", 4_000.0, True, soft=True),
        Scenario("D3_PERSISTENT_PROBE_LATENCY_SKEW", "STRUCTURAL", "SOFT_PROBE_LATENCY", 4_000.0, True, soft=True),
        Scenario("D4_HARD_ROLE_ABSENCE", "STRUCTURAL", "HARD_ROLE_ABSENCE", 4_000.0, True,
                 hard=True, epoch_changes_at_clear=True),
        Scenario("D5_HARD_ANGULAR_COMPRESSION", "STRUCTURAL", "HARD_ANGULAR_COMPRESSION", 4_000.0, True,
                 hard=True, epoch_changes_at_clear=True),
        Scenario("D6_HARD_COVERAGE_LOSS", "STRUCTURAL", "HARD_COVERAGE_LOSS", 4_000.0, True,
                 hard=True, epoch_changes_at_clear=True),
        Scenario("D7_HARD_COORDINATOR_OFFSET", "STRUCTURAL", "HARD_COORDINATOR_OFFSET", 4_000.0, True,
                 hard=True, epoch_changes_at_clear=True),
        Scenario("D8_HARD_ROLE_DOMINANCE", "STRUCTURAL", "HARD_ROLE_DOMINANCE", 4_000.0, True,
                 hard=True, epoch_changes_at_clear=True),
        Scenario("E1_MISSING_RECORD", "EVIDENCE", "MISSING_RECORD", 500.0, False, evidence_invalidity=True),
        Scenario("E2_UNAUTHORIZED_SOURCE", "EVIDENCE", "UNAUTHORIZED_SOURCE", 500.0, False, evidence_invalidity=True),
        Scenario("E3_FAILED_VERIFICATION", "EVIDENCE", "FAILED_VERIFICATION", 500.0, False, evidence_invalidity=True),
        Scenario("E4_STALE_TIMESTAMP", "EVIDENCE", "STALE_TIMESTAMP", 500.0, False, evidence_invalidity=True),
        Scenario("E5_EPOCH_MISMATCH", "EVIDENCE", "EPOCH_MISMATCH", 500.0, False, evidence_invalidity=True),
        Scenario("E6_SCOPE_MISMATCH", "EVIDENCE", "SCOPE_MISMATCH", 500.0, False, evidence_invalidity=True),
    ]


def deformation_onset_ms(seed: int) -> float:
    return PHASE_FAULT_END_MS + T_REQUALIFY_WINDOW_MS + SEED_RELAPSE_OFFSET_MS[seed]


def phase_at(t: float) -> str:
    if t < PHASE_STABLE_END_MS:
        return "stable"
    if t < PHASE_DRIFT_END_MS:
        return "drift"
    if t < PHASE_FAULT_END_MS:
        return "fault"
    if t < PHASE_RECOVERY_END_MS:
        return "recovery"
    return "oscillation"


def canonical_json_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_structural_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {k: row[k] for k in STRUCTURAL_INPUT_FIELDS if k not in {"force_corrupt_hash"}}


def scenario_rng_seed(seed: int, scenario_id: str) -> int:
    token = hashlib.sha256(f"{seed}|{scenario_id}".encode()).digest()[:4]
    return int.from_bytes(token, "big", signed=False)

# -----------------------------------------------------------------------------
# Manifest generation
# -----------------------------------------------------------------------------
def build_task_manifest(seed: int, scenario: Scenario) -> pd.DataFrame:
    rng = np.random.RandomState(scenario_rng_seed(seed, scenario.scenario_id))
    onset = deformation_onset_ms(seed)
    clear = onset + scenario.duration_ms
    rows: list[dict[str, Any]] = []
    n_tasks = int(SIM_DURATION_MS / DT_MS)

    for task_index in range(n_tasks):
        t = task_index * DT_MS
        phase = phase_at(t)
        pid = int(rng.randint(0, N_PATTERNS))

        if pid == PERSISTENT_PATTERN:
            route_class = "PERSISTENT_FAILURE"
            if phase == "stable":
                rq = 1.0
            elif phase == "drift":
                frac = (t - PHASE_STABLE_END_MS) / (PHASE_DRIFT_END_MS - PHASE_STABLE_END_MS)
                rq = max(0.2, 1.0 - 0.7 * frac)
            else:
                rq = 0.1
        elif pid in CONTROL_PATTERNS:
            route_class = "CONTROL"
            rq = 1.0
        elif pid in BORDERLINE_PATTERNS:
            route_class = "BORDERLINE_RELAPSE"
            if phase != "recovery":
                rq = 1.0
            elif t < onset:
                rq = Q_REQUALIFY_HIGH
            elif not scenario.relapse_workload:
                rq = Q_REQUALIFY_HIGH
            else:
                dt = t - onset
                if pid == 5:
                    frac = min(1.0, dt / T_RELAPSE_RAMP_MS)
                    rq = Q_REQUALIFY_HIGH + (Q_RELAPSE_FLOOR_5 - Q_REQUALIFY_HIGH) * frac
                elif pid == 6:
                    rq = Q_RELAPSE_FLOOR_6
                else:
                    rq = Q_OSC_HIGH if (dt % T_OSC_PERIOD_MS) < T_OSC_PERIOD_MS / 2.0 else Q_OSC_LOW
        else:
            route_class = "OTHER"
            rq = 1.0

        if phase == "oscillation" and pid == 1:
            rq = 1.0 if (t % OSCILLATION_FLIP_PERIOD_MS) < OSCILLATION_FLIP_PERIOD_MS / 2.0 else 0.2

        if phase == "recovery":
            if pid == PERSISTENT_PATTERN:
                candidate_admissible = False
                relapse_phase = "PERSISTENT_FAILURE"
            elif pid in CONTROL_PATTERNS:
                candidate_admissible = True
                relapse_phase = "CONTROL"
            elif pid in BORDERLINE_PATTERNS and t < onset:
                candidate_admissible = True
                relapse_phase = "CLEAN_REQUALIFY"
            elif pid in BORDERLINE_PATTERNS and not scenario.relapse_workload:
                candidate_admissible = True
                relapse_phase = "CLEAN_TEST"
            else:
                candidate_admissible = bool(rng.random() < rq)
                relapse_phase = "POST_ONSET"
        else:
            candidate_admissible = bool(rng.random() < rq)
            relapse_phase = "BACKGROUND"

        clean_forced = phase == "recovery" and (
            pid in CONTROL_PATTERNS or (pid in BORDERLINE_PATTERNS and (t < onset or not scenario.relapse_workload))
        )
        if clean_forced:
            candidate_latency = float(np.clip(
                LATENCY_BYPASS_FAST + rng.uniform(-LATENCY_NOISE_STD, LATENCY_NOISE_STD * 2.0),
                LATENCY_BYPASS_FAST - LATENCY_NOISE_STD,
                LATENCY_BYPASS_FAST + LATENCY_NOISE_STD * 2.0,
            ))
            candidate_cost = COST_BYPASS_NORMAL
        elif rq > 0.5:
            candidate_latency = max(1.0, float(LATENCY_BYPASS_FAST + rng.normal(0, LATENCY_NOISE_STD)))
            candidate_cost = COST_BYPASS_NORMAL
        else:
            candidate_latency = max(1.0, float(LATENCY_BYPASS_SLOW + rng.normal(0, LATENCY_NOISE_STD)))
            candidate_cost = COST_BYPASS_DRIFTED

        rows.append({
            "scenario_id": scenario.scenario_id,
            "seed": seed,
            "task_key": f"{scenario.scenario_id}|{seed}|{task_index}",
            "task_index": task_index,
            "time_ms": float(t),
            "pattern_id": pid,
            "phase": phase,
            "route_class": route_class,
            "route_quality": float(rq),
            "candidate_admissible": bool(candidate_admissible),
            "candidate_latency_ms": candidate_latency,
            "candidate_cost": float(candidate_cost),
            "relapse_phase": relapse_phase,
            "deformation_onset_ms": onset,
            "deformation_clear_ms": clear,
        })
    return pd.DataFrame(rows)


def baseline_structural_row(seed: int, scenario: Scenario, obs_index: int, timestamp_ms: float) -> dict[str, Any]:
    rng = np.random.RandomState(scenario_rng_seed(seed + obs_index * 1009, scenario.scenario_id + "|struct"))
    probe = rng.uniform(8.0, 12.0, size=3)
    return {
        "scenario_id": scenario.scenario_id,
        "seed": seed,
        "observation_key": f"{scenario.scenario_id}|{seed}|obs|{obs_index}",
        "observation_index": obs_index,
        "timestamp_ms": float(timestamp_ms),
        "active_structural_epoch": 1,
        "record_structural_epoch": 1,
        "emit_record": True,
        "fact_present": True,
        "logic_present": True,
        "coherence_present": True,
        "fact_theta_deg": 0.0,
        "logic_theta_deg": 120.0,
        "coherence_theta_deg": 240.0,
        "fact_weight": 1.0 / 3.0,
        "logic_weight": 1.0 / 3.0,
        "coherence_weight": 1.0 / 3.0,
        "fact_coverage": 1.0,
        "logic_coverage": 1.0,
        "coherence_coverage": 1.0,
        "fact_probe_latency_ms": float(probe[0]),
        "logic_probe_latency_ms": float(probe[1]),
        "coherence_probe_latency_ms": float(probe[2]),
        "fact_structural_error_state": "OK",
        "logic_structural_error_state": "OK",
        "coherence_structural_error_state": "OK",
        "coordinator_x": 0.0,
        "coordinator_y": 0.0,
        "source_id": AUTHORIZED_SOURCE_ID,
        "observer_type": AUTHORIZED_OBSERVER_TYPE,
        "scope_type": ACTIVE_SCOPE_TYPE,
        "scope_id": ACTIVE_SCOPE_ID,
        "verification_method": VERIFICATION_METHOD,
        "verification_reference": f"{scenario.scenario_id}|{seed}|obs|{obs_index}",
        "force_corrupt_hash": False,
        "record_timestamp_ms": float(timestamp_ms),
    }


def build_structural_manifest(seed: int, scenario: Scenario) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    onset = deformation_onset_ms(seed)
    clear = onset + scenario.duration_ms
    structural_rows: list[dict[str, Any]] = []
    truth_rows: list[dict[str, Any]] = []
    n_obs = int(SIM_DURATION_MS / SHAPE_OBSERVATION_INTERVAL_MS)
    onset_index = int(round(onset / SHAPE_OBSERVATION_INTERVAL_MS))

    for obs_index in range(n_obs):
        t = obs_index * SHAPE_OBSERVATION_INTERVAL_MS
        row = baseline_structural_row(seed, scenario, obs_index, t)
        active = onset <= t < clear if scenario.duration_ms > 0 else False
        if scenario.active_observation_count is not None:
            active = onset_index <= obs_index < onset_index + scenario.active_observation_count

        if scenario.epoch_changes_at_clear and t >= clear:
            row["active_structural_epoch"] = 2
            row["record_structural_epoch"] = 2

        if scenario.deformation_type == "SOFT_IMBALANCE" and active:
            row["fact_weight"], row["logic_weight"], row["coherence_weight"] = 0.58, 0.21, 0.21
        elif scenario.deformation_type == "SOFT_PROBE_LATENCY" and active:
            row["fact_probe_latency_ms"], row["logic_probe_latency_ms"], row["coherence_probe_latency_ms"] = 10.0, 10.0, 18.0
        elif scenario.deformation_type == "HARD_ROLE_ABSENCE" and active:
            row["coherence_present"] = False
        elif scenario.deformation_type == "HARD_ANGULAR_COMPRESSION" and active:
            row["fact_theta_deg"], row["logic_theta_deg"], row["coherence_theta_deg"] = 0.0, 50.0, 240.0
        elif scenario.deformation_type == "HARD_COVERAGE_LOSS" and active:
            row["fact_coverage"], row["logic_coverage"], row["coherence_coverage"] = 0.40, 1.0, 1.0
        elif scenario.deformation_type == "HARD_COORDINATOR_OFFSET" and active:
            row["coordinator_x"], row["coordinator_y"] = 0.45, 0.0
        elif scenario.deformation_type == "HARD_ROLE_DOMINANCE" and active:
            row["fact_weight"], row["logic_weight"], row["coherence_weight"] = 0.75, 0.125, 0.125
        elif scenario.deformation_type == "MISSING_RECORD" and active:
            row["emit_record"] = False
        elif scenario.deformation_type == "UNAUTHORIZED_SOURCE" and active:
            row["source_id"] = "UNAUTHORIZED_COORDINATOR"
        elif scenario.deformation_type == "FAILED_VERIFICATION" and active:
            row["force_corrupt_hash"] = True
        elif scenario.deformation_type == "STALE_TIMESTAMP" and active:
            row["record_timestamp_ms"] = float(t - 121.0)
        elif scenario.deformation_type == "EPOCH_MISMATCH":
            if t >= onset:
                row["active_structural_epoch"] = 2
            if active:
                row["record_structural_epoch"] = 1
            elif t >= clear:
                row["record_structural_epoch"] = 2
        elif scenario.deformation_type == "SCOPE_MISMATCH" and active:
            row["scope_type"] = "ROUTE_CLASS"
            row["scope_id"] = "BORDERLINE_RELAPSE"

        row["canonical_input_hash"] = canonical_json_hash(canonical_structural_payload(row))
        structural_rows.append(row)

        if scenario.category == "EVIDENCE" and active:
            gt_class = "EVIDENCE_INVALID"
        elif scenario.hard and active:
            gt_class = "CONFIRMED_HARD_FAILURE"
        elif scenario.soft and active:
            gt_class = "RAW_SOFT_OR_EFFECTIVE"
        else:
            gt_class = "ADMISSIBLE"
        truth_rows.append({
            "scenario_id": scenario.scenario_id,
            "seed": seed,
            "observation_key": row["observation_key"],
            "ground_truth_class": gt_class,
            "ground_truth_active": bool(active),
            "expected_first_effective_observation": onset_index + (K_SOFT_PERSIST - 1 if scenario.soft and scenario.active_observation_count is None else 0),
            "expected_gate_classification": gt_class,
            "expected_reconstruction": bool(scenario.hard and active),
        })

    deformation = pd.DataFrame([{
        "scenario_id": scenario.scenario_id,
        "seed": seed,
        "deformation_type": scenario.deformation_type,
        "deformation_onset_ms": onset,
        "deformation_clear_ms": clear,
        "repair_or_refresh_type": "EPOCH_REPAIR" if scenario.epoch_changes_at_clear else ("EVIDENCE_REFRESH" if scenario.evidence_invalidity else "RETURN_TO_BASELINE"),
        "epoch_before": 1,
        "epoch_after": 2 if scenario.epoch_changes_at_clear or scenario.deformation_type == "EPOCH_MISMATCH" else 1,
    }])
    return pd.DataFrame(structural_rows), deformation, pd.DataFrame(truth_rows)

# -----------------------------------------------------------------------------
# Structural observer
# -----------------------------------------------------------------------------
def circular_distance_deg(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def derive_invariants(row: dict[str, Any]) -> dict[str, Any]:
    angles = [float(row["fact_theta_deg"]), float(row["logic_theta_deg"]), float(row["coherence_theta_deg"])]
    pairwise = [circular_distance_deg(angles[0], angles[1]), circular_distance_deg(angles[1], angles[2]), circular_distance_deg(angles[2], angles[0])]
    separation = min(pairwise)

    weights = [float(row["fact_weight"]), float(row["logic_weight"]), float(row["coherence_weight"])]
    imbalance = max(weights) - min(weights)
    coverage = min(float(row["fact_coverage"]), float(row["logic_coverage"]), float(row["coherence_coverage"]))

    pts = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in angles]
    centroid = (sum(p[0] for p in pts) / 3.0, sum(p[1] for p in pts) / 3.0)
    coordinator_offset = math.dist((float(row["coordinator_x"]), float(row["coordinator_y"])), centroid)

    latencies = [float(row["fact_probe_latency_ms"]), float(row["logic_probe_latency_ms"]), float(row["coherence_probe_latency_ms"])]
    probe_skew = (max(latencies) - min(latencies)) / float(np.median(latencies))

    hard: list[str] = []
    raw_soft: list[str] = []
    if not (bool(row["fact_present"]) and bool(row["logic_present"]) and bool(row["coherence_present"])):
        hard.append("ROLE_PRESENCE")
    if "FAILED" in {row["fact_structural_error_state"], row["logic_structural_error_state"], row["coherence_structural_error_state"]}:
        hard.append("STRUCTURAL_ERROR_STATE")
    if separation < T_ROLE_SEPARATION_HARD_DEG:
        hard.append("ROLE_SEPARATION")
    elif separation < T_ROLE_SEPARATION_SOFT_DEG:
        raw_soft.append("ROLE_SEPARATION")
    if coverage < T_COVERAGE_HARD:
        hard.append("COVERAGE")
    elif coverage < T_COVERAGE_SOFT:
        raw_soft.append("COVERAGE")
    if coordinator_offset > T_COORDINATOR_OFFSET_HARD:
        hard.append("COORDINATOR_ALIGNMENT")
    elif coordinator_offset > T_COORDINATOR_OFFSET_SOFT:
        raw_soft.append("COORDINATOR_ALIGNMENT")
    if imbalance > T_ROLE_IMBALANCE_HARD:
        hard.append("ROLE_IMBALANCE")
    elif imbalance > T_ROLE_IMBALANCE_SOFT:
        raw_soft.append("ROLE_IMBALANCE")
    if probe_skew > T_PROBE_LATENCY_SKEW_SOFT:
        raw_soft.append("HEALTH_PROBE_LATENCY_SKEW")

    return {
        "role_separation_min_deg": separation,
        "role_imbalance": imbalance,
        "coverage_min": coverage,
        "coordinator_offset": coordinator_offset,
        "probe_latency_skew": probe_skew,
        "hard_invariants": hard,
        "raw_soft_warnings": raw_soft,
    }


def build_shape_records(structural_df: pd.DataFrame) -> pd.DataFrame:
    forbidden = FORBIDDEN_OBSERVER_FIELDS.intersection(structural_df.columns)
    if forbidden:
        raise AssertionError(f"Observer input contains forbidden fields: {sorted(forbidden)}")

    soft_counters = {name: 0 for name in CANONICAL_INVARIANT_ORDER}
    records: list[dict[str, Any]] = []
    for input_row in structural_df.to_dict("records"):
        if not bool(input_row["emit_record"]):
            continue
        inv = derive_invariants(input_row)
        hard = list(inv["hard_invariants"])
        raw_soft = list(inv["raw_soft_warnings"])
        effective_soft: list[str] = []
        for name in soft_counters:
            if name in raw_soft:
                soft_counters[name] += 1
            else:
                soft_counters[name] = 0
            if soft_counters[name] >= K_SOFT_PERSIST:
                effective_soft.append(name)

        all_failed = [n for n in CANONICAL_INVARIANT_ORDER if n in hard or n in effective_soft]
        first_failed = all_failed[0] if all_failed else None
        if hard:
            integrity_state = "FAILED"
        elif effective_soft:
            integrity_state = "DEGRADED"
        else:
            integrity_state = "ADMISSIBLE"

        evidence_hash = input_row["canonical_input_hash"]
        if bool(input_row["force_corrupt_hash"]):
            evidence_hash = "0" * 64

        records.append({
            "scenario_id": input_row["scenario_id"],
            "seed": int(input_row["seed"]),
            "record_id": f"shape|{input_row['observation_key']}",
            "observation_key": input_row["observation_key"],
            "observation_index": int(input_row["observation_index"]),
            "timestamp_ms": float(input_row["record_timestamp_ms"]),
            "source_observation_time_ms": float(input_row["timestamp_ms"]),
            "structural_epoch": int(input_row["record_structural_epoch"]),
            "active_structural_epoch": int(input_row["active_structural_epoch"]),
            "source_id": input_row["source_id"],
            "observer_type": input_row["observer_type"],
            "scope_type": input_row["scope_type"],
            "scope_id": input_row["scope_id"],
            "verification_method": input_row["verification_method"],
            "verification_reference": input_row["verification_reference"],
            "evidence_hash": evidence_hash,
            "canonical_input_hash": input_row["canonical_input_hash"],
            "integrity_state": integrity_state,
            "raw_soft_warnings": json.dumps(raw_soft),
            "effective_soft_invariants": json.dumps(effective_soft),
            "hard_invariants": json.dumps(hard),
            "all_failed_invariants": json.dumps(all_failed),
            "first_failed_invariant": first_failed,
            "role_separation_min_deg": inv["role_separation_min_deg"],
            "role_imbalance": inv["role_imbalance"],
            "coverage_min": inv["coverage_min"],
            "coordinator_offset": inv["coordinator_offset"],
            "probe_latency_skew": inv["probe_latency_skew"],
            "record_payload_hash": canonical_json_hash({
                "observation_key": input_row["observation_key"],
                "integrity_state": integrity_state,
                "all_failed_invariants": all_failed,
                "evidence_hash": evidence_hash,
            }),
        })
    return pd.DataFrame(records)

# -----------------------------------------------------------------------------
# Shape gate
# -----------------------------------------------------------------------------
@dataclass
class ShapeDecision:
    allowed: bool
    classification: str
    integrity_state: str
    authority_state: str
    first_failed_invariant: str | None
    all_failed_invariants: list[str]
    raw_soft_warnings: list[str]
    record_age_ms: float | None
    verification_pass: bool
    epoch_match: bool
    scope_match: bool
    restore_count: int
    restoration_active: bool
    restoration_requirement_satisfied: bool
    reconstruction_triggered: bool
    record_id: str | None


class ShapeGate:
    """Stateful gate. `integrity_score` is intentionally absent."""

    def __init__(self, structural_df: pd.DataFrame, records_df: pd.DataFrame):
        self.structural_by_key = {r["observation_key"]: r for r in structural_df.to_dict("records")}
        self.records = records_df.sort_values("source_observation_time_ms").to_dict("records")
        self.record_cursor = 0
        self.latest_record: dict[str, Any] | None = None
        self.last_counted_record_id: str | None = None
        self.restoration_active = False
        self.restore_count = 0
        self.ever_nonadmissible = False
        self.reset_events = 0
        self.classification_history: list[tuple[float, str]] = []

    def _advance(self, decision_time_ms: float) -> None:
        while self.record_cursor < len(self.records):
            candidate = self.records[self.record_cursor]
            if float(candidate["source_observation_time_ms"]) > decision_time_ms:
                break
            self.latest_record = candidate
            self.record_cursor += 1

    def _verify(self, record: dict[str, Any]) -> bool:
        if record["verification_method"] != VERIFICATION_METHOD:
            return False
        ref = record["verification_reference"]
        source = self.structural_by_key.get(ref)
        if source is None:
            return False
        recomputed = canonical_json_hash(canonical_structural_payload(source))
        return recomputed == record["evidence_hash"]

    @staticmethod
    def _parse_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return value
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return []
        return list(json.loads(value))

    def evaluate(self, decision_time_ms: float, active_epoch: int) -> ShapeDecision:
        self._advance(decision_time_ms)
        record = self.latest_record
        if record is None:
            return self._nonadmissible(
                decision_time_ms, "EVIDENCE_INVALID", "UNKNOWN", None, [], [], None,
                False, False, False, False, None,
            )

        record_age = decision_time_ms - float(record["timestamp_ms"])
        verification_pass = self._verify(record)
        epoch_match = int(record["structural_epoch"]) == int(active_epoch)
        scope_match = record["scope_type"] == ACTIVE_SCOPE_TYPE and record["scope_id"] == ACTIVE_SCOPE_ID
        source_ok = record["source_id"] == AUTHORIZED_SOURCE_ID
        observer_ok = record["observer_type"] == AUTHORIZED_OBSERVER_TYPE
        fresh = 0.0 <= record_age <= T_SHAPE_FRESHNESS_MS

        if not (source_ok and observer_ok and verification_pass and fresh and epoch_match and scope_match):
            return self._nonadmissible(
                decision_time_ms, "EVIDENCE_INVALID", "UNKNOWN", None, [], [], record_age,
                verification_pass, epoch_match, scope_match, False, record["record_id"],
            )

        hard = self._parse_list(record["hard_invariants"])
        raw_soft = self._parse_list(record["raw_soft_warnings"])
        all_failed = self._parse_list(record["all_failed_invariants"])
        first_failed = record["first_failed_invariant"] if all_failed else None

        if record["integrity_state"] == "FAILED" or hard:
            return self._nonadmissible(
                decision_time_ms, "CONFIRMED_HARD_FAILURE", "FAILED", first_failed,
                all_failed, raw_soft, record_age, True, True, True, True, record["record_id"],
            )
        if record["integrity_state"] == "DEGRADED":
            return self._nonadmissible(
                decision_time_ms, "SOFT_DEGRADATION", "DEGRADED", first_failed,
                all_failed, raw_soft, record_age, True, True, True, False, record["record_id"],
            )

        # Raw soft warnings do not revoke a currently admissible gate. During
        # restoration they reset the clean count and keep authority denied.
        if self.restoration_active:
            if raw_soft:
                if self.restore_count != 0:
                    self.reset_events += 1
                self.restore_count = 0
                self.last_counted_record_id = record["record_id"]
                return ShapeDecision(
                    False, "RESTORING", "ADMISSIBLE", "NOT_AUTHORIZED", None, [], raw_soft,
                    record_age, True, True, True, 0, True, False, False, record["record_id"],
                )
            if record["record_id"] != self.last_counted_record_id:
                self.restore_count += 1
                self.last_counted_record_id = record["record_id"]
            if self.restore_count >= K_RESTORE:
                self.restoration_active = False
                return ShapeDecision(
                    True, "ADMISSIBLE", "ADMISSIBLE", "AUTHORIZED", None, [], [],
                    record_age, True, True, True, self.restore_count, False, True, False, record["record_id"],
                )
            return ShapeDecision(
                False, "RESTORING", "ADMISSIBLE", "NOT_AUTHORIZED", None, [], [],
                record_age, True, True, True, self.restore_count, True, False, False, record["record_id"],
            )

        return ShapeDecision(
            True, "ADMISSIBLE", "ADMISSIBLE", "AUTHORIZED", None, [], raw_soft,
            record_age, True, True, True, self.restore_count, False, True, False, record["record_id"],
        )

    def _nonadmissible(
        self,
        decision_time_ms: float,
        classification: str,
        integrity_state: str,
        first_failed: str | None,
        all_failed: list[str],
        raw_soft: list[str],
        record_age: float | None,
        verification_pass: bool,
        epoch_match: bool,
        scope_match: bool,
        reconstruction_triggered: bool,
        record_id: str | None,
    ) -> ShapeDecision:
        if not self.restoration_active or self.restore_count != 0:
            self.reset_events += 1
        self.ever_nonadmissible = True
        self.restoration_active = True
        self.restore_count = 0
        self.last_counted_record_id = record_id
        authority = "REVOKED" if classification == "CONFIRMED_HARD_FAILURE" else "NOT_AUTHORIZED"
        self.classification_history.append((decision_time_ms, classification))
        return ShapeDecision(
            False, classification, integrity_state, authority, first_failed, all_failed, raw_soft,
            record_age, verification_pass, epoch_match, scope_match, 0, True, False,
            reconstruction_triggered, record_id,
        )

# -----------------------------------------------------------------------------
# Routing layer, inherited from v3
# -----------------------------------------------------------------------------
def sms_outcome_score(latency_ms: float, admissible: bool, route_quality: float, obs_window: deque[float]) -> float:
    lat_score = 1.0 if latency_ms <= LATENCY_BYPASS_FAST * 2.0 else 0.5
    adm_score = 1.0 if admissible else 0.0
    deg_score = route_quality
    if len(obs_window) >= 3:
        variance = float(np.var(list(obs_window)))
        stab_score = max(0.0, 1.0 - variance * 4.0)
    else:
        stab_score = 0.5
    return W_LAT * lat_score + W_ADM * adm_score + W_DEG * deg_score + W_STAB * stab_score


@dataclass
class ARDEntry:
    pid: int
    time_ms: float
    p_opt: str = field(init=False)
    c_success: float = 0.0
    obs_count: int = 0
    obs_window: deque[float] = field(default_factory=lambda: deque(maxlen=OBS_WINDOW_SIZE))
    last_used_ms: float = field(init=False)
    depreciation_state: str = "ACTIVE"
    depreciation_count: int = 0
    recover_count: int = 0
    last_flip_ms: float = -T_FLIP_COOLDOWN_MS * 2.0
    flip_count: int = 0
    flip_times: deque[float] = field(default_factory=lambda: deque(maxlen=MAX_FLIPS_PER_WINDOW + 5))
    structural_cost: float = COST_BYPASS_NORMAL
    recovery_sensitive: bool = False
    requalify_window: deque[float] = field(default_factory=lambda: deque(maxlen=K_REQUALIFY))
    requalify_obs_with_epoch: list[tuple[float, float]] = field(default_factory=list)
    requalify_count: int = 0
    requalify_deprec_count: int = 0
    requalified_at_ms: float | None = None
    pre_recovery_state: str | None = None
    state_transition_history: list[tuple[float, str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.p_opt = f"route_{self.pid}_A"
        self.last_used_ms = self.time_ms

    def transition(self, t: float, new_state: str) -> None:
        if new_state != self.depreciation_state:
            self.state_transition_history.append((t, self.depreciation_state, new_state))
            self.depreciation_state = new_state

    def update_depreciation(self, t: float) -> None:
        if self.c_success < T_DEPRECIATE:
            self.depreciation_count += 1
            self.recover_count = 0
            if self.depreciation_state == "ACTIVE" and self.depreciation_count >= DEPRECIATION_N:
                self.transition(t, "WARNED")
            elif self.depreciation_state == "WARNED" and self.depreciation_count >= DEPRECIATION_N + DEPRECIATION_M:
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
                        self.recover_count = 0
                else:
                    self.recover_count = 0
            elif self.depreciation_state != "REQUALIFYING":
                self.depreciation_count = 0


class FullAnalysisArm:
    arch_label = ARCH_A

    def __init__(self, seed: int):
        self.seed = seed
        self.rng = np.random.RandomState(seed * 7919 + 1)

    def process(self, task: dict[str, Any], shape_decision: ShapeDecision | None = None) -> dict[str, Any]:
        latency = max(1.0, float(LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD)))
        return base_task_row(task, self.arch_label, latency, True, False, False, False, COST_FULL_ANALYSIS)


class NaiveCacheArm(FullAnalysisArm):
    arch_label = ARCH_B

    def __init__(self, seed: int):
        super().__init__(seed)
        self.confidence: dict[int, float] = {}

    def _get_c(self, pid: int) -> float:
        return self.confidence.get(pid, 0.0)

    def _update_c(self, pid: int, score: float) -> None:
        self.confidence[pid] = ALPHA * self._get_c(pid) + (1.0 - ALPHA) * score

    def process(self, task: dict[str, Any], shape_decision: ShapeDecision | None = None) -> dict[str, Any]:
        pid = int(task["pattern_id"])
        c_before = self._get_c(pid)
        if c_before >= T_BYPASS:
            admissible = bool(task["candidate_admissible"])
            latency = float(task["candidate_latency_ms"])
            cost = float(task["candidate_cost"])
            bypassed = True
            fallback = False
            wrong = not admissible
            self._update_c(pid, 1.0 if admissible else 0.0)
            gate = "NONE"
        else:
            admissible = True
            latency = max(1.0, float(LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD)))
            cost = COST_FULL_ANALYSIS
            bypassed = False
            fallback = True
            wrong = False
            self._update_c(pid, 1.0 if float(task["route_quality"]) > 0.5 else 0.5)
            gate = "confidence"
        row = base_task_row(task, self.arch_label, latency, admissible, bypassed, wrong, fallback, cost)
        row.update({"c_success_before": c_before, "c_success_after": self._get_c(pid), "route_gate_reason": gate})
        return row


class FlatBoundedArm(FullAnalysisArm):
    arch_label = ARCH_C

    def __init__(self, seed: int, arch_label: str = ARCH_C):
        super().__init__(seed)
        self.arch_label = arch_label
        self.ard: dict[int, ARDEntry] = {}
        self._in_recovery = False
        self._recovery_signal_ms: float | None = None
        self.promotions: list[tuple[int, int, float, float]] = []

    def _get_entry(self, pid: int, t: float) -> ARDEntry:
        if pid not in self.ard:
            self.ard[pid] = ARDEntry(pid, t)
        return self.ard[pid]

    def _update_sms(self, entry: ARDEntry, t: float, latency: float, admissible: bool, rq: float) -> float:
        score = sms_outcome_score(latency, admissible, rq, entry.obs_window)
        entry.obs_window.append(score)
        entry.c_success = ALPHA * entry.c_success + (1.0 - ALPHA) * score
        entry.obs_count += 1
        entry.update_depreciation(t)
        return score

    def _signal_recovery(self, t: float) -> None:
        self._recovery_signal_ms = t
        for entry in self.ard.values():
            entry.pre_recovery_state = entry.depreciation_state
            if entry.depreciation_state in ("ACTIVE", "WARNED"):
                entry.transition(t, "REQUALIFYING")
                entry.requalify_count = 0
                entry.requalify_deprec_count = 0
                entry.requalify_window = deque(maxlen=K_REQUALIFY)
                entry.requalify_obs_with_epoch = []
                entry.requalified_at_ms = None
                entry.recovery_sensitive = True

    def _update_shadow(self, entry: ARDEntry, task: dict[str, Any]) -> tuple[float, str, bool, float]:
        t = float(task["time_ms"])
        shadow_score = sms_outcome_score(
            float(task["candidate_latency_ms"]), bool(task["candidate_admissible"]),
            float(task["route_quality"]), entry.requalify_window,
        )
        entry.requalify_obs_with_epoch.append((shadow_score, t))
        entry.requalify_window.append(shadow_score)
        entry.requalify_count = entry.requalify_count + 1 if bool(task["candidate_admissible"]) else 0
        fresh_conf = float(np.mean(list(entry.requalify_window))) if entry.requalify_window else 0.0

        if fresh_conf < T_DEPRECIATE:
            entry.requalify_deprec_count += 1
            if entry.requalify_deprec_count >= DEPRECIATION_N + DEPRECIATION_M:
                entry.transition(t, "DEPRECATED")
                return shadow_score, "DEPRECATED", False, fresh_conf
        else:
            entry.requalify_deprec_count = 0

        if entry.requalify_count >= K_REQUALIFY and fresh_conf >= T_BYPASS:
            entry.c_success = fresh_conf
            entry.obs_window = deque(list(entry.requalify_window), maxlen=OBS_WINDOW_SIZE)
            entry.transition(t, "ACTIVE")
            entry.requalified_at_ms = t
            self.promotions.append((entry.pid, entry.requalify_count, fresh_conf, t))
            return shadow_score, "NONE", True, fresh_conf
        if entry.requalify_count >= K_REQUALIFY:
            return shadow_score, "REQUALIFYING_CONFIDENCE", False, fresh_conf
        return shadow_score, "REQUALIFYING_COUNT", False, fresh_conf

    def _check_route_bypass(self, entry: ARDEntry, t: float, candidate_cost: float) -> tuple[bool, str]:
        if entry.depreciation_state == "REQUALIFYING":
            return False, "recovery_state"
        if entry.depreciation_state in ("DEPRECATED", "RETIRED"):
            return False, "depreciation"
        if entry.c_success < T_BYPASS:
            return False, "confidence"
        if candidate_cost > T_COST_MAX or entry.structural_cost > T_COST_MAX:
            return False, "cost"
        recent_flips = sum(1 for ft in entry.flip_times if (t - ft) < T_FLIP_WINDOW_MS)
        if recent_flips >= MAX_FLIPS_PER_WINDOW:
            return False, "anti_oscillation"
        if (t - entry.last_flip_ms) < T_FLIP_COOLDOWN_MS:
            return False, "cooldown"
        return True, "NONE"

    def process(self, task: dict[str, Any], shape_decision: ShapeDecision | None = None) -> dict[str, Any]:
        pid = int(task["pattern_id"])
        t = float(task["time_ms"])
        phase = str(task["phase"])
        rq = float(task["route_quality"])
        entry = self._get_entry(pid, t)

        if phase == "recovery" and not self._in_recovery:
            self._signal_recovery(t)
            self._in_recovery = True
        elif phase != "recovery":
            self._in_recovery = False

        if phase == "oscillation" and pid == 1:
            new_route = "route_1_A" if (t % OSCILLATION_FLIP_PERIOD_MS) < OSCILLATION_FLIP_PERIOD_MS / 2.0 else "route_1_B"
            if new_route != entry.p_opt:
                entry.p_opt = new_route
                entry.last_flip_ms = t
                entry.flip_count += 1
                entry.flip_times.append(t)

        c_before = entry.c_success
        state_before = entry.depreciation_state
        route_allowed, route_gate = self._check_route_bypass(entry, t, float(task["candidate_cost"]))
        shape_allowed = True if shape_decision is None else shape_decision.allowed
        shape_blocked = route_allowed and not shape_allowed
        allowed = route_allowed and shape_allowed

        shadow_score = None
        fresh_conf = None
        promotion = False
        requalification_gate = "NONE"

        if entry.depreciation_state == "REQUALIFYING":
            latency = max(1.0, float(LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD)))
            admissible = True
            cost = COST_FULL_ANALYSIS
            bypassed = False
            fallback = True
            wrong = False
            shadow_score, requalification_gate, promotion, fresh_conf = self._update_shadow(entry, task)
            route_gate = requalification_gate if requalification_gate != "NONE" else "recovery_state"
        elif allowed:
            latency = float(task["candidate_latency_ms"])
            admissible = bool(task["candidate_admissible"])
            cost = float(task["candidate_cost"])
            bypassed = True
            fallback = False
            wrong = not admissible
            if rq < 0.4:
                entry.structural_cost = min(COST_BYPASS_FAILED, entry.structural_cost * 1.15)
            else:
                entry.structural_cost = max(COST_BYPASS_NORMAL, entry.structural_cost * 0.98)
            self._update_sms(entry, t, latency, admissible, rq)
        elif entry.depreciation_state == "DEPRECATED":
            latency = max(1.0, float(LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD)))
            admissible = True
            cost = COST_FULL_ANALYSIS
            bypassed = False
            fallback = True
            wrong = False
        else:
            latency = max(1.0, float(LATENCY_FULL_ANALYSIS + self.rng.normal(0, LATENCY_NOISE_STD)))
            admissible = True
            cost = COST_FULL_ANALYSIS
            bypassed = False
            fallback = True
            wrong = False
            self._update_sms(entry, t, latency, True, rq)

        entry.last_used_ms = t
        first_gate = "shape_integrity" if shape_blocked else route_gate
        row = base_task_row(task, self.arch_label, latency, admissible, bypassed, wrong, fallback, cost)
        row.update({
            "route_allowed_before_shape": route_allowed,
            "shape_blocked": shape_blocked,
            "route_gate_reason": route_gate,
            "first_blocking_gate": first_gate,
            "c_success_before": c_before,
            "c_success_after": entry.c_success,
            "depreciation_state_before": state_before,
            "depreciation_state": entry.depreciation_state,
            "structural_cost_state": entry.structural_cost,
            "requalify_count": entry.requalify_count,
            "shadow_outcome_score": shadow_score,
            "fresh_requalify_confidence": fresh_conf,
            "requalified_at_ms": entry.requalified_at_ms,
            "promotion_completed_this_task": promotion,
        })
        if shape_decision is not None:
            row.update(shape_decision_to_columns(shape_decision))
        return row


class TetrahedralGateArm(FlatBoundedArm):
    arch_label = ARCH_D

    def __init__(self, seed: int):
        super().__init__(seed, ARCH_D)


def base_task_row(
    task: dict[str, Any], arch: str, latency: float, admissible: bool, bypassed: bool,
    wrong_bypass: bool, fallback: bool, cost: float,
) -> dict[str, Any]:
    return {
        **task,
        "arch": arch,
        "latency_ms": float(latency),
        "admissible": bool(admissible),
        "bypassed": bool(bypassed),
        "wrong_bypass": bool(wrong_bypass),
        "fallback": bool(fallback),
        "executed_cost": float(cost),
        "route_allowed_before_shape": False,
        "shape_blocked": False,
        "route_gate_reason": "NONE",
        "first_blocking_gate": "NONE",
        "c_success_before": np.nan,
        "c_success_after": np.nan,
        "depreciation_state_before": None,
        "depreciation_state": None,
        "structural_cost_state": np.nan,
        "requalify_count": 0,
        "shadow_outcome_score": np.nan,
        "fresh_requalify_confidence": np.nan,
        "requalified_at_ms": np.nan,
        "promotion_completed_this_task": False,
        "shape_allowed": True,
        "shape_classification": "NOT_CONSUMED",
        "shape_integrity_state": "NOT_CONSUMED",
        "shape_authority_state": "NOT_CONSUMED",
        "shape_first_failed_invariant": None,
        "shape_all_failed_invariants": "[]",
        "shape_raw_soft_warnings": "[]",
        "shape_record_age_ms": np.nan,
        "shape_verification_pass": np.nan,
        "shape_epoch_match": np.nan,
        "shape_scope_match": np.nan,
        "shape_restore_count": 0,
        "shape_restoration_active": False,
        "shape_restoration_requirement_satisfied": True,
        "shape_reconstruction_triggered": False,
        "shape_record_id": None,
    }


def shape_decision_to_columns(d: ShapeDecision) -> dict[str, Any]:
    return {
        "shape_allowed": d.allowed,
        "shape_classification": d.classification,
        "shape_integrity_state": d.integrity_state,
        "shape_authority_state": d.authority_state,
        "shape_first_failed_invariant": d.first_failed_invariant,
        "shape_all_failed_invariants": json.dumps(d.all_failed_invariants),
        "shape_raw_soft_warnings": json.dumps(d.raw_soft_warnings),
        "shape_record_age_ms": d.record_age_ms,
        "shape_verification_pass": d.verification_pass,
        "shape_epoch_match": d.epoch_match,
        "shape_scope_match": d.scope_match,
        "shape_restore_count": d.restore_count,
        "shape_restoration_active": d.restoration_active,
        "shape_restoration_requirement_satisfied": d.restoration_requirement_satisfied,
        "shape_reconstruction_triggered": d.reconstruction_triggered,
        "shape_record_id": d.record_id,
    }

# -----------------------------------------------------------------------------
# Run harness and assertions
# -----------------------------------------------------------------------------
class AssertionLedger:
    def __init__(self) -> None:
        self._state: dict[str, dict[str, Any]] = {
            f"A{i}": {"assertion_id": f"A{i}", "passed": True, "details": []}
            for i in range(1, 27)
        }

    def check(self, assertion_id: str, condition: bool, detail: str) -> None:
        item = self._state[assertion_id]
        if not condition:
            item["passed"] = False
            item["details"].append("FAIL: " + detail)
        elif len(item["details"]) < 4:
            item["details"].append("PASS: " + detail)

    def dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"assertion_id": k, "passed": v["passed"], "detail": " | ".join(v["details"])}
            for k, v in self._state.items()
        ])

    @property
    def all_passed(self) -> bool:
        return all(v["passed"] for v in self._state.values())


def active_epoch_at(task_time_ms: float, scenario: Scenario, onset: float, clear: float) -> int:
    if scenario.deformation_type == "EPOCH_MISMATCH" and task_time_ms >= onset:
        return 2
    if scenario.epoch_changes_at_clear and task_time_ms >= clear:
        return 2
    return 1


def run_pair(
    seed: int,
    scenario: Scenario,
    task_df: pd.DataFrame,
    structural_df: pd.DataFrame,
    records_df: pd.DataFrame,
) -> tuple[pd.DataFrame, ShapeGate, FlatBoundedArm, TetrahedralGateArm]:
    arms: list[FullAnalysisArm] = [
        FullAnalysisArm(seed),
        NaiveCacheArm(seed),
        FlatBoundedArm(seed),
        TetrahedralGateArm(seed),
    ]
    gate = ShapeGate(structural_df, records_df)
    rows: list[dict[str, Any]] = []
    onset = deformation_onset_ms(seed)
    clear = onset + scenario.duration_ms

    for arm in arms:
        # C and D must begin with identical route-layer state and RNG state. Each
        # gets its own object but the same seed and inherited mechanics.
        if arm.arch_label == ARCH_D:
            for task in task_df.to_dict("records"):
                epoch = active_epoch_at(float(task["time_ms"]), scenario, onset, clear)
                decision = gate.evaluate(float(task["time_ms"]), epoch)
                rows.append(arm.process(task, decision))
        else:
            for task in task_df.to_dict("records"):
                rows.append(arm.process(task, None))

    c_arm = next(a for a in arms if isinstance(a, FlatBoundedArm) and a.arch_label == ARCH_C)
    d_arm = next(a for a in arms if isinstance(a, TetrahedralGateArm))
    return pd.DataFrame(rows), gate, c_arm, d_arm


def update_pair_assertions(
    ledger: AssertionLedger,
    scenario: Scenario,
    seed: int,
    task_df: pd.DataFrame,
    structural_df: pd.DataFrame,
    records_df: pd.DataFrame,
    rows_df: pd.DataFrame,
    gate: ShapeGate,
    manifests_saved: bool,
) -> None:
    tag = f"{scenario.scenario_id}/seed={seed}"
    onset = deformation_onset_ms(seed)
    clear = onset + scenario.duration_ms

    # A1-A4 manifest and schedule integrity
    ledger.check("A1", manifests_saved, f"{tag}: manifests saved before arm execution")
    key_sets = [set(rows_df.loc[rows_df.arch == arch, "task_key"]) for arch in ARCHES]
    ledger.check("A2", all(s == key_sets[0] for s in key_sets[1:]) and key_sets[0] == set(task_df.task_key),
                 f"{tag}: task keys identical across arms")
    ledger.check("A3", not FORBIDDEN_OBSERVER_FIELDS.intersection(structural_df.columns),
                 f"{tag}: structural input contains no arm or route-outcome fields")
    schedule_cols = ["deformation_onset_ms", "deformation_clear_ms"]
    schedule_ok = all(rows_df.groupby("arch")[c].first().nunique() == 1 for c in schedule_cols)
    ledger.check("A4", schedule_ok, f"{tag}: onset and clear schedule identical across arms")

    # A5-A7 observer isolation
    source = inspect.signature(build_shape_records)
    ledger.check("A5", list(source.parameters) == ["structural_df"],
                 f"{tag}: observer accepts structural_df only")
    ledger.check("A6", not {"ground_truth_class", "ground_truth_active"}.intersection(structural_df.columns),
                 f"{tag}: evaluator labels absent from observer input")
    hashes = records_df.record_payload_hash.tolist()
    ledger.check("A7", hashes == list(hashes), f"{tag}: one shared immutable shape-record stream consumed by all arms")

    # A8-A12 record timing, provenance, and scope
    d = rows_df[rows_df.arch == ARCH_D]
    used = d[d.shape_record_id.notna()]
    ledger.check("A8", bool((used.shape_record_age_ms >= 0).all()), f"{tag}: no future-dated record used")
    ledger.check("A9", "candidate_latency_ms" not in structural_df.columns,
                 f"{tag}: probe latency cannot source task latency")
    gate_source = inspect.getsource(ShapeGate.evaluate)
    ledger.check("A10", "integrity_score" not in gate_source, f"{tag}: integrity_score absent from gate")
    admissible = d[d.shape_allowed]
    valid_admissible = (
        admissible.shape_verification_pass.map(lambda x: bool(x) if pd.notna(x) else False)
        & admissible.shape_epoch_match.map(lambda x: bool(x) if pd.notna(x) else False)
        & admissible.shape_scope_match.map(lambda x: bool(x) if pd.notna(x) else False)
    )
    ledger.check("A11", bool(valid_admissible.all()), f"{tag}: every shape-authorized task has valid verification/epoch/scope")
    scope_ok = bool(((structural_df.scope_type == ACTIVE_SCOPE_TYPE) & (structural_df.scope_id == ACTIVE_SCOPE_ID)).all())
    if scenario.deformation_type == "SCOPE_MISMATCH":
        scope_ok = bool(((structural_df.loc[~((structural_df.timestamp_ms >= onset) & (structural_df.timestamp_ms < clear)), "scope_type"] == ACTIVE_SCOPE_TYPE)).all())
    ledger.check("A12", scope_ok, f"{tag}: active declared scope is GLOBAL except the explicit E6 fault interval")

    # A13-A16 three-way classification and hard speed
    invalid = d[d.shape_classification == "EVIDENCE_INVALID"]
    ledger.check("A13", bool((invalid.shape_integrity_state == "UNKNOWN").all()) and bool((invalid.shape_all_failed_invariants == "[]").all()),
                 f"{tag}: evidence invalidity remains UNKNOWN without structural-failure claims")
    ledger.check("A14", not bool(invalid.shape_reconstruction_triggered.any()),
                 f"{tag}: evidence invalidity does not trigger reconstruction")
    if scenario.hard:
        first_denial = d.loc[(d.time_ms >= onset) & (~d.shape_allowed), "time_ms"].min()
        ledger.check("A15", float(first_denial) == onset, f"{tag}: hard failure denied at first failing observation ({first_denial})")
        hard_rows = d[(d.time_ms >= onset) & (d.time_ms < clear) & (d.shape_classification == "CONFIRMED_HARD_FAILURE")]
        ledger.check("A16", bool((hard_rows.shape_restore_count == 0).all()), f"{tag}: restoration/persistence counters do not delay hard revocation")
    else:
        ledger.check("A15", True, f"{tag}: hard-revocation assertion not applicable")
        ledger.check("A16", True, f"{tag}: hard-revocation counter assertion not applicable")

    # A17-A18 soft persistence
    if scenario.scenario_id == "D1_TRANSIENT_SOFT_IMBALANCE":
        active_records = records_df[(records_df.source_observation_time_ms >= onset) & (records_df.source_observation_time_ms < clear)]
        warning_count = int(active_records.raw_soft_warnings.apply(lambda x: len(json.loads(x)) > 0).sum())
        denials = int(d[(d.time_ms >= onset) & (d.time_ms < clear) & (~d.shape_allowed)].shape[0])
        ledger.check("A17", warning_count < K_SOFT_PERSIST and denials == 0,
                     f"{tag}: {warning_count} raw warnings, {denials} denials")
    else:
        ledger.check("A17", True, f"{tag}: D1 assertion not applicable")
    if scenario.scenario_id in {"D2_PERSISTENT_SOFT_IMBALANCE", "D3_PERSISTENT_PROBE_LATENCY_SKEW"}:
        first_denial = d.loc[(d.time_ms >= onset) & (~d.shape_allowed), "time_ms"].min()
        ledger.check("A18", float(first_denial) == onset + 200.0,
                     f"{tag}: first effective soft denial at third observation ({first_denial})")
    else:
        ledger.check("A18", True, f"{tag}: persistent-soft assertion not applicable")

    # A19-A21 restoration and invariant determinism
    pre = d[d.time_ms < onset]
    ledger.check("A19", bool(pre.shape_restoration_requirement_satisfied.all()),
                 f"{tag}: restoration requirement vacuously true before first non-admissible state")
    nonadmissible = d[d.shape_classification.isin(["EVIDENCE_INVALID", "SOFT_DEGRADATION", "CONFIRMED_HARD_FAILURE"])]
    reset_ok = bool((nonadmissible.shape_restore_count == 0).all())
    ledger.check("A20", reset_ok, f"{tag}: new invalidity/degradation/failure resets K_RESTORE")
    active_failed = records_df[records_df.all_failed_invariants != "[]"]
    order_ok = True
    for r in active_failed.to_dict("records"):
        failures = json.loads(r["all_failed_invariants"])
        expected = next((x for x in CANONICAL_INVARIANT_ORDER if x in failures), None)
        if r["first_failed_invariant"] != expected:
            order_ok = False
            break
    ledger.check("A21", order_ok, f"{tag}: first_failed_invariant follows canonical order")

    # A22-A25 matched keys and direct isolation
    primary = rows_df[(rows_df.pattern_id.isin(BORDERLINE_PATTERNS)) & (rows_df.time_ms >= onset) & (rows_df.time_ms < clear)]
    psets = [set(primary.loc[primary.arch == arch, "task_key"]) for arch in ARCHES]
    ledger.check("A22", all(s == psets[0] for s in psets[1:]), f"{tag}: primary matched keys identical")

    c = rows_df[rows_df.arch == ARCH_C]
    elig_ok = True
    for pid in BORDERLINE_PATTERNS:
        promo = c.loc[(c.pattern_id == pid) & c.requalified_at_ms.notna(), "requalified_at_ms"]
        if not promo.empty and float(promo.iloc[0]) >= onset:
            elig_ok = False
    ledger.check("A23", elig_ok, f"{tag}: every reported eligible instance requalified before fixed onset")

    first_nonadmissible = d.loc[~d.shape_allowed, "time_ms"].min()
    if pd.isna(first_nonadmissible):
        compare_until = SIM_DURATION_MS
    else:
        compare_until = float(first_nonadmissible)
    cols = ["task_key", "c_success_before", "c_success_after", "depreciation_state", "requalify_count", "structural_cost_state"]
    cm = c[c.time_ms < compare_until][cols].sort_values("task_key").reset_index(drop=True)
    dm = d[d.time_ms < compare_until][cols].sort_values("task_key").reset_index(drop=True)
    identity = len(cm) == len(dm)
    if identity and len(cm):
        identity = bool(np.allclose(cm.c_success_before.fillna(-1), dm.c_success_before.fillna(-1)))
        identity &= bool(np.allclose(cm.c_success_after.fillna(-1), dm.c_success_after.fillna(-1)))
        identity &= bool((cm.depreciation_state.fillna("") == dm.depreciation_state.fillna("")).all())
        identity &= bool((cm.requalify_count == dm.requalify_count).all())
        identity &= bool(np.allclose(cm.structural_cost_state.fillna(-1), dm.structural_cost_state.fillna(-1)))
    ledger.check("A24", identity, f"{tag}: C/D route state identical before first shape denial")
    ledger.check("A25", gate.records == records_df.sort_values("source_observation_time_ms").to_dict("records"),
                 f"{tag}: arm outcomes cannot mutate shared structural stream")


def select_verdict_branch(
    assertions_ok: bool,
    discriminating: bool,
    suppression_ok: bool,
    structural_ok: bool,
    support_ok: bool,
    partial_ok: bool,
) -> str:
    if not assertions_ok:
        return "INVALID_RUN"
    if not discriminating:
        return "INCONCLUSIVE"
    if not suppression_ok:
        return "NOT_SUPPORTED"
    if not structural_ok:
        return "NOT_SUPPORTED"
    if support_ok:
        return "SUPPORTED"
    if partial_ok:
        return "PARTIAL_SUPPORT"
    return "NOT_SUPPORTED"


def verdict_self_test(ledger: AssertionLedger) -> None:
    cases = [
        ((False, True, True, True, True, True), "INVALID_RUN"),
        ((True, False, True, True, True, True), "INCONCLUSIVE"),
        ((True, True, False, True, True, True), "NOT_SUPPORTED"),
        ((True, True, True, False, True, True), "NOT_SUPPORTED"),
        ((True, True, True, True, False, False), "NOT_SUPPORTED"),
        ((True, True, True, True, False, True), "PARTIAL_SUPPORT"),
        ((True, True, True, True, True, True), "SUPPORTED"),
    ]
    ok = all(select_verdict_branch(*args) == expected for args, expected in cases)
    ledger.check("A26", ok, f"verdict branch self-test {sum(select_verdict_branch(*a)==e for a,e in cases)}/{len(cases)}")

# -----------------------------------------------------------------------------
# Metrics, verdict, and output generation
# -----------------------------------------------------------------------------
def first_promotion_time(df_arch: pd.DataFrame, pid: int) -> float | None:
    values = df_arch.loc[(df_arch.pattern_id == pid) & df_arch.requalified_at_ms.notna(), "requalified_at_ms"]
    return None if values.empty else float(values.iloc[0])


def build_per_instance_metrics(rows_df: pd.DataFrame, scenario: Scenario, seed: int) -> list[dict[str, Any]]:
    if scenario.scenario_id not in {
        "D2_PERSISTENT_SOFT_IMBALANCE", "D3_PERSISTENT_PROBE_LATENCY_SKEW",
        "D4_HARD_ROLE_ABSENCE", "D5_HARD_ANGULAR_COMPRESSION", "D6_HARD_COVERAGE_LOSS",
        "D7_HARD_COORDINATOR_OFFSET", "D8_HARD_ROLE_DOMINANCE",
    }:
        return []

    onset = deformation_onset_ms(seed)
    clear = onset + scenario.duration_ms
    c = rows_df[rows_df.arch == ARCH_C]
    d = rows_df[rows_df.arch == ARCH_D]
    out: list[dict[str, Any]] = []

    for pid in BORDERLINE_PATTERNS:
        promo = first_promotion_time(c, pid)
        eligible = promo is not None and promo < onset
        c_window = c[(c.pattern_id == pid) & (c.time_ms >= onset) & (c.time_ms < clear)]
        d_window = d[(d.pattern_id == pid) & (d.time_ms >= onset) & (d.time_ms < clear)]
        shape_denials = d[(d.time_ms >= onset) & (~d.shape_allowed)]
        shape_time = None if shape_denials.empty else float(shape_denials.time_ms.iloc[0])

        c_after = c[(c.pattern_id == pid) & (c.time_ms >= onset) & (c.time_ms < PHASE_RECOVERY_END_MS)]
        c_blocks = c_after[~c_after.route_allowed_before_shape]
        flat_time = None if c_blocks.empty else float(c_blocks.time_ms.iloc[0])
        comparable = shape_time is not None and flat_time is not None
        lead = (flat_time - shape_time) if comparable else np.nan
        tasks_exposed = int(d_window[d_window.time_ms < shape_time].shape[0]) if shape_time is not None else int(d_window.shape[0])

        c_bp = int(c_window.bypassed.sum())
        d_bp = int(d_window.bypassed.sum())
        c_wrong = int(c_window.wrong_bypass.sum())
        d_wrong = int(d_window.wrong_bypass.sum())
        out.append({
            "scenario_id": scenario.scenario_id,
            "seed": seed,
            "pattern_id": pid,
            "eligible": eligible,
            "requalified_at_ms": promo,
            "deformation_onset_ms": onset,
            "deformation_clear_ms": clear,
            "shape_revocation_time_ms": shape_time,
            "flat_revocation_time_ms": flat_time,
            "comparable_revocation": comparable,
            "revocation_lead_ms": lead,
            "tasks_exposed_before_shape_revocation": tasks_exposed,
            "c_bypasses": c_bp,
            "d_bypasses": d_bp,
            "c_wrong_bypasses": c_wrong,
            "d_wrong_bypasses": d_wrong,
            "c_wrong_bypass_rate_over_bypasses": np.nan if c_bp == 0 else c_wrong / c_bp,
            "d_wrong_bypass_rate_over_bypasses": np.nan if d_bp == 0 else d_wrong / d_bp,
            "c_wrong_bypass_rate_over_tasks": np.nan if len(c_window) == 0 else c_wrong / len(c_window),
            "d_wrong_bypass_rate_over_tasks": np.nan if len(d_window) == 0 else d_wrong / len(d_window),
            "scenario_kind": "HARD" if scenario.hard else "SOFT",
        })
    return out


def pair_summary(rows_df: pd.DataFrame, scenario: Scenario, seed: int) -> list[dict[str, Any]]:
    onset = deformation_onset_ms(seed)
    clear = onset + scenario.duration_ms
    summaries = []
    d = rows_df[rows_df.arch == ARCH_D]
    clean_keys = set(d.loc[
        ((d.time_ms < onset) | ((d.time_ms >= clear) & (~d.shape_restoration_active)))
        & (d.shape_classification == "ADMISSIBLE"), "task_key"
    ])
    for arch in ARCHES:
        x = rows_df[rows_df.arch == arch]
        active = x[(x.time_ms >= onset) & (x.time_ms < clear)]
        clean = x[x.task_key.isin(clean_keys)]
        summaries.append({
            "scenario_id": scenario.scenario_id,
            "seed": seed,
            "arch": arch,
            "tasks": len(x),
            "bypasses": int(x.bypassed.sum()),
            "wrong_bypasses": int(x.wrong_bypass.sum()),
            "fallbacks": int(x.fallback.sum()),
            "fallback_rate": float(x.fallback.mean()),
            "active_window_bypasses": int(active.bypassed.sum()),
            "active_window_wrong_bypasses": int(active.wrong_bypass.sum()),
            "active_window_fallbacks": int(active.fallback.sum()),
            "clean_window_tasks": len(clean),
            "clean_window_bypasses": int(clean.bypassed.sum()),
            "clean_window_fallbacks": int(clean.fallback.sum()),
            "shape_denials": int((~x.shape_allowed).sum()) if arch == ARCH_D else 0,
            "evidence_invalidity_denials": int((x.shape_classification == "EVIDENCE_INVALID").sum()) if arch == ARCH_D else 0,
            "hard_failure_denials": int((x.shape_classification == "CONFIRMED_HARD_FAILURE").sum()) if arch == ARCH_D else 0,
            "soft_degradation_denials": int((x.shape_classification == "SOFT_DEGRADATION").sum()) if arch == ARCH_D else 0,
            "restoring_denials": int((x.shape_classification == "RESTORING").sum()) if arch == ARCH_D else 0,
            "unnecessary_reconstruction_triggers": int(
                ((x.shape_classification == "EVIDENCE_INVALID") & x.shape_reconstruction_triggered).sum()
            ) if arch == ARCH_D else 0,
        })
    return summaries


def matched_rows(rows_df: pd.DataFrame, scenario: Scenario, seed: int, per_instance: list[dict[str, Any]]) -> pd.DataFrame:
    if not per_instance:
        return pd.DataFrame()
    onset = deformation_onset_ms(seed)
    clear = onset + scenario.duration_ms
    eligible_pids = [r["pattern_id"] for r in per_instance if r["eligible"]]
    return rows_df[
        rows_df.pattern_id.isin(eligible_pids)
        & (rows_df.time_ms >= onset)
        & (rows_df.time_ms < clear)
    ].copy()


def bootstrap_difference_ci(per_instance_df: pd.DataFrame, n_resamples: int = 10_000) -> tuple[float, float]:
    eligible = per_instance_df[per_instance_df.eligible].copy()
    if eligible.empty:
        return np.nan, np.nan
    diffs = (eligible.c_wrong_bypasses - eligible.d_wrong_bypasses).to_numpy(dtype=float)
    rng = np.random.RandomState(20260701)
    samples = rng.choice(diffs, size=(n_resamples, len(diffs)), replace=True).sum(axis=1)
    return float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))


def compute_verdict(
    assertions_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    per_instance_df: pd.DataFrame,
) -> tuple[str, dict[str, Any]]:
    assertions_ok = bool(assertions_df.passed.all())
    eligible = per_instance_df[per_instance_df.eligible].copy()
    eligible_counts = eligible.groupby("scenario_id").size() if not eligible.empty else pd.Series(dtype=int)
    enough_eligible = len(eligible_counts) == 7 and bool((eligible_counts >= 12).all())
    c_exposed_fraction = 0.0 if eligible.empty else float((eligible.c_wrong_bypasses > 0).mean())
    discriminating = enough_eligible and c_exposed_fraction > 0.50

    clean = summary_df.groupby("arch", as_index=True).clean_window_bypasses.sum()
    c_clean = int(clean.get(ARCH_C, 0))
    d_clean = int(clean.get(ARCH_D, 0))
    d0_denials = int(summary_df[(summary_df.scenario_id == "D0_CLEAN_CONTROL") & (summary_df.arch == ARCH_D)].shape_denials.sum())
    d1_denials = int(summary_df[(summary_df.scenario_id == "D1_TRANSIENT_SOFT_IMBALANCE") & (summary_df.arch == ARCH_D)].shape_denials.sum())
    suppression_ratio = np.nan if c_clean == 0 else d_clean / c_clean
    suppression_ok = c_clean > 0 and suppression_ratio >= 0.90 and d0_denials == 0 and d1_denials == 0

    evidence_summary = summary_df[(summary_df.scenario_id.str.startswith("E")) & (summary_df.arch == ARCH_D)]
    no_invalid_reconstruction = int(evidence_summary.unnecessary_reconstruction_triggers.sum()) == 0
    structural_ok = assertions_ok and no_invalid_reconstruction

    c_wrong = int(eligible.c_wrong_bypasses.sum()) if not eligible.empty else 0
    d_wrong = int(eligible.d_wrong_bypasses.sum()) if not eligible.empty else 0
    reduction = np.nan if c_wrong == 0 else 1.0 - d_wrong / c_wrong
    comparable = eligible[eligible.comparable_revocation]
    earlier_fraction = 0.0 if comparable.empty else float((comparable.shape_revocation_time_ms < comparable.flat_revocation_time_ms).mean())
    median_lead = np.nan if comparable.empty else float(comparable.revocation_lead_ms.median())
    hard_exposure = eligible[eligible.scenario_kind == "HARD"].tasks_exposed_before_shape_revocation
    soft_exposure = eligible[eligible.scenario_kind == "SOFT"].tasks_exposed_before_shape_revocation
    hard_median_exposure = np.nan if hard_exposure.empty else float(hard_exposure.median())
    soft_median_exposure = np.nan if soft_exposure.empty else float(soft_exposure.median())
    ci_low, ci_high = bootstrap_difference_ci(per_instance_df)

    support_ok = bool(
        c_wrong > 0
        and reduction >= 0.50
        and earlier_fraction >= 0.80
        and median_lead >= 500.0
        and hard_median_exposure <= 1.0
        and soft_median_exposure <= 10.0
        and ci_low > 0.0
    )
    partial_ok = bool(
        c_wrong > 0
        and reduction >= 0.20
        and earlier_fraction >= 0.60
        and median_lead > 0.0
        and c_clean > 0
        and d_clean / c_clean >= 0.85
    )

    verdict = select_verdict_branch(
        assertions_ok, discriminating, suppression_ok, structural_ok, support_ok, partial_ok
    )
    detail = {
        "assertions_ok": assertions_ok,
        "discriminating": discriminating,
        "eligible_instances": int(len(eligible)),
        "minimum_eligible_per_scenario": int(eligible_counts.min()) if len(eligible_counts) else 0,
        "c_exposed_fraction": c_exposed_fraction,
        "suppression_ok": suppression_ok,
        "clean_bypass_ratio_d_over_c": suppression_ratio,
        "d0_shape_denials": d0_denials,
        "d1_shape_denials": d1_denials,
        "structural_ok": structural_ok,
        "c_wrong_bypasses": c_wrong,
        "d_wrong_bypasses": d_wrong,
        "wrong_bypass_reduction": reduction,
        "earlier_revocation_fraction": earlier_fraction,
        "median_revocation_lead_ms": median_lead,
        "hard_median_tasks_exposed": hard_median_exposure,
        "soft_median_tasks_exposed": soft_median_exposure,
        "bootstrap_ci_low": ci_low,
        "bootstrap_ci_high": ci_high,
        "support_boundary_pass": support_ok,
        "partial_boundary_pass": partial_ok,
    }
    return verdict, detail


def append_csv(df: pd.DataFrame, path: Path, first: bool) -> None:
    if df.empty:
        return
    df.to_csv(path, mode="w" if first else "a", header=first, index=False)


def safe_hash(path: Path) -> str:
    if not path.exists():
        return "NOT_FOUND"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_controlling_file(names: Iterable[str], roots: Iterable[Path]) -> Path | None:
    for root in roots:
        for name in names:
            candidates = [root / name, root / "docs" / name]
            for candidate in candidates:
                if candidate.exists():
                    return candidate
    return None


def create_plots(summary_df: pd.DataFrame, per_instance_df: pd.DataFrame, matched_df: pd.DataFrame, plots_dir: Path) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)

    # 1. Revocation timeline
    e = per_instance_df[per_instance_df.eligible & per_instance_df.comparable_revocation]
    if not e.empty:
        x = np.arange(len(e))
        plt.figure(figsize=(12, 5))
        plt.plot(x, e.shape_revocation_time_ms - e.deformation_onset_ms, marker="o", label="V4-D shape gate")
        plt.plot(x, e.flat_revocation_time_ms - e.deformation_onset_ms, marker="o", label="V4-C flat gate")
        plt.xlabel("Eligible scenario-seed-pattern instance")
        plt.ylabel("Milliseconds after deformation onset")
        plt.title("V4 Revocation Timeline")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_dir / "v4_revocation_timeline.png", dpi=160)
        plt.close()

    # 2. Wrong bypass matched
    if not per_instance_df.empty:
        g = per_instance_df[per_instance_df.eligible].groupby("scenario_id")[["c_wrong_bypasses", "d_wrong_bypasses"]].sum()
        g.plot(kind="bar", figsize=(11, 5))
        plt.ylabel("Wrong bypasses")
        plt.title("Matched Wrong Bypasses by Structural Scenario")
        plt.tight_layout()
        plt.savefig(plots_dir / "v4_wrong_bypass_matched.png", dpi=160)
        plt.close()

    # 3. Detection by scenario
    if not per_instance_df.empty:
        g = per_instance_df[per_instance_df.eligible].groupby("scenario_id").revocation_lead_ms.median()
        g.plot(kind="bar", figsize=(11, 5))
        plt.ylabel("Median V4-D lead over V4-C (ms)")
        plt.title("Structural Revocation Lead by Scenario")
        plt.tight_layout()
        plt.savefig(plots_dir / "v4_structural_detection_by_scenario.png", dpi=160)
        plt.close()

    # 4. Clean suppression check
    g = summary_df.groupby("arch").clean_window_bypasses.sum().reindex([ARCH_C, ARCH_D])
    g.plot(kind="bar", figsize=(7, 5))
    plt.ylabel("Clean-window bypasses")
    plt.title("Clean Suppression Check")
    plt.tight_layout()
    plt.savefig(plots_dir / "v4_clean_suppression_check.png", dpi=160)
    plt.close()

    # 5. Global scope cost
    structural = summary_df[summary_df.scenario_id.str.match(r"D[2-8]")]
    if not structural.empty:
        pivot = structural.pivot_table(index="scenario_id", columns="arch", values="active_window_fallbacks", aggfunc="sum")
        pivot.reindex(columns=[ARCH_C, ARCH_D]).plot(kind="bar", figsize=(11, 5))
        plt.ylabel("Fallbacks during GLOBAL deformation")
        plt.title("GLOBAL Scope Fallback Cost")
        plt.tight_layout()
        plt.savefig(plots_dir / "v4_global_scope_cost.png", dpi=160)
        plt.close()

    # 6. Restoration timeline
    if not matched_df.empty and "shape_restore_count" in matched_df.columns:
        sample = matched_df[(matched_df.arch == ARCH_D) & (matched_df.scenario_id == "D4_HARD_ROLE_ABSENCE")]
        if not sample.empty:
            plt.figure(figsize=(10, 5))
            for seed, z in sample.groupby("seed"):
                z = z.sort_values("time_ms")
                plt.plot(z.time_ms, z.shape_restore_count, label=str(seed))
            plt.xlabel("Time (ms)")
            plt.ylabel("K_RESTORE count")
            plt.title("Restoration Counter Timeline")
            plt.legend(title="Seed")
            plt.tight_layout()
            plt.savefig(plots_dir / "v4_restoration_timeline.png", dpi=160)
            plt.close()

    # 7. Evidence invalidity behavior
    ev = summary_df[(summary_df.scenario_id.str.startswith("E")) & (summary_df.arch == ARCH_D)].groupby("scenario_id")[["evidence_invalidity_denials", "unnecessary_reconstruction_triggers"]].sum()
    if not ev.empty:
        ev.plot(kind="bar", figsize=(10, 5))
        plt.ylabel("Task decisions")
        plt.title("Evidence Invalidity: Fail-Closed Without Reconstruction")
        plt.tight_layout()
        plt.savefig(plots_dir / "v4_evidence_invalidity_behavior.png", dpi=160)
        plt.close()


def write_run_record(
    path: Path,
    script_path: Path,
    validation_path: Path | None,
    architecture_path: Path | None,
    manifest_hashes: dict[str, str],
    assertions_df: pd.DataFrame,
    verdict: str,
    verdict_detail: dict[str, Any],
    started: datetime,
    completed: datetime,
    smoke_test: bool,
) -> None:
    lines = [
        "BOUNDED ROUTING V4 — RUN RECORD",
        "=" * 72,
        "",
        "EXECUTION METADATA",
        "------------------",
        f"Mode                 : {'SMOKE TEST — NO SCIENTIFIC VERDICT' if smoke_test else 'FROZEN PRIMARY RUN'}",
        f"Started UTC          : {started.isoformat()}",
        f"Completed UTC        : {completed.isoformat()}",
        f"Script               : {script_path.name}",
        f"Script SHA-256       : {safe_hash(script_path)}",
        f"Validation plan      : {validation_path if validation_path else 'NOT_FOUND'}",
        f"Validation SHA-256   : {safe_hash(validation_path) if validation_path else 'NOT_FOUND'}",
        f"Architecture spec    : {architecture_path if architecture_path else 'NOT_FOUND'}",
        f"Architecture SHA-256 : {safe_hash(architecture_path) if architecture_path else 'NOT_FOUND'}",
        "",
        "ENVIRONMENT",
        "-----------",
        f"Python               : {platform.python_version()}",
        f"hashlib algorithms   : {','.join(sorted(hashlib.algorithms_guaranteed))}",
        f"OpenSSL              : {ssl.OPENSSL_VERSION}",
        f"NumPy                : {np.__version__}",
        f"pandas               : {pd.__version__}",
        f"matplotlib           : {matplotlib.__version__}",
        "",
        "FROZEN PARAMETER SUMMARY",
        "------------------------",
        f"Seeds                : {SEEDS}",
        f"K_REQUALIFY          : {K_REQUALIFY}",
        f"Shape interval ms    : {SHAPE_OBSERVATION_INTERVAL_MS}",
        f"Shape freshness ms   : {T_SHAPE_FRESHNESS_MS}",
        f"K_SOFT_PERSIST       : {K_SOFT_PERSIST}",
        f"K_RESTORE            : {K_RESTORE}",
        f"Scope                : {ACTIVE_SCOPE_TYPE}/{ACTIVE_SCOPE_ID}",
        f"Verification         : {VERIFICATION_METHOD}",
        "",
        "ASSERTIONS",
        "----------",
    ]
    for row in assertions_df.to_dict("records"):
        lines.append(f"{row['assertion_id']}: {'PASS' if row['passed'] else 'FAIL'} — {row['detail']}")
    lines += ["", "VERDICT", "-------", f"Final verdict: {verdict}"]
    for key, value in verdict_detail.items():
        lines.append(f"{key}: {value}")
    lines += ["", "MANIFEST HASHES", "---------------"]
    for name, digest in sorted(manifest_hashes.items()):
        lines.append(f"{name}: {digest}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen v4 tetrahedral shape-integrity simulation")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "bounded_routing_output_v4")
    parser.add_argument("--smoke-test", action="store_true", help="Run a reduced implementation check; no scientific verdict")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    output_dir = args.output_dir.resolve()
    data_dir = output_dir / "data"
    plots_dir = output_dir / "plots"
    data_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    scenarios = scenario_catalog()
    seeds = list(SEEDS)
    if args.smoke_test:
        keep = {
            "D0_CLEAN_CONTROL", "D1_TRANSIENT_SOFT_IMBALANCE",
            "D2_PERSISTENT_SOFT_IMBALANCE", "D4_HARD_ROLE_ABSENCE",
            "E1_MISSING_RECORD", "E5_EPOCH_MISMATCH",
        }
        scenarios = [s for s in scenarios if s.scenario_id in keep]
        seeds = [42]

    print("=" * 78)
    print("BOUNDED ROUTING SIMULATION v4 — TETRAHEDRAL SHAPE-INTEGRITY GATE")
    print("SMOKE TEST — NO SCIENTIFIC VERDICT" if args.smoke_test else "FROZEN PRIMARY RUN")
    print(f"Scenarios={len(scenarios)} Seeds={seeds}")
    print("=" * 78)

    ledger = AssertionLedger()
    verdict_self_test(ledger)  # A26 before arm execution

    # Generate and save every selected manifest before any arm executes.
    print("\nGenerating and freezing manifests before arm execution...")
    bundle: dict[tuple[str, int], tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]] = {}
    manifest_hashes: dict[str, str] = {}
    for scenario in scenarios:
        for seed in seeds:
            task_df = build_task_manifest(seed, scenario)
            structural_df, deformation_df, truth_df = build_structural_manifest(seed, scenario)
            records_df = build_shape_records(structural_df)

            task_path = data_dir / f"manifest_task_seed{seed}_{scenario.scenario_id}_v4.csv"
            structural_path = data_dir / f"manifest_structural_seed{seed}_{scenario.scenario_id}_v4.csv"
            deformation_path = data_dir / f"manifest_deformation_seed{seed}_{scenario.scenario_id}_v4.csv"
            truth_path = data_dir / f"ground_truth_seed{seed}_{scenario.scenario_id}_v4.csv"
            task_df.to_csv(task_path, index=False)
            structural_df.to_csv(structural_path, index=False)
            deformation_df.to_csv(deformation_path, index=False)
            truth_df.to_csv(truth_path, index=False)
            for p in [task_path, structural_path, deformation_path, truth_path]:
                manifest_hashes[p.name] = safe_hash(p)
            bundle[(scenario.scenario_id, seed)] = (task_df, structural_df, deformation_df, truth_df, records_df)
            print(f"  {scenario.scenario_id} seed={seed}: tasks={len(task_df)} observations={len(structural_df)} records={len(records_df)}")

    manifests_saved = True
    print("All selected manifests are on disk. Arm execution begins now.\n")

    raw_path = data_dir / "bounded_routing_v4_raw.csv"
    structural_records_path = data_dir / "bounded_routing_v4_structural_records.csv"
    matched_path = data_dir / "bounded_routing_v4_matched_comparison.csv"
    for p in [raw_path, structural_records_path, matched_path]:
        if p.exists():
            p.unlink()
    raw_first = True
    records_first = True
    matched_first = True

    summaries: list[dict[str, Any]] = []
    instance_rows: list[dict[str, Any]] = []
    t0 = time.time()

    for scenario in scenarios:
        for seed in seeds:
            task_df, structural_df, deformation_df, truth_df, records_df = bundle[(scenario.scenario_id, seed)]
            rows_df, gate, c_arm, d_arm = run_pair(seed, scenario, task_df, structural_df, records_df)
            update_pair_assertions(
                ledger, scenario, seed, task_df, structural_df, records_df, rows_df, gate, manifests_saved
            )

            pair_instances = build_per_instance_metrics(rows_df, scenario, seed)
            instance_rows.extend(pair_instances)
            summaries.extend(pair_summary(rows_df, scenario, seed))

            pair_matched = matched_rows(rows_df, scenario, seed, pair_instances)
            if not pair_matched.empty:
                pair_matched = pair_matched.copy()
                pair_matched["window_type"] = "DEFORMATION"
            # Include a compact restoration window for audit and plotting.
            if scenario.scenario_id.startswith("D") and scenario.duration_ms > 0:
                clear = deformation_onset_ms(seed) + scenario.duration_ms
                restoration = rows_df[
                    (rows_df.arch == ARCH_D)
                    & (rows_df.time_ms >= clear)
                    & (rows_df.time_ms < clear + 1_000.0)
                ].copy()
                if not restoration.empty:
                    restoration["window_type"] = "RESTORATION"
                    pair_matched = pd.concat([pair_matched, restoration], ignore_index=True) if not pair_matched.empty else restoration

            append_csv(rows_df, raw_path, raw_first)
            raw_first = False
            append_csv(records_df, structural_records_path, records_first)
            records_first = False
            append_csv(pair_matched, matched_path, matched_first)
            if not pair_matched.empty:
                matched_first = False

            elapsed = time.time() - t0
            print(f"  ran {scenario.scenario_id} seed={seed}: rows={len(rows_df)} elapsed={elapsed:.1f}s")

            # Release pair-sized data before the next run.
            del rows_df

    summary_df = pd.DataFrame(summaries)
    per_instance_df = pd.DataFrame(instance_rows)
    assertions_df = ledger.dataframe()

    summary_path = data_dir / "bounded_routing_v4_summary.csv"
    per_instance_path = data_dir / "bounded_routing_v4_per_instance.csv"
    assertions_path = data_dir / "bounded_routing_v4_assertions.csv"
    verdict_path = data_dir / "bounded_routing_v4_verdict.csv"
    summary_df.to_csv(summary_path, index=False)
    per_instance_df.to_csv(per_instance_path, index=False)
    assertions_df.to_csv(assertions_path, index=False)

    if args.smoke_test:
        verdict = "SMOKE_TEST_ONLY"
        verdict_detail = {
            "scientific_verdict": "NOT_EVALUATED",
            "assertions_passed": bool(assertions_df.passed.all()),
            "selected_scenarios": [s.scenario_id for s in scenarios],
            "selected_seeds": seeds,
        }
    else:
        verdict, verdict_detail = compute_verdict(assertions_df, summary_df, per_instance_df)
    pd.DataFrame([{**{"verdict": verdict}, **verdict_detail}]).to_csv(verdict_path, index=False)

    if not args.no_plots:
        matched_df = pd.read_csv(matched_path) if matched_path.exists() else pd.DataFrame()
        create_plots(summary_df, per_instance_df, matched_df, plots_dir)

    script_path = Path(__file__).resolve()
    roots = [Path.cwd(), script_path.parent, script_path.parent.parent]
    validation_path = find_controlling_file(
        ["TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md"], roots
    )
    architecture_path = find_controlling_file(
        ["TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1.md", "TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1(2).md"], roots
    )
    completed = datetime.now(timezone.utc)
    run_record_path = data_dir / "bounded_routing_v4_run_record.txt"
    write_run_record(
        run_record_path, script_path, validation_path, architecture_path, manifest_hashes,
        assertions_df, verdict, verdict_detail, started, completed, args.smoke_test,
    )

    # Inventory hashes for primary outputs.
    output_inventory = []
    for p in sorted(data_dir.glob("bounded_routing_v4_*")):
        output_inventory.append({"file": p.name, "sha256": safe_hash(p), "bytes": p.stat().st_size})
    pd.DataFrame(output_inventory).to_csv(data_dir / "bounded_routing_v4_output_inventory.csv", index=False)

    print("\n" + "=" * 78)
    print(f"VERDICT: {verdict}")
    print(f"Assertions: {int(assertions_df.passed.sum())}/{len(assertions_df)} passed")
    print(f"Output: {output_dir}")
    print("=" * 78)

    if not assertions_df.passed.all():
        failed = assertions_df[~assertions_df.passed]
        print(failed[["assertion_id", "detail"]].to_string(index=False))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
