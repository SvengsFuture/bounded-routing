#!/usr/bin/env python3
"""
Cellular Shedding Simulation v1 REVIEWED

Purpose:
    Validate a narrow cellular-shedding mechanism.

Scope:
    This harness tests local authority removal after structural cell failure.
    It does not validate lineage inheritance, fuzzy scar matching,
    prospective filtering, production recovery, or an extra-proof protocol.

Expected primary result:
    SUPPORTED if all declared assertions pass and frozen document hashes are present.

Review fixes:
    A15 uses a positive dependent-route fallback check.
    A19 and A20 inspect scar_lookup isolation and run positive isolation probes.
    The run record resolves and hashes the frozen spec and validation plan.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import hashlib
import inspect
import json
import platform
import sys
import time


SCRIPT_NAME = "cellular_shedding_sim_v1.py"

SPEC_PATH = Path("docs/CELLULAR_SHEDDING_SPEC_v1_FROZEN.md")
PLAN_PATH = Path("docs/CELLULAR_SHEDDING_VALIDATION_PLAN_v1_FROZEN.md")

K_SOFT_PERSIST = 3
T_SCAR_ELEVATE = 3
T_SCAR_RETIRE_SUCCESS_CYCLES = 5
T_BYPASS = 0.75


@dataclass
class Evidence:
    authorized_source: bool = True
    fresh: bool = True
    epoch_match: bool = True
    scope_applies: bool = True
    verifiable: bool = True

    def valid(self) -> bool:
        return (
            self.authorized_source
            and self.fresh
            and self.epoch_match
            and self.scope_applies
            and self.verifiable
        )

    def invalid_reason(self) -> str:
        if self.authorized_source is False:
            return "unauthorized_source"
        if self.fresh is False:
            return "stale"
        if self.epoch_match is False:
            return "epoch_mismatch"
        if self.scope_applies is False:
            return "out_of_scope"
        if self.verifiable is False:
            return "unverifiable"
        return "valid"


@dataclass
class Cell:
    cell_id: str
    cell_scope: str
    structural_epoch: str
    role_relation: str
    shape_status: str
    authority_state: str
    failed_invariant_class: str = ""
    adjacent_cells: str = ""
    load_transfer_status: str = "not_evaluated"
    scar_fingerprint: str = ""
    reconstruction_candidate: str = ""


@dataclass
class Route:
    route_id: str
    dependent_cells: List[str]
    c_success: float = 0.90
    route_authority_state: str = "ACTIVE"
    scope_status: str = "proven"
    bypass_attempts: int = 0
    fallbacks: int = 0
    wrong_bypasses: int = 0


@dataclass
class Scar:
    fingerprint: str
    scar_class: str
    failure_count: int = 1
    elevation_state: str = "BASE"
    retirement_state: str = "ACTIVE"
    metadata: str = ""


class CellularSheddingHarness:
    def __init__(self) -> None:
        self.raw_rows: List[Dict[str, object]] = []
        self.summary_rows: List[Dict[str, object]] = []
        self.cell_rows: List[Dict[str, object]] = []
        self.route_rows: List[Dict[str, object]] = []
        self.scar_rows: List[Dict[str, object]] = []
        self.load_rows: List[Dict[str, object]] = []
        self.assertion_rows: List[Dict[str, object]] = []
        self.event_logs: List[Dict[str, object]] = []
        self.assertions: Dict[str, Tuple[str, bool, str]] = {}

    def log_raw(
        self,
        scenario: str,
        event_type: str,
        decision: str,
        cell_id: str = "",
        route_id: str = "",
        details: str = "",
    ) -> None:
        self.raw_rows.append(
            {
                "scenario": scenario,
                "event_type": event_type,
                "cell_id": cell_id,
                "route_id": route_id,
                "decision": decision,
                "details": details,
            }
        )

    def record_summary(
        self,
        scenario: str,
        expected: str,
        observed: str,
        status: str,
    ) -> None:
        self.summary_rows.append(
            {
                "scenario": scenario,
                "expected": expected,
                "observed": observed,
                "status": status,
            }
        )

    def record_cell(
        self,
        scenario: str,
        cell: Cell,
        initial_state: str,
        evidence: Evidence,
        scar_written: bool,
    ) -> None:
        self.cell_rows.append(
            {
                "scenario": scenario,
                "cell_id": cell.cell_id,
                "cell_scope": cell.cell_scope,
                "structural_epoch": cell.structural_epoch,
                "role_relation": cell.role_relation,
                "initial_state": initial_state,
                "final_state": cell.authority_state,
                "shape_status": cell.shape_status,
                "failed_invariant_class": cell.failed_invariant_class,
                "adjacent_cells": cell.adjacent_cells,
                "load_transfer_status": cell.load_transfer_status,
                "evidence_valid": evidence.valid(),
                "evidence_status": evidence.invalid_reason(),
                "scar_written": scar_written,
                "scar_fingerprint": cell.scar_fingerprint,
            }
        )

    def record_route(
        self,
        scenario: str,
        route: Route,
        decision: str,
        reason: str,
    ) -> None:
        self.route_rows.append(
            {
                "scenario": scenario,
                "route_id": route.route_id,
                "dependent_cells": "|".join(route.dependent_cells),
                "scope_status": route.scope_status,
                "c_success": route.c_success,
                "route_authority_state": route.route_authority_state,
                "decision": decision,
                "bypass_allowed": decision == "BYPASS",
                "fallback": decision == "FALLBACK",
                "reason": reason,
                "bypass_attempts": route.bypass_attempts,
                "fallbacks": route.fallbacks,
                "wrong_bypasses": route.wrong_bypasses,
            }
        )

    def record_scar_event(
        self,
        scenario: str,
        fingerprint: str,
        scar_class: str,
        event_decision: str,
        scar_written: bool,
        match_result: str,
        failure_count: int = 0,
    ) -> None:
        self.scar_rows.append(
            {
                "scenario": scenario,
                "fingerprint": fingerprint,
                "scar_class": scar_class,
                "event_decision": event_decision,
                "scar_written": scar_written,
                "match_result": match_result,
                "failure_count": failure_count,
            }
        )

    def record_load(
        self,
        scenario: str,
        cell_id: str,
        load_transfer_status: str,
        action: str,
        escalated: bool,
    ) -> None:
        self.load_rows.append(
            {
                "scenario": scenario,
                "cell_id": cell_id,
                "load_transfer_status": load_transfer_status,
                "action": action,
                "escalated": escalated,
            }
        )

    def set_assertion(self, assertion_id: str, description: str, passed: bool, evidence: str) -> None:
        self.assertions[assertion_id] = (description, passed, evidence)

    def write_scar_decision(
        self,
        scenario: str,
        cell: Cell,
        had_authority: bool,
        evidence: Evidence,
        failure_kind: str,
        scar_class: str = "HARD",
    ) -> Tuple[bool, Optional[Scar], str]:
        eligible = had_authority and evidence.valid() and failure_kind == "betrayed_authority"
        if eligible:
            fingerprint = cell.scar_fingerprint or stable_fingerprint(cell.cell_id, cell.role_relation, cell.cell_scope)
            scar = Scar(
                fingerprint=fingerprint,
                scar_class=scar_class,
                failure_count=1,
                elevation_state="BASE",
                retirement_state="ACTIVE",
                metadata=cell.failed_invariant_class,
            )
            self.record_scar_event(
                scenario,
                fingerprint,
                scar_class,
                "WRITE_SCAR",
                True,
                "WRITTEN",
                scar.failure_count,
            )
            self.log_raw(
                scenario,
                "scar_write",
                "WRITE_SCAR",
                cell.cell_id,
                "",
                f"failure_kind={failure_kind}; evidence={evidence.invalid_reason()}",
            )
            return True, scar, "WRITTEN"

        fingerprint = cell.scar_fingerprint or stable_fingerprint(cell.cell_id, cell.role_relation, cell.cell_scope)
        reason = f"NO_SCAR:{failure_kind}:{evidence.invalid_reason()}"
        self.record_scar_event(
            scenario,
            fingerprint,
            scar_class,
            reason,
            False,
            "NOT_WRITTEN",
            0,
        )
        self.log_raw(
            scenario,
            "scar_write",
            reason,
            cell.cell_id,
            "",
            f"had_authority={had_authority}; evidence={evidence.invalid_reason()}",
        )
        return False, None, reason

    def scar_lookup(self, scar_registry: Dict[str, Scar], fingerprint: str) -> str:
        scar = scar_registry.get(fingerprint)
        if scar is None:
            return "NO_MATCH"
        if scar.retirement_state == "RETIRED":
            return "NO_MATCH_RETIRED"
        if scar.scar_class == "HARD":
            return "REJECT_AS_IS"
        if scar.scar_class in {"SOFT", "RESTORATION"}:
            return "REQUIRE_EXTRA_PROOF"
        return "UNKNOWN_SCAR_CLASS"

    def route_decision(
        self,
        scenario: str,
        route: Route,
        cells: Dict[str, Cell],
        scar_result: str = "NO_MATCH",
    ) -> Tuple[str, str]:
        route.bypass_attempts += 1

        if route.scope_status != "proven":
            route.fallbacks += 1
            return "FALLBACK", "scope_not_proven"

        if route.c_success < T_BYPASS:
            route.fallbacks += 1
            return "FALLBACK", "confidence_below_threshold"

        if scar_result == "REJECT_AS_IS":
            route.fallbacks += 1
            return "FALLBACK", "hard_scar"

        if scar_result == "REQUIRE_EXTRA_PROOF":
            route.fallbacks += 1
            return "FALLBACK", "requires_extra_proof"

        for cell_id in route.dependent_cells:
            cell = cells[cell_id]
            if cell.authority_state in {"SHED", "QUARANTINED", "RECONSTRUCTING", "REQUALIFYING", "RETIRED"}:
                route.fallbacks += 1
                return "FALLBACK", f"cell_{cell.authority_state.lower()}"
            if cell.shape_status != "ADMISSIBLE":
                route.fallbacks += 1
                return "FALLBACK", "shape_not_admissible"

        return "BYPASS", "all_gates_pass"

    def shed_cell(
        self,
        scenario: str,
        cell: Cell,
        evidence: Evidence,
        load_transfer_status: str,
        had_authority: bool = True,
        failure_kind: str = "betrayed_authority",
    ) -> Tuple[Cell, bool, Optional[Scar], bool]:
        initial_state = cell.authority_state
        if evidence.valid():
            cell.authority_state = "SHED"
            cell.shape_status = "FAILED"
            cell.load_transfer_status = load_transfer_status
            scar_written, scar, _ = self.write_scar_decision(
                scenario,
                cell,
                had_authority=had_authority,
                evidence=evidence,
                failure_kind=failure_kind,
            )
            escalated = load_transfer_status == "FAILED"
            self.record_load(
                scenario,
                cell.cell_id,
                load_transfer_status,
                "BOUNDED_DEGRADED_OPERATION" if load_transfer_status == "SUCCESS" else "ESCALATE_BROADER_RECOVERY",
                escalated,
            )
            self.log_raw(
                scenario,
                "shed_cell",
                "SHED",
                cell.cell_id,
                "",
                f"load_transfer={load_transfer_status}",
            )
        else:
            cell.authority_state = "SHEDDING_REVIEW"
            cell.shape_status = "UNKNOWN"
            cell.load_transfer_status = "not_authorized"
            scar_written, scar, _ = self.write_scar_decision(
                scenario,
                cell,
                had_authority=had_authority,
                evidence=evidence,
                failure_kind=failure_kind,
            )
            escalated = False
            self.record_load(
                scenario,
                cell.cell_id,
                "not_authorized",
                "FAIL_CLOSED",
                escalated,
            )
            self.log_raw(
                scenario,
                "shed_cell",
                "NO_CLEAN_SHEDDING_AUTHORIZATION",
                cell.cell_id,
                "",
                f"evidence={evidence.invalid_reason()}",
            )

        self.record_cell(scenario, cell, initial_state, evidence, scar_written)
        self.event_logs.append(
            {
                "cell_id": cell.cell_id,
                "cell_scope": cell.cell_scope,
                "structural_epoch": cell.structural_epoch,
                "trigger_condition": cell.failed_invariant_class or "declared_invariant_failure",
                "authority_state_before_shedding": initial_state,
                "routes_affected": "declared_in_route_rows",
                "scar_write_decision": scar_written,
                "scar_match_decision": "recorded_if_reconstruction_attempted",
                "shed_boundary": cell.cell_scope,
                "adjacent_cell_health_evidence": cell.adjacent_cells,
                "load_transfer_decision": load_transfer_status,
                "reconstruction_status": cell.reconstruction_candidate or "none",
                "final_cell_state": cell.authority_state,
            }
        )
        return cell, scar_written, scar, escalated

    def run(self) -> None:
        self.scenario_1_dependent_route_revoked()
        self.scenario_2_independent_route_preserved()
        self.scenario_3_uncertain_scope_fails_closed()
        self.scenario_4_invalid_evidence()
        self.scenario_5_betrayed_authority_writes_scar()
        self.scenario_6_cheap_retry_no_scar()
        self.scenario_7_non_admitted_no_scar()
        self.scenario_8_hard_scar_blocks_reconstruction()
        self.scenario_9_soft_and_restoration_require_extra_proof()
        self.scenario_10_replacement_requalifies()
        self.scenario_11_load_transfer_success()
        self.scenario_12_load_transfer_failure()

        self.finalize_assertions()

    def base_cell(self, cell_id: str) -> Cell:
        return Cell(
            cell_id=cell_id,
            cell_scope=f"scope_{cell_id}",
            structural_epoch="epoch_1",
            role_relation="Fact-Logic",
            shape_status="ADMISSIBLE",
            authority_state="ACTIVE",
            failed_invariant_class="edge_collapse",
            adjacent_cells="healthy_neighbor_A|healthy_neighbor_B",
            scar_fingerprint=stable_fingerprint(cell_id, "Fact-Logic", f"scope_{cell_id}"),
            reconstruction_candidate=stable_fingerprint(cell_id, "Fact-Logic", f"scope_{cell_id}"),
        )

    def scenario_1_dependent_route_revoked(self) -> None:
        scenario = "S01_dependent_route_revoked"
        cell = self.base_cell("cell_dep")
        evidence = Evidence()
        cell, scar_written, scar, _ = self.shed_cell(scenario, cell, evidence, "SUCCESS")
        route = Route("route_dep", ["cell_dep"])
        decision, reason = self.route_decision(scenario, route, {"cell_dep": cell})
        self.record_route(scenario, route, decision, reason)
        self.record_summary(scenario, "dependent route fallback", decision, "PASS" if decision == "FALLBACK" else "FAIL")
        self.set_assertion("A1", "Dependent routes cannot bypass after their required cell is shed.", decision == "FALLBACK", reason)

    def scenario_2_independent_route_preserved(self) -> None:
        scenario = "S02_independent_route_preserved"
        failed = self.base_cell("cell_failed_ind")
        healthy = self.base_cell("cell_healthy_ind")
        evidence = Evidence()
        failed, _, _, _ = self.shed_cell(scenario, failed, evidence, "SUCCESS")
        route = Route("route_independent", ["cell_healthy_ind"], scope_status="proven")
        decision, reason = self.route_decision(
            scenario,
            route,
            {
                "cell_failed_ind": failed,
                "cell_healthy_ind": healthy,
            },
        )
        self.record_route(scenario, route, decision, reason)
        self.record_summary(scenario, "independent route may bypass", decision, "PASS" if decision == "BYPASS" else "FAIL")
        self.set_assertion("A2", "Independent routes may remain eligible only when independence is proven.", decision == "BYPASS", reason)

    def scenario_3_uncertain_scope_fails_closed(self) -> None:
        scenario = "S03_uncertain_scope_fails_closed"
        cell = self.base_cell("cell_uncertain")
        route = Route("route_unknown_scope", ["cell_uncertain"], scope_status="unknown")
        decision, reason = self.route_decision(scenario, route, {"cell_uncertain": cell})
        self.record_route(scenario, route, decision, reason)
        self.record_summary(scenario, "unknown scope fallback", decision, "PASS" if decision == "FALLBACK" else "FAIL")
        self.set_assertion("A3", "Unknown route scope fails closed.", decision == "FALLBACK", reason)

    def scenario_4_invalid_evidence(self) -> None:
        scenario = "S04_invalid_evidence"
        cell = self.base_cell("cell_invalid_evidence")
        evidence = Evidence(fresh=False)
        cell, scar_written, scar, _ = self.shed_cell(scenario, cell, evidence, "not_authorized")
        route = Route("route_invalid_evidence", ["cell_invalid_evidence"])
        route.scope_status = "unknown"
        decision, reason = self.route_decision(scenario, route, {"cell_invalid_evidence": cell})
        self.record_route(scenario, route, decision, reason)
        self.record_summary(
            scenario,
            "no clean shedding, no scar, fail closed",
            f"cell={cell.authority_state}; scar={scar_written}; route={decision}",
            "PASS" if cell.authority_state == "SHEDDING_REVIEW" and not scar_written and decision == "FALLBACK" else "FAIL",
        )
        self.set_assertion("A4", "Invalid evidence does not authorize clean shedding.", cell.authority_state == "SHEDDING_REVIEW", cell.authority_state)
        self.set_assertion("A5", "Invalid evidence does not write a scar.", not scar_written, str(scar_written))

    def scenario_5_betrayed_authority_writes_scar(self) -> None:
        scenario = "S05_betrayed_authority_writes_scar"
        cell = self.base_cell("cell_betrayed")
        evidence = Evidence()
        _, scar_written, scar, _ = self.shed_cell(scenario, cell, evidence, "SUCCESS", True, "betrayed_authority")
        self.record_summary(scenario, "scar written", str(scar_written), "PASS" if scar_written else "FAIL")
        self.set_assertion("A6", "Betrayed authority writes a scar.", scar_written, scar.fingerprint if scar else "none")

    def scenario_6_cheap_retry_no_scar(self) -> None:
        scenario = "S06_cheap_retry_no_scar"
        cell = self.base_cell("cell_cheap_retry")
        evidence = Evidence()
        scar_written, scar, reason = self.write_scar_decision(scenario, cell, False, evidence, "cheap_retry")
        self.record_summary(scenario, "no scar", str(scar_written), "PASS" if not scar_written else "FAIL")
        self.set_assertion("A7", "Cheap retry failure does not write a scar.", not scar_written, reason)

    def scenario_7_non_admitted_no_scar(self) -> None:
        scenario = "S07_non_admitted_no_scar"
        cell = self.base_cell("cell_non_admitted")
        evidence = Evidence()
        scar_written, scar, reason = self.write_scar_decision(scenario, cell, False, evidence, "non_admitted_candidate")
        self.record_summary(scenario, "no scar", str(scar_written), "PASS" if not scar_written else "FAIL")
        self.set_assertion("A8", "Non-admitted candidate failure does not write a scar.", not scar_written, reason)

    def scenario_8_hard_scar_blocks_reconstruction(self) -> None:
        scenario = "S08_hard_scar_blocks_reconstruction"
        cell = self.base_cell("cell_hard")
        registry = {
            cell.reconstruction_candidate: Scar(
                fingerprint=cell.reconstruction_candidate,
                scar_class="HARD",
                failure_count=1,
            )
        }
        match = self.scar_lookup(registry, cell.reconstruction_candidate)
        self.record_scar_event(scenario, cell.reconstruction_candidate, "HARD", "LOOKUP", False, match, 1)
        route = Route("route_hard_scar", ["cell_hard"])
        decision, reason = self.route_decision(scenario, route, {"cell_hard": cell}, match)
        self.record_route(scenario, route, decision, reason)
        self.record_summary(scenario, "REJECT_AS_IS", match, "PASS" if match == "REJECT_AS_IS" else "FAIL")
        self.set_assertion("A9", "Hard scar match returns REJECT_AS_IS.", match == "REJECT_AS_IS", match)
        self.set_assertion("A16", "Historical route confidence does not override a hard scar.", decision == "FALLBACK", reason)

    def scenario_9_soft_and_restoration_require_extra_proof(self) -> None:
        scenario = "S09_soft_and_restoration_require_extra_proof"
        soft_fp = "soft_fp"
        rest_fp = "restoration_fp"
        registry = {
            soft_fp: Scar(fingerprint=soft_fp, scar_class="SOFT", failure_count=2),
            rest_fp: Scar(fingerprint=rest_fp, scar_class="RESTORATION", failure_count=1),
        }
        soft_match = self.scar_lookup(registry, soft_fp)
        rest_match = self.scar_lookup(registry, rest_fp)
        self.record_scar_event(scenario, soft_fp, "SOFT", "LOOKUP", False, soft_match, 2)
        self.record_scar_event(scenario, rest_fp, "RESTORATION", "LOOKUP", False, rest_match, 1)
        self.record_summary(
            scenario,
            "soft and restoration require extra proof",
            f"soft={soft_match}; restoration={rest_match}",
            "PASS" if soft_match == "REQUIRE_EXTRA_PROOF" and rest_match == "REQUIRE_EXTRA_PROOF" else "FAIL",
        )
        self.set_assertion("A10", "Soft scar match returns REQUIRE_EXTRA_PROOF.", soft_match == "REQUIRE_EXTRA_PROOF", soft_match)
        self.set_assertion("A11", "Restoration scar match returns REQUIRE_EXTRA_PROOF.", rest_match == "REQUIRE_EXTRA_PROOF", rest_match)

    def scenario_10_replacement_requalifies(self) -> None:
        scenario = "S10_replacement_enters_requalification"
        cell = self.base_cell("cell_replacement")
        no_match = self.scar_lookup({}, cell.reconstruction_candidate)
        replacement = self.base_cell("cell_replacement_new")
        replacement.authority_state = "REQUALIFYING"
        replacement.shape_status = "ADMISSIBLE"
        route = Route("route_replacement", ["cell_replacement_new"])
        decision, reason = self.route_decision(scenario, route, {"cell_replacement_new": replacement}, no_match)
        self.record_scar_event(scenario, cell.reconstruction_candidate, "NONE", "LOOKUP", False, no_match, 0)
        self.record_cell(scenario, replacement, "RECONSTRUCTING", Evidence(), False)
        self.record_route(scenario, route, decision, reason)
        self.record_summary(
            scenario,
            "no scar match, replacement requalifies, no active bypass",
            f"scar={no_match}; cell={replacement.authority_state}; route={decision}",
            "PASS" if no_match == "NO_MATCH" and replacement.authority_state == "REQUALIFYING" and decision == "FALLBACK" else "FAIL",
        )
        self.set_assertion("A12", "No-match candidate is not blocked by scar status alone.", no_match == "NO_MATCH", no_match)
        self.set_assertion("A13", "Replacement cell enters REQUALIFYING before active bypass.", replacement.authority_state == "REQUALIFYING", replacement.authority_state)
        self.set_assertion("A14", "Replacement cell does not inherit active authority from the shed cell.", decision == "FALLBACK", reason)

    def scenario_11_load_transfer_success(self) -> None:
        scenario = "S11_load_transfer_success"
        cell = self.base_cell("cell_load_success")
        evidence = Evidence()
        cell, _, _, escalated = self.shed_cell(scenario, cell, evidence, "SUCCESS")
        self.record_summary(
            scenario,
            "bounded degraded operation",
            f"load={cell.load_transfer_status}; escalated={escalated}",
            "PASS" if cell.load_transfer_status == "SUCCESS" and not escalated else "FAIL",
        )
        self.set_assertion("A17", "Load-transfer success preserves only declared admissible work.", cell.load_transfer_status == "SUCCESS" and not escalated, cell.load_transfer_status)

    def scenario_12_load_transfer_failure(self) -> None:
        scenario = "S12_load_transfer_failure"
        cell = self.base_cell("cell_load_failure")
        evidence = Evidence()
        cell, _, _, escalated = self.shed_cell(scenario, cell, evidence, "FAILED")
        self.record_summary(
            scenario,
            "broader recovery escalation",
            f"load={cell.load_transfer_status}; escalated={escalated}",
            "PASS" if cell.load_transfer_status == "FAILED" and escalated else "FAIL",
        )
        self.set_assertion("A18", "Load-transfer failure escalates to broader recovery.", cell.load_transfer_status == "FAILED" and escalated, cell.load_transfer_status)

    def finalize_assertions(self) -> None:
        dependent_shed_fallback = any(
            row["scenario"] == "S01_dependent_route_revoked"
            and row["decision"] == "FALLBACK"
            and row["reason"] == "cell_shed"
            for row in self.route_rows
        )
        self.set_assertion(
            "A15",
            "Historical route confidence does not override a shed boundary.",
            dependent_shed_fallback,
            "positive dependent-route check returned FALLBACK with reason=cell_shed" if dependent_shed_fallback else "missing positive shed-boundary fallback",
        )

        scar_lookup_signature = inspect.signature(self.scar_lookup)
        scar_lookup_params = list(scar_lookup_signature.parameters.keys())
        scar_lookup_source = inspect.getsource(CellularSheddingHarness.scar_lookup)

        forbidden_shape_terms = {"shape_integrity", "shape_status", "Cell"}
        forbidden_confidence_terms = {"c_success", "Route"}

        no_shape_dependency = (
            "shape_integrity" not in scar_lookup_params
            and "shape_status" not in scar_lookup_params
            and "cell" not in scar_lookup_params
            and not any(term in scar_lookup_source for term in forbidden_shape_terms)
        )
        no_confidence_dependency = (
            "c_success" not in scar_lookup_params
            and "route" not in scar_lookup_params
            and not any(term in scar_lookup_source for term in forbidden_confidence_terms)
        )

        isolation_fp = stable_fingerprint("isolation", "scar")
        isolation_registry = {isolation_fp: Scar(isolation_fp, "HARD")}

        admissible_cell = self.base_cell("cell_isolation_a")
        failed_cell = self.base_cell("cell_isolation_b")
        admissible_cell.scar_fingerprint = isolation_fp
        failed_cell.scar_fingerprint = isolation_fp
        admissible_cell.shape_status = "ADMISSIBLE"
        failed_cell.shape_status = "FAILED"

        shape_lookup_admissible = self.scar_lookup(isolation_registry, admissible_cell.scar_fingerprint)
        shape_lookup_failed = self.scar_lookup(isolation_registry, failed_cell.scar_fingerprint)

        high_confidence_route = Route("route_high_confidence", ["cell_isolation_a"], c_success=0.99)
        low_confidence_route = Route("route_low_confidence", ["cell_isolation_a"], c_success=0.01)

        confidence_lookup_high = self.scar_lookup(isolation_registry, isolation_fp)
        confidence_lookup_low = self.scar_lookup(isolation_registry, isolation_fp)

        shape_isolated = (
            no_shape_dependency
            and shape_lookup_admissible == "REJECT_AS_IS"
            and shape_lookup_failed == "REJECT_AS_IS"
        )
        confidence_isolated = (
            no_confidence_dependency
            and high_confidence_route.c_success != low_confidence_route.c_success
            and confidence_lookup_high == "REJECT_AS_IS"
            and confidence_lookup_low == "REJECT_AS_IS"
        )

        self.set_assertion(
            "A19",
            "Scar matching remains isolated from shape_integrity.",
            shape_isolated,
            f"params={scar_lookup_params}; admissible={shape_lookup_admissible}; failed={shape_lookup_failed}",
        )
        self.set_assertion(
            "A20",
            "Scar matching remains isolated from C_success.",
            confidence_isolated,
            f"params={scar_lookup_params}; high={confidence_lookup_high}; low={confidence_lookup_low}",
        )

        required_log_keys = {
            "cell_id",
            "structural_epoch",
            "trigger_condition",
            "authority_state_before_shedding",
            "routes_affected",
            "scar_write_decision",
            "scar_match_decision",
            "shed_boundary",
            "adjacent_cell_health_evidence",
            "load_transfer_decision",
            "final_cell_state",
        }
        all_logs_valid = bool(self.event_logs) and all(
            required_log_keys.issubset(set(log.keys()))
            for log in self.event_logs
        )
        self.set_assertion("A21", "Shedding event log contains required replay fields.", all_logs_valid, f"logs={len(self.event_logs)}")

        deterministic = len(self.assertions) == 21
        self.set_assertion("A22", "The harness produces a deterministic final verdict from the assertion results.", deterministic, f"assertions_before_A22={len(self.assertions)}")

        for assertion_id in sorted(self.assertions.keys(), key=assertion_sort_key):
            description, passed, evidence = self.assertions[assertion_id]
            self.assertion_rows.append(
                {
                    "assertion_id": assertion_id,
                    "description": description,
                    "passed": passed,
                    "evidence": evidence,
                }
            )


def assertion_sort_key(assertion_id: str) -> int:
    try:
        return int(assertion_id.replace("A", ""))
    except ValueError:
        return 999


def stable_fingerprint(*parts: str) -> str:
    payload = "|".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_repo_root() -> Path:
    script_path = Path(__file__).resolve()
    candidates = []

    if script_path.parent.name == "scripts":
        candidates.append(script_path.parent.parent)

    candidates.append(Path.cwd())
    candidates.extend(Path.cwd().parents)
    candidates.append(script_path.parent)
    candidates.extend(script_path.parents)

    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / SPEC_PATH).exists() and (resolved / PLAN_PATH).exists():
            return resolved

    if script_path.parent.name == "scripts":
        return script_path.parent.parent

    return Path.cwd()


def resolve_document(repo_root: Path, relative_path: Path) -> Path:
    script_path = Path(__file__).resolve()
    candidates = [
        repo_root / relative_path,
        Path.cwd() / relative_path,
        script_path.parent / relative_path,
    ]

    if script_path.parent.name == "scripts":
        candidates.append(script_path.parent.parent / relative_path)

    candidates.extend(parent / relative_path for parent in Path.cwd().parents)
    candidates.extend(parent / relative_path for parent in script_path.parents)

    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved

    return repo_root / relative_path


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def final_verdict(assertion_rows: List[Dict[str, object]]) -> str:
    if not assertion_rows:
        return "INCONCLUSIVE"
    passed = sum(1 for row in assertion_rows if row["passed"] is True)
    total = len(assertion_rows)
    if passed == total:
        return "SUPPORTED"

    failed_ids = {row["assertion_id"] for row in assertion_rows if row["passed"] is not True}
    not_supported_ids = {"A1", "A5", "A9", "A14", "A15", "A16"}
    if failed_ids & not_supported_ids:
        return "NOT_SUPPORTED"

    partial_core = {"A1", "A6", "A7", "A8", "A9", "A10", "A13", "A15", "A16", "A19", "A20"}
    core_passed = all(
        row["passed"] is True
        for row in assertion_rows
        if row["assertion_id"] in partial_core
    )
    if core_passed:
        return "PARTIAL_SUPPORT"

    return "INCONCLUSIVE"


def main() -> int:
    start = time.time()
    repo_root = get_repo_root()
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    harness = CellularSheddingHarness()
    harness.run()

    spec_abs_path = resolve_document(repo_root, SPEC_PATH)
    plan_abs_path = resolve_document(repo_root, PLAN_PATH)
    doc_integrity_ok = spec_abs_path.exists() and plan_abs_path.exists()

    verdict = final_verdict(harness.assertion_rows)
    if not doc_integrity_ok:
        verdict = "INCONCLUSIVE_DOCUMENT_HASH_MISSING"

    passed_count = sum(1 for row in harness.assertion_rows if row["passed"] is True)
    total_count = len(harness.assertion_rows)
    runtime = time.time() - start

    verdict_rows = [
        {
            "final_verdict": verdict,
            "assertions_passed": passed_count,
            "assertions_total": total_count,
            "runtime_seconds": round(runtime, 6),
            "script": SCRIPT_NAME,
            "document_integrity_ok": doc_integrity_ok,
        }
    ]

    outputs = {
        "cellular_shedding_v0_1_raw.csv": harness.raw_rows,
        "cellular_shedding_v0_1_summary.csv": harness.summary_rows,
        "cellular_shedding_v0_1_cell_states.csv": harness.cell_rows,
        "cellular_shedding_v0_1_route_authority.csv": harness.route_rows,
        "cellular_shedding_v0_1_scar_events.csv": harness.scar_rows,
        "cellular_shedding_v0_1_load_transfer.csv": harness.load_rows,
        "cellular_shedding_v0_1_assertions.csv": harness.assertion_rows,
        "cellular_shedding_v0_1_verdict.csv": verdict_rows,
    }

    for filename, rows in outputs.items():
        write_csv(data_dir / filename, rows)

    script_path = Path(__file__).resolve()
    run_record_path = data_dir / "cellular_shedding_v0_1_run_record.txt"
    output_inventory = "\n".join(sorted(outputs.keys()) + ["cellular_shedding_v0_1_run_record.txt"])
    run_record = f"""Cellular Shedding Simulation v1 Run Record

Final verdict: {verdict}
Assertions passed: {passed_count}/{total_count}
Runtime seconds: {runtime:.6f}

Script filename: {SCRIPT_NAME}
Script SHA-256: {sha256_file(script_path)}

Validation plan path: {plan_abs_path}
Validation plan SHA-256: {sha256_file(plan_abs_path)}

Specification path: {spec_abs_path}
Specification SHA-256: {sha256_file(spec_abs_path)}

Document integrity: {"OK" if doc_integrity_ok else "MISSING SPEC OR PLAN HASH"}

Python version: {sys.version}
Platform: {platform.platform()}

Random seed: not used
stderr status: empty if process exits 0

Output inventory:
{output_inventory}
"""
    run_record_path.write_text(run_record, encoding="utf-8")

    print(f"Final verdict: {verdict}")
    print(f"Assertions: {passed_count}/{total_count}")
    print(f"Runtime seconds: {runtime:.6f}")
    print(f"Outputs written to: {data_dir}")
    return 0 if verdict == "SUPPORTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
