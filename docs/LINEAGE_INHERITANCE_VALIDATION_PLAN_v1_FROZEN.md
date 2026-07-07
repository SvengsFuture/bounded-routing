# Lineage Inheritance Validation Plan v0.1

Status: Frozen for implementation planning.

## Purpose

This document defines the first validation plan for lineage inheritance.

The goal is narrow.

The test should determine whether a replacement cell can inherit compact constraints from a parent context without inheriting active authority, full history, old route confidence, or old shape integrity.

This plan does not validate production recovery.

This plan does not validate fuzzy scar matching.

This plan does not validate prospective filtering.

This plan does not validate a full extra-proof protocol.

This plan does not validate source-level escalation for repeated contaminated lineage packets.

## Controlling Question

Can a child cell inherit constraints without inheriting authority?

## Frozen Harness Parameters

The validation harness uses the following declared parameters.

```text
REQUALIFICATION_THRESHOLD = 5
PARTIAL_REQUALIFICATION_PROGRESS = 3
SCOPE_OVERLAP_MODEL = explicit boolean scope_overlap_proven field
```

A child has not held authority until it completes all five requalification steps and passes the final admission check.

A child at three of five steps has partial progress only.

Partial progress is not authority.

Scope overlap is not inferred by a string-matching algorithm in this validation. The harness uses an explicit `scope_overlap_proven` field on the lineage packet. If that field is true, the harness may inherit only the declared overlapping constraints. If that field is false or unknown, overlap is not proven.

The mechanism is supported only if the harness shows all of the following.

Hard scar constraints are inherited as rejection constraints.

Soft scar constraints are inherited as extra-proof constraints.

Restoration scar constraints are inherited as extra-proof constraints.

No scar match does not block the child by scar status alone.

No scar match does not admit the child directly into active authority.

A child with valid reconstruction evidence enters REQUALIFYING before active authority.

A child cannot inherit parent C_success as authority.

A child cannot inherit parent shape_integrity as authority.

A child cannot inherit active bypass permission.

A contaminated lineage packet is rejected for inheritance.

A stale packet is rejected for inheritance.

An epoch-mismatched packet is rejected for inheritance.

An unknown-scope packet is rejected for inheritance.

A narrower proven scope inherits only overlapping constraints.

A failure during partial requalification does not create a scar.

A child creates a scar only after it has completed requalification, held authority, and then failed under valid evidence.

## Model Boundary

The validation harness should model parent cells, child cells, lineage packets, scar constraints, scope decisions, and authority states.

The harness does not need full tetrahedral physics.

The harness does not need route simulation beyond enough route authority state to test that inherited authority is blocked.

The harness does not need fuzzy matching.

The harness does not need source escalation.

The harness should be deterministic.

## Minimal Entities

The harness should define parent cells.

Each parent cell should include:

```text
parent_cell_id
parent_final_state
parent_scope
parent_structural_epoch
parent_c_success
parent_shape_integrity
parent_active_authority
parent_bypass_permission
```

The harness should define child cells.

Each child cell should include:

```text
child_cell_id
child_candidate_state
child_scope
child_structural_epoch
child_initial_state
child_final_state
child_c_success
child_shape_integrity
child_active_authority
child_bypass_permission
requalification_progress
requalification_threshold
```

The harness should define lineage packets.

Each lineage packet should include:

```text
packet_id
parent_cell_id
child_cell_id
structural_epoch
lineage_boundary
source
timestamp_status
provenance_status
scope_status
scope_overlap_proven
verification_status
contains_active_authority
contains_full_history
contains_route_confidence_as_authority
contains_parent_shape_integrity_as_authority
scar_fingerprints
blocked_candidates
required_extra_proof
scope_limits
requalification_required
```

The harness should define scars.

Each scar should include:

```text
fingerprint
scar_class
retirement_state
```

## Child States

The validation harness should use these child states.

```text
RECONSTRUCTING
REQUALIFYING
QUARANTINED
REJECTED
ACTIVE
```

A child may enter ACTIVE only after the declared requalification threshold is complete and the final admission check passes.

A child must not enter ACTIVE directly from lineage inheritance.

## Packet Validity Rules

A lineage packet is valid only if all of the following are true.

The packet has a parent cell identifier.

The packet has a child cell identifier.

The packet has valid provenance.

The packet is fresh.

The packet matches the current structural epoch.

The packet scope applies to the child scope or has a provable overlap.

The packet is verifiable.

The packet does not contain active authority.

The packet does not contain full history.

The packet does not contain route confidence presented as authority.

The packet does not contain parent shape integrity presented as authority.

If any of these checks fail, the packet is rejected for inheritance.

Packet rejection does not necessarily reject reconstruction.

It means the child cannot inherit that packet's constraints or authority.

Since authority inheritance is always prohibited, a contaminated packet also cannot grant bypass permission.

## Scar Constraint Rules

A hard scar match returns REJECT_AS_IS.

