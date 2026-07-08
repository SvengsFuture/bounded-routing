# Prospective Filtering Validation Plan v0.1

Status: Frozen for implementation planning.

## Purpose

This document defines the first validation plan for prospective filtering.

The goal is narrow.

The test should determine whether a candidate replacement, reconstruction, route, child cell, or local structural configuration can be screened before promotion without granting active authority, bypass permission, or inherited trust.

The test should also determine whether invalid evidence, contaminated packets, unknown scope, epoch mismatch, and scar constraints produce the correct pre-promotion filter decisions.

This plan does not validate production recovery.

This plan does not validate fuzzy scar matching.

This plan does not validate a full extra-proof protocol.

This plan does not validate source-level escalation for repeated contaminated packets.

This plan does not validate that every unsafe candidate can be detected before requalification.

## Controlling Question

Can a prospective filter block or constrain candidate promotion before authority is granted?

The mechanism is supported only if the harness shows all of the following.

Hard scar matches reject the candidate as-is.

Soft scar matches require extra proof.

Restoration scar matches require extra proof.

No scar match does not prove safety.

No scar match may pass only to requalification.

The filter cannot place a candidate directly into active authority.

The filter cannot grant bypass permission.

The filter cannot mutate the scar registry during lookup.

The filter cannot mutate lineage packets during lookup.

The filter cannot mutate C_success.

The filter cannot mutate shape_integrity.

The filter cannot mutate parent or child authority into active authority.

Invalid evidence fails closed.

Invalid provenance fails closed.

Epoch mismatch fails closed.

Unknown scope fails closed.

Contaminated authority fails closed.

Route confidence presented as authority fails closed.

Parent shape integrity presented as authority fails closed.

A valid candidate with no lineage packet may be screened directly without inherited constraints.

A candidate that depends on invalid lineage evidence cannot silently pass as clean.

A narrower proven overlap applies only the declared overlapping constraints.

A contaminated packet with a hard scar match must fail closed on contamination before returning a trusted hard-scar result.

## Frozen Harness Parameters

The validation harness uses the following declared parameters.

```text
SCOPE_OVERLAP_MODEL = explicit boolean scope_overlap_proven field
FILTER_DECISION_PRECEDENCE = evidence, provenance, epoch, scope, contamination, hard scar, soft/restoration scar, lineage constraint, no-match pass
SCAR_MATCH_MODEL = exact fingerprint only
EXTRA_PROOF_PROTOCOL = not implemented; REQUIRE_EXTRA_PROOF is a routing state only
SOURCE_ESCALATION = not implemented; repeated contamination is recorded only
```

Scope overlap is not inferred by a semantic or string-matching algorithm.

The harness uses an explicit `scope_overlap_proven` field.

If that field is true, the filter may apply only the declared overlapping constraints.

If that field is false or unknown, overlap is not proven.

## Model Boundary

The validation harness should model candidates, filter packets, scar constraints, lineage constraints, scope decisions, filter decisions, and authority states.

The harness does not need full tetrahedral physics.

The harness does not need full route simulation beyond enough route-authority state to test that authority is not granted.

The harness does not need fuzzy matching.

The harness does not need a full extra-proof protocol.

The harness does not need source-level escalation.

The harness should be deterministic.

## Minimal Entities

The harness should define candidates.

Each candidate should include:

```text
candidate_id
candidate_type
candidate_fingerprint
candidate_scope
candidate_structural_epoch
candidate_source
candidate_timestamp_status
candidate_provenance_status
candidate_verification_status
candidate_state
candidate_active_authority
candidate_bypass_permission
candidate_c_success
candidate_shape_integrity
```

The harness should define filter packets.

Each filter packet should include:

```text
filter_packet_id
candidate_id
candidate_type
candidate_fingerprint
candidate_scope
candidate_structural_epoch
candidate_source
candidate_timestamp_status
candidate_provenance_status
candidate_verification_status
scope_status
scope_overlap_proven
contains_active_authority
contains_bypass_permission
contains_full_history_as_admission
contains_route_confidence_as_authority
contains_parent_shape_integrity_as_authority
depends_on_lineage
lineage_packet_status
scar_fingerprints
lineage_constraints
overlapping_constraints
required_extra_proof
```

