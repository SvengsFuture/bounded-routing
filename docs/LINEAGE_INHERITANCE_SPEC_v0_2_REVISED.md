# Lineage Inheritance Specification v0.1

Status: Revised draft for review.

## Purpose

This document defines the next architectural layer after cellular shedding.

The scar layer records rejected structural configurations after betrayed authority.

Cellular shedding removes a damaged local cell from active authority.

Lineage inheritance defines what a replacement cell may inherit after the damaged cell has been shed.

The purpose is narrow.

A regenerated or replacement cell may inherit compact constraints.

It may not inherit active authority.

It may not inherit full history.

It may not inherit old route confidence as permission to bypass.

It may not erase or weaken scars created before reconstruction.

This document is not a validation plan.

This document is not a simulation harness.

This document does not define fuzzy scar matching.

This document does not define a full extra-proof protocol.

## Controlling Principle

Lineage inheritance is constraint inheritance, not authority inheritance.

A replacement cell may receive a compact list of rejected configurations, blocked structural patterns, prior failure boundaries, and declared requalification requirements.

A replacement cell must not receive active bypass authority merely because it descends from a previous cell.

The governing rule is:

```text
Inherit constraints, not authority.
```

A replacement cell can be born with warnings.

It cannot be born trusted.

Authority must be earned again under current evidence.

## Relationship To Existing Layers

Bounded routing decides whether a learned route may bypass full analysis.

The shape-integrity gate decides whether current structural condition permits bypass authority.

The scar registry records configurations that had authority and later failed.

Cellular shedding removes the damaged local cell from active authority.

Lineage inheritance transfers compact rejection knowledge into the replacement path without transferring old authority.

These jobs must remain separate.

The router does not create lineage.

The scar registry does not grant authority.

The shedding layer does not define inherited memory.

The replacement cell does not inherit active bypass permission.

Lineage inheritance only defines what compact constraints follow from old structure into new structure.

## Definitions

A parent cell is a cell that previously existed inside the structural substrate and was later shed, quarantined, retired, or replaced.

A child cell is a reconstructed, regenerated, or replacement cell proposed to occupy a role, relation, or local structural function after the parent cell has lost authority.

A lineage packet is the compact constraint record passed from parent context into child context.

A lineage boundary is the declared scope over which inherited constraints apply.

A lineage fingerprint is the identity of the parent-child relation and the constrained structural role.

A constraint is inherited information that can restrict, require, or block future promotion.

Authority is permission to support bypass or active structural function.

Inherited authority is prohibited.

Inherited constraints are allowed when evidence, scope, and provenance are valid.

A contaminated lineage packet is a lineage packet that contains stale authority, full history, unverifiable data, out-of-scope data, or route confidence disguised as structural permission.

## Required Inputs

A lineage inheritance decision requires valid evidence.

The minimum required inputs are:

parent cell identifier

child cell identifier

structural epoch

lineage boundary

parent final state

child proposed role or relation

applicable scar fingerprints

shed boundary

reconstruction proposal identity

source of lineage packet

timestamp

scope

provenance

verification status

requalification requirement

Missing, stale, unverifiable, epoch-mismatched, or out-of-scope lineage evidence cannot authorize inheritance.

When lineage evidence is invalid, the replacement cell may still be created, but it must not inherit constraints from the invalid packet and must not inherit authority.

## What May Be Inherited

A child cell may inherit compact constraints.

Allowed inherited items include:

```text
hard scar fingerprints
soft scar fingerprints
restoration scar fingerprints
blocked reconstruction candidates
required extra-proof flags
parent failure class metadata
shed boundary metadata
scope limits
requalification requirements
load-transfer limits
quarantine reason
retirement reason
```

These inherited items restrict what the child may do.

They do not grant permission.

## What Must Not Be Inherited

A child cell must not inherit active authority.

A child cell must not inherit active bypass permission.

A child cell must not inherit route confidence as authority.

A child cell must not inherit a clean shape-integrity state from the parent.

A child cell must not inherit the parent's final active status.

A child cell must not inherit full event history.

A child cell must not inherit stale recovery context.

A child cell must not inherit an old structural epoch.

A child cell must not inherit permission to ignore hard scars.

A child cell must not inherit permission to bypass extra proof.

A child cell must not inherit a parent's successful past performance as present admissibility.

## Lineage Packet

A lineage packet is the compact record passed from parent context to child context.

A lineage packet should include:

```text
packet_id
parent_cell_id
child_cell_id
structural_epoch
lineage_boundary
parent_final_state
child_candidate_state
scar_fingerprints
blocked_candidates
required_extra_proof
scope_limits
requalification_required
source
timestamp
provenance
verification_status
```

A lineage packet is not general memory.

It is not a replay log.

It is not a full history.

It is a compact constraint envelope.

## Initial Child State

A child cell created through lineage inheritance must enter one of these states:

```text
RECONSTRUCTING
REQUALIFYING
QUARANTINED
REJECTED
```

A child cell must not enter ACTIVE directly from lineage inheritance.

A child cell may become ACTIVE only through the declared requalification process.

If a hard scar blocks the child candidate as-is, the child enters REJECTED.

If a soft or restoration scar applies, the child enters REQUALIFYING with extra proof required.

If lineage evidence is invalid but reconstruction is still allowed, the child enters REQUALIFYING with no inherited constraint packet.

If reconstruction evidence is invalid, the child enters QUARANTINED or REJECTED according to the recovery rule.

## Scar Interaction

Hard scars are inherited as blocking constraints.

A child candidate matching a hard scar must be rejected as-is.

Soft scars are inherited as extra-proof constraints.