A soft scar match returns REQUIRE_EXTRA_PROOF.

A restoration scar match returns REQUIRE_EXTRA_PROOF.

A no-match result returns NO_SCAR_MATCH.

NO_SCAR_MATCH does not prove safety.

NO_SCAR_MATCH does not place the child into ACTIVE.

If reconstruction evidence, provenance, scope, and structural checks are valid, a no-match child may enter REQUALIFYING.

A retired scar is out of scope for this validation plan unless explicitly modeled as inert historical metadata.

## Authority Rules

Lineage inheritance may transfer constraints.

Lineage inheritance must not transfer active authority.

Lineage inheritance must not transfer bypass permission.

Lineage inheritance must not transfer parent C_success as authority.

Lineage inheritance must not transfer parent shape_integrity as authority.

A child cell cannot support bypass while RECONSTRUCTING, REQUALIFYING, QUARANTINED, or REJECTED.

A child cell can support bypass only after it has entered ACTIVE through the declared requalification process.

## Requalification Rules

Partial requalification progress is not authority.

A child with partial requalification progress cannot create a scar if it fails.

A child that has not completed the full requalification threshold has not held authority.

A child can create a scar only if it completed requalification, was admitted into active authority, then failed under valid evidence.

## Scope Rules

Scope overlap is represented by the explicit `scope_overlap_proven` field in this validation harness.

The harness does not infer overlap from file paths, names, text similarity, or semantic matching.

A packet with proven matching scope may constrain the child.

A packet with proven narrower overlap may constrain the child only inside the overlap.

A packet with unknown scope is rejected for inheritance.

A packet with broader parent scope cannot authorize a broader child scope without new evidence.

A packet with no provable overlap is rejected for inheritance.

## Test Scenarios

Scenario 1: hard scar inherited.

A valid lineage packet contains a hard scar fingerprint matching the child candidate.

Expected result: child state REJECTED, scar result REJECT_AS_IS.

Scenario 2: soft scar inherited.

A valid lineage packet contains a soft scar fingerprint matching the child candidate.

Expected result: child state REQUALIFYING, extra proof required.

Scenario 3: restoration scar inherited.

A valid lineage packet contains a restoration scar fingerprint matching the child candidate.

Expected result: child state REQUALIFYING, extra proof required.

Scenario 4: no scar match enters requalification.

A valid lineage packet contains no scar match and all reconstruction evidence is valid.

Expected result: child state REQUALIFYING, not ACTIVE.

Scenario 5: contaminated active authority rejected.

A lineage packet contains active authority.

Expected result: packet rejected for inheritance, child does not inherit authority, child does not bypass.

Scenario 6: contaminated route confidence rejected.

A lineage packet contains parent C_success presented as authority.

Expected result: packet rejected for inheritance, child does not inherit C_success as permission.

Scenario 7: contaminated shape integrity rejected.

A lineage packet contains parent shape_integrity presented as authority.

Expected result: packet rejected for inheritance, child does not inherit shape_integrity as permission.

Scenario 8: full history rejected.

A lineage packet contains full parent history rather than compact constraints.

Expected result: packet rejected for inheritance.

Scenario 9: stale packet rejected.

A lineage packet has stale timestamp status.

Expected result: packet rejected for inheritance.

Scenario 10: epoch mismatch rejected.

A lineage packet belongs to a different structural epoch.

Expected result: packet rejected for inheritance.

Scenario 11: unknown scope rejected.

A lineage packet has unknown scope relation to the child.

Expected result: packet rejected for inheritance.

Scenario 12: narrower proven overlap.

A lineage packet has a broader parent boundary and a narrower child overlap.

The packet sets `scope_overlap_proven = true` and declares the exact overlapping constraint set.

Expected result: only the declared overlapping constraints are inherited.

Scenario 13: no direct ACTIVE state.

A child receives a valid lineage packet with no hard scar and valid reconstruction evidence.

Expected result: child enters REQUALIFYING, not ACTIVE.

Scenario 14: partial requalification failure creates no scar.

A child progresses to `PARTIAL_REQUALIFICATION_PROGRESS = 3` while the required `REQUALIFICATION_THRESHOLD = 5`.

The child then fails before meeting the full threshold.

Expected result: no scar written.

Scenario 15: post-authority child failure creates scar.

A child completes `REQUALIFICATION_THRESHOLD = 5`, enters ACTIVE, then fails under valid evidence.

Expected result: scar written using the child cell fingerprint, not the parent cell fingerprint.

Scenario 16: repeated contaminated source recorded but not escalated.

The same source provides repeated contaminated packets.

Expected result: contamination events are recorded, packets are rejected, and no source-level quarantine, blacklist, or escalation is claimed.

## Assertions

A1: Hard scar constraint returns REJECT_AS_IS.

A2: Hard scar constraint places child in REJECTED.

A3: Soft scar constraint returns REQUIRE_EXTRA_PROOF.