The harness should define scars.

Each scar should include:

```text
fingerprint
scar_class
retirement_state
```

The harness should define lineage constraints.

Each lineage constraint should include:

```text
constraint_id
constraint_class
constraint_fingerprint
scope
source_packet_id
```

## Filter Decisions And Candidate States

The validation harness should use these filter decisions.

```text
REJECT_AS_IS
REQUIRE_EXTRA_PROOF
PASS_TO_REQUALIFICATION
QUARANTINE
FALLBACK_FULL_ANALYSIS
```

The validation harness should use these candidate states.

```text
FILTER_REJECTED
FILTER_EXTRA_PROOF_REQUIRED
FILTER_PASSED_TO_REQUALIFICATION
FILTER_QUARANTINED
FALLBACK_FULL_ANALYSIS
```

ACTIVE is not a filter output state. It is reached only through the separate requalification process, which is out of scope for this plan.

A candidate may enter ACTIVE only through a separate requalification process.

A candidate must not enter ACTIVE directly from prospective filtering.

A candidate must not support bypass directly from prospective filtering.

`PASS_TO_REQUALIFICATION` maps to `FILTER_PASSED_TO_REQUALIFICATION`.

`REQUIRE_EXTRA_PROOF` maps to `FILTER_EXTRA_PROOF_REQUIRED`.

`REJECT_AS_IS` maps to `FILTER_REJECTED`.

`QUARANTINE` maps to `FILTER_QUARANTINED`.

`FALLBACK_FULL_ANALYSIS` maps to `FALLBACK_FULL_ANALYSIS`.

## Filter Decision Precedence

When multiple conditions are true at the same time, the filter evaluates them in this order.

```text
1. evidence validity
2. provenance validity
3. epoch validity
4. scope validity
5. contamination checks
6. hard scar match
7. soft or restoration scar match
8. lineage constraint match
9. no-match pass to requalification
```

Invalid evidence, invalid provenance, epoch mismatch, unknown scope, or contamination returns `QUARANTINE` or `FALLBACK_FULL_ANALYSIS` before scar matching is treated as an authoritative filter result.

This prevents a contaminated packet from producing a trusted `REJECT_AS_IS` result merely because it also contains a hard scar match.

Hard scars block only after the evidence carrying the hard scar is valid, scoped, current, and verified.

## Packet Validity Rules

A filter packet is valid only if all of the following are true.

The packet has a candidate identifier.

The packet has a candidate fingerprint.

The candidate evidence is fresh.

The candidate provenance is valid.

The candidate structural epoch matches the current epoch.

The candidate verification status is verified.

The candidate scope is known.

The packet is not contaminated with active authority.

The packet is not contaminated with bypass permission.

The packet does not contain full history as admission evidence.

The packet does not contain route confidence presented as authority.

The packet does not contain parent shape integrity presented as authority.

If any of these checks fail, the candidate must not pass through the filter as clean.

The candidate enters `FILTER_QUARANTINED` or `FALLBACK_FULL_ANALYSIS`.

## Scar Constraint Rules

A hard scar match returns `REJECT_AS_IS`.

A soft scar match returns `REQUIRE_EXTRA_PROOF`.

A restoration scar match returns `REQUIRE_EXTRA_PROOF`.

A no-match result returns `NO_SCAR_MATCH`.

`NO_SCAR_MATCH` does not prove safety.

`NO_SCAR_MATCH` does not place the candidate into ACTIVE.

If reconstruction evidence, provenance, scope, epoch, and structural checks are valid, a no-match candidate may enter `FILTER_PASSED_TO_REQUALIFICATION`.

A retired scar is out of scope for this validation plan unless explicitly modeled as inert historical metadata.

## Lineage Constraint Rules

A valid hard inherited lineage constraint returns `REJECT_AS_IS`.

A valid soft inherited lineage constraint returns `REQUIRE_EXTRA_PROOF`.

A valid restoration inherited lineage constraint returns `REQUIRE_EXTRA_PROOF`.

A candidate with no lineage packet is not lineage-dependent.

A candidate with no lineage packet may be screened directly against scar registry and current structural evidence without inheriting constraints.

A candidate that depends on invalid lineage evidence must not silently pass as clean.

