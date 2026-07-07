# Lineage Inheritance V1 Primary Result Summary

Status: Frozen primary result summary.

## Purpose

This document records the primary validation result for Lineage Inheritance V1.

The test asks whether a replacement child cell can inherit compact constraints from a parent context without inheriting active authority, bypass permission, full history, parent route confidence, or parent shape integrity.

The governing rule is:

```text
Inherit constraints, not authority.
```

## Primary Verdict

```text
SUPPORTED
```

The primary lineage inheritance harness passed all declared assertions.

```text
Assertions passed: 32/32
Document integrity: OK
Script filename: lineage_inheritance_sim_v1_REVIEWED.py
```

## Frozen Inputs

```text
Specification:
docs/LINEAGE_INHERITANCE_SPEC_v1_FROZEN.md
SHA-256: 7aa05bf40a2a787f79e5eed9a7f7d3e1aca3baa83dd2be576ba1ef17458f8ebe

Validation plan:
docs/LINEAGE_INHERITANCE_VALIDATION_PLAN_v1_FROZEN.md
SHA-256: 1f02a1fc94b419799b2ee88e26b6d69f2dd1bdeb026fc558c655ad9a57ffa803

Script:
scripts/lineage_inheritance_sim_v1_REVIEWED.py
SHA-256: bd44dd160c1541485e8cc93b9fd3e0d5784940d0f43382d5ea5d2e9ae865798c
```

## Frozen Harness Parameters

```text
REQUALIFICATION_THRESHOLD = 5
PARTIAL_REQUALIFICATION_PROGRESS = 3
SCOPE_OVERLAP_MODEL = explicit boolean scope_overlap_proven field
```

## Validated Boundary

The V1 harness supports the narrow lineage-inheritance claim.

A child cell can inherit constraint information from a parent context without inheriting authority.

The supported boundary includes hard scar inheritance, soft scar inheritance, restoration scar inheritance, no-scar-match behavior, contaminated packet rejection, stale packet rejection, epoch mismatch rejection, unknown-scope rejection, narrower proven overlap, partial requalification failure, post-authority child failure, and isolation of parent state.

## Validated Behaviors

The harness validates that hard scar constraints are inherited as rejection constraints.

It validates that soft scar constraints require extra proof.

It validates that restoration scar constraints require extra proof.

It validates that no scar match does not prove safety and does not place the child directly into active authority.

It validates that a valid no-match child enters requalification.

It validates that a child cannot inherit active authority.

It validates that a child cannot inherit bypass permission.

It validates that a child cannot inherit parent C_success as permission.

It validates that a child cannot inherit parent shape_integrity as permission.

It validates that packets containing active authority are rejected for inheritance.

It validates that packets containing route confidence as authority are rejected for inheritance.

It validates that packets containing parent shape integrity as authority are rejected for inheritance.

It validates that packets containing full history are rejected for inheritance.

It validates that stale packets are rejected for inheritance.

It validates that epoch-mismatched packets are rejected for inheritance.

It validates that unknown-scope packets are rejected for inheritance.

It validates that narrower proven overlap inherits only the declared overlapping constraints.

It validates that a child cannot enter ACTIVE directly from lineage inheritance.

It validates that partial requalification progress is not authority.

It validates that failure during partial requalification creates no scar.

It validates that a child failure after completed requalification and active authority creates a scar.

It validates that the scar written after post-authority child failure carries the child cell fingerprint, not the parent cell fingerprint.

It validates that repeated contaminated packets are recorded without claiming source-level escalation.

It validates that lineage lookup does not mutate the scar registry.

It validates that lineage processing does not mutate parent C_success.

It validates that lineage processing does not mutate parent shape_integrity.

It validates that the event log contains the required replay fields.

It validates that the harness produces a deterministic final verdict from assertion results.

## Output Files

The primary run produced the following files in `data/`:

```text
lineage_inheritance_v0_1_assertions.csv
lineage_inheritance_v0_1_child_states.csv
lineage_inheritance_v0_1_constraints.csv
lineage_inheritance_v0_1_packets.csv
lineage_inheritance_v0_1_raw.csv
lineage_inheritance_v0_1_run_record.txt
lineage_inheritance_v0_1_scar_events.csv
lineage_inheritance_v0_1_scope_decisions.csv
lineage_inheritance_v0_1_summary.csv
lineage_inheritance_v0_1_verdict.csv
```

The data output package hash is:

```text
lineage_inheritance_v0_1_data_outputs.zip
SHA-256: 2697721be302b887800b5082969b7e85ec2e24cbe67f020a3f78ce3291934be8
```

## Non-Claims

This result does not prove production recovery.

It does not prove fuzzy scar matching.

It does not prove prospective filtering.

It does not prove a full extra-proof protocol.

It does not prove source-level escalation for repeated contaminated packets.

It does not prove that every child cell is safe.

It does not prove that all damaged cells can be replaced.

It does not prove that lineage packets are sufficient for all recovery cases.

It does not prove production reliability.

## Interpretation

Lineage Inheritance V1 supports a narrow recovery primitive.

A replacement cell can be given inherited constraint knowledge without being handed the parent's authority.

That distinction matters because cellular shedding cuts away failed local authority, but reconstruction still needs bounded continuity.

Lineage inheritance supplies that continuity as a constraint envelope, not as trust.

The result therefore strengthens the larger bounded-routing stack by adding a controlled path from shedding to reconstruction without silently preserving failed authority.