A4: Soft scar constraint places child in REQUALIFYING.

A5: Restoration scar constraint returns REQUIRE_EXTRA_PROOF.

A6: Restoration scar constraint places child in REQUALIFYING.

A7: No scar match does not block child by scar status alone.

A8: No scar match does not place child in ACTIVE.

A9: Valid no-match child enters REQUALIFYING.

A10: Child cannot inherit active authority.

A11: Child cannot inherit bypass permission.

A12: Packet containing active authority is rejected for inheritance.

A13: Packet containing route confidence as authority is rejected for inheritance.

A14: Child cannot inherit parent C_success as permission.

A15: Packet containing parent shape integrity as authority is rejected for inheritance.

A16: Child cannot inherit parent shape_integrity as permission.

A17: Packet containing full history is rejected for inheritance.

A18: Stale packet is rejected for inheritance.

A19: Epoch-mismatched packet is rejected for inheritance.

A20: Unknown-scope packet is rejected for inheritance.

A21: Narrower proven overlap inherits only overlapping constraints.

A22: Child cannot enter ACTIVE directly from lineage inheritance.

A23: Partial requalification progress is not authority.

A24: Failure during partial requalification creates no scar.

A25: Child failure after completed requalification and active authority creates a scar.

A26: The scar written after post-authority child failure carries the child cell fingerprint, not the parent cell fingerprint.

A27: Repeated contaminated packets are recorded without source-level escalation claim.

A28: Lineage inheritance does not mutate the scar registry during lookup. Verification method: compute a stable hash or serialized snapshot of the scar registry before lineage lookup and after lineage lookup. The values must match.

A29: Lineage inheritance does not mutate parent C_success. Verification method: record parent C_success before lineage processing and after lineage processing. The values must match, and the child must not receive that value as authority.

A30: Lineage inheritance does not mutate parent shape_integrity. Verification method: record parent shape_integrity before lineage processing and after lineage processing. The values must match, and the child must not receive that value as authority.

A31: The lineage event log contains packet id, parent id, child id, epoch, boundary, inherited constraints, rejected constraints, scope decision, provenance decision, requalification requirement, and final child state.

A32: The harness produces a deterministic final verdict from the assertion results.

## Output Files

The validation run should produce:

```text
lineage_inheritance_v0_1_raw.csv
lineage_inheritance_v0_1_summary.csv
lineage_inheritance_v0_1_packets.csv
lineage_inheritance_v0_1_child_states.csv
lineage_inheritance_v0_1_constraints.csv
lineage_inheritance_v0_1_scar_events.csv
lineage_inheritance_v0_1_scope_decisions.csv
lineage_inheritance_v0_1_assertions.csv
lineage_inheritance_v0_1_verdict.csv
lineage_inheritance_v0_1_run_record.txt
```

Plots should come only after data output is stable.

Suggested plots:

```text
lineage_assertion_status.png
lineage_packet_accept_reject.png
lineage_child_state_outcomes.png
lineage_constraint_inheritance.png
lineage_scar_behavior.png
```

## Verdict Boundary

The result is SUPPORTED only if all declared assertions pass.

The result is NOT SUPPORTED if any of these failures occur:

```text
child enters ACTIVE directly from lineage
child inherits active authority
child inherits bypass permission
child inherits parent C_success as authority
child inherits parent shape_integrity as authority
hard scar does not block same candidate as-is
partial requalification failure creates a scar
post-authority child failure writes a parent fingerprint instead of the child fingerprint
contaminated packet grants inheritance
```

The result is INCONCLUSIVE if the harness does not exercise hard scar, soft scar, restoration scar, no-match, contaminated packet, stale packet, epoch mismatch, unknown scope, narrower overlap, partial requalification failure, and post-authority failure cases.

## Required Run Record

The run record should include:

```text
script filename
script SHA-256 hash
validation plan SHA-256 hash
specification SHA-256 hash
runtime
Python version
random seed if used
assertion count
assertion pass count
final verdict
output file inventory
stderr status
```

## Non-Claims

This validation plan does not prove production recovery.

It does not prove fuzzy scar matching.

It does not prove prospective filtering.

It does not prove a full extra-proof protocol.

It does not prove source-level escalation for repeated contaminated packets.

It does not prove that every child cell is safe.

It does not prove that all damaged cells can be replaced.

It does not prove that lineage packets are sufficient for all recovery cases.

It does not prove production reliability.

## Freeze Criteria

Before implementation, this plan should be reviewed for three questions.

First, does the plan test constraint inheritance without accidentally granting authority inheritance?

Second, does the plan preserve the separation among scar matching, shape integrity, route confidence, shedding, lineage, and requalification?

Third, does the verdict boundary punish the failures that would silently preserve failed authority?

Once those questions are answered, this plan can be frozen as:

```text
LINEAGE_INHERITANCE_VALIDATION_PLAN_v1_FROZEN.md
```