If `depends_on_lineage = true` and `lineage_packet_status` is invalid, stale, epoch-mismatched, unknown-scope, contaminated, or unverifiable, the filter returns `FILTER_QUARANTINED` or `FALLBACK_FULL_ANALYSIS`.

## Authority Rules

Prospective filtering may block or constrain promotion.

Prospective filtering must not grant active authority.

Prospective filtering must not grant bypass permission.

Prospective filtering must not transfer parent C_success as candidate authority.

Prospective filtering must not transfer parent shape_integrity as candidate authority.

A candidate cannot support bypass while `FILTER_REJECTED`, `FILTER_EXTRA_PROOF_REQUIRED`, `FILTER_PASSED_TO_REQUALIFICATION`, `FILTER_QUARANTINED`, or `FALLBACK_FULL_ANALYSIS`.

A candidate can support bypass only after a separate declared requalification process admits it.

That requalification process is out of scope for this validation plan.

## Scope Rules

Scope overlap is represented by the explicit `scope_overlap_proven` field in this validation harness.

The harness does not infer overlap from file paths, names, text similarity, semantic matching, or structural analogy.

A packet with matching verified scope may constrain the candidate.

A packet with proven narrower overlap may constrain the candidate only inside the declared overlapping constraint set.

A packet with unknown scope is rejected for filtering.

A packet with broader evidence than candidate scope cannot authorize unsupported scope.

A packet with no provable overlap cannot be used as trusted evidence for that candidate.

## Isolation Rules

The filter must not mutate the scar registry during lookup.

Verification method: compute a stable hash or serialized snapshot of the scar registry before filtering and after filtering. The values must match.

The filter must not mutate lineage packets during lookup.

Verification method: compute a stable hash or serialized snapshot of the lineage packet before filtering and after filtering. The values must match.

The filter must not mutate C_success.

Verification method: record candidate and parent C_success before filtering and after filtering. The values must match unless a separate out-of-scope requalification process changes them. The filter itself must not change them.

The filter must not mutate shape_integrity.

Verification method: record candidate and parent shape_integrity before filtering and after filtering. The values must match unless a separate authorized structural observer changes them. The filter itself must not change them.

The filter must not mutate active authority or bypass permission into true.

Verification method: record active authority and bypass permission before filtering and after filtering. They must remain false for all candidates handled only by the filter.

## Test Scenarios

Scenario 1: valid hard scar match.

A valid filter packet contains a hard scar fingerprint matching the candidate.

Expected result: filter decision `REJECT_AS_IS`, candidate state `FILTER_REJECTED`.

Scenario 2: valid soft scar match.

A valid filter packet contains a soft scar fingerprint matching the candidate.

Expected result: filter decision `REQUIRE_EXTRA_PROOF`, candidate state `FILTER_EXTRA_PROOF_REQUIRED`.

Scenario 3: valid restoration scar match.

A valid filter packet contains a restoration scar fingerprint matching the candidate.

Expected result: filter decision `REQUIRE_EXTRA_PROOF`, candidate state `FILTER_EXTRA_PROOF_REQUIRED`.

Scenario 4: no scar match.

A valid filter packet contains no scar match and all candidate evidence is valid.

Expected result: filter decision `PASS_TO_REQUALIFICATION`, candidate state `FILTER_PASSED_TO_REQUALIFICATION`, not ACTIVE.

Scenario 5: active authority contamination.

A filter packet contains active authority.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`, no authority granted.

Scenario 6: bypass permission contamination.

A filter packet contains bypass permission.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`, no bypass granted.

Scenario 7: route confidence as authority contamination.

A filter packet contains route confidence presented as authority.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`, C_success not inherited as authority.

Scenario 8: parent shape integrity as authority contamination.

A filter packet contains parent shape integrity presented as authority.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`, shape_integrity not inherited as authority.

Scenario 9: full history as admission evidence.

A filter packet contains full history as admission evidence.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`.

Scenario 10: stale evidence.

A filter packet has stale timestamp status.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`.

Scenario 11: invalid provenance.

A filter packet has invalid provenance.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`.

Scenario 12: epoch mismatch.

A filter packet belongs to a different structural epoch.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`.

Scenario 13: unknown scope.

