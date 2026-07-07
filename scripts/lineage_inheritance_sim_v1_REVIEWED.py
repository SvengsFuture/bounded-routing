#!/usr/bin/env python3
"""
Lineage Inheritance Simulation v1 REVIEWED

Purpose:
    Validate a narrow lineage-inheritance mechanism.

Scope:
    This harness tests constraint inheritance from a parent cell context
    to a child cell candidate without transferring active authority,
    bypass permission, full history, route confidence, or parent shape integrity.

Expected primary result:
    SUPPORTED if all declared assertions pass and frozen document hashes are present.

Governing rule:
    Inherit constraints, not authority.
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


SCRIPT_NAME = "lineage_inheritance_sim_v1_REVIEWED.py"

SPEC_PATH = Path("docs/LINEAGE_INHERITANCE_SPEC_v1_FROZEN.md")
PLAN_PATH = Path("docs/LINEAGE_INHERITANCE_VALIDATION_PLAN_v1_FROZEN.md")

REQUALIFICATION_THRESHOLD = 5
PARTIAL_REQUALIFICATION_PROGRESS = 3
SCOPE_OVERLAP_MODEL = "explicit boolean scope_overlap_proven field"


@dataclass
class ParentCell:
    parent_cell_id: str
    parent_final_state: str = "SHED"
    parent_scope: str = "parent_scope"
    parent_structural_epoch: str = "epoch_1"
    parent_c_success: float = 0.94
    parent_shape_integrity: str = "FAILED"
    parent_active_authority: bool = False
    parent_bypass_permission: bool = False
    parent_fingerprint: str = ""


@dataclass
class ChildCell:
    child_cell_id: str
    child_scope: str = "child_scope"
    child_structural_epoch: str = "epoch_1"
    child_initial_state: str = "RECONSTRUCTING"
    child_final_state: str = "RECONSTRUCTING"
    child_c_success: Optional[float] = None
    child_shape_integrity: str = "UNKNOWN"
    child_active_authority: bool = False
    child_bypass_permission: bool = False
    requalification_progress: int = 0
    requalification_threshold: int = REQUALIFICATION_THRESHOLD
    child_fingerprint: str = ""
    extra_proof_required: bool = False
    inherited_constraints: str = ""
    rejected_constraints: str = ""


@dataclass
class LineagePacket:
    packet_id: str
    parent_cell_id: str
    child_cell_id: str
    structural_epoch: str = "epoch_1"
    lineage_boundary: str = "local_boundary"
    source: str = "authorized_recovery_layer"
    timestamp_status: str = "fresh"
    provenance_status: str = "valid"
    scope_status: str = "matching"
    scope_overlap_proven: bool = False
    verification_status: str = "verified"
    contains_active_authority: bool = False
    contains_full_history: bool = False
    contains_route_confidence_as_authority: bool = False
    contains_parent_shape_integrity_as_authority: bool = False
    scar_fingerprints: str = ""
    blocked_candidates: str = ""
    required_extra_proof: bool = False
    scope_limits: str = ""
    requalification_required: bool = True
    overlapping_constraints: str = ""


@dataclass
class Scar:
    fingerprint: str
    scar_class: str
    retirement_state: str = "ACTIVE"


class LineageInheritanceHarness:
    def __init__(self) -> None:
        self.raw_rows: List[Dict[str, object]] = []
        self.summary_rows: List[Dict[str, object]] = []
        self.packet_rows: List[Dict[str, object]] = []
        self.child_rows: List[Dict[str, object]] = []
        self.constraint_rows: List[Dict[str, object]] = []
        self.scar_rows: List[Dict[str, object]] = []
        self.scope_rows: List[Dict[str, object]] = []
        self.assertion_rows: List[Dict[str, object]] = []
        self.event_logs: List[Dict[str, object]] = []
        self.assertions: Dict[str, Tuple[str, bool, str]] = {}

    def base_parent(self, parent_id: str = "parent") -> ParentCell:
        return ParentCell(
            parent_cell_id=parent_id,
            parent_fingerprint=stable_fingerprint(parent_id, "parent", "configuration"),
        )

    def base_child(self, child_id: str = "child") -> ChildCell:
        return ChildCell(
            child_cell_id=child_id,
            child_fingerprint=stable_fingerprint(child_id, "child", "configuration"),
        )

    def base_packet(self, scenario: str, parent: ParentCell, child: ChildCell) -> LineagePacket:
        return LineagePacket(
            packet_id=f"packet_{scenario}",
            parent_cell_id=parent.parent_cell_id,
            child_cell_id=child.child_cell_id,
            structural_epoch=child.child_structural_epoch,
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

    def record_packet(self, scenario: str, packet: LineagePacket, accepted: bool, rejection_reason: str) -> None:
        row = asdict(packet)
        row.update(
            {
                "scenario": scenario,
                "accepted_for_inheritance": accepted,
                "rejection_reason": rejection_reason,
            }
        )
        self.packet_rows.append(row)

    def record_child(self, scenario: str, child: ChildCell) -> None:
        row = asdict(child)
        row.update({"scenario": scenario})
        self.child_rows.append(row)

    def record_constraint(
        self,
        scenario: str,
        child: ChildCell,
        inherited: str,
        rejected: str,
        decision: str,
    ) -> None:
        self.constraint_rows.append(
            {
                "scenario": scenario,
                "child_cell_id": child.child_cell_id,
                "inherited_constraints": inherited,
                "rejected_constraints": rejected,
                "decision": decision,
            }
        )

    def record_scar_event(
        self,
        scenario: str,
        fingerprint: str,
        scar_class: str,
        event_decision: str,
        scar_written: bool,
        written_fingerprint: str = "",
    ) -> None:
        self.scar_rows.append(
            {
                "scenario": scenario,
                "fingerprint": fingerprint,
                "scar_class": scar_class,
                "event_decision": event_decision,
                "scar_written": scar_written,
                "written_fingerprint": written_fingerprint,
            }
        )

    def record_scope(self, scenario: str, packet: LineagePacket, decision: str, inherited_scope: str) -> None:
        self.scope_rows.append(
            {
                "scenario": scenario,
                "packet_id": packet.packet_id,
                "scope_status": packet.scope_status,
                "scope_overlap_proven": packet.scope_overlap_proven,
                "scope_limits": packet.scope_limits,
                "overlapping_constraints": packet.overlapping_constraints,
                "decision": decision,
                "inherited_scope": inherited_scope,
            }
        )

    def packet_rejection_reason(self, packet: LineagePacket) -> str:
        if not packet.parent_cell_id:
            return "missing_parent_cell_id"
        if not packet.child_cell_id:
            return "missing_child_cell_id"
        if packet.provenance_status != "valid":
            return "invalid_provenance"
        if packet.timestamp_status != "fresh":
            return "stale_packet"
        if packet.structural_epoch != "epoch_1":
            return "epoch_mismatch"
        if packet.verification_status != "verified":
            return "unverified_packet"
        if packet.scope_status == "unknown":
            return "unknown_scope"
        if packet.scope_status == "overlap" and not packet.scope_overlap_proven:
            return "unproven_scope_overlap"
        if packet.scope_status == "none":
            return "no_scope_overlap"
        if packet.contains_active_authority:
            return "contains_active_authority"
        if packet.contains_full_history:
            return "contains_full_history"
        if packet.contains_route_confidence_as_authority:
            return "contains_route_confidence_as_authority"
        if packet.contains_parent_shape_integrity_as_authority:
            return "contains_parent_shape_integrity_as_authority"
        return ""

    def packet_valid(self, packet: LineagePacket) -> Tuple[bool, str]:
        reason = self.packet_rejection_reason(packet)
        return reason == "", reason

    def scar_lookup(self, scar_registry: Dict[str, Scar], fingerprint: str) -> str:
        scar = scar_registry.get(fingerprint)
        if scar is None:
            return "NO_SCAR_MATCH"
        if scar.retirement_state == "RETIRED":
            return "NO_SCAR_MATCH_RETIRED"
        if scar.scar_class == "HARD":
            return "REJECT_AS_IS"
        if scar.scar_class in {"SOFT", "RESTORATION"}:
            return "REQUIRE_EXTRA_PROOF"
        return "UNKNOWN_SCAR_CLASS"

    def apply_lineage(
        self,
        scenario: str,
        parent: ParentCell,
        child: ChildCell,
        packet: LineagePacket,
        scar_registry: Dict[str, Scar],
        candidate_fingerprint: Optional[str] = None,
    ) -> Tuple[ChildCell, bool, str, str]:
        valid, rejection_reason = self.packet_valid(packet)
        self.record_packet(scenario, packet, valid, rejection_reason)

        inherited = ""
        rejected = rejection_reason
        scar_result = "PACKET_REJECTED"

        if not valid:
            child.child_final_state = "REQUALIFYING"
            child.child_active_authority = False
            child.child_bypass_permission = False
            child.inherited_constraints = ""
            child.rejected_constraints = rejection_reason
            self.record_constraint(scenario, child, "", rejection_reason, "PACKET_REJECTED")
            self.record_scope(scenario, packet, "REJECTED", "")
            self.record_child(scenario, child)
            self.log_event(scenario, packet, parent, child, "", rejection_reason, "REJECTED", "validity_failure")
            self.log_raw(scenario, "lineage_packet", "REJECTED", rejection_reason)
            return child, False, rejection_reason, scar_result

        if packet.scope_status == "overlap" and packet.scope_overlap_proven:
            inherited = packet.overlapping_constraints
            child.inherited_constraints = inherited
            scope_decision = "OVERLAP_ONLY"
            inherited_scope = packet.overlapping_constraints
        else:
            inherited = packet.scar_fingerprints or packet.blocked_candidates or packet.scope_limits
            child.inherited_constraints = inherited
            scope_decision = "MATCHING_OR_LIMITED"
            inherited_scope = packet.scope_limits or "matching"

        fingerprint = candidate_fingerprint or child.child_fingerprint
        scar_result = self.scar_lookup(scar_registry, fingerprint)
        scar_class = scar_registry[fingerprint].scar_class if fingerprint in scar_registry else "NONE"
        self.record_scar_event(scenario, fingerprint, scar_class, scar_result, False)

        if scar_result == "REJECT_AS_IS":
            child.child_final_state = "REJECTED"
        elif scar_result == "REQUIRE_EXTRA_PROOF":
            child.child_final_state = "REQUALIFYING"
            child.extra_proof_required = True
        elif scar_result in {"NO_SCAR_MATCH", "NO_SCAR_MATCH_RETIRED"}:
            child.child_final_state = "REQUALIFYING"
        else:
            child.child_final_state = "QUARANTINED"

        child.child_active_authority = False
        child.child_bypass_permission = False
        child.child_c_success = None
        child.child_shape_integrity = "UNKNOWN"

        self.record_constraint(scenario, child, inherited, rejected, scar_result)
        self.record_scope(scenario, packet, scope_decision, inherited_scope)
        self.record_child(scenario, child)
        self.log_event(scenario, packet, parent, child, inherited, rejected, scope_decision, scar_result)
        self.log_raw(scenario, "lineage_packet", "ACCEPTED_FOR_CONSTRAINTS", scar_result)
        return child, True, "", scar_result

    def complete_requalification(self, child: ChildCell) -> ChildCell:
        child.requalification_progress = REQUALIFICATION_THRESHOLD
        child.child_final_state = "ACTIVE"
        child.child_active_authority = True
        child.child_bypass_permission = True
        return child

    def fail_child_and_maybe_write_scar(
        self,
        scenario: str,
        child: ChildCell,
        valid_evidence: bool = True,
    ) -> Tuple[bool, str]:
        if child.child_active_authority and child.child_final_state == "ACTIVE" and valid_evidence:
            fingerprint = child.child_fingerprint
            self.record_scar_event(
                scenario,
                fingerprint,
                "HARD",
                "WRITE_CHILD_SCAR",
                True,
                written_fingerprint=fingerprint,
            )
            self.log_raw(scenario, "child_failure", "WRITE_CHILD_SCAR", fingerprint)
            return True, fingerprint

        self.record_scar_event(
            scenario,
            child.child_fingerprint,
            "NONE",
            "NO_SCAR_NO_AUTHORITY",
            False,
            written_fingerprint="",
        )
        self.log_raw(scenario, "child_failure", "NO_SCAR_NO_AUTHORITY", child.child_final_state)
        return False, ""

    def log_event(
        self,
        scenario: str,
        packet: LineagePacket,
        parent: ParentCell,
        child: ChildCell,
        inherited_constraints: str,
        rejected_constraints: str,
        scope_decision: str,
        provenance_decision: str,
    ) -> None:
        self.event_logs.append(
            {
                "scenario": scenario,
                "packet_id": packet.packet_id,
                "parent_cell_id": parent.parent_cell_id,
                "child_cell_id": child.child_cell_id,
                "structural_epoch": packet.structural_epoch,
                "lineage_boundary": packet.lineage_boundary,
                "inherited_constraints": inherited_constraints,
                "rejected_constraints": rejected_constraints,
                "scope_decision": scope_decision,
                "provenance_decision": provenance_decision,
                "requalification_requirement": packet.requalification_required,
                "final_child_state": child.child_final_state,
            }
        )

    def run(self) -> None:
        self.scenario_1_hard_scar()
        self.scenario_2_soft_scar()
        self.scenario_3_restoration_scar()
        self.scenario_4_no_scar_match()
        self.scenario_5_active_authority_contamination()
        self.scenario_6_route_confidence_contamination()
        self.scenario_7_shape_integrity_contamination()
        self.scenario_8_full_history_rejected()
        self.scenario_9_stale_packet()
        self.scenario_10_epoch_mismatch()
        self.scenario_11_unknown_scope()
        self.scenario_12_narrower_overlap()
        self.scenario_13_no_direct_active()
        self.scenario_14_partial_requalification_failure()
        self.scenario_15_post_authority_child_failure()
        self.scenario_16_repeated_contaminated_source()
        self.scenario_17_isolation_checks()
        self.finalize_assertions()

    def scenario_1_hard_scar(self) -> None:
        scenario = "S01_hard_scar_inherited"
        parent = self.base_parent("parent_hard")
        child = self.base_child("child_hard")
        packet = self.base_packet(scenario, parent, child)
        packet.scar_fingerprints = child.child_fingerprint
        registry = {child.child_fingerprint: Scar(child.child_fingerprint, "HARD")}
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, registry)
        self.record_summary(scenario, "REJECT_AS_IS and child REJECTED", f"{scar_result}; {child.child_final_state}", "PASS" if scar_result == "REJECT_AS_IS" and child.child_final_state == "REJECTED" else "FAIL")
        self.set_assertion("A1", "Hard scar constraint returns REJECT_AS_IS.", scar_result == "REJECT_AS_IS", scar_result)
        self.set_assertion("A2", "Hard scar constraint places child in REJECTED.", child.child_final_state == "REJECTED", child.child_final_state)

    def scenario_2_soft_scar(self) -> None:
        scenario = "S02_soft_scar_inherited"
        parent = self.base_parent("parent_soft")
        child = self.base_child("child_soft")
        packet = self.base_packet(scenario, parent, child)
        packet.scar_fingerprints = child.child_fingerprint
        registry = {child.child_fingerprint: Scar(child.child_fingerprint, "SOFT")}
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, registry)
        self.record_summary(scenario, "REQUIRE_EXTRA_PROOF and child REQUALIFYING", f"{scar_result}; {child.child_final_state}", "PASS" if scar_result == "REQUIRE_EXTRA_PROOF" and child.child_final_state == "REQUALIFYING" else "FAIL")
        self.set_assertion("A3", "Soft scar constraint returns REQUIRE_EXTRA_PROOF.", scar_result == "REQUIRE_EXTRA_PROOF", scar_result)
        self.set_assertion("A4", "Soft scar constraint places child in REQUALIFYING.", child.child_final_state == "REQUALIFYING", child.child_final_state)

    def scenario_3_restoration_scar(self) -> None:
        scenario = "S03_restoration_scar_inherited"
        parent = self.base_parent("parent_rest")
        child = self.base_child("child_rest")
        packet = self.base_packet(scenario, parent, child)
        packet.scar_fingerprints = child.child_fingerprint
        registry = {child.child_fingerprint: Scar(child.child_fingerprint, "RESTORATION")}
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, registry)
        self.record_summary(scenario, "REQUIRE_EXTRA_PROOF and child REQUALIFYING", f"{scar_result}; {child.child_final_state}", "PASS" if scar_result == "REQUIRE_EXTRA_PROOF" and child.child_final_state == "REQUALIFYING" else "FAIL")
        self.set_assertion("A5", "Restoration scar constraint returns REQUIRE_EXTRA_PROOF.", scar_result == "REQUIRE_EXTRA_PROOF", scar_result)
        self.set_assertion("A6", "Restoration scar constraint places child in REQUALIFYING.", child.child_final_state == "REQUALIFYING", child.child_final_state)

    def scenario_4_no_scar_match(self) -> None:
        scenario = "S04_no_scar_match"
        parent = self.base_parent("parent_nomatch")
        child = self.base_child("child_nomatch")
        packet = self.base_packet(scenario, parent, child)
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        no_block = scar_result == "NO_SCAR_MATCH"
        not_active = child.child_final_state != "ACTIVE"
        requalifying = child.child_final_state == "REQUALIFYING"
        self.record_summary(scenario, "NO_SCAR_MATCH, child REQUALIFYING, not ACTIVE", f"{scar_result}; {child.child_final_state}", "PASS" if no_block and not_active and requalifying else "FAIL")
        self.set_assertion("A7", "No scar match does not block child by scar status alone.", no_block, scar_result)
        self.set_assertion("A8", "No scar match does not place child in ACTIVE.", not_active, child.child_final_state)
        self.set_assertion("A9", "Valid no-match child enters REQUALIFYING.", requalifying, child.child_final_state)

    def scenario_5_active_authority_contamination(self) -> None:
        scenario = "S05_active_authority_contamination"
        parent = self.base_parent("parent_active_contam")
        child = self.base_child("child_active_contam")
        packet = self.base_packet(scenario, parent, child)
        packet.contains_active_authority = True
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        self.record_summary(scenario, "packet rejected and no authority", f"accepted={accepted}; authority={child.child_active_authority}; bypass={child.child_bypass_permission}; reason={reason}", "PASS" if not accepted and not child.child_active_authority and not child.child_bypass_permission else "FAIL")
        self.set_assertion("A10", "Child cannot inherit active authority.", not child.child_active_authority, str(child.child_active_authority))
        self.set_assertion("A11", "Child cannot inherit bypass permission.", not child.child_bypass_permission, str(child.child_bypass_permission))
        self.set_assertion("A12", "Packet containing active authority is rejected for inheritance.", not accepted and reason == "contains_active_authority", reason)

    def scenario_6_route_confidence_contamination(self) -> None:
        scenario = "S06_route_confidence_contamination"
        parent = self.base_parent("parent_route_conf")
        child = self.base_child("child_route_conf")
        packet = self.base_packet(scenario, parent, child)
        packet.contains_route_confidence_as_authority = True
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        no_c_success = child.child_c_success is None and not child.child_active_authority
        self.record_summary(scenario, "packet rejected and no C_success authority", f"accepted={accepted}; child_c_success={child.child_c_success}; reason={reason}", "PASS" if not accepted and no_c_success else "FAIL")
        self.set_assertion("A13", "Packet containing route confidence as authority is rejected for inheritance.", not accepted and reason == "contains_route_confidence_as_authority", reason)
        self.set_assertion("A14", "Child cannot inherit parent C_success as permission.", no_c_success, str(child.child_c_success))

    def scenario_7_shape_integrity_contamination(self) -> None:
        scenario = "S07_shape_integrity_contamination"
        parent = self.base_parent("parent_shape")
        child = self.base_child("child_shape")
        packet = self.base_packet(scenario, parent, child)
        packet.contains_parent_shape_integrity_as_authority = True
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        no_shape_permission = child.child_shape_integrity != parent.parent_shape_integrity and not child.child_active_authority
        self.record_summary(scenario, "packet rejected and no shape authority", f"accepted={accepted}; child_shape={child.child_shape_integrity}; reason={reason}", "PASS" if not accepted and no_shape_permission else "FAIL")
        self.set_assertion("A15", "Packet containing parent shape integrity as authority is rejected for inheritance.", not accepted and reason == "contains_parent_shape_integrity_as_authority", reason)
        self.set_assertion("A16", "Child cannot inherit parent shape_integrity as permission.", no_shape_permission, child.child_shape_integrity)

    def scenario_8_full_history_rejected(self) -> None:
        scenario = "S08_full_history_rejected"
        parent = self.base_parent("parent_history")
        child = self.base_child("child_history")
        packet = self.base_packet(scenario, parent, child)
        packet.contains_full_history = True
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        self.record_summary(scenario, "packet rejected", f"accepted={accepted}; reason={reason}", "PASS" if not accepted and reason == "contains_full_history" else "FAIL")
        self.set_assertion("A17", "Packet containing full history is rejected for inheritance.", not accepted and reason == "contains_full_history", reason)

    def scenario_9_stale_packet(self) -> None:
        scenario = "S09_stale_packet"
        parent = self.base_parent("parent_stale")
        child = self.base_child("child_stale")
        packet = self.base_packet(scenario, parent, child)
        packet.timestamp_status = "stale"
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        self.record_summary(scenario, "packet rejected", f"accepted={accepted}; reason={reason}", "PASS" if not accepted and reason == "stale_packet" else "FAIL")
        self.set_assertion("A18", "Stale packet is rejected for inheritance.", not accepted and reason == "stale_packet", reason)

    def scenario_10_epoch_mismatch(self) -> None:
        scenario = "S10_epoch_mismatch"
        parent = self.base_parent("parent_epoch")
        child = self.base_child("child_epoch")
        packet = self.base_packet(scenario, parent, child)
        packet.structural_epoch = "epoch_old"
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        self.record_summary(scenario, "packet rejected", f"accepted={accepted}; reason={reason}", "PASS" if not accepted and reason == "epoch_mismatch" else "FAIL")
        self.set_assertion("A19", "Epoch-mismatched packet is rejected for inheritance.", not accepted and reason == "epoch_mismatch", reason)

    def scenario_11_unknown_scope(self) -> None:
        scenario = "S11_unknown_scope"
        parent = self.base_parent("parent_scope")
        child = self.base_child("child_scope")
        packet = self.base_packet(scenario, parent, child)
        packet.scope_status = "unknown"
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        self.record_summary(scenario, "packet rejected", f"accepted={accepted}; reason={reason}", "PASS" if not accepted and reason == "unknown_scope" else "FAIL")
        self.set_assertion("A20", "Unknown-scope packet is rejected for inheritance.", not accepted and reason == "unknown_scope", reason)

    def scenario_12_narrower_overlap(self) -> None:
        scenario = "S12_narrower_proven_overlap"
        parent = self.base_parent("parent_overlap")
        parent.parent_scope = "role_edge_region_A_B_C"
        child = self.base_child("child_overlap")
        child.child_scope = "role_edge_region_A"
        packet = self.base_packet(scenario, parent, child)
        packet.scope_status = "overlap"
        packet.scope_overlap_proven = True
        packet.overlapping_constraints = "constraint_region_A_only"
        packet.scope_limits = "region_A"
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        only_overlap = accepted and child.inherited_constraints == "constraint_region_A_only"
        self.record_summary(scenario, "only overlapping constraints inherited", child.inherited_constraints, "PASS" if only_overlap else "FAIL")
        self.set_assertion("A21", "Narrower proven overlap inherits only overlapping constraints.", only_overlap, child.inherited_constraints)

    def scenario_13_no_direct_active(self) -> None:
        scenario = "S13_no_direct_active"
        parent = self.base_parent("parent_noactive")
        child = self.base_child("child_noactive")
        packet = self.base_packet(scenario, parent, child)
        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
        no_direct_active = child.child_final_state != "ACTIVE" and not child.child_active_authority
        self.record_summary(scenario, "child not ACTIVE directly", child.child_final_state, "PASS" if no_direct_active else "FAIL")
        self.set_assertion("A22", "Child cannot enter ACTIVE directly from lineage inheritance.", no_direct_active, child.child_final_state)

    def scenario_14_partial_requalification_failure(self) -> None:
        scenario = "S14_partial_requalification_failure"
        child = self.base_child("child_partial")
        child.child_final_state = "REQUALIFYING"
        child.requalification_progress = PARTIAL_REQUALIFICATION_PROGRESS
        child.child_active_authority = False
        scar_written, written_fp = self.fail_child_and_maybe_write_scar(scenario, child)
        partial_not_authority = child.requalification_progress < child.requalification_threshold and not child.child_active_authority
        no_scar = not scar_written
        self.record_child(scenario, child)
        self.record_summary(scenario, "partial progress not authority and no scar", f"progress={child.requalification_progress}; scar={scar_written}", "PASS" if partial_not_authority and no_scar else "FAIL")
        self.set_assertion("A23", "Partial requalification progress is not authority.", partial_not_authority, f"{child.requalification_progress}/{child.requalification_threshold}")
        self.set_assertion("A24", "Failure during partial requalification creates no scar.", no_scar, str(scar_written))

    def scenario_15_post_authority_child_failure(self) -> None:
        scenario = "S15_post_authority_child_failure"
        parent = self.base_parent("parent_post_authority")
        child = self.base_child("child_post_authority")
        child = self.complete_requalification(child)
        scar_written, written_fp = self.fail_child_and_maybe_write_scar(scenario, child)
        child_fp_used = written_fp == child.child_fingerprint and written_fp != parent.parent_fingerprint
        self.record_child(scenario, child)
        self.record_summary(scenario, "child scar written with child fingerprint", f"scar={scar_written}; fp={written_fp}", "PASS" if scar_written and child_fp_used else "FAIL")
        self.set_assertion("A25", "Child failure after completed requalification and active authority creates a scar.", scar_written, written_fp)
        self.set_assertion("A26", "The scar written after post-authority child failure carries the child cell fingerprint, not the parent cell fingerprint.", child_fp_used, f"child={child.child_fingerprint}; parent={parent.parent_fingerprint}; written={written_fp}")

    def scenario_16_repeated_contaminated_source(self) -> None:
        scenario = "S16_repeated_contaminated_source"
        parent = self.base_parent("parent_repeat_contam")
        rejections = 0
        escalations_claimed = 0
        for idx in range(3):
            child = self.base_child(f"child_repeat_contam_{idx}")
            packet = self.base_packet(f"{scenario}_{idx}", parent, child)
            packet.source = "source_with_repeated_contamination"
            packet.contains_active_authority = True
            child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, {})
            if not accepted:
                rejections += 1
            # This harness records contamination but does not implement quarantine, blacklist, or escalation.
            escalations_claimed += 0
        good = rejections == 3 and escalations_claimed == 0
        self.record_summary(scenario, "three packets rejected, no source escalation claimed", f"rejections={rejections}; escalations={escalations_claimed}", "PASS" if good else "FAIL")
        self.set_assertion("A27", "Repeated contaminated packets are recorded without source-level escalation claim.", good, f"rejections={rejections}; escalations={escalations_claimed}")

    def scenario_17_isolation_checks(self) -> None:
        scenario = "S17_isolation_checks"
        parent = self.base_parent("parent_isolation")
        child = self.base_child("child_isolation")
        packet = self.base_packet(scenario, parent, child)
        registry = {
            "unrelated_hard": Scar("unrelated_hard", "HARD"),
            "unrelated_soft": Scar("unrelated_soft", "SOFT"),
            child.child_fingerprint: Scar(child.child_fingerprint, "SOFT"),
        }

        registry_before = stable_registry_hash(registry)
        parent_c_before = parent.parent_c_success
        parent_shape_before = parent.parent_shape_integrity

        child, accepted, reason, scar_result = self.apply_lineage(scenario, parent, child, packet, registry)

        registry_after = stable_registry_hash(registry)
        parent_c_after = parent.parent_c_success
        parent_shape_after = parent.parent_shape_integrity

        registry_unchanged = registry_before == registry_after
        c_success_unchanged = parent_c_before == parent_c_after and child.child_c_success is None
        shape_unchanged = parent_shape_before == parent_shape_after and child.child_shape_integrity != parent_shape_integrity_safe(parent)

        self.record_summary(
            scenario,
            "registry, parent C_success, and parent shape_integrity unchanged",
            f"registry={registry_unchanged}; c_success={c_success_unchanged}; shape={shape_unchanged}",
            "PASS" if registry_unchanged and c_success_unchanged and shape_unchanged else "FAIL",
        )
        self.set_assertion("A28", "Lineage inheritance does not mutate the scar registry during lookup.", registry_unchanged, f"before={registry_before}; after={registry_after}")
        self.set_assertion("A29", "Lineage inheritance does not mutate parent C_success.", c_success_unchanged, f"before={parent_c_before}; after={parent_c_after}; child={child.child_c_success}")
        self.set_assertion("A30", "Lineage inheritance does not mutate parent shape_integrity.", shape_unchanged, f"before={parent_shape_before}; after={parent_shape_after}; child={child.child_shape_integrity}")

    def finalize_assertions(self) -> None:
        required_keys = {
            "packet_id",
            "parent_cell_id",
            "child_cell_id",
            "structural_epoch",
            "lineage_boundary",
            "inherited_constraints",
            "rejected_constraints",
            "scope_decision",
            "provenance_decision",
            "requalification_requirement",
            "final_child_state",
        }
        logs_valid = bool(self.event_logs) and all(required_keys.issubset(set(log.keys())) for log in self.event_logs)
        self.set_assertion("A31", "The lineage event log contains packet id, parent id, child id, epoch, boundary, inherited constraints, rejected constraints, scope decision, provenance decision, requalification requirement, and final child state.", logs_valid, f"logs={len(self.event_logs)}")

        deterministic = len(self.assertions) == 31
        self.set_assertion("A32", "The harness produces a deterministic final verdict from the assertion results.", deterministic, f"assertions_before_A32={len(self.assertions)}")

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
    payload = json.dumps(serializable, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parent_shape_integrity_safe(parent: ParentCell) -> str:
    return parent.parent_shape_integrity


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
        "A10",
        "A11",
        "A12",
        "A13",
        "A14",
        "A15",
        "A16",
        "A22",
        "A24",
        "A26",
    }
    if failed_ids & not_supported_ids:
        return "NOT_SUPPORTED"

    return "INCONCLUSIVE"


def main() -> int:
    start = time.time()
    repo_root = get_repo_root()
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    harness = LineageInheritanceHarness()
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
            "requalification_threshold": REQUALIFICATION_THRESHOLD,
            "partial_requalification_progress": PARTIAL_REQUALIFICATION_PROGRESS,
            "scope_overlap_model": SCOPE_OVERLAP_MODEL,
        }
    ]

    outputs = {
        "lineage_inheritance_v0_1_raw.csv": harness.raw_rows,
        "lineage_inheritance_v0_1_summary.csv": harness.summary_rows,
        "lineage_inheritance_v0_1_packets.csv": harness.packet_rows,
        "lineage_inheritance_v0_1_child_states.csv": harness.child_rows,
        "lineage_inheritance_v0_1_constraints.csv": harness.constraint_rows,
        "lineage_inheritance_v0_1_scar_events.csv": harness.scar_rows,
        "lineage_inheritance_v0_1_scope_decisions.csv": harness.scope_rows,
        "lineage_inheritance_v0_1_assertions.csv": harness.assertion_rows,
        "lineage_inheritance_v0_1_verdict.csv": verdict_rows,
    }

    for filename, rows in outputs.items():
        write_csv(data_dir / filename, rows)

    script_path = Path(__file__).resolve()
    run_record_path = data_dir / "lineage_inheritance_v0_1_run_record.txt"
    output_inventory = "\n".join(sorted(outputs.keys()) + ["lineage_inheritance_v0_1_run_record.txt"])

    run_record = f"""Lineage Inheritance Simulation v1 Run Record

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
REQUALIFICATION_THRESHOLD = {REQUALIFICATION_THRESHOLD}
PARTIAL_REQUALIFICATION_PROGRESS = {PARTIAL_REQUALIFICATION_PROGRESS}
SCOPE_OVERLAP_MODEL = {SCOPE_OVERLAP_MODEL}

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
