# Prospective Filtering Specification v0.1

Status: Frozen for validation planning.

## Purpose

This document defines the next architectural layer after lineage inheritance.

The scar layer records rejected structural configurations after betrayed authority.

Cellular shedding removes a damaged local cell from active authority.

Lineage inheritance passes compact constraints into a replacement child path without passing authority.

Prospective filtering uses those constraints before promotion.

The purpose is narrow.

A candidate replacement, reconstruction, route, or child cell should be screened before it can enter requalification or active authority.

The filter may reject a candidate as-is.

The filter may require extra proof.

The filter may allow the candidate to proceed into requalification.

The filter may quarantine the candidate if evidence is invalid or scope cannot be proven.

The filter must not grant active authority.

The filter must not grant bypass permission.

The filter must not write scars by itself.

The filter must not mutate C_success.

The filter must not mutate shape_integrity.

The filter must not mutate the scar registry during lookup.

This document is not a validation plan.

This document is not a simulation harness.

This document does not define fuzzy scar matching.

This document does not define a full extra-proof protocol.

This document does not define source-level escalation for repeated contaminated packets.

## Controlling Principle

Prospective filtering blocks unsafe promotion before authority is granted.

The governing rule is:

```text
Filter before promotion, not after failure.
```

The filter is preventive.

It does not repair the candidate.

It does not explain the failure.

It does not decide that the candidate is safe.

It only decides whether the candidate may proceed, must provide extra proof, must be rejected as-is, or must be quarantined because the evidence boundary is invalid.

## Relationship To Existing Layers

Bounded routing decides whether a learned route may bypass full analysis.

The shape-integrity gate decides whether current structural condition permits bypass authority.

The scar registry records configurations that had authority and later failed.

Cellular shedding removes the damaged local cell from active authority.

Lineage inheritance transfers compact constraints into the replacement path without transferring authority.

Prospective filtering consumes current candidate evidence, applicable scars, lineage constraints, scope, provenance, and structural epoch before the candidate is allowed to proceed.

These jobs must remain separate.

The router does not create prospective filters.

The scar registry does not grant authority.

The shedding layer does not filter future candidates by itself.

The lineage layer transfers constraints, but it does not decide final candidate admission.

The prospective filter evaluates candidate admissibility before requalification or promotion.

## Definitions

A candidate is a proposed route, reconstruction, child cell, replacement cell, or local structural configuration that seeks to enter requalification or active authority.

A prospective filter is a pre-promotion screening operation applied to a candidate.

A filter packet is the compact evidence bundle used by the filter.

A candidate fingerprint is the structural identity of the proposed candidate.

A constraint source is a scar registry, lineage packet, shed boundary, structural observer, or frozen recovery rule used by the filter.

A filter decision is the output of the prospective filter.

A promotion path is the path from candidate proposal to requalification and then to active authority.

A filter hit is a match between the candidate and an applicable blocking or extra-proof constraint.

A filter miss is the absence of an applicable constraint match. A filter miss does not prove safety.

## Required Inputs

A prospective filtering decision requires valid evidence.

The minimum required inputs are:

```text
candidate_id
candidate_type
candidate_fingerprint
candidate_scope
candidate_structural_epoch
candidate_source
candidate_timestamp
candidate_provenance
candidate_verification_status
applicable_scar_fingerprints
applicable_lineage_constraints
shed_boundary
scope_relation
scope_overlap_proven
current_shape_integrity_status
current_route_authority_status
```

Missing, stale, unverifiable, epoch-mismatched, or out-of-scope evidence cannot authorize the candidate.

If the filter lacks enough evidence to make a valid screening decision, the candidate must fail closed into quarantine or full fallback.

## Filter Decisions

The prospective filter may return one of these decisions:

```text
REJECT_AS_IS
REQUIRE_EXTRA_PROOF
PASS_TO_REQUALIFICATION
QUARANTINE
FALLBACK_FULL_ANALYSIS
```

`REJECT_AS_IS` means the candidate matches a hard blocking constraint and cannot proceed unchanged.

`REQUIRE_EXTRA_PROOF` means the candidate matches a soft, restoration, inherited, or uncertain constraint that requires additional proof before requalification can continue.

`PASS_TO_REQUALIFICATION` means the candidate is not blocked by the filter and may proceed to the declared requalification process.

`QUARANTINE` means the candidate or filter packet has invalid evidence, unknown scope, unverifiable provenance, or contamination.