Restoration scars are inherited as extra-proof constraints.

A missing scar match does not prove safety.

When no scar match is found, scar status alone does not block the child candidate. If provenance, scope, reconstruction evidence, and structural evidence are valid, the child may enter REQUALIFYING. It must not enter ACTIVE from a no-match result.

A retired scar may be inherited only as historical constraint metadata if the validation plan declares that behavior.

Scar inheritance must remain separate from shape integrity.

Scar inheritance must remain separate from C_success.

Scar inheritance must not mutate the scar registry unless a new betrayed-authority event occurs.

## Requalification

Lineage inheritance does not complete requalification.

A child cell with inherited constraints must still pass current structural checks.

A child cell must satisfy declared requalification before it can support bypass authority.

Requalification must use current evidence.

Requalification must not use parent authority.

Requalification must not use parent route confidence as a substitute for current admissibility.

A child cell that fails requalification under valid evidence may create a new scar only if it had authority before that failure.

A child cell has not held authority until it has completed the full declared requalification threshold and has been admitted into active authority.

Partial requalification progress is not authority.

A child cell that fails during requalification does not create a scar regardless of how far requalification had progressed.

A child cell that never received authority cannot create a scar through failed requalification alone.

## Scope

Lineage inheritance must be scoped.

A parent cell may have failed in one role, relation, or local boundary.

The child may be proposed for the same role, a neighboring role, or a reconstructed relation.

Inherited constraints apply only inside declared scope.

If scope is unknown, the system fails closed.

If the child scope is broader than the parent scope, the inherited packet cannot authorize the broader scope.

If the child scope is narrower than the parent scope, the packet may restrict the child only inside the overlap.

If scope overlap cannot be proven, the packet is treated as invalid for that child.

## Provenance

A lineage packet must carry provenance.

The system must know where the packet came from, what parent it describes, what child it applies to, what structural epoch it belongs to, and what observer or recovery process created it.

Lineage packets without provenance cannot constrain a child as trusted evidence.

They also cannot grant authority.

They are rejected or quarantined.

## Evidence Log

Every lineage inheritance event must leave an evidence log.

The log should record:

```text
packet_id
parent_cell_id
child_cell_id
structural_epoch
lineage_boundary
parent_final_state
child_initial_state
inherited_constraints
rejected_constraints
scar match results
scope decision
provenance decision
requalification requirement
final child state
```

This log is not full memory.

It is a replay record for audit, recovery, and validation.

## Safety Rules

A child cell cannot inherit active authority.

A child cell cannot inherit bypass permission.

A child cell cannot inherit C_success as structural permission.

A child cell cannot inherit shape_integrity from the parent.

A child cell cannot ignore a hard inherited scar.

A child cell cannot treat a missing scar as proof of safety.

A child cell cannot use lineage to skip requalification.

A child cell cannot broaden inherited scope without new evidence.

A contaminated lineage packet must fail closed.

A lineage packet cannot erase a scar.

A lineage packet cannot retire a scar.

A lineage packet cannot create a scar unless a new betrayed-authority event occurs under valid evidence.

## Contaminated Packet Conditions

A lineage packet is contaminated if it contains active authority, full history, stale evidence, unverifiable provenance, mismatched epoch, out-of-scope constraints, missing parent identity, missing child identity, or route confidence presented as authority.

A contaminated packet must not be accepted.

A child cell may still proceed under a clean reconstruction path, but it must not inherit the contaminated packet.

The correct behavior is fail closed on inheritance, not necessarily fail closed on all reconstruction.

## Open Question: Contaminated Source Escalation

This draft does not define escalation behavior for repeated contaminated lineage packets from the same source.

A stale, unverifiable, epoch-mismatched, out-of-scope, or authority-contaminated packet is rejected for inheritance.

Whether repeated contaminated packets from the same source should elevate into a source-level warning, quarantine, blacklist, or recovery escalation is intentionally deferred.

The first validation plan must not invent source-escalation logic.

The first validation plan may record repeated contamination as an observed condition, but it should treat source escalation as out of scope unless a later specification defines it.

## Non-Claims

This document does not prove lineage inheritance.

It does not prove production recovery.

It does not prove fuzzy scar matching.

It does not prove prospective filtering.

It does not prove an extra-proof protocol.

It does not prove that a regenerated cell is safe.

It does not prove that all damaged cells can be replaced.

It does not prove that lineage packets are sufficient for all recovery cases.

It does not prove that full history is unnecessary in every possible system.

It defines the narrow inheritance boundary for this architecture.

## Validation Direction

The first validation plan should test lineage inheritance as a narrow mechanism.

The test should not attempt full production recovery.

The test should ask whether inherited packets transfer constraints without transferring authority.

A valid first test should include these cases:

```text
child receives hard scar constraint and is rejected as-is
child receives soft scar constraint and requires extra proof
child receives restoration scar constraint and requires extra proof
child receives no scar and enters requalification, not active bypass
child with contaminated packet does not inherit constraints
child with stale packet fails closed on inheritance
child with epoch mismatch fails closed on inheritance
child with unknown scope fails closed on inheritance
child with narrower proven scope inherits only overlapping constraints
child cannot inherit parent C_success as authority
child cannot inherit parent shape_integrity as authority
child cannot enter ACTIVE directly from lineage
```

The expected result is not automatic recovery.

The expected result is bounded inheritance of constraints without silent preservation of failed authority.

## Next Document

The next document should be:

```text
LINEAGE_INHERITANCE_VALIDATION_PLAN_v0_1.md
```

That plan should freeze the test cases, assertions, output files, and verdict boundary before any simulation script is written.
