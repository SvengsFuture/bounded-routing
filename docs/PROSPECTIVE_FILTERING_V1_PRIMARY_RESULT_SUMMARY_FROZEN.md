# Prospective Filtering V1 Primary Result Summary

Status: Frozen primary result summary.

## Purpose

This document records the primary validation result for Prospective Filtering V1.

The test asks whether a candidate replacement, reconstruction, route, child cell, or local structural configuration can be screened before promotion without granting active authority, bypass permission, inherited trust, parent route confidence, or parent shape integrity.

The governing rule is:

```text
Filter before promotion, not after failure.
```

## Primary Verdict

```text
SUPPORTED
```

The primary prospective filtering harness passed all declared assertions.

```text
Assertions passed: 37/37
Document integrity: OK
Script filename: prospective_filtering_sim_v1_REVIEWED.py
```

## Frozen Inputs

```text
Specification:
docs/PROSPECTIVE_FILTERING_SPEC_v1_FROZEN.md
SHA-256: 01c7dda142d63aebc1f739c35b0ea23e15ac91c578f9593cdedcd903a33fc3b0

Validation plan:
docs/PROSPECTIVE_FILTERING_VALIDATION_PLAN_v1_FROZEN.md
SHA-256: 58ffccde8d5f96e7330f1d3e62ad6745909ef94a70db18b2be750aa3c5342e5c

Script:
scripts/prospective_filtering_sim_v1_REVIEWED.py
SHA-256: 2f538acd8cc8bf2b9bdde4b8d13fca83d00fb06d8453efc584ab0ccb32053a0d
```

## Frozen Harness Parameters

```text
SCOPE_OVERLAP_MODEL = explicit boolean scope_overlap_proven field
FILTER_DECISION_PRECEDENCE = evidence, provenance, epoch, scope, contamination, hard scar, soft/restoration scar, lineage constraint, no-match pass
SCAR_MATCH_MODEL = exact fingerprint only
EXTRA_PROOF_PROTOCOL = not implemented; REQUIRE_EXTRA_PROOF is a routing state only
SOURCE_ESCALATION = not implemented; repeated contamination is recorded only
```

## Validated Boundary

The V1 harness supports the narrow prospective-filtering claim.

A candidate can be screened before promotion without receiving active authority or bypass permission from the filter itself.

The supported boundary includes hard scar matching, soft scar matching, restoration scar matching, no-scar-match behavior, contamination rejection, invalid evidence rejection, provenance rejection, epoch mismatch rejection, unknown-scope rejection, narrower proven overlap, no-lineage candidate handling, invalid-lineage dependency blocking, inherited lineage constraints, contamination precedence, isolation checks, repeated contamination recording without source escalation, and event-log coverage.

## Validated Behaviors

The harness validates that a hard scar match returns `REJECT_AS_IS` and places the candidate in `FILTER_REJECTED`.

It validates that a soft scar match returns `REQUIRE_EXTRA_PROOF` and places the candidate in `FILTER_EXTRA_PROOF_REQUIRED`.

It validates that a restoration scar match returns `REQUIRE_EXTRA_PROOF` and places the candidate in `FILTER_EXTRA_PROOF_REQUIRED`.

It validates that no scar match does not prove safety.

It validates that no scar match records `NO_SCAR_MATCH` in the filter event log.

It validates that no scar match does not place the candidate in `ACTIVE`.

It validates that a valid no-match candidate enters `FILTER_PASSED_TO_REQUALIFICATION`.

It validates that a candidate cannot receive active authority from prospective filtering.

It validates that a candidate cannot receive bypass permission from prospective filtering.

It validates that a packet containing active authority returns `QUARANTINE`.

It validates that a packet containing bypass permission returns `QUARANTINE`.

It validates that a packet containing route confidence as authority returns `QUARANTINE`.

It validates that a candidate cannot inherit `C_success` as authority.

It validates that a packet containing parent shape integrity as authority returns `QUARANTINE`.