`FALLBACK_FULL_ANALYSIS` means the filter cannot safely support the candidate path and the system should use the safe non-bypass path.

The filter decision and candidate state use the same fallback term: `FALLBACK_FULL_ANALYSIS`.

No filter decision grants active authority.

No filter decision grants bypass permission.

`PASS_TO_REQUALIFICATION` is not `ACTIVE`.

## Filter Decision Precedence

When multiple conditions are true at the same time, the filter evaluates them in this order:

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

## What The Filter May Consume

The filter may consume compact constraints.

Allowed inputs include:

```text
hard scar fingerprints
soft scar fingerprints
restoration scar fingerprints
lineage constraints
blocked reconstruction candidates
required extra-proof flags
shed boundaries
scope limits
epoch identifiers
candidate fingerprints
candidate provenance
candidate verification status
current structural observer status
```

The filter may use these inputs to restrict candidate promotion.

It may not use them to grant authority.

## What The Filter Must Not Consume As Authority

The filter must not treat parent authority as candidate authority.

The filter must not treat parent route confidence as candidate authority.

The filter must not treat parent shape integrity as candidate authority.

The filter must not treat old bypass permission as candidate bypass permission.

The filter must not treat missing scar match as proof of safety.

The filter must not treat lineage inheritance as automatic admission.

The filter must not treat a clean filter result as active authority.

The filter must not treat full history as a substitute for current evidence.

## Scar Interaction

A hard scar match returns `REJECT_AS_IS`.

A soft scar match returns `REQUIRE_EXTRA_PROOF`.

A restoration scar match returns `REQUIRE_EXTRA_PROOF`.

A no-scar-match result does not prove safety.

When no scar match is found, scar status alone does not block the candidate. If provenance, scope, epoch, structural evidence, and candidate evidence are valid, the candidate may proceed to requalification.

The filter must not write scars during lookup.

The filter must not elevate scars during lookup.

The filter must not retire scars during lookup.

A new scar may be written only later, after a candidate has held authority and then failed under valid evidence.

## Lineage Interaction

Lineage constraints may be used as filter inputs.

A hard inherited constraint may block the candidate as-is.

A soft inherited constraint may require extra proof.

A restoration inherited constraint may require extra proof.

A lineage packet with invalid provenance, stale timestamp, epoch mismatch, unknown scope, contaminated authority, full history, route confidence as authority, or parent shape integrity as authority cannot support filtering.

Invalid lineage evidence should not be silently ignored if the candidate depends on it.

A candidate that arrives with no lineage packet is not lineage-dependent and may be screened against the scar registry and current structural evidence directly without inheriting any constraints.

If the candidate depends on invalid lineage evidence, the filter returns `QUARANTINE` or `FALLBACK_FULL_ANALYSIS`.

## Scope

Prospective filtering must be scoped.

A candidate can be screened only against constraints that apply to its declared scope.

If scope is matching and verified, the filter may apply the constraint.

If scope overlap is explicitly proven, the filter may apply only the overlapping constraint set.

If scope is unknown, the filter fails closed.

If scope is broader than the evidence supports, the filter fails closed for the unsupported portion.

If no overlap can be proven, the constraint cannot be used as trusted evidence for that candidate.

A missing applicable constraint does not prove safety.

## Provenance

A filter packet must carry provenance.

The system must know where the candidate came from, which observer supplied structural state, which lineage packet supplied inherited constraints, which scar registry supplied scar status, what structural epoch applies, and what scope is being screened.

A filter packet without provenance cannot support candidate promotion.

It must return `QUARANTINE` or `FALLBACK_FULL_ANALYSIS`.

## Candidate States

A candidate screened by the prospective filter may enter one of these states:

```text
FILTER_REJECTED
FILTER_EXTRA_PROOF_REQUIRED
FILTER_PASSED_TO_REQUALIFICATION
FILTER_QUARANTINED
FALLBACK_FULL_ANALYSIS
```

A candidate must not enter `ACTIVE` directly from the filter.

A candidate must not support bypass directly from the filter.

A candidate may become active only after the separate declared requalification process admits it.

## Evidence Log

Every prospective filtering event must leave an evidence log.

The log should record:

```text
filter_event_id
candidate_id
candidate_type
candidate_fingerprint
candidate_scope
candidate_epoch
candidate_provenance
candidate_verification_status
scar_result
lineage_result
scope_decision
provenance_decision
filter_decision
extra_proof_required
requalification_allowed
active_authority_granted
bypass_permission_granted
```

