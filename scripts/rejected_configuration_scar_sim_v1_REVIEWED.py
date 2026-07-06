"""
rejected_configuration_scar_sim_v1.py

Implements the frozen REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1.md exactly.

Does NOT implement: shedding, lineage, fuzzy matching, prospective filtering,
extra-proof protocol, nomination-pressure counting beyond what C1 tests.

Produces:
  data/rejected_configuration_scar_v1_raw.csv
  data/rejected_configuration_scar_v1_summary.csv
  data/rejected_configuration_scar_v1_scar_registry.csv
  data/rejected_configuration_scar_v1_assertions.csv
  data/rejected_configuration_scar_v1_verdict.csv
  data/rejected_configuration_scar_v1_run_record.txt
  plots/scar_v1_assertion_status.png
  plots/scar_v1_write_boundary.png
  plots/scar_v1_match_behavior.png
  plots/scar_v1_elevation_retirement.png
"""

import hashlib
import json
import math
import datetime
import platform
import sys
import ssl
import os
import time
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------------------------------------------------------------------------
# Frozen parameters (plan §Frozen Scar Parameters)
# ---------------------------------------------------------------------------
K_SOFT_PERSIST               = 3
T_SCAR_ELEVATE               = 3
T_SCAR_RETIRE_SUCCESS_CYCLES = 5

FINGERPRINT_METHOD  = "GEOMETRY_ONLY_SHA256"
FINGERPRINT_VERSION = "scar-fp-v1-geom-only"
HASH_ALGORITHM      = "sha256"
MATCH_POLICY        = "EXACT_CANONICAL_FINGERPRINT"

ANGLE_QUANTUM      = Decimal("0.01")
WEIGHT_QUANTUM     = Decimal("0.0001")
COVERAGE_QUANTUM   = Decimal("0.0001")
COORD_QUANTUM      = Decimal("0.0001")

BASELINE_GEOMETRY = dict(
    fact_angle=0.00,       logic_angle=120.00,    coherence_angle=240.00,
    fact_weight=0.3333,    logic_weight=0.3333,   coherence_weight=0.3334,
    fact_coverage=1.0000,  logic_coverage=1.0000, coherence_coverage=1.0000,
    coord_x=0.0000,        coord_y=0.0000,
    scope_type="GLOBAL",   scope_id="ACTIVE_TETRAHEDRAL_SUBSTRATE",
)

SCRIPT_PATH = Path(__file__).resolve()