It validates that a candidate cannot inherit parent `shape_integrity` as authority.

It validates that a packet containing full history as admission evidence returns `QUARANTINE`.

It validates that stale evidence returns `QUARANTINE`.

It validates that invalid provenance returns `QUARANTINE`.

It validates that epoch mismatch returns `QUARANTINE`.

It validates that unknown scope returns `QUARANTINE`.

It validates that narrower proven overlap applies only the declared overlapping constraints.

It validates that a candidate with no lineage packet receives no inherited constraints.

It validates that a candidate with no lineage packet may pass only to requalification, not `ACTIVE`.

It validates that a candidate depending on invalid lineage evidence returns `QUARANTINE`.

It validates that a valid hard inherited lineage constraint returns `REJECT_AS_IS`.

It validates that a valid soft inherited lineage constraint returns `REQUIRE_EXTRA_PROOF`.

It validates that a contaminated packet with a hard scar match returns `QUARANTINE` before any trusted scar result.

It validates that filter lookup does not mutate the scar registry.

It validates that filter lookup does not mutate the lineage packet.

It validates that filter lookup does not mutate `C_success`.

It validates that filter lookup does not mutate `shape_integrity`.

It validates that filter lookup does not mutate active authority or bypass permission into true.

It validates that repeated contaminated packets are recorded without claiming source-level escalation.

It validates that the filter event log contains the required replay fields.

It validates that the harness produces a deterministic final verdict from assertion results.

## Tie-Break Behavior

The implementation checks stale packet status before invalid provenance inside `packet_rejection_reason`.

In the frozen decision precedence, stale timestamp is treated as evidence invalidity. Because evidence validity precedes provenance validity, a packet that is both stale and invalid-provenance would return `stale_packet` first.

The V1 harness does not include a simultaneous stale-plus-invalid-provenance scenario, so no assertion depends on that tie-break.

This is recorded here as implementation behavior, not as an expanded claim.

## Output Files

The primary run produced the following files in `data/`:

```text
prospective_filtering_v0_1_assertions.csv
prospective_filtering_v0_1_candidates.csv
prospective_filtering_v0_1_constraints.csv
prospective_filtering_v0_1_decisions.csv
prospective_filtering_v0_1_isolation.csv
prospective_filtering_v0_1_packets.csv
prospective_filtering_v0_1_raw.csv
prospective_filtering_v0_1_run_record.txt
prospective_filtering_v0_1_scope_decisions.csv
prospective_filtering_v0_1_summary.csv
prospective_filtering_v0_1_verdict.csv
```

The data output package hash is:

```text
prospective_filtering_v0_1_data_outputs.zip
SHA-256: f3a86df7720200a383f5a1061b4b2c9ecbf44d1ad6a91de23dec1d4c2c616c41
```

## Non-Claims

This result does not prove production recovery.

It does not prove fuzzy scar matching.

It does not prove a full extra-proof protocol.

It does not prove source-level escalation for repeated contaminated packets.

It does not prove that every unsafe candidate can be detected before requalification.

It does not prove that every safe candidate can be admitted.

It does not prove production reliability.

It does not prove that all damaged cells can be replaced.

It does not prove that lineage packets are sufficient for all recovery cases.

It does not prove that a clean filter result is authority.

It does not prove that a candidate is safe merely because it passed to requalification.

## Interpretation

Prospective Filtering V1 supports a narrow pre-promotion screening primitive.

The filter can reject, quarantine, require extra proof, or pass a candidate to requalification without granting authority itself.

That distinction matters because lineage inheritance can give a replacement candidate compact constraints, but those constraints still need to be consumed before promotion.

The result therefore extends the recovery stack by adding a preventive screening boundary between inherited constraints and candidate requalification.

The filter does not make the candidate trusted.

It only prevents obvious invalid, contaminated, out-of-scope, or blocked candidates from moving forward as if they were clean.