This log is not full memory.

It is a replay record for audit, recovery, and validation.

## Isolation Rules

Prospective filtering must not mutate the scar registry during lookup.

Prospective filtering must not mutate lineage packets.

Prospective filtering must not mutate C_success.

Prospective filtering must not mutate shape_integrity.

Prospective filtering must not mutate parent authority state.

Prospective filtering must not mutate child authority state into active authority.

Prospective filtering must not mutate bypass permission into true.

Non-mutation must be verified by before-and-after snapshots or stable hashes in validation.

## Contaminated Filter Packet Conditions

A filter packet is contaminated if it contains active authority, bypass permission, full history as admission evidence, route confidence as authority, parent shape integrity as authority, stale evidence, unverifiable provenance, mismatched epoch, unknown scope, or out-of-scope constraints presented as applicable constraints.

A contaminated filter packet must not be accepted.

If the candidate depends on the contaminated packet, the candidate must not pass through the filter.

The correct behavior is fail closed on candidate promotion, not silent acceptance.

## Safety Rules

A candidate cannot receive active authority from prospective filtering.

A candidate cannot receive bypass permission from prospective filtering.

A candidate cannot enter ACTIVE directly from prospective filtering.

A hard scar match blocks the candidate as-is.

A soft scar match requires extra proof.

A restoration scar match requires extra proof.

A missing scar match does not prove safety.

A clean filter result allows only requalification.

A contaminated packet fails closed.

Unknown scope fails closed.

Epoch mismatch fails closed.

Invalid provenance fails closed.

The filter cannot erase a scar.

The filter cannot retire a scar.

The filter cannot create a scar unless a later authority failure occurs under valid evidence.

## Open Question: Extra-Proof Protocol

This draft does not define the full extra-proof protocol.

`REQUIRE_EXTRA_PROOF` is a routing state, not a completed proof.

The first validation plan may test that extra proof is required, but it must not claim to validate the proof protocol itself.

## Open Question: Fuzzy Matching

This draft does not define fuzzy scar matching or approximate structural similarity.

The first validation plan should use exact fingerprints only.

If fuzzy matching is added later, it should be defined in a separate specification.

## Open Question: Source-Level Escalation

This draft does not define source-level escalation for repeated contaminated filter packets.

The first validation plan may record repeated contamination events, but it must not claim source quarantine, blacklist, or escalation unless a later specification defines it.

## Non-Claims

This document does not prove prospective filtering.

It does not prove production recovery.

It does not prove fuzzy scar matching.

It does not prove a full extra-proof protocol.

It does not prove source-level escalation.

It does not prove that every unsafe candidate can be detected before requalification.

It does not prove that every safe candidate can be admitted.

It does not prove production reliability.

It does not prove that all damaged cells can be replaced.

It does not prove that lineage packets are sufficient for all recovery cases.

It defines the narrow pre-promotion filtering boundary for this architecture.

## Validation Direction

The first validation plan should test prospective filtering as a narrow mechanism.

The test should not attempt full production recovery.

The test should ask whether unsafe or insufficiently evidenced candidates are blocked before promotion without granting active authority.

A valid first test should include these cases:

```text
hard scar match returns REJECT_AS_IS
soft scar match returns REQUIRE_EXTRA_PROOF
restoration scar match returns REQUIRE_EXTRA_PROOF
no scar match may pass only to requalification
candidate cannot enter ACTIVE directly from filter
candidate cannot inherit bypass permission from filter
candidate with contaminated active authority packet is quarantined
candidate with route confidence as authority is quarantined
candidate with parent shape integrity as authority is quarantined
candidate with stale evidence is quarantined
candidate with epoch mismatch is quarantined
candidate with unknown scope is quarantined
candidate with proven narrower overlap applies only overlapping constraints
candidate with no lineage packet may be screened directly without inherited constraints
filter lookup does not mutate scar registry
filter lookup does not mutate lineage packet
filter lookup does not mutate C_success
filter lookup does not mutate shape_integrity
filter result log contains required replay fields
```

The expected result is not automatic safety.

The expected result is bounded pre-promotion screening without silent authority preservation.

## Next Document

The next document should be:

```text
PROSPECTIVE_FILTERING_VALIDATION_PLAN_v0_1.md
```

That plan should freeze the test cases, assertions, output files, and verdict boundary before any simulation script is written.