A filter packet has unknown scope relation to the candidate.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`.

Scenario 14: narrower proven overlap.

A filter packet has broader evidence and a narrower candidate overlap.

The packet sets `scope_overlap_proven = true` and declares the exact overlapping constraint set.

Expected result: only the declared overlapping constraints are applied.

Scenario 15: candidate with no lineage packet.

A valid candidate arrives with no lineage packet and no scar match.

Expected result: the candidate is screened directly against scar registry and current structural evidence, receives no inherited constraints, and may pass only to requalification.

Scenario 16: candidate depends on invalid lineage evidence.

A candidate sets `depends_on_lineage = true` and the lineage packet status is invalid.

Expected result: filter decision `QUARANTINE`, candidate state `FILTER_QUARANTINED`.

Scenario 17: valid hard lineage constraint.

A valid lineage constraint carries a hard inherited block matching the candidate.

Expected result: filter decision `REJECT_AS_IS`, candidate state `FILTER_REJECTED`.

Scenario 18: valid soft lineage constraint.

A valid lineage constraint carries a soft inherited constraint matching the candidate.

Expected result: filter decision `REQUIRE_EXTRA_PROOF`, candidate state `FILTER_EXTRA_PROOF_REQUIRED`.

Scenario 19: contaminated packet with hard scar match.

A filter packet contains active authority and also contains a hard scar match.

Expected result: filter decision `QUARANTINE`, not trusted `REJECT_AS_IS`, because contamination has precedence over scar matching.

Scenario 20: isolation checks.

A valid filter lookup is run against scar registry, lineage packet, C_success, shape_integrity, active authority, and bypass permission snapshots.

Expected result: all before-and-after snapshots match, and no authority or bypass field becomes true.

Scenario 21: repeated contaminated source recorded but not escalated.

The same source provides repeated contaminated filter packets.

Expected result: contamination events are recorded, packets are rejected, and no source-level quarantine, blacklist, or escalation is claimed.

Scenario 22: event log coverage.

A representative filter run records all required replay fields.

Expected result: the event log contains candidate id, fingerprint, scope, epoch, provenance, scar result, lineage result, scope decision, filter decision, extra-proof status, requalification allowance, authority grant status, and bypass grant status.

## Assertions

A1: Hard scar match returns REJECT_AS_IS.

A2: Hard scar match places candidate in FILTER_REJECTED.

A3: Soft scar match returns REQUIRE_EXTRA_PROOF.

A4: Soft scar match places candidate in FILTER_EXTRA_PROOF_REQUIRED.

A5: Restoration scar match returns REQUIRE_EXTRA_PROOF.

A6: Restoration scar match places candidate in FILTER_EXTRA_PROOF_REQUIRED.

A7: No scar match does not prove safety. Verified by confirming the filter event log records NO_SCAR_MATCH and the candidate does not enter ACTIVE.

A8: No scar match does not place candidate in ACTIVE.

A9: Valid no-match candidate enters FILTER_PASSED_TO_REQUALIFICATION.

A10: Candidate cannot receive active authority from prospective filtering.

A11: Candidate cannot receive bypass permission from prospective filtering.

A12: Packet containing active authority returns QUARANTINE.

A13: Packet containing bypass permission returns QUARANTINE.

A14: Packet containing route confidence as authority returns QUARANTINE.

A15: Candidate cannot inherit C_success as authority.

A16: Packet containing parent shape integrity as authority returns QUARANTINE.

A17: Candidate cannot inherit parent shape_integrity as authority.

A18: Packet containing full history as admission evidence returns QUARANTINE.

A19: Stale packet returns QUARANTINE.

A20: Invalid provenance returns QUARANTINE.

A21: Epoch mismatch returns QUARANTINE.

A22: Unknown scope returns QUARANTINE.

A23: Narrower proven overlap applies only declared overlapping constraints.

A24: Candidate with no lineage packet receives no inherited constraints.

A25: Candidate with no lineage packet may pass only to requalification, not ACTIVE.

A26: Candidate depending on invalid lineage evidence returns QUARANTINE.

A27: Valid hard inherited lineage constraint returns REJECT_AS_IS.

A28: Valid soft inherited lineage constraint returns REQUIRE_EXTRA_PROOF.

A29: Contaminated packet with hard scar match returns QUARANTINE before trusted scar result.

A30: Filter lookup does not mutate scar registry. Verification method: stable hash or serialized snapshot before filtering and after filtering must match.

A31: Filter lookup does not mutate lineage packet. Verification method: stable hash or serialized snapshot before filtering and after filtering must match.

A32: Filter lookup does not mutate C_success. Verification method: before-and-after C_success values must match.

A33: Filter lookup does not mutate shape_integrity. Verification method: before-and-after shape_integrity values must match.

A34: Filter lookup does not mutate active authority or bypass permission into true. Verification method: before-and-after authority and bypass fields must remain false.

A35: Repeated contaminated packets are recorded without source-level escalation claim.

A36: The filter event log contains candidate id, fingerprint, scope, epoch, provenance, scar result, lineage result, scope decision, filter decision, extra-proof status, requalification allowance, authority grant status, and bypass grant status.

A37: The harness produces a deterministic final verdict from assertion results.

## Output Files

The validation run should produce:

```text
prospective_filtering_v0_1_raw.csv
prospective_filtering_v0_1_summary.csv
prospective_filtering_v0_1_packets.csv
prospective_filtering_v0_1_candidates.csv
prospective_filtering_v0_1_decisions.csv
prospective_filtering_v0_1_constraints.csv
prospective_filtering_v0_1_scope_decisions.csv
prospective_filtering_v0_1_isolation.csv
prospective_filtering_v0_1_assertions.csv
prospective_filtering_v0_1_verdict.csv
prospective_filtering_v0_1_run_record.txt
```

Plots should come only after data output is stable.

Suggested plots:

```text
prospective_filtering_assertion_status.png
prospective_filtering_decision_counts.png
prospective_filtering_candidate_states.png
prospective_filtering_contamination_precedence.png
prospective_filtering_isolation_checks.png
```

## Verdict Boundary

The result is SUPPORTED only if all declared assertions pass.

The result is NOT SUPPORTED if any of these failures occur:

```text
candidate enters ACTIVE directly from filter
candidate receives active authority from filter
candidate receives bypass permission from filter
hard scar match does not block valid candidate as-is
soft scar match does not require extra proof
restoration scar match does not require extra proof
contaminated active-authority packet passes through filter
route confidence as authority passes through filter
parent shape integrity as authority passes through filter
unknown scope passes through filter
epoch mismatch passes through filter
candidate depending on invalid lineage evidence passes as clean
contaminated packet with hard scar match returns trusted REJECT_AS_IS instead of QUARANTINE
filter lookup mutates scar registry
filter lookup mutates lineage packet
filter lookup mutates C_success
filter lookup mutates shape_integrity
```

The result is INCONCLUSIVE if the harness does not exercise hard scar, soft scar, restoration scar, no-match, active-authority contamination, bypass-permission contamination, route-confidence contamination, shape-integrity contamination, full-history contamination, stale evidence, invalid provenance, epoch mismatch, unknown scope, narrower overlap, no-lineage candidate, invalid-lineage dependency, hard lineage constraint, soft lineage constraint, contamination precedence, scar registry non-mutation, lineage packet non-mutation, C_success non-mutation, shape_integrity non-mutation, authority and bypass permission non-mutation, repeated contamination recording, and event log coverage.

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

It does not prove a full extra-proof protocol.

It does not prove source-level escalation for repeated contaminated packets.

It does not prove that every unsafe candidate can be detected before requalification.

It does not prove that every safe candidate can be admitted.

It does not prove production reliability.

It does not prove that all damaged cells can be replaced.

It does not prove that lineage packets are sufficient for all recovery cases.

## Freeze Criteria

Before implementation, this plan should be reviewed for three questions.

First, does the plan test filtering before promotion without accidentally granting authority?

Second, does the plan preserve the separation among scar matching, lineage inheritance, shape integrity, C_success, shedding, filtering, and requalification?

Third, does the verdict boundary punish failures that would silently admit unsafe or insufficiently evidenced candidates?

Once those questions are answered, this plan can be frozen as:

```text
PROSPECTIVE_FILTERING_VALIDATION_PLAN_v1_FROZEN.md
```