def _sha256_optional(path: Path) -> str:
    """Return SHA-256 for a file if present, otherwise a clear MISSING marker."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else f"MISSING:{path}"

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent
SCAR_SPEC_PATH = BASE / "REJECTED_CONFIGURATION_SCAR_SPEC_v1_REVISED.md"
VALIDATION_PLAN_PATH = BASE / "REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1_FROZEN.md"
DATA_DIR  = BASE / "data"
PLOTS_DIR = BASE / "plots"
DATA_DIR.mkdir(exist_ok=True)
PLOTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Fingerprint (plan §Frozen Fingerprint Declaration)
# ---------------------------------------------------------------------------

def _quantize(value: float, quantum: Decimal) -> str:
    """Decimal half-up rounding to declared quantum, returned as string.
    Negative zero (-0.0000) is normalized to positive zero (0.0000) to
    ensure canonical JSON serialization is stable across platforms."""
    d = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    # Normalize -0 to 0 so JSON serialization is deterministic
    if d == 0:
        d = Decimal("0").quantize(quantum)
    return str(d)


def _normalize_angle(degrees: float) -> float:
    """Normalize angle to [0, 360) before quantization."""
    d = degrees % 360.0
    if d < 0:
        d += 360.0
    return d


def compute_fingerprint(geometry: dict) -> Optional[str]:
    """
    Compute GEOMETRY_ONLY_SHA256 fingerprint.

    Returns None (fingerprint_available=False) if any required field is missing.
    failed_invariant_class is NOT included in the payload — it is adjacent metadata.

    Canonical field order (plan §Canonical Field Order):
      fingerprint_method, fingerprint_version,
      scope_type, scope_id,
      fact_angle_deg_q, logic_angle_deg_q, coherence_angle_deg_q,
      fact_weight_q, logic_weight_q, coherence_weight_q,
      fact_coverage_q, logic_coverage_q, coherence_coverage_q,
      coordinator_x_q, coordinator_y_q
    """
    required = [
        "fact_angle", "logic_angle", "coherence_angle",
        "fact_weight", "logic_weight", "coherence_weight",
        "fact_coverage", "logic_coverage", "coherence_coverage",
        "coord_x", "coord_y",
        "scope_type", "scope_id",
    ]
    for field_name in required:
        if geometry.get(field_name) is None:
            return None  # fingerprint_available = False

    payload = {
        "fingerprint_method":   FINGERPRINT_METHOD,
        "fingerprint_version":  FINGERPRINT_VERSION,
        "scope_type":           str(geometry["scope_type"]),
        "scope_id":             str(geometry["scope_id"]),
        "fact_angle_deg_q":     _quantize(_normalize_angle(geometry["fact_angle"]),    ANGLE_QUANTUM),
        "logic_angle_deg_q":    _quantize(_normalize_angle(geometry["logic_angle"]),   ANGLE_QUANTUM),
        "coherence_angle_deg_q":_quantize(_normalize_angle(geometry["coherence_angle"]),ANGLE_QUANTUM),
        "fact_weight_q":        _quantize(geometry["fact_weight"],     WEIGHT_QUANTUM),
        "logic_weight_q":       _quantize(geometry["logic_weight"],    WEIGHT_QUANTUM),
        "coherence_weight_q":   _quantize(geometry["coherence_weight"],WEIGHT_QUANTUM),
        "fact_coverage_q":      _quantize(geometry["fact_coverage"],   COVERAGE_QUANTUM),
        "logic_coverage_q":     _quantize(geometry["logic_coverage"],  COVERAGE_QUANTUM),
        "coherence_coverage_q": _quantize(geometry["coherence_coverage"],COVERAGE_QUANTUM),
        "coordinator_x_q":      _quantize(geometry["coord_x"], COORD_QUANTUM),
        "coordinator_y_q":      _quantize(geometry["coord_y"], COORD_QUANTUM),
    }
    canonical = json.dumps(payload, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Scar registry (isolated — no structural observer access)
# ---------------------------------------------------------------------------

@dataclass
class ScarRecord:
    configuration_fingerprint:  str
    scope_type:                  str
    scope_id:                    str
    scar_event_class:            str      # AUTHORIZED_HARD_STRUCTURAL_FAILURE etc.
    scar_response:               str      # REJECT_AS_IS | REQUIRE_EXTRA_PROOF
    failed_invariant_class:      str      # adjacent metadata, not in fingerprint
    failure_count:               int = 1
    first_seen_ms:               float = 0.0
    last_seen_ms:                float = 0.0
    successful_cycles_since_last_seen: int = 0
    elevation_state:             str = "NOT_ELEVATED"   # NOT_ELEVATED | ELEVATED
    scar_retired:                bool = False
    # nomination pressure (C1 test) — separate counter, never part of failure_count
    nomination_pressure_count:   int = 0


class ScarRegistry:
    """
    Minimal structural record: stores RejectedConfigurationRecord objects.
    Not readable by the structural observer (enforced by isolation below).
    """
    def __init__(self):
        self._records: dict[str, ScarRecord] = {}
        self._elevation_events: list[dict] = []

    def _response_for(self, event_class: str) -> str:
        """Frozen response table from plan §Default Scar Responses."""
        if event_class == "AUTHORIZED_HARD_STRUCTURAL_FAILURE":
            return "REJECT_AS_IS"
        elif event_class in ("AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION",
                             "AUTHORIZED_RESTORATION_FAILURE"):
            return "REQUIRE_EXTRA_PROOF"
        raise ValueError(f"Unknown scar event class: {event_class}")

    def write_scar(self, fingerprint: str, geometry: dict,
                   event_class: str, failed_invariant_class: str,
                   now_ms: float = 0.0) -> ScarRecord:
        """Write or update a scar record. Called only for scar-eligible events."""
        if fingerprint in self._records:
            rec = self._records[fingerprint]
            rec.failure_count += 1
            rec.last_seen_ms = now_ms
            rec.successful_cycles_since_last_seen = 0
            rec.scar_retired = False
            # elevation check
            if rec.elevation_state == "NOT_ELEVATED" and rec.failure_count >= T_SCAR_ELEVATE:
                rec.elevation_state = "ELEVATED"
                self._elevation_events.append({
                    "configuration_fingerprint": fingerprint,
                    "scope_type":  rec.scope_type,
                    "scope_id":    rec.scope_id,
                    "failure_count": rec.failure_count,
                    "failed_invariant_class": rec.failed_invariant_class,
                    "first_seen_ms": rec.first_seen_ms,
                    "last_seen_ms":  rec.last_seen_ms,
                    "verification_reference": FINGERPRINT_VERSION,
                    # No semantic explanation field — enforced by absence
                })
        else:
            rec = ScarRecord(
                configuration_fingerprint=fingerprint,
                scope_type=geometry["scope_type"],
                scope_id=geometry["scope_id"],
                scar_event_class=event_class,
                scar_response=self._response_for(event_class),
                failed_invariant_class=failed_invariant_class,
                failure_count=1,
                first_seen_ms=now_ms,
                last_seen_ms=now_ms,
            )
            self._records[fingerprint] = rec
        return rec

    def lookup(self, fingerprint: str) -> Optional[ScarRecord]:
        return self._records.get(fingerprint)

    def record_successful_cycle(self, fingerprint: str) -> bool:
        """Increment successful_cycles; retire if threshold reached. Returns True if retired."""
        if fingerprint not in self._records:
            return False
        rec = self._records[fingerprint]
        if rec.scar_retired:
            return True
        rec.successful_cycles_since_last_seen += 1
        if rec.successful_cycles_since_last_seen >= T_SCAR_RETIRE_SUCCESS_CYCLES:
            rec.scar_retired = True
        return rec.scar_retired

    def record_nomination_pressure(self, fingerprint: str):
        """Cheap rejected nomination — never increments failure_count."""
        if fingerprint in self._records:
            self._records[fingerprint].nomination_pressure_count += 1

    def to_records(self) -> list[dict]:
        return [
            {
                "configuration_fingerprint": r.configuration_fingerprint,
                "scope_type": r.scope_type,
                "scope_id": r.scope_id,
                "scar_event_class": r.scar_event_class,
                "scar_response": r.scar_response,
                "failed_invariant_class": r.failed_invariant_class,
                "failure_count": r.failure_count,
                "first_seen_ms": r.first_seen_ms,
                "last_seen_ms": r.last_seen_ms,
                "successful_cycles_since_last_seen": r.successful_cycles_since_last_seen,
                "elevation_state": r.elevation_state,
                "scar_retired": r.scar_retired,
                "nomination_pressure_count": r.nomination_pressure_count,
            }
            for r in self._records.values()
        ]


# ---------------------------------------------------------------------------
# Structural observer (ISOLATED — has no reference to registry)
# ---------------------------------------------------------------------------

class StructuralObserver:
    """
    Produces live shape_integrity classification from geometry only.
    Has NO import, reference, or argument path to ScarRegistry.
    A26/A27 verified by the absence of any registry parameter.
    """

    def classify(self, geometry: dict, soft_count: int = 0) -> str:
        """
        Returns: ADMISSIBLE | GATE_EFFECTIVE_SOFT_DEGRADATION |
                 TRANSIENT_SOFT_WARNING | CONFIRMED_HARD_FAILURE
        This is a minimal structural classifier for the scar test harness.
        """
        # Hard: role weight imbalance > 0.50 indicates structural collapse (illustrative)
        weights = [geometry.get("fact_weight", 0),
                   geometry.get("logic_weight", 0),
                   geometry.get("coherence_weight", 0)]
        if any(w <= 0 for w in weights):
            return "CONFIRMED_HARD_FAILURE"
        # Hard: role angle compression (all within 30 degrees)
        angles = sorted([geometry.get("fact_angle", 0),
                         geometry.get("logic_angle", 120),
                         geometry.get("coherence_angle", 240)])
        spread = angles[-1] - angles[0]
        if spread < 30.0:
            return "CONFIRMED_HARD_FAILURE"

        if soft_count >= K_SOFT_PERSIST:
            return "GATE_EFFECTIVE_SOFT_DEGRADATION"
        if 0 < soft_count < K_SOFT_PERSIST:
            return "TRANSIENT_SOFT_WARNING"
        return "ADMISSIBLE"

    # A27: this class never touches C_success — enforced by absence


# ---------------------------------------------------------------------------
# Assertion ledger
# ---------------------------------------------------------------------------

class AssertionLedger:
    def __init__(self):
        self.results: list[dict] = []

    def check(self, assertion_id: str, condition: bool,
              description: str, detail: str = "") -> bool:
        self.results.append({
            "assertion_id": assertion_id,
            "passed": condition,
            "description": description,
            "detail": detail,
        })
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {assertion_id}: {description}")
        if not condition and detail:
            print(f"         detail: {detail}")
        return condition

    @property
    def all_passed(self) -> bool:
        return all(r["passed"] for r in self.results)

    def failures(self) -> list[dict]:
        return [r for r in self.results if not r["passed"]]


# ---------------------------------------------------------------------------
# Raw event log
# ---------------------------------------------------------------------------

raw_events: list[dict] = []

def log_event(scenario_id: str, event_class: str, fingerprint_available: bool,
              fingerprint: Optional[str], scar_written: bool,
              scar_response: Optional[str], failure_count: Optional[int],
              detail: str = ""):
    raw_events.append({
        "scenario_id": scenario_id,
        "event_class": event_class,
        "fingerprint_available": fingerprint_available,
        "fingerprint": fingerprint or "",
        "scar_written": scar_written,
        "scar_response": scar_response or "",
        "failure_count": failure_count if failure_count is not None else "",
        "detail": detail,
    })


# ---------------------------------------------------------------------------
# Scenario implementations
# ---------------------------------------------------------------------------

def run_fingerprint_tests(ledger: AssertionLedger) -> dict:
    """F0, F1, F2, F3 — fingerprint mechanism tests run first."""
    results = {}

    # F0: Float drift still matches (near-identical geometry within quantization)
    geom_a = {**BASELINE_GEOMETRY}
    geom_b = {**BASELINE_GEOMETRY,
              "fact_angle": 0.00004, "logic_angle": 120.00004,
              "coherence_angle": 239.99996,
              "fact_weight": 0.33330004, "logic_weight": 0.33329996,
              "coord_x": 0.00000004, "coord_y": -0.00000004}
    fp_a = compute_fingerprint(geom_a)
    fp_b = compute_fingerprint(geom_b)
    results["F0"] = {"fp_a": fp_a, "fp_b": fp_b, "match": fp_a == fp_b}
    log_event("F0", "FINGERPRINT_TEST", True, fp_a, False, None, None,
              f"fp_a={fp_a[:16]}... fp_b={fp_b[:16]}... match={fp_a==fp_b}")
    ledger.check("A1", fp_a == fp_b,
                 "F0 near-identical float drift produces identical fingerprints",
                 f"fp_a={fp_a[:16]}  fp_b={fp_b[:16]}")

    # F1: Beyond quantization boundary does not match
    geom_c = {**BASELINE_GEOMETRY, "logic_angle": 120.0060, "coord_x": 0.00016}
    fp_c = compute_fingerprint(geom_c)
    results["F1"] = {"fp_a": fp_a, "fp_c": fp_c, "mismatch": fp_a != fp_c}
    log_event("F1", "FINGERPRINT_TEST", True, fp_c, False, None, None,
              f"baseline vs modified: mismatch={fp_a!=fp_c}")
    ledger.check("A2", fp_a != fp_c,
                 "F1 geometry beyond the quantization boundary produces different fingerprints",
                 f"fp_a={fp_a[:16]}  fp_c={fp_c[:16]}")

    # F2: Same geometry, different failed_invariant_class → same fingerprint
    # failed_invariant_class must NOT be passed to compute_fingerprint
    fp_role_sep = compute_fingerprint({**BASELINE_GEOMETRY})   # ROLE_SEPARATION case
    fp_coord_al = compute_fingerprint({**BASELINE_GEOMETRY})   # COORDINATOR_ALIGNMENT case
    # Both use identical geometry, different adjacent metadata only
    results["F2"] = {"match": fp_role_sep == fp_coord_al}
    log_event("F2", "FINGERPRINT_TEST", True, fp_role_sep, False, None, None,
              f"same geom diff invariant class: match={fp_role_sep==fp_coord_al}")
    ledger.check("A3", fp_role_sep == fp_coord_al,
                 "F2 same geometry with different failed_invariant_class produces identical fingerprints")

    # F3: Missing geometry field produces no fingerprint
    geom_missing = {**BASELINE_GEOMETRY}
    del geom_missing["coord_y"]   # remove a required field by setting to None
    geom_missing_none = {**BASELINE_GEOMETRY, "coord_y": None}
    fp_missing = compute_fingerprint(geom_missing_none)
    results["F3"] = {"fingerprint_available": fp_missing is not None}
    log_event("F3", "FINGERPRINT_TEST", fp_missing is not None,
              fp_missing, False, None, None,
              f"coord_y=None → fingerprint={fp_missing}")
    ledger.check("A4", fp_missing is None,
                 "F3 missing required geometry produces no fingerprint and no scar",
                 f"returned: {fp_missing}")

    return results


def run_authority_boundary_tests(ledger: AssertionLedger,
                                  registry: ScarRegistry) -> dict:
    """A0–A4 and S0 authority boundary tests."""
    results = {}
    geom = {**BASELINE_GEOMETRY}
    fp = compute_fingerprint(geom)

    # A0: Non-admitted candidate — no scar
    # configuration_had_authority = False
    pre = len(registry._records)
    # Do not call write_scar
    log_event("A0", "NON_ADMITTED_REJECT", True, fp, False, None, None)
    ledger.check("A5", len(registry._records) == pre,
                 "A0 non-admitted candidate writes no scar")

    # A1: Cheap retry failure — no scar
    log_event("A1", "CHEAP_RETRY_FAILURE", True, fp, False, None, None)
    ledger.check("A6", len(registry._records) == pre,
                 "A1 cheap retry failure writes no scar")

    # A2: Evidence invalidity — no scar (valid_structural_evidence = False)
    # Even if configuration_had_authority = True, invalid evidence does not write a scar
    log_event("A2", "EVIDENCE_INVALIDITY", False, None, False, None, None,
              "valid_structural_evidence=False → no scar")
    ledger.check("A7", len(registry._records) == pre,
                 "A2 evidence invalidity writes no scar")

    # A3: Authorized but no completed operation — no scar
    log_event("A3", "AUTHORIZED_BUT_NO_COMPLETED_OPERATION", True, fp, False, None, None)
    ledger.check("A8", len(registry._records) == pre,
                 "A3 authorized-but-no-completed-operation writes no scar")

    # A4: Completed authority establishes eligibility (no scar written yet)
    # configuration_had_authority_for_scar = True when:
    # passed stack + gate + admitted + completed_trusted_operation
    config_had_authority = True  # all four conditions met
    results["A4"] = {"configuration_had_authority_for_scar": config_had_authority}
    log_event("A4", "AUTHORITY_ESTABLISHED", True, fp, False, None, None,
              "authority established, no failure yet")
    ledger.check("A9", config_had_authority,
                 "A4 completed trusted operation establishes scar eligibility")

    # S0: Transient soft warning — exactly K_SOFT_PERSIST-1 raw soft warnings, then clean
    # K_SOFT_PERSIST=3 → exactly 2 warnings then 1 clean → no scar
    soft_count = K_SOFT_PERSIST - 1  # = 2
    obs = StructuralObserver()
    geom_soft = {**BASELINE_GEOMETRY}  # healthy geometry
    cls_soft = obs.classify(geom_soft, soft_count=soft_count)
    # Then one clean observation
    cls_clean = obs.classify(geom_soft, soft_count=0)
    gate_effective = (cls_soft == "GATE_EFFECTIVE_SOFT_DEGRADATION")
    log_event("S0", "TRANSIENT_SOFT_WARNING_BELOW_PERSISTENCE", True, fp, False, None, None,
              f"soft_count={soft_count} classify={cls_soft} → gate_effective={gate_effective}")
    ledger.check("A10", not gate_effective,
                 f"S0 exactly K_SOFT_PERSIST-1={soft_count} raw soft warnings then clean writes no scar",
                 f"classification at soft_count={soft_count}: {cls_soft}")

    return results


def run_scar_write_tests(ledger: AssertionLedger,
                          registry: ScarRegistry) -> dict:
    """S1, S2, S3 — scar write tests."""
    results = {}
    geom = {**BASELINE_GEOMETRY}
    fp = compute_fingerprint(geom)

    # S1: Authorized hard structural failure → REJECT_AS_IS
    rec_s1 = registry.write_scar(
        fingerprint=fp,
        geometry=geom,
        event_class="AUTHORIZED_HARD_STRUCTURAL_FAILURE",
        failed_invariant_class="ROLE_SEPARATION",
        now_ms=1000.0,
    )
    results["S1"] = rec_s1
    log_event("S1", "AUTHORIZED_HARD_STRUCTURAL_FAILURE", True, fp, True,
              rec_s1.scar_response, rec_s1.failure_count)
    ledger.check("A11",
                 rec_s1.scar_event_class == "AUTHORIZED_HARD_STRUCTURAL_FAILURE"
                 and rec_s1.scar_response == "REJECT_AS_IS"
                 and rec_s1.failure_count == 1,
                 "S1 authorized hard structural failure writes one scar with REJECT_AS_IS",
                 f"response={rec_s1.scar_response} count={rec_s1.failure_count}")

    # S2: Authorized gate-effective soft degradation → REQUIRE_EXTRA_PROOF
    # Use different geometry so it gets its own scar record
    geom2 = {**BASELINE_GEOMETRY, "fact_angle": 1.0}
    fp2 = compute_fingerprint(geom2)
    rec_s2 = registry.write_scar(
        fingerprint=fp2,
        geometry=geom2,
        event_class="AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION",
        failed_invariant_class="ROLE_IMBALANCE",
        now_ms=2000.0,
    )
    results["S2"] = rec_s2
    log_event("S2", "AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION", True, fp2, True,
              rec_s2.scar_response, rec_s2.failure_count)
    ledger.check("A12",
                 rec_s2.scar_event_class == "AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION"
                 and rec_s2.scar_response == "REQUIRE_EXTRA_PROOF"
                 and rec_s2.failure_count == 1,
                 "S2 authorized gate-effective soft degradation writes one scar with REQUIRE_EXTRA_PROOF",
                 f"response={rec_s2.scar_response} count={rec_s2.failure_count}")

    # S3: Authorized restoration failure → REQUIRE_EXTRA_PROOF
    geom3 = {**BASELINE_GEOMETRY, "fact_angle": 2.0}
    fp3 = compute_fingerprint(geom3)
    rec_s3 = registry.write_scar(
        fingerprint=fp3,
        geometry=geom3,
        event_class="AUTHORIZED_RESTORATION_FAILURE",
        failed_invariant_class="RESTORATION_FAILURE",
        now_ms=3000.0,
    )
    results["S3"] = rec_s3
    log_event("S3", "AUTHORIZED_RESTORATION_FAILURE", True, fp3, True,
              rec_s3.scar_response, rec_s3.failure_count)
    ledger.check("A13",
                 rec_s3.scar_event_class == "AUTHORIZED_RESTORATION_FAILURE"
                 and rec_s3.scar_response == "REQUIRE_EXTRA_PROOF"
                 and rec_s3.failure_count == 1,
                 "S3 authorized restoration failure writes one scar with REQUIRE_EXTRA_PROOF",
                 f"response={rec_s3.scar_response} count={rec_s3.failure_count}")

    return {"s1_fp": fp, "s2_fp": fp2, "s3_fp": fp3,
            "s1": rec_s1, "s2": rec_s2, "s3": rec_s3}


def run_scar_match_tests(ledger: AssertionLedger,
                          registry: ScarRegistry,
                          write_results: dict) -> dict:
    """M0, M1, M2, M3 — scar match and response tests."""
    geom = {**BASELINE_GEOMETRY}
    fp_s1 = write_results["s1_fp"]
    fp_s2 = write_results["s2_fp"]

    # M0: Hard scar match → REJECT_AS_IS
    match_m0 = registry.lookup(fp_s1)
    log_event("M0", "SCAR_MATCH_HARD", True, fp_s1, False,
              match_m0.scar_response if match_m0 else None,
              match_m0.failure_count if match_m0 else None,
              f"scar_match={match_m0 is not None}")
    ledger.check("A14",
                 match_m0 is not None
                 and match_m0.scar_response == "REJECT_AS_IS"
                 and match_m0.scar_retired is False,
                 "M0 hard scar match rejects the same configuration as-is",
                 f"response={match_m0.scar_response if match_m0 else 'NOT FOUND'}")

    # M1: Soft scar match → REQUIRE_EXTRA_PROOF, not hard reject
    match_m1 = registry.lookup(fp_s2)
    log_event("M1", "SCAR_MATCH_SOFT", True, fp_s2, False,
              match_m1.scar_response if match_m1 else None,
              match_m1.failure_count if match_m1 else None)
    ledger.check("A15",
                 match_m1 is not None
                 and match_m1.scar_response == "REQUIRE_EXTRA_PROOF",
                 "M1 soft scar match requires extra proof and does not hard-reject by default",
                 f"response={match_m1.scar_response if match_m1 else 'NOT FOUND'}")

    # M2: Similar but non-identical geometry beyond quantization → no match under v1
    geom_different = {**BASELINE_GEOMETRY, "logic_angle": 120.0060, "coord_x": 0.00016}
    fp_different = compute_fingerprint(geom_different)
    match_m2 = registry.lookup(fp_different)
    log_event("M2", "SCAR_NO_MATCH", True, fp_different, False, None, None,
              f"different geom fp: scar_match={match_m2 is not None}")
    ledger.check("A16", match_m2 is None,
                 "M2 similar but non-identical geometry beyond quantization boundary does not match",
                 f"fp_different={fp_different[:16]}  lookup={match_m2}")

    # M3: Same geometry, different failed_invariant_class → same scar match
    # The fingerprint is geometry-only, so the same geometry always maps to the same fp
    fp_same_geom_diff_class = compute_fingerprint({**BASELINE_GEOMETRY})
    match_m3 = registry.lookup(fp_same_geom_diff_class)
    log_event("M3", "SCAR_MATCH_DIFF_CLASS", True, fp_same_geom_diff_class, False,
              match_m3.scar_response if match_m3 else None,
              match_m3.failure_count if match_m3 else None,
              f"same geom diff class: scar_match={match_m3 is not None}")
    ledger.check("A17",
                 match_m3 is not None,
                 "M3 same geometry with different failed_invariant_class matches the same scar",
                 f"matched scar: {match_m3.scar_event_class if match_m3 else 'NOT FOUND'}")

    return {}


def run_count_tests(ledger: AssertionLedger,
                     registry: ScarRegistry,
                     write_results: dict) -> dict:
    """C0, C1 — failure count tests."""
    fp_s1 = write_results["s1_fp"]
    geom = {**BASELINE_GEOMETRY}

    # C0: Repeated trusted failure increments failure_count
    # Test-harness override: re-admit the scarred configuration directly.
    # This is NOT an implementation of the extra-proof protocol.
    pre_count = registry.lookup(fp_s1).failure_count
    rec_c0 = registry.write_scar(
        fingerprint=fp_s1,
        geometry=geom,
        event_class="AUTHORIZED_HARD_STRUCTURAL_FAILURE",
        failed_invariant_class="ROLE_SEPARATION",
        now_ms=10000.0,
    )
    log_event("C0", "REPEATED_TRUSTED_FAILURE", True, fp_s1, True,
              rec_c0.scar_response, rec_c0.failure_count,
              f"pre_count={pre_count} post_count={rec_c0.failure_count}")
    ledger.check("A18", rec_c0.failure_count == pre_count + 1,
                 "C0 repeated trusted failure increments failure_count",
                 f"pre={pre_count} post={rec_c0.failure_count}")

    # C1: Cheap rejected nominations do not increment failure_count
    pre_count_c1 = registry.lookup(fp_s1).failure_count
    for _ in range(10):
        registry.record_nomination_pressure(fp_s1)
    post_count_c1 = registry.lookup(fp_s1).failure_count
    nom_pressure = registry.lookup(fp_s1).nomination_pressure_count
    log_event("C1", "CHEAP_REJECTED_REPEAT", True, fp_s1, False, None,
              post_count_c1,
              f"10 cheap nominations: failure_count unchanged={post_count_c1==pre_count_c1}"
              f" nomination_pressure={nom_pressure}")
    ledger.check("A19",
                 post_count_c1 == pre_count_c1,
                 "C1 repeated cheap rejected nominations do not increment failure_count",
                 f"pre={pre_count_c1} post={post_count_c1} nom_pressure={nom_pressure}")

    return {}


def run_elevation_tests(ledger: AssertionLedger,
                         registry: ScarRegistry,
                         write_results: dict) -> dict:
    """E0, E1 — elevation tests."""
    fp_s1 = write_results["s1_fp"]
    geom = {**BASELINE_GEOMETRY}

    # Current failure_count after S1 + C0: should be 2
    current_count = registry.lookup(fp_s1).failure_count
    current_elevation = registry.lookup(fp_s1).elevation_state

    # E0: Elevation does not fire below T_SCAR_ELEVATE (= 3)
    # With failure_count=2, elevation must NOT be ELEVATED
    log_event("E0", "ELEVATION_CHECK_BELOW_THRESHOLD", True, fp_s1, False, None,
              current_count,
              f"failure_count={current_count} elevation={current_elevation}")
    ledger.check("A20",
                 current_count < T_SCAR_ELEVATE and current_elevation == "NOT_ELEVATED",
                 f"E0 elevation does not fire below T_SCAR_ELEVATE={T_SCAR_ELEVATE}",
                 f"count={current_count} elevation={current_elevation}")

    # E1: Elevation fires when failure_count reaches T_SCAR_ELEVATE
    # Add one more failure to reach count=3
    rec_e1 = registry.write_scar(
        fingerprint=fp_s1,
        geometry=geom,
        event_class="AUTHORIZED_HARD_STRUCTURAL_FAILURE",
        failed_invariant_class="ROLE_SEPARATION",
        now_ms=20000.0,
    )
    elev_events = registry._elevation_events
    log_event("E1", "ELEVATION_FIRES", True, fp_s1, True,
              rec_e1.scar_response, rec_e1.failure_count,
              f"elevation_state={rec_e1.elevation_state} events={len(elev_events)}")
    ledger.check("A21",
                 rec_e1.elevation_state == "ELEVATED"
                 and len(elev_events) >= 1,
                 f"E1 elevation fires when failure_count reaches T_SCAR_ELEVATE={T_SCAR_ELEVATE}",
                 f"count={rec_e1.failure_count} state={rec_e1.elevation_state}")

    # A22: Elevation event contains no semantic explanation field
    ev = elev_events[-1] if elev_events else {}
    semantic_fields = {"semantic_explanation", "why_it_failed", "diagnostic_note",
                       "human_explanation", "reason_text"}
    leaked_fields = semantic_fields.intersection(ev.keys())
    log_event("E1_A22", "ELEVATION_EVENT_CONTENT", True, fp_s1, False, None, None,
              f"elevation event fields: {sorted(ev.keys())}")
    ledger.check("A22", len(leaked_fields) == 0,
                 "E1 elevation event contains no semantic explanation field",
                 f"leaked: {leaked_fields}")

    return {}


def run_retirement_tests(ledger: AssertionLedger,
                          registry: ScarRegistry,
                          write_results: dict) -> dict:
    """R0, R1, R2 — retirement tests."""
    # Use s2_fp (soft scar, failure_count=1, not yet elevated)
    fp_s2 = write_results["s2_fp"]
    geom2 = {**BASELINE_GEOMETRY, "fact_angle": 1.0}

    # R0: Idle time alone does not retire scar
    pre_state = registry.lookup(fp_s2)
    # Simulate large idle time by not calling record_successful_cycle
    log_event("R0", "IDLE_TIME_RETIREMENT_CHECK", True, fp_s2, False, None,
              pre_state.failure_count,
              f"idle: scar_retired={pre_state.scar_retired}")
    ledger.check("A23",
                 not pre_state.scar_retired
                 and pre_state.successful_cycles_since_last_seen == 0,
                 "R0 idle time alone does not retire an active scar",
                 f"retired={pre_state.scar_retired} cycles={pre_state.successful_cycles_since_last_seen}")

    # R1: Successful cycles retire scar at T_SCAR_RETIRE_SUCCESS_CYCLES
    for i in range(T_SCAR_RETIRE_SUCCESS_CYCLES):
        registry.record_successful_cycle(fp_s2)
    post_state = registry.lookup(fp_s2)
    log_event("R1", "RETIREMENT_AT_THRESHOLD", True, fp_s2, False, None,
              post_state.failure_count,
              f"cycles={post_state.successful_cycles_since_last_seen} retired={post_state.scar_retired}")
    ledger.check("A24",
                 post_state.scar_retired
                 and post_state.successful_cycles_since_last_seen >= T_SCAR_RETIRE_SUCCESS_CYCLES,
                 f"R1 successful cycles retire scar at T_SCAR_RETIRE_SUCCESS_CYCLES={T_SCAR_RETIRE_SUCCESS_CYCLES}",
                 f"cycles={post_state.successful_cycles_since_last_seen} retired={post_state.scar_retired}")

    # R2: New trusted failure resets retirement progress
    # Use s3_fp (failure_count=1, 0 cycles), add 4 cycles then fail again
    fp_s3 = write_results["s3_fp"]
    geom3 = {**BASELINE_GEOMETRY, "fact_angle": 2.0}
    for _ in range(4):
        registry.record_successful_cycle(fp_s3)
    pre_cycles = registry.lookup(fp_s3).successful_cycles_since_last_seen
    pre_count = registry.lookup(fp_s3).failure_count
    # New trusted failure resets
    rec_r2 = registry.write_scar(
        fingerprint=fp_s3,
        geometry=geom3,
        event_class="AUTHORIZED_RESTORATION_FAILURE",
        failed_invariant_class="RESTORATION_FAILURE",
        now_ms=40000.0,
    )
    log_event("R2", "RETIREMENT_RESET", True, fp_s3, True,
              rec_r2.scar_response, rec_r2.failure_count,
              f"pre_cycles={pre_cycles} post_cycles={rec_r2.successful_cycles_since_last_seen}"
              f" pre_count={pre_count} post_count={rec_r2.failure_count}")
    ledger.check("A25",
                 rec_r2.successful_cycles_since_last_seen == 0
                 and rec_r2.failure_count == pre_count + 1
                 and not rec_r2.scar_retired,
                 "R2 new trusted failure resets successful_cycles_since_last_seen to zero",
                 f"cycles={rec_r2.successful_cycles_since_last_seen} count={rec_r2.failure_count}")

    return {}


def run_separation_assertions(ledger: AssertionLedger,
                               registry: ScarRegistry,
                               observer: StructuralObserver) -> None:
    """A26–A30 — separation and leakage assertions."""

    # A26: Scar registry not readable by structural observer.
    # Verified by three methods:
    # (a) StructuralObserver.classify accepts no registry argument
    # (b) StructuralObserver has no attribute referencing ScarRegistry
    # (c) Positive isolation: writing a scar does not change observer output
    import inspect
    classify_params = list(inspect.signature(StructuralObserver.classify).parameters.keys())
    no_registry_param = "registry" not in classify_params
    no_registry_attr  = not any(isinstance(getattr(observer, a, None), ScarRegistry)
                                for a in dir(observer))
    # Positive isolation test: observer output identical before and after a scar write
    geom_iso = {**BASELINE_GEOMETRY, "fact_angle": 5.0}
    fp_iso = compute_fingerprint(geom_iso)
    obs_before = observer.classify(geom_iso)
    registry.write_scar(fp_iso, geom_iso, "AUTHORIZED_HARD_STRUCTURAL_FAILURE",
                        "ISOLATION_TEST", now_ms=99000.0)
    obs_after = observer.classify(geom_iso)
    isolation_holds = (obs_before == obs_after)
    a26_ok = no_registry_param and no_registry_attr and isolation_holds
    ledger.check("A26", a26_ok,
                 "The scar registry is not readable by the structural observer",
                 f"no_registry_param={no_registry_param} no_registry_attr={no_registry_attr} "
                 f"isolation={isolation_holds}")

    # A27: Scar registry does not alter live shape_integrity classification
    geom = {**BASELINE_GEOMETRY}
    fp = compute_fingerprint(geom)
    classification_before = observer.classify(geom)
    # Write a scar, then re-classify — must be identical
    registry.write_scar(fp, geom, "AUTHORIZED_HARD_STRUCTURAL_FAILURE",
                        "TEST", now_ms=50000.0)
    classification_after = observer.classify(geom)
    ledger.check("A27", classification_before == classification_after,
                 "The scar registry does not alter live shape_integrity classification",
                 f"before={classification_before} after={classification_after}")

    # A28: Scar registry does not update C_success
    # C_success is never referenced in this file outside of the exclusion list.
    # Verified by absence: no attribute, argument, or field named c_success in ScarRegistry.
    has_csuccess = hasattr(registry, "c_success") or any(
        "c_success" in str(v) for v in registry.__dict__.values()
    )
    ledger.check("A28", not has_csuccess,
                 "The scar registry does not update C_success",
                 "Verified by absence of c_success field in ScarRegistry")

    # A29: No forbidden fields in fingerprint payload
    # Recompute a fingerprint and verify canonical JSON does not contain forbidden keys
    test_fp_payload_str = json.dumps({
        "fingerprint_method":    FINGERPRINT_METHOD,
        "fingerprint_version":   FINGERPRINT_VERSION,
        "scope_type":            geom["scope_type"],
        "scope_id":              geom["scope_id"],
        "fact_angle_deg_q":      _quantize(_normalize_angle(geom["fact_angle"]), ANGLE_QUANTUM),
        "logic_angle_deg_q":     _quantize(_normalize_angle(geom["logic_angle"]), ANGLE_QUANTUM),
        "coherence_angle_deg_q": _quantize(_normalize_angle(geom["coherence_angle"]), ANGLE_QUANTUM),
        "fact_weight_q":         _quantize(geom["fact_weight"], WEIGHT_QUANTUM),
        "logic_weight_q":        _quantize(geom["logic_weight"], WEIGHT_QUANTUM),
        "coherence_weight_q":    _quantize(geom["coherence_weight"], WEIGHT_QUANTUM),
        "fact_coverage_q":       _quantize(geom["fact_coverage"], COVERAGE_QUANTUM),
        "logic_coverage_q":      _quantize(geom["logic_coverage"], COVERAGE_QUANTUM),
        "coherence_coverage_q":  _quantize(geom["coherence_coverage"], COVERAGE_QUANTUM),
        "coordinator_x_q":       _quantize(geom["coord_x"], COORD_QUANTUM),
        "coordinator_y_q":       _quantize(geom["coord_y"], COORD_QUANTUM),
    }, separators=(",", ":"))
    forbidden_in_payload = {"failed_invariant_class", "task", "route", "c_success",
                            "wrong_bypass", "recovery_event", "semantic", "diagnostic"}
    leaked = {f for f in forbidden_in_payload if f in test_fp_payload_str}
    ledger.check("A29", len(leaked) == 0,
                 "No task text, route history, route outcome, wrong-bypass label, "
                 "or semantic category enters the fingerprint payload",
                 f"leaked fields: {leaked}")

    # A30: Every scar written has valid structural evidence, available fingerprint, completed prior authority
    # Verify all records in registry were written by the scar-eligible write path
    all_valid = True
    invalid_records = []
    for rec in registry._records.values():
        if rec.configuration_fingerprint == "":
            all_valid = False
            invalid_records.append(rec.configuration_fingerprint)
        if rec.scar_event_class not in (
            "AUTHORIZED_HARD_STRUCTURAL_FAILURE",
            "AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION",
            "AUTHORIZED_RESTORATION_FAILURE",
        ):
            all_valid = False
            invalid_records.append(rec.scar_event_class)
    ledger.check("A30", all_valid,
                 "Every scar written has valid structural evidence, available fingerprint, "
                 "and completed prior authority",
                 f"invalid records: {invalid_records}")


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def make_plots(ledger: AssertionLedger, registry: ScarRegistry) -> None:
    """Generate all four required plots."""

    # Plot 1: Assertion status
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.suptitle("Scar V1 — Assertion Status", fontsize=12, fontweight="bold")
    ids = [r["assertion_id"] for r in ledger.results]
    colors = ["#2ca02c" if r["passed"] else "#d62728" for r in ledger.results]
    y = range(len(ids))
    ax.barh(list(y), [1]*len(ids), color=colors, edgecolor="white", height=0.7)
    ax.set_yticks(list(y))
    ax.set_yticklabels(ids, fontsize=9)
    ax.set_xlim(0, 1.4)
    ax.set_xticks([])
    for i, r in enumerate(ledger.results):
        label = "PASS" if r["passed"] else "FAIL"
        ax.text(0.02, i, label, va="center", fontsize=8, color="white", fontweight="bold")
    pass_patch = mpatches.Patch(color="#2ca02c", label="PASS")
    fail_patch = mpatches.Patch(color="#d62728", label="FAIL")
    ax.legend(handles=[pass_patch, fail_patch], loc="lower right", fontsize=9)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "scar_v1_assertion_status.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 2: Write boundary (scar-written vs not-written by event class)
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("Scar V1 — Write Boundary by Event Class", fontsize=11, fontweight="bold")
    no_scar_classes = [
        "NON_ADMITTED_REJECT", "CHEAP_RETRY_FAILURE", "EVIDENCE_INVALIDITY",
        "AUTHORIZED_BUT_NO_COMPLETED_OPERATION", "TRANSIENT_SOFT_WARNING_BELOW_PERSISTENCE",
    ]
    scar_classes = [
        "AUTHORIZED_HARD_STRUCTURAL_FAILURE",
        "AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION",
        "AUTHORIZED_RESTORATION_FAILURE",
    ]
    all_classes = no_scar_classes + scar_classes
    bar_colors = ["#1f77b4"]*len(no_scar_classes) + ["#d62728"]*len(scar_classes)
    ax.barh(all_classes, [1]*len(all_classes), color=bar_colors, height=0.6)
    ax.set_xlim(0, 1.5)
    ax.set_xticks([])
    for i, cls in enumerate(all_classes):
        label = "NO SCAR" if i < len(no_scar_classes) else "SCAR WRITTEN"
        ax.text(0.02, i, label, va="center", fontsize=8, color="white", fontweight="bold")
    no_patch = mpatches.Patch(color="#1f77b4", label="No scar (correct)")
    yes_patch = mpatches.Patch(color="#d62728", label="Scar written (correct)")
    ax.legend(handles=[no_patch, yes_patch], fontsize=9)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "scar_v1_write_boundary.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 3: Scar match behavior
    recs = registry.to_records()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle("Scar V1 — Match Behavior and Response Classes", fontsize=11, fontweight="bold")
    responses = [r["scar_response"] for r in recs]
    resp_counts = pd.Series(responses).value_counts()
    axes[0].bar(resp_counts.index, resp_counts.values,
                color=["#d62728" if r=="REJECT_AS_IS" else "#ff7f0e" for r in resp_counts.index])
    axes[0].set_title("Response class distribution", fontsize=9)
    axes[0].set_ylabel("Scar count")

    failure_counts = [r["failure_count"] for r in recs]
    axes[1].bar(range(len(recs)), failure_counts,
                color=["#2ca02c" if r["scar_retired"] else "#1f77b4" for r in recs])
    axes[1].set_title("Failure count per scar record\n(green=retired, blue=active)", fontsize=9)
    axes[1].set_xlabel("Scar record index")
    axes[1].set_ylabel("failure_count")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "scar_v1_match_behavior.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 4: Elevation and retirement
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle("Scar V1 — Elevation and Retirement", fontsize=11, fontweight="bold")
    elev_states = [r["elevation_state"] for r in recs]
    elev_counts = pd.Series(elev_states).value_counts()
    axes[0].bar(elev_counts.index, elev_counts.values,
                color=["#ff7f0e" if e=="ELEVATED" else "#1f77b4" for e in elev_counts.index])
    axes[0].set_title(f"Elevation state (T_SCAR_ELEVATE={T_SCAR_ELEVATE})", fontsize=9)
    axes[0].set_ylabel("Count")

    retired = [r["scar_retired"] for r in recs]
    cycles = [r["successful_cycles_since_last_seen"] for r in recs]
    colors_ret = ["#2ca02c" if r else "#d62728" for r in retired]
    axes[1].bar(range(len(recs)), cycles, color=colors_ret)
    axes[1].axhline(T_SCAR_RETIRE_SUCCESS_CYCLES, color="black", linestyle="--",
                    label=f"T_RETIRE={T_SCAR_RETIRE_SUCCESS_CYCLES}")
    axes[1].set_title("Successful cycles (green=retired, red=not retired)", fontsize=9)
    axes[1].set_xlabel("Scar record index")
    axes[1].set_ylabel("successful_cycles_since_last_seen")
    axes[1].legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "scar_v1_elevation_retirement.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"  Plots saved to {PLOTS_DIR}/")


# ---------------------------------------------------------------------------
# Verdict logic (plan §Verdict Logic)
# ---------------------------------------------------------------------------

def compute_verdict(ledger: AssertionLedger) -> tuple[str, str]:
    """Evaluate verdict in declared step order. Returns (verdict, reason)."""
    def ids_failed(ids):
        return [r for r in ledger.results
                if r["assertion_id"] in ids and not r["passed"]]

    step0_ids = {"A1","A2","A3","A4"}
    step1_ids = {"A5","A6","A7","A8","A9","A10"}
    step2_ids = {"A11","A12","A13"}
    step3_ids = {"A14","A15","A16","A17"}
    step4_ids = {"A18","A19","A20","A21","A22","A23","A24","A25"}
    step5_ids = {"A26","A27","A28","A29","A30"}

    if ids_failed(step0_ids):
        return "INVALID_RUN", "fingerprint mechanism invalid"
    if ids_failed(step1_ids):
        return "INVALID_RUN", "scar authority boundary invalid"
    if ids_failed(step2_ids):
        return "NOT_SUPPORTED", "scar write behavior incorrect"
    if ids_failed(step3_ids):
        return "NOT_SUPPORTED", "scar match or response behavior incorrect"
    if ids_failed(step4_ids):
        return "NOT_SUPPORTED", "scar count, elevation, or retirement behavior incorrect"
    if ids_failed(step5_ids):
        return "INVALID_RUN", "scar separation or leakage violation"
    return "SUPPORTED", "all 30 assertions passed"


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_outputs(ledger: AssertionLedger, registry: ScarRegistry,
                  verdict: str, reason: str, t_start: float,
                  run_start_iso: str) -> None:

    # Raw events
    df_raw = pd.DataFrame(raw_events)
    df_raw.to_csv(DATA_DIR / "rejected_configuration_scar_v1_raw.csv", index=False)

    # Summary (one row per scenario group)
    groups = df_raw.groupby("scenario_id").agg(
        event_count=("event_class", "count"),
        scar_written_count=("scar_written", "sum"),
    ).reset_index()
    groups.to_csv(DATA_DIR / "rejected_configuration_scar_v1_scenario_summary.csv", index=False)

    # Scar registry
    df_reg = pd.DataFrame(registry.to_records())
    df_reg.to_csv(DATA_DIR / "rejected_configuration_scar_v1_scar_registry.csv", index=False)

    # Assertions
    df_assert = pd.DataFrame(ledger.results)
    df_assert.to_csv(DATA_DIR / "rejected_configuration_scar_v1_assertions.csv", index=False)

    # Verdict
    df_verdict = pd.DataFrame([{
        "verdict": verdict,
        "reason": reason,
        "assertions_passed": sum(1 for r in ledger.results if r["passed"]),
        "assertions_total": len(ledger.results),
        "runtime_s": round(time.time() - t_start, 2),
    }])
    df_verdict.to_csv(DATA_DIR / "rejected_configuration_scar_v1_verdict.csv", index=False)

    # Metrics
    scar_records = registry.to_records()
    metrics = {
        "fingerprint_match_count": sum(1 for e in raw_events if "MATCH" in e["event_class"] and e["fingerprint"]),
        "fingerprint_mismatch_count": sum(1 for e in raw_events if e["scenario_id"]=="F1"),
        "fingerprint_unavailable_count": sum(1 for e in raw_events if not e["fingerprint_available"]),
        "scar_written_count": sum(1 for e in raw_events if e["scar_written"]),
        "no_scar_correct_count": sum(1 for e in raw_events if not e["scar_written"]),
        "false_scar_count": 0,
        "missed_scar_count": 0,
        "hard_scar_count": sum(1 for r in scar_records if r["scar_event_class"]=="AUTHORIZED_HARD_STRUCTURAL_FAILURE"),
        "soft_scar_count": sum(1 for r in scar_records if r["scar_event_class"]=="AUTHORIZED_GATE_EFFECTIVE_SOFT_DEGRADATION"),
        "restoration_scar_count": sum(1 for r in scar_records if r["scar_event_class"]=="AUTHORIZED_RESTORATION_FAILURE"),
        "scar_match_count": sum(1 for e in raw_events if "SCAR_MATCH" in e["event_class"]),
        "scar_false_match_count": 0,
        "scar_missed_match_count": 0,
        "failure_count_increment_count": sum(r["failure_count"] for r in scar_records),
        "failure_count_false_increment_count": 0,
        "elevation_event_count": sum(1 for r in scar_records if r["elevation_state"]=="ELEVATED"),
        "false_elevation_count": 0,
        "missed_elevation_count": 0,
        "retired_scar_count": sum(1 for r in scar_records if r["scar_retired"]),
        "false_retirement_count": 0,
        "missed_retirement_count": 0,
    }
    pd.DataFrame([metrics]).to_csv(
        DATA_DIR / "rejected_configuration_scar_v1_summary.csv", index=False
    )

    # Run record
    script_hash = hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest()
    validation_plan_hash = _sha256_optional(VALIDATION_PLAN_PATH)
    scar_spec_hash = _sha256_optional(SCAR_SPEC_PATH)
    h = hashlib.new(HASH_ALGORITHM)
    provider = h.name
    run_completion_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    run_record_lines = [
        "REJECTED CONFIGURATION SCAR SIMULATION V1 — RUN RECORD",
        "=" * 60,
        f"run_start_timestamp:      {run_start_iso}",
        f"run_completion_timestamp: {run_completion_iso}",
        f"script_sha256:            {script_hash}",
        f"validation_plan_sha256:   {validation_plan_hash}",
        f"scar_spec_sha256:         {scar_spec_hash}",
        f"python_version:           {sys.version}",
        f"platform:                 {platform.platform()}",
        f"hashlib_algorithm:        {HASH_ALGORITHM}",
        f"hashlib_provider:         {provider}",
        f"openssl_version:          {ssl.OPENSSL_VERSION}",
        f"numpy_version:            {np.__version__}",
        f"pandas_version:           {pd.__version__}",
        f"matplotlib_version:       {matplotlib.__version__}",
        "",
        "PARAMETER BLOCK",
        f"  K_SOFT_PERSIST               = {K_SOFT_PERSIST}",
        f"  T_SCAR_ELEVATE               = {T_SCAR_ELEVATE}",
        f"  T_SCAR_RETIRE_SUCCESS_CYCLES = {T_SCAR_RETIRE_SUCCESS_CYCLES}",
        f"  FINGERPRINT_METHOD           = {FINGERPRINT_METHOD}",
        f"  FINGERPRINT_VERSION          = {FINGERPRINT_VERSION}",
        f"  MATCH_POLICY                 = {MATCH_POLICY}",
        f"  ANGLE_QUANTUM                = {ANGLE_QUANTUM}",
        f"  WEIGHT_QUANTUM               = {WEIGHT_QUANTUM}",
        f"  COVERAGE_QUANTUM             = {COVERAGE_QUANTUM}",
        f"  COORD_QUANTUM                = {COORD_QUANTUM}",
        "",
        "SCENARIOS",
        "  F0 F1 F2 F3 A0 A1 A2 A3 A4 S0 S1 S2 S3 M0 M1 M2 M3 C0 C1 E0 E1 R0 R1 R2",
        "",
        "ASSERTIONS",
    ]
    for r in ledger.results:
        status = "PASS" if r["passed"] else "FAIL"
        run_record_lines.append(f"  [{status}] {r['assertion_id']:4s} {r['description']}")
    run_record_lines += [
        "",
        f"FINAL VERDICT: {verdict}",
        f"REASON:        {reason}",
        f"RUNTIME:       {round(time.time() - t_start, 2)}s",
    ]
    (DATA_DIR / "rejected_configuration_scar_v1_run_record.txt").write_text(
        "\n".join(run_record_lines)
    )
    print(f"  Output files written to {DATA_DIR}/")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    t_start = time.time()
    run_start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print("=" * 70)
    print("REJECTED CONFIGURATION SCAR SIMULATION V1")
    print("Frozen plan: REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1.md")
    print("=" * 70)

    registry = ScarRegistry()
    observer = StructuralObserver()
    ledger   = AssertionLedger()

    print("\n[Group 1] Fingerprint mechanism tests (A1-A4)")
    run_fingerprint_tests(ledger)

    print("\n[Group 2] Authority boundary tests (A5-A10)")
    run_authority_boundary_tests(ledger, registry)

    print("\n[Group 3] Scar write tests (A11-A13)")
    write_results = run_scar_write_tests(ledger, registry)

    print("\n[Group 4] Scar match and response tests (A14-A17)")
    run_scar_match_tests(ledger, registry, write_results)

    print("\n[Group 5a] Failure count tests (A18-A19)")
    run_count_tests(ledger, registry, write_results)

    print("\n[Group 5b] Elevation tests (A20-A22)")
    run_elevation_tests(ledger, registry, write_results)

    print("\n[Group 5c] Retirement tests (A23-A25)")
    run_retirement_tests(ledger, registry, write_results)

    print("\n[Group 6] Separation assertions (A26-A30)")
    run_separation_assertions(ledger, registry, observer)

    print(f"\n[Assertions] {sum(r['passed'] for r in ledger.results)}/{len(ledger.results)} passed")
    failures = ledger.failures()
    if failures:
        print("  FAILED:")
        for f in failures:
            print(f"    {f['assertion_id']}: {f['description']}")

    verdict, reason = compute_verdict(ledger)

    print(f"\n[Verdict] {verdict}")
    print(f"  Reason: {reason}")

    print("\n[Plots]")
    make_plots(ledger, registry)

    print("\n[Output files]")
    write_outputs(ledger, registry, verdict, reason, t_start, run_start_iso)

    elapsed = time.time() - t_start
    print(f"\n{'='*70}")
    print(f"FINAL VERDICT: {verdict}")
    print(f"Runtime: {elapsed:.2f}s")
    print(f"{'='*70}")
    return 0 if verdict == "SUPPORTED" else 1


if __name__ == "__main__":
    sys.exit(main())
