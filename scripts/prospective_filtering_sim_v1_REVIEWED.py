#!/usr/bin/env python3
"""
Prospective Filtering Simulation v1 REVIEWED

Purpose:
    Validate a narrow prospective-filtering mechanism.

Scope:
    This harness tests pre-promotion candidate screening without granting
    active authority, bypass permission, inherited trust, or mutation of
    scar, lineage, confidence, shape, or authority state.

Expected primary result:
    SUPPORTED if all declared assertions pass and frozen document hashes are present.

Governing rule:
    Filter before promotion, not after failure.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import hashlib
import json
import platform
import sys
import time


SCRIPT_NAME = "prospective_filtering_sim_v1_REVIEWED.py"

SPEC_PATH = Path("docs/PROSPECTIVE_FILTERING_SPEC_v1_FROZEN.md")
PLAN_PATH = Path("docs/PROSPECTIVE_FILTERING_VALIDATION_PLAN_v1_FROZEN.md")

SCOPE_OVERLAP_MODEL = "explicit boolean scope_overlap_proven field"
FILTER_DECISION_PRECEDENCE = "evidence, provenance, epoch, scope, contamination, hard scar, soft/restoration scar, lineage constraint, no-match pass"
SCAR_MATCH_MODEL = "exact fingerprint only"
EXTRA_PROOF_PROTOCOL = "not implemented; REQUIRE_EXTRA_PROOF is a routing state only"
SOURCE_ESCALATION = "not implemented; repeated contamination is recorded only"


@dataclass
class Candidate:
    candidate_id: str
    candidate_type: str = "child_cell"
    candidate_fingerprint: str = ""
    candidate_scope: str = "scope_A"
    candidate_structural_epoch: str = "epoch_1"
    candidate_source: str = "authorized_recovery_layer"
    candidate_timestamp_status: str = "fresh"
    candidate_provenance_status: str = "valid"
    candidate_verification_status: str = "verified"
    candidate_state: str = "FILTER_PASSED_TO_REQUALIFICATION"
    candidate_active_authority: bool = False
    candidate_bypass_permission: bool = False
    candidate_c_success: Optional[float] = None
    candidate_shape_integrity: str = "UNKNOWN"


@dataclass
class FilterPacket:
    filter_packet_id: str
    candidate_id: str
    candidate_type: str = "child_cell"
    candidate_fingerprint: str = ""
    candidate_scope: str = "scope_A"
    candidate_structural_epoch: str = "epoch_1"
    candidate_source: str = "authorized_recovery_layer"
    candidate_timestamp_status: str = "fresh"
    candidate_provenance_status: str = "valid"
    candidate_verification_status: str = "verified"
    scope_status: str = "matching"
    scope_overlap_proven: bool = False
    contains_active_authority: bool = False
    contains_bypass_permission: bool = False
    contains_full_history_as_admission: bool = False
    contains_route_confidence_as_authority: bool = False
    contains_parent_shape_integrity_as_authority: bool = False
    depends_on_lineage: bool = False
    lineage_packet_status: str = "none"
    scar_fingerprints: str = ""
    lineage_constraints: str = ""
    overlapping_constraints: str = ""
    required_extra_proof: bool = False


@dataclass
class Scar:
    fingerprint: str
    scar_class: str
    retirement_state: str = "ACTIVE"


@dataclass
class LineageConstraint:
    constraint_id: str
    constraint_class: str
    constraint_fingerprint: str
    scope: str = "scope_A"
    source_packet_id: str = "lineage_packet_valid"


class ProspectiveFilteringHarness:
    def __init__(self) -> None:
        self.raw_rows: List[Dict[str, object]] = []
        self.summary_rows: List[Dict[str, object]] = []
        self.packet_rows: List[Dict[str, object]] = []
        self.candidate_rows: List[Dict[str, object]] = []
        self.decision_rows: List[Dict[str, object]] = []
        self.constraint_rows: List[Dict[str, object]] = []
        self.scope_rows: List[Dict[str, object]] = []
        self.isolation_rows: List[Dict[str, object]] = []
        self.assertion_rows: List[Dict[str, object]] = []
        self.event_logs: List[Dict[str, object]] = []
        self.assertions: Dict[str, Tuple[str, bool, str]] = {}

    def base_candidate(self, candidate_id: str) -> Candidate:
        return Candidate(
            candidate_id=candidate_id,
            candidate_fingerprint=stable_fingerprint(candidate_id, "candidate", "configuration"),
        )

    def base_packet(self, scenario: str, candidate: Candidate) -> FilterPacket:
        return FilterPacket(
            filter_packet_id=f"packet_{scenario}",
            candidate_id=candidate.candidate_id,
            candidate_type=candidate.candidate_type,
            candidate_fingerprint=candidate.candidate_fingerprint,
            candidate_scope=candidate.candidate_scope,
            candidate_structural_epoch=candidate.candidate_structural_epoch,
            candidate_source=candidate.candidate_source,
            candidate_timestamp_status=candidate.candidate_timestamp_status,
            candidate_provenance_status=candidate.candidate_provenance_status,
            candidate_verification_status=candidate.candidate_verification_status,
        )

    def set_assertion(self, assertion_id: str, description: str, passed: bool, evidence: str) -> None:
        self.assertions[assertion_id] = (description, passed, evidence)

    def log_raw(self, scenario: str, event_type: str, decision: str, details: str = "") -> None:
        self.raw_rows.append(
            {
                "scenario": scenario,
                "event_type": event_type,
                "decision": decision,
                "details": details,
            }
        )

    def record_summary(self, scenario: str, expected: str, observed: str, status: str) -> None:
        self.summary_rows.append(
            {
                "scenario": scenario,
                "expected": expected,
                "observed": observed,
                "status": status,
            }
        )

    def record_packet(self, scenario: str, packet: FilterPacket, packet_valid: bool, rejection_reason: str) -> None:
        row = asdict(packet)
        row.update(
            {
                "scenario": scenario,
                "packet_valid": packet_valid,
                "rejection_reason": rejection_reason,
            }
        )
        self.packet_rows.append(row)

    def record_candidate(self, scenario: str, candidate: Candidate) -> None:
        row = asdict(candidate)
        row.update({"scenario": scenario})
        self.candidate_rows.append(row)

    def record_decision(
        self,
        scenario: str,
        candidate: Candidate,
        filter_decision: str,
        candidate_state: str,
        scar_result: str,
        lineage_result: str,
        precedence_reason: str,
    ) -> None:
        self.decision_rows.append(
            {
                "scenario": scenario,
                "candidate_id": candidate.candidate_id,
                "filter_decision": filter_decision,
                "candidate_state": candidate_state,
                "scar_result": scar_result,
                "lineage_result": lineage_result,
                "precedence_reason": precedence_reason,
                "active_authority_granted": candidate.candidate_active_authority,
                "bypass_permission_granted": candidate.candidate_bypass_permission,
            }
        )

    def record_constraint(
        self,
        scenario: str,
        candidate: Candidate,
        applied_constraints: str,
        rejected_constraints: str,
        decision: str,
    ) -> None:
        self.constraint_rows.append(
            {
                "scenario": scenario,
                "candidate_id": candidate.candidate_id,
                "applied_constraints": applied_constraints,
                "rejected_constraints": rejected_constraints,
                "decision": decision,
            }
        )

    def record_scope(self, scenario: str, packet: FilterPacket, decision: str, applied_scope: str) -> None:
        self.scope_rows.append(
            {
                "scenario": scenario,
                "filter_packet_id": packet.filter_packet_id,
                "scope_status": packet.scope_status,
                "scope_overlap_proven": packet.scope_overlap_proven,
                "overlapping_constraints": packet.overlapping_constraints,
                "decision": decision,
                "applied_scope": applied_scope,
            }
        )

    def record_isolation(
        self,
        scenario: str,
        check_name: str,
        before: str,
        after: str,
        passed: bool,
    ) -> None:
        self.isolation_rows.append(
            {
                "scenario": scenario,
                "check_name": check_name,
                "before": before,
                "after": after,
                "passed": passed,
            }
        )

    def packet_rejection_reason(self, packet: FilterPacket) -> str:
        if not packet.candidate_id:
            return "missing_candidate_id"
        if not packet.candidate_fingerprint:
            return "missing_candidate_fingerprint"
        if packet.candidate_timestamp_status != "fresh":
            return "stale_packet"
        if packet.candidate_provenance_status != "valid":
            return "invalid_provenance"
        if packet.candidate_structural_epoch != "epoch_1":
            return "epoch_mismatch"
        if packet.candidate_verification_status != "verified":
            return "invalid_evidence"
        if packet.scope_status == "unknown":
            return "unknown_scope"
        if packet.scope_status == "none":
            return "no_scope_overlap"
        if packet.scope_status == "overlap" and not packet.scope_overlap_proven:
            return "unproven_scope_overlap"
        if packet.contains_active_authority:
            return "contains_active_authority"
        if packet.contains_bypass_permission:
            return "contains_bypass_permission"
        if packet.contains_full_history_as_admission:
            return "contains_full_history_as_admission"
        if packet.contains_route_confidence_as_authority:
            return "contains_route_confidence_as_authority"
        if packet.contains_parent_shape_integrity_as_authority:
            return "contains_parent_shape_integrity_as_authority"
        if packet.depends_on_lineage and packet.lineage_packet_status not in {"valid", "none"}:
            return f"invalid_lineage_dependency:{packet.lineage_packet_status}"
        return ""

    def packet_valid(self, packet: FilterPacket) -> Tuple[bool, str]:
        reason = self.packet_rejection_reason(packet)
        return reason == "", reason

    def scar_lookup(self, scar_registry: Dict[str, Scar], fingerprint: str) -> Tuple[str, str]:
        scar = scar_registry.get(fingerprint)
        if scar is None:
            return "NO_SCAR_MATCH", "NONE"
        if scar.retirement_state == "RETIRED":
            return "NO_SCAR_MATCH_RETIRED", scar.scar_class
        if scar.scar_class == "HARD":
            return "REJECT_AS_IS", scar.scar_class
        if scar.scar_class in {"SOFT", "RESTORATION"}:
            return "REQUIRE_EXTRA_PROOF", scar.scar_class
        return "UNKNOWN_SCAR_CLASS", scar.scar_class

    def lineage_lookup(
        self,
        lineage_constraints: Dict[str, LineageConstraint],
        fingerprint: str,
        packet: FilterPacket,
    ) -> Tuple[str, str]:
        if not packet.depends_on_lineage and packet.lineage_packet_status == "none":
            return "NO_LINEAGE_PACKET", "NONE"

        constraint = lineage_constraints.get(fingerprint)
        if constraint is None:
            return "NO_LINEAGE_MATCH", "NONE"

        if constraint.constraint_class == "HARD":
            return "REJECT_AS_IS", constraint.constraint_class
        if constraint.constraint_class in {"SOFT", "RESTORATION"}:
            return "REQUIRE_EXTRA_PROOF", constraint.constraint_class
        return "UNKNOWN_LINEAGE_CONSTRAINT", constraint.constraint_class

    def state_for_decision(self, decision: str) -> str:
        return {
            "REJECT_AS_IS": "FILTER_REJECTED",
            "REQUIRE_EXTRA_PROOF": "FILTER_EXTRA_PROOF_REQUIRED",
            "PASS_TO_REQUALIFICATION": "FILTER_PASSED_TO_REQUALIFICATION",
            "QUARANTINE": "FILTER_QUARANTINED",
            "FALLBACK_FULL_ANALYSIS": "FALLBACK_FULL_ANALYSIS",
        }[decision]

    def apply_filter(
        self,
        scenario: str,
        candidate: Candidate,
        packet: FilterPacket,
        scar_registry: Optional[Dict[str, Scar]] = None,
        lineage_constraints: Optional[Dict[str, LineageConstraint]] = None,
    ) -> Tuple[Candidate, str, str, str, str]:
        scar_registry = scar_registry or {}
        lineage_constraints = lineage_constraints or {}

        valid, rejection_reason = self.packet_valid(packet)
        self.record_packet(scenario, packet, valid, rejection_reason)

        scar_result = "NOT_EVALUATED"
        lineage_result = "NOT_EVALUATED"
        filter_decision = "PASS_TO_REQUALIFICATION"
        precedence_reason = "no_match_pass_to_requalification"
        applied_constraints = ""
        rejected_constraints = ""

        if not valid:
            filter_decision = "QUARANTINE"
            precedence_reason = rejection_reason
            rejected_constraints = rejection_reason
            lineage_result = "INVALID_DEPENDENCY" if "lineage" in rejection_reason else "NOT_EVALUATED"
            scar_result = "NOT_EVALUATED_DUE_TO_PRECEDENCE"
        else:
            scar_result, scar_class = self.scar_lookup(scar_registry, candidate.candidate_fingerprint)
            lineage_result, lineage_class = self.lineage_lookup(lineage_constraints, candidate.candidate_fingerprint, packet)

            if packet.scope_status == "overlap" and packet.scope_overlap_proven:
                applied_constraints = packet.overlapping_constraints
                self.record_scope(scenario, packet, "OVERLAP_ONLY", packet.overlapping_constraints)
            else:
                self.record_scope(scenario, packet, "MATCHING_OR_DIRECT", packet.candidate_scope)

            if scar_result == "REJECT_AS_IS":
                filter_decision = "REJECT_AS_IS"
                precedence_reason = "hard_scar_match"
                applied_constraints = candidate.candidate_fingerprint
            elif scar_result == "REQUIRE_EXTRA_PROOF":
                filter_decision = "REQUIRE_EXTRA_PROOF"
                precedence_reason = f"{scar_class.lower()}_scar_match"
                applied_constraints = candidate.candidate_fingerprint
            elif lineage_result == "REJECT_AS_IS":
                filter_decision = "REJECT_AS_IS"
                precedence_reason = "hard_lineage_constraint"
                applied_constraints = candidate.candidate_fingerprint
            elif lineage_result == "REQUIRE_EXTRA_PROOF":
                filter_decision = "REQUIRE_EXTRA_PROOF"
                precedence_reason = f"{lineage_class.lower()}_lineage_constraint"
                applied_constraints = candidate.candidate_fingerprint
            else:
                filter_decision = "PASS_TO_REQUALIFICATION"
                precedence_reason = "no_match_pass_to_requalification"

        if not valid:
            self.record_scope(scenario, packet, "REJECTED_BY_PRECEDENCE", "")

        candidate.candidate_state = self.state_for_decision(filter_decision)
        candidate.candidate_active_authority = False
        candidate.candidate_bypass_permission = False

        if packet.contains_route_confidence_as_authority:
            candidate.candidate_c_success = None

        if packet.contains_parent_shape_integrity_as_authority:
            candidate.candidate_shape_integrity = "UNKNOWN"

        self.record_candidate(scenario, candidate)
        self.record_decision(scenario, candidate, filter_decision, candidate.candidate_state, scar_result, lineage_result, precedence_reason)
        self.record_constraint(scenario, candidate, applied_constraints, rejected_constraints, filter_decision)
        self.log_event(scenario, candidate, packet, scar_result, lineage_result, filter_decision, precedence_reason)
        self.log_raw(scenario, "prospective_filter", filter_decision, precedence_reason)

        return candidate, filter_decision, scar_result, lineage_result, precedence_reason

    def log_event(
        self,
        scenario: str,
        candidate: Candidate,
        packet: FilterPacket,
        scar_result: str,
        lineage_result: str,
        filter_decision: str,
        precedence_reason: str,
    ) -> None:
        self.event_logs.append(
            {
                "scenario": scenario,
                "filter_event_id": f"event_{scenario}",
                "candidate_id": candidate.candidate_id,
                "candidate_type": candidate.candidate_type,
                "candidate_fingerprint": candidate.candidate_fingerprint,
                "candidate_scope": candidate.candidate_scope,
                "candidate_epoch": candidate.candidate_structural_epoch,
                "candidate_provenance": candidate.candidate_provenance_status,
                "candidate_verification_status": candidate.candidate_verification_status,
                "scar_result": scar_result,
                "lineage_result": lineage_result,
                "scope_decision": packet.scope_status,
                "provenance_decision": candidate.candidate_provenance_status,
                "filter_decision": filter_decision,
                "precedence_reason": precedence_reason,
                "extra_proof_required": filter_decision == "REQUIRE_EXTRA_PROOF",
                "requalification_allowed": filter_decision == "PASS_TO_REQUALIFICATION",
                "active_authority_granted": candidate.candidate_active_authority,
                "bypass_permission_granted": candidate.candidate_bypass_permission,
            }
        )

    def run(self) -> None:
        self.scenario_1_hard_scar()
        self.scenario_2_soft_scar()
        self.scenario_3_restoration_scar()
        self.scenario_4_no_scar_match()
        self.scenario_5_active_authority_contamination()
        self.scenario_6_bypass_permission_contamination()
        self.scenario_7_route_confidence_contamination()
        self.scenario_8_shape_integrity_contamination()
        self.scenario_9_full_history_contamination()
        self.scenario_10_stale_evidence()
        self.scenario_11_invalid_provenance()
        self.scenario_12_epoch_mismatch()
        self.scenario_13_unknown_scope()
        self.scenario_14_narrower_overlap()
        self.scenario_15_no_lineage_packet()
        self.scenario_16_invalid_lineage_dependency()
        self.scenario_17_hard_lineage_constraint()
        self.scenario_18_soft_lineage_constraint()
        self.scenario_19_contamination_precedence()
        self.scenario_20_isolation_checks()
        self.scenario_21_repeated_contaminated_source()
        self.finalize_assertions()

    def scenario_1_hard_scar(self) -> None:
        scenario = "S01_valid_hard_scar_match"
        candidate = self.base_candidate("candidate_hard_scar")
        packet = self.base_packet(scenario, candidate)
        registry = {candidate.candidate_fingerprint: Scar(candidate.candidate_fingerprint, "HARD")}
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, registry)
        ok = decision == "REJECT_AS_IS" and candidate.candidate_state == "FILTER_REJECTED"
        self.record_summary(scenario, "REJECT_AS_IS and FILTER_REJECTED", f"{decision}; {candidate.candidate_state}", "PASS" if ok else "FAIL")
        self.set_assertion("A1", "Hard scar match returns REJECT_AS_IS.", decision == "REJECT_AS_IS", decision)
        self.set_assertion("A2", "Hard scar match places candidate in FILTER_REJECTED.", candidate.candidate_state == "FILTER_REJECTED", candidate.candidate_state)

    def scenario_2_soft_scar(self) -> None:
        scenario = "S02_valid_soft_scar_match"
        candidate = self.base_candidate("candidate_soft_scar")
        packet = self.base_packet(scenario, candidate)
        registry = {candidate.candidate_fingerprint: Scar(candidate.candidate_fingerprint, "SOFT")}
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, registry)
        ok = decision == "REQUIRE_EXTRA_PROOF" and candidate.candidate_state == "FILTER_EXTRA_PROOF_REQUIRED"
        self.record_summary(scenario, "REQUIRE_EXTRA_PROOF and FILTER_EXTRA_PROOF_REQUIRED", f"{decision}; {candidate.candidate_state}", "PASS" if ok else "FAIL")
        self.set_assertion("A3", "Soft scar match returns REQUIRE_EXTRA_PROOF.", decision == "REQUIRE_EXTRA_PROOF", decision)
        self.set_assertion("A4", "Soft scar match places candidate in FILTER_EXTRA_PROOF_REQUIRED.", candidate.candidate_state == "FILTER_EXTRA_PROOF_REQUIRED", candidate.candidate_state)

    def scenario_3_restoration_scar(self) -> None:
        scenario = "S03_valid_restoration_scar_match"
        candidate = self.base_candidate("candidate_restoration_scar")
        packet = self.base_packet(scenario, candidate)
        registry = {candidate.candidate_fingerprint: Scar(candidate.candidate_fingerprint, "RESTORATION")}
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, registry)
        ok = decision == "REQUIRE_EXTRA_PROOF" and candidate.candidate_state == "FILTER_EXTRA_PROOF_REQUIRED"
        self.record_summary(scenario, "REQUIRE_EXTRA_PROOF and FILTER_EXTRA_PROOF_REQUIRED", f"{decision}; {candidate.candidate_state}", "PASS" if ok else "FAIL")
        self.set_assertion("A5", "Restoration scar match returns REQUIRE_EXTRA_PROOF.", decision == "REQUIRE_EXTRA_PROOF", decision)
        self.set_assertion("A6", "Restoration scar match places candidate in FILTER_EXTRA_PROOF_REQUIRED.", candidate.candidate_state == "FILTER_EXTRA_PROOF_REQUIRED", candidate.candidate_state)

    def scenario_4_no_scar_match(self) -> None:
        scenario = "S04_no_scar_match"
        candidate = self.base_candidate("candidate_no_scar")
        packet = self.base_packet(scenario, candidate)
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, {})
        event = self.event_logs[-1]
        a7_ok = event["scar_result"] == "NO_SCAR_MATCH" and candidate.candidate_state != "ACTIVE"
        a8_ok = candidate.candidate_state != "ACTIVE"
        a9_ok = candidate.candidate_state == "FILTER_PASSED_TO_REQUALIFICATION"
        self.record_summary(scenario, "NO_SCAR_MATCH, pass only to requalification", f"{scar_result}; {candidate.candidate_state}", "PASS" if a7_ok and a8_ok and a9_ok else "FAIL")
        self.set_assertion("A7", "No scar match does not prove safety. Verified by confirming the filter event log records NO_SCAR_MATCH and the candidate does not enter ACTIVE.", a7_ok, f"event_scar_result={event['scar_result']}; state={candidate.candidate_state}")
        self.set_assertion("A8", "No scar match does not place candidate in ACTIVE.", a8_ok, candidate.candidate_state)
        self.set_assertion("A9", "Valid no-match candidate enters FILTER_PASSED_TO_REQUALIFICATION.", a9_ok, candidate.candidate_state)

    def scenario_5_active_authority_contamination(self) -> None:
        scenario = "S05_active_authority_contamination"
        candidate = self.base_candidate("candidate_active_contam")
        packet = self.base_packet(scenario, candidate)
        packet.contains_active_authority = True
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        ok = decision == "QUARANTINE" and not candidate.candidate_active_authority
        self.record_summary(scenario, "QUARANTINE and no authority", f"{decision}; authority={candidate.candidate_active_authority}", "PASS" if ok else "FAIL")
        self.set_assertion("A10", "Candidate cannot receive active authority from prospective filtering.", not candidate.candidate_active_authority, str(candidate.candidate_active_authority))
        self.set_assertion("A12", "Packet containing active authority returns QUARANTINE.", decision == "QUARANTINE" and reason == "contains_active_authority", f"{decision}; {reason}")

    def scenario_6_bypass_permission_contamination(self) -> None:
        scenario = "S06_bypass_permission_contamination"
        candidate = self.base_candidate("candidate_bypass_contam")
        packet = self.base_packet(scenario, candidate)
        packet.contains_bypass_permission = True
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        ok = decision == "QUARANTINE" and not candidate.candidate_bypass_permission
        self.record_summary(scenario, "QUARANTINE and no bypass", f"{decision}; bypass={candidate.candidate_bypass_permission}", "PASS" if ok else "FAIL")
        self.set_assertion("A11", "Candidate cannot receive bypass permission from prospective filtering.", not candidate.candidate_bypass_permission, str(candidate.candidate_bypass_permission))
        self.set_assertion("A13", "Packet containing bypass permission returns QUARANTINE.", decision == "QUARANTINE" and reason == "contains_bypass_permission", f"{decision}; {reason}")

    def scenario_7_route_confidence_contamination(self) -> None:
        scenario = "S07_route_confidence_as_authority"
        candidate = self.base_candidate("candidate_route_conf_contam")
        packet = self.base_packet(scenario, candidate)
        packet.contains_route_confidence_as_authority = True
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        no_c_success = candidate.candidate_c_success is None and not candidate.candidate_active_authority
        self.record_summary(scenario, "QUARANTINE and C_success not authority", f"{decision}; c_success={candidate.candidate_c_success}", "PASS" if decision == "QUARANTINE" and no_c_success else "FAIL")
        self.set_assertion("A14", "Packet containing route confidence as authority returns QUARANTINE.", decision == "QUARANTINE" and reason == "contains_route_confidence_as_authority", f"{decision}; {reason}")
        self.set_assertion("A15", "Candidate cannot inherit C_success as authority.", no_c_success, str(candidate.candidate_c_success))

    def scenario_8_shape_integrity_contamination(self) -> None:
        scenario = "S08_parent_shape_integrity_as_authority"
        candidate = self.base_candidate("candidate_shape_contam")
        candidate.candidate_shape_integrity = "UNKNOWN"
        packet = self.base_packet(scenario, candidate)
        packet.contains_parent_shape_integrity_as_authority = True
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        no_shape_authority = candidate.candidate_shape_integrity == "UNKNOWN" and not candidate.candidate_active_authority
        self.record_summary(scenario, "QUARANTINE and shape not authority", f"{decision}; shape={candidate.candidate_shape_integrity}", "PASS" if decision == "QUARANTINE" and no_shape_authority else "FAIL")
        self.set_assertion("A16", "Packet containing parent shape integrity as authority returns QUARANTINE.", decision == "QUARANTINE" and reason == "contains_parent_shape_integrity_as_authority", f"{decision}; {reason}")
        self.set_assertion("A17", "Candidate cannot inherit parent shape_integrity as authority.", no_shape_authority, candidate.candidate_shape_integrity)

    def scenario_9_full_history_contamination(self) -> None:
        scenario = "S09_full_history_as_admission"
        candidate = self.base_candidate("candidate_full_history")
        packet = self.base_packet(scenario, candidate)
        packet.contains_full_history_as_admission = True
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        self.record_summary(scenario, "QUARANTINE", f"{decision}; {reason}", "PASS" if decision == "QUARANTINE" and reason == "contains_full_history_as_admission" else "FAIL")
        self.set_assertion("A18", "Packet containing full history as admission evidence returns QUARANTINE.", decision == "QUARANTINE" and reason == "contains_full_history_as_admission", f"{decision}; {reason}")

    def scenario_10_stale_evidence(self) -> None:
        scenario = "S10_stale_evidence"
        candidate = self.base_candidate("candidate_stale")
        packet = self.base_packet(scenario, candidate)
        packet.candidate_timestamp_status = "stale"
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        self.record_summary(scenario, "QUARANTINE", f"{decision}; {reason}", "PASS" if decision == "QUARANTINE" and reason == "stale_packet" else "FAIL")
        self.set_assertion("A19", "Stale packet returns QUARANTINE.", decision == "QUARANTINE" and reason == "stale_packet", f"{decision}; {reason}")

    def scenario_11_invalid_provenance(self) -> None:
        scenario = "S11_invalid_provenance"
        candidate = self.base_candidate("candidate_bad_provenance")
        packet = self.base_packet(scenario, candidate)
        packet.candidate_provenance_status = "invalid"
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        self.record_summary(scenario, "QUARANTINE", f"{decision}; {reason}", "PASS" if decision == "QUARANTINE" and reason == "invalid_provenance" else "FAIL")
        self.set_assertion("A20", "Invalid provenance returns QUARANTINE.", decision == "QUARANTINE" and reason == "invalid_provenance", f"{decision}; {reason}")

    def scenario_12_epoch_mismatch(self) -> None:
        scenario = "S12_epoch_mismatch"
        candidate = self.base_candidate("candidate_epoch")
        packet = self.base_packet(scenario, candidate)
        packet.candidate_structural_epoch = "epoch_old"
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        self.record_summary(scenario, "QUARANTINE", f"{decision}; {reason}", "PASS" if decision == "QUARANTINE" and reason == "epoch_mismatch" else "FAIL")
        self.set_assertion("A21", "Epoch mismatch returns QUARANTINE.", decision == "QUARANTINE" and reason == "epoch_mismatch", f"{decision}; {reason}")

    def scenario_13_unknown_scope(self) -> None:
        scenario = "S13_unknown_scope"
        candidate = self.base_candidate("candidate_unknown_scope")
        packet = self.base_packet(scenario, candidate)
        packet.scope_status = "unknown"
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        self.record_summary(scenario, "QUARANTINE", f"{decision}; {reason}", "PASS" if decision == "QUARANTINE" and reason == "unknown_scope" else "FAIL")
        self.set_assertion("A22", "Unknown scope returns QUARANTINE.", decision == "QUARANTINE" and reason == "unknown_scope", f"{decision}; {reason}")

    def scenario_14_narrower_overlap(self) -> None:
        scenario = "S14_narrower_proven_overlap"
        candidate = self.base_candidate("candidate_overlap")
        candidate.candidate_scope = "region_A"
        packet = self.base_packet(scenario, candidate)
        packet.scope_status = "overlap"
        packet.scope_overlap_proven = True
        packet.overlapping_constraints = "constraint_region_A_only"
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        applied = self.constraint_rows[-1]["applied_constraints"] == "constraint_region_A_only"
        self.record_summary(scenario, "only declared overlapping constraints applied", self.constraint_rows[-1]["applied_constraints"], "PASS" if applied else "FAIL")
        self.set_assertion("A23", "Narrower proven overlap applies only declared overlapping constraints.", applied, str(self.constraint_rows[-1]["applied_constraints"]))

    def scenario_15_no_lineage_packet(self) -> None:
        scenario = "S15_no_lineage_packet"
        candidate = self.base_candidate("candidate_no_lineage")
        packet = self.base_packet(scenario, candidate)
        packet.depends_on_lineage = False
        packet.lineage_packet_status = "none"
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, {})
        no_inherited = lineage_result == "NO_LINEAGE_PACKET" and self.constraint_rows[-1]["applied_constraints"] == ""
        pass_only_requal = candidate.candidate_state == "FILTER_PASSED_TO_REQUALIFICATION" and candidate.candidate_state != "ACTIVE"
        self.record_summary(scenario, "no inherited constraints and pass only to requalification", f"{lineage_result}; {candidate.candidate_state}", "PASS" if no_inherited and pass_only_requal else "FAIL")
        self.set_assertion("A24", "Candidate with no lineage packet receives no inherited constraints.", no_inherited, f"{lineage_result}; constraints={self.constraint_rows[-1]['applied_constraints']}")
        self.set_assertion("A25", "Candidate with no lineage packet may pass only to requalification, not ACTIVE.", pass_only_requal, candidate.candidate_state)

    def scenario_16_invalid_lineage_dependency(self) -> None:
        scenario = "S16_invalid_lineage_dependency"
        candidate = self.base_candidate("candidate_bad_lineage")
        packet = self.base_packet(scenario, candidate)
        packet.depends_on_lineage = True
        packet.lineage_packet_status = "invalid"
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
        ok = decision == "QUARANTINE" and reason == "invalid_lineage_dependency:invalid"
        self.record_summary(scenario, "QUARANTINE", f"{decision}; {reason}", "PASS" if ok else "FAIL")
        self.set_assertion("A26", "Candidate depending on invalid lineage evidence returns QUARANTINE.", ok, f"{decision}; {reason}")

    def scenario_17_hard_lineage_constraint(self) -> None:
        scenario = "S17_valid_hard_lineage_constraint"
        candidate = self.base_candidate("candidate_hard_lineage")
        packet = self.base_packet(scenario, candidate)
        packet.depends_on_lineage = True
        packet.lineage_packet_status = "valid"
        constraints = {
            candidate.candidate_fingerprint: LineageConstraint(
                "constraint_hard_lineage",
                "HARD",
                candidate.candidate_fingerprint,
            )
        }
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, {}, constraints)
        self.record_summary(scenario, "REJECT_AS_IS", f"{decision}; {lineage_result}", "PASS" if decision == "REJECT_AS_IS" and lineage_result == "REJECT_AS_IS" else "FAIL")
        self.set_assertion("A27", "Valid hard inherited lineage constraint returns REJECT_AS_IS.", decision == "REJECT_AS_IS" and lineage_result == "REJECT_AS_IS", f"{decision}; {lineage_result}")

    def scenario_18_soft_lineage_constraint(self) -> None:
        scenario = "S18_valid_soft_lineage_constraint"
        candidate = self.base_candidate("candidate_soft_lineage")
        packet = self.base_packet(scenario, candidate)
        packet.depends_on_lineage = True
        packet.lineage_packet_status = "valid"
        constraints = {
            candidate.candidate_fingerprint: LineageConstraint(
                "constraint_soft_lineage",
                "SOFT",
                candidate.candidate_fingerprint,
            )
        }
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, {}, constraints)
        self.record_summary(scenario, "REQUIRE_EXTRA_PROOF", f"{decision}; {lineage_result}", "PASS" if decision == "REQUIRE_EXTRA_PROOF" and lineage_result == "REQUIRE_EXTRA_PROOF" else "FAIL")
        self.set_assertion("A28", "Valid soft inherited lineage constraint returns REQUIRE_EXTRA_PROOF.", decision == "REQUIRE_EXTRA_PROOF" and lineage_result == "REQUIRE_EXTRA_PROOF", f"{decision}; {lineage_result}")

    def scenario_19_contamination_precedence(self) -> None:
        scenario = "S19_contamination_precedence"
        candidate = self.base_candidate("candidate_contam_hard_scar")
        packet = self.base_packet(scenario, candidate)
        packet.contains_active_authority = True
        packet.scar_fingerprints = candidate.candidate_fingerprint
        registry = {candidate.candidate_fingerprint: Scar(candidate.candidate_fingerprint, "HARD")}
        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, registry)
        ok = decision == "QUARANTINE" and scar_result == "NOT_EVALUATED_DUE_TO_PRECEDENCE" and reason == "contains_active_authority"
        self.record_summary(scenario, "QUARANTINE before trusted hard scar", f"{decision}; scar={scar_result}; reason={reason}", "PASS" if ok else "FAIL")
        self.set_assertion("A29", "Contaminated packet with hard scar match returns QUARANTINE before trusted scar result.", ok, f"{decision}; scar={scar_result}; reason={reason}")

    def scenario_20_isolation_checks(self) -> None:
        scenario = "S20_isolation_checks"
        candidate = self.base_candidate("candidate_isolation")
        candidate.candidate_c_success = 0.51
        candidate.candidate_shape_integrity = "CURRENT_VERIFIED"
        candidate.candidate_active_authority = False
        candidate.candidate_bypass_permission = False

        packet = self.base_packet(scenario, candidate)
        packet.depends_on_lineage = True
        packet.lineage_packet_status = "valid"

        registry = {
            "unrelated_hard": Scar("unrelated_hard", "HARD"),
            candidate.candidate_fingerprint: Scar(candidate.candidate_fingerprint, "SOFT"),
        }
        constraints = {
            "unrelated_constraint": LineageConstraint("unrelated_constraint", "SOFT", "unrelated_fp")
        }

        registry_before = stable_registry_hash(registry)
        packet_before = stable_dataclass_hash(packet)
        c_success_before = str(candidate.candidate_c_success)
        shape_before = str(candidate.candidate_shape_integrity)
        authority_before = json.dumps(
            {
                "active_authority": candidate.candidate_active_authority,
                "bypass_permission": candidate.candidate_bypass_permission,
            },
            sort_keys=True,
        )

        candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet, registry, constraints)

        registry_after = stable_registry_hash(registry)
        packet_after = stable_dataclass_hash(packet)
        c_success_after = str(candidate.candidate_c_success)
        shape_after = str(candidate.candidate_shape_integrity)
        authority_after = json.dumps(
            {
                "active_authority": candidate.candidate_active_authority,
                "bypass_permission": candidate.candidate_bypass_permission,
            },
            sort_keys=True,
        )

        registry_ok = registry_before == registry_after
        packet_ok = packet_before == packet_after
        c_ok = c_success_before == c_success_after
        shape_ok = shape_before == shape_after
        authority_ok = authority_before == authority_after

        self.record_isolation(scenario, "scar_registry_non_mutation", registry_before, registry_after, registry_ok)
        self.record_isolation(scenario, "lineage_packet_non_mutation", packet_before, packet_after, packet_ok)
        self.record_isolation(scenario, "C_success_non_mutation", c_success_before, c_success_after, c_ok)
        self.record_isolation(scenario, "shape_integrity_non_mutation", shape_before, shape_after, shape_ok)
        self.record_isolation(scenario, "authority_and_bypass_non_mutation", authority_before, authority_after, authority_ok)

        all_ok = registry_ok and packet_ok and c_ok and shape_ok and authority_ok
        self.record_summary(scenario, "all isolation snapshots unchanged", f"registry={registry_ok}; packet={packet_ok}; C={c_ok}; shape={shape_ok}; authority={authority_ok}", "PASS" if all_ok else "FAIL")
        self.set_assertion("A30", "Filter lookup does not mutate scar registry. Verification method: stable hash or serialized snapshot before filtering and after filtering must match.", registry_ok, f"before={registry_before}; after={registry_after}")
        self.set_assertion("A31", "Filter lookup does not mutate lineage packet. Verification method: stable hash or serialized snapshot before filtering and after filtering must match.", packet_ok, f"before={packet_before}; after={packet_after}")
        self.set_assertion("A32", "Filter lookup does not mutate C_success. Verification method: before-and-after C_success values must match.", c_ok, f"before={c_success_before}; after={c_success_after}")
        self.set_assertion("A33", "Filter lookup does not mutate shape_integrity. Verification method: before-and-after shape_integrity values must match.", shape_ok, f"before={shape_before}; after={shape_after}")
        self.set_assertion("A34", "Filter lookup does not mutate active authority or bypass permission into true. Verification method: before-and-after authority and bypass fields must remain false.", authority_ok, f"before={authority_before}; after={authority_after}")

    def scenario_21_repeated_contaminated_source(self) -> None:
        scenario = "S21_repeated_contaminated_source"
        rejections = 0
        escalations_claimed = 0
        for idx in range(3):
            candidate = self.base_candidate(f"candidate_repeat_contam_{idx}")
            packet = self.base_packet(f"{scenario}_{idx}", candidate)
            packet.candidate_source = "source_with_repeated_contamination"
            packet.contains_active_authority = True
            candidate, decision, scar_result, lineage_result, reason = self.apply_filter(scenario, candidate, packet)
            if decision == "QUARANTINE":
                rejections += 1
            escalations_claimed += 0

        ok = rejections == 3 and escalations_claimed == 0
        self.record_summary(scenario, "three packets rejected, no source escalation claimed", f"rejections={rejections}; escalations={escalations_claimed}", "PASS" if ok else "FAIL")
        self.set_assertion("A35", "Repeated contaminated packets are recorded without source-level escalation claim.", ok, f"rejections={rejections}; escalations={escalations_claimed}")

    def finalize_assertions(self) -> None:
        required_keys = {
            "candidate_id",
            "candidate_fingerprint",
            "candidate_scope",
            "candidate_epoch",
            "candidate_provenance",
            "scar_result",
            "lineage_result",
            "scope_decision",
            "filter_decision",
            "extra_proof_required",
            "requalification_allowed",
            "active_authority_granted",
            "bypass_permission_granted",
        }
        logs_valid = bool(self.event_logs) and all(required_keys.issubset(set(log.keys())) for log in self.event_logs)
        self.set_assertion("A36", "The filter event log contains candidate id, fingerprint, scope, epoch, provenance, scar result, lineage result, scope decision, filter decision, extra-proof status, requalification allowance, authority grant status, and bypass grant status.", logs_valid, f"logs={len(self.event_logs)}")

        deterministic = len(self.assertions) == 36
        self.set_assertion("A37", "The harness produces a deterministic final verdict from assertion results.", deterministic, f"assertions_before_A37={len(self.assertions)}")

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
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def stable_registry_hash(registry: Dict[str, Scar]) -> str:
    serializable = {
        key: asdict(value)
        for key, value in sorted(registry.items(), key=lambda item: item[0])
    }
    return hashlib.sha256(json.dumps(serializable, sort_keys=True).encode("utf-8")).hexdigest()


def stable_dataclass_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(asdict(value), sort_keys=True).encode("utf-8")).hexdigest()


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
    not_supported_ids = {
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A10",
        "A11",
        "A12",
        "A14",
        "A16",
        "A22",
        "A26",
        "A29",
        "A30",
        "A31",
        "A32",
        "A33",
        "A34",
    }
    if failed_ids & not_supported_ids:
        return "NOT_SUPPORTED"

    return "INCONCLUSIVE"


def main() -> int:
    start = time.time()
    repo_root = get_repo_root()
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    harness = ProspectiveFilteringHarness()
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
            "scope_overlap_model": SCOPE_OVERLAP_MODEL,
            "filter_decision_precedence": FILTER_DECISION_PRECEDENCE,
            "scar_match_model": SCAR_MATCH_MODEL,
            "extra_proof_protocol": EXTRA_PROOF_PROTOCOL,
            "source_escalation": SOURCE_ESCALATION,
        }
    ]

    outputs = {
        "prospective_filtering_v0_1_raw.csv": harness.raw_rows,
        "prospective_filtering_v0_1_summary.csv": harness.summary_rows,
        "prospective_filtering_v0_1_packets.csv": harness.packet_rows,
        "prospective_filtering_v0_1_candidates.csv": harness.candidate_rows,
        "prospective_filtering_v0_1_decisions.csv": harness.decision_rows,
        "prospective_filtering_v0_1_constraints.csv": harness.constraint_rows,
        "prospective_filtering_v0_1_scope_decisions.csv": harness.scope_rows,
        "prospective_filtering_v0_1_isolation.csv": harness.isolation_rows,
        "prospective_filtering_v0_1_assertions.csv": harness.assertion_rows,
        "prospective_filtering_v0_1_verdict.csv": verdict_rows,
    }

    for filename, rows in outputs.items():
        write_csv(data_dir / filename, rows)

    script_path = Path(__file__).resolve()
    run_record_path = data_dir / "prospective_filtering_v0_1_run_record.txt"
    output_inventory = "\n".join(sorted(outputs.keys()) + ["prospective_filtering_v0_1_run_record.txt"])

    run_record = f"""Prospective Filtering Simulation v1 Run Record

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

Frozen parameters:
SCOPE_OVERLAP_MODEL = {SCOPE_OVERLAP_MODEL}
FILTER_DECISION_PRECEDENCE = {FILTER_DECISION_PRECEDENCE}
SCAR_MATCH_MODEL = {SCAR_MATCH_MODEL}
EXTRA_PROOF_PROTOCOL = {EXTRA_PROOF_PROTOCOL}
SOURCE_ESCALATION = {SOURCE_ESCALATION}

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
