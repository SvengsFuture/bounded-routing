# Cellular Shedding Specification v0.1

Status: Frozen for validation planning.

## Purpose

This document defines the next architectural layer after the rejected-configuration scar registry.

The scar layer records that an authorized structural configuration failed and should not be promoted again as-is.

Cellular shedding defines what happens next.

A damaged cell must be cut away without collapsing the whole structure, without preserving stale authority, and without rebuilding the same rejected configuration unchanged.

This document is not a validation plan.

This document is not a simulation harness.

This document does not define lineage inheritance yet.

Lineage inheritance comes after shedding.

## Controlling Principle

Cellular shedding is local structural removal under bounded authority.

A failed cell is not repaired in place merely because it was useful before.

A failed cell is not allowed to continue carrying authority merely because surrounding structure remains healthy.

A failed cell is removed from active authority, isolated from route promotion, and replaced only through a reconstruction process that respects current shape integrity and rejected-configuration scars.

The governing rule is:

Do not preserve failed authority through continuity of form.

A structure that looks like the old cell is not trusted merely because it occupies the same position.

It must earn authority again under current evidence.

## Relationship to Existing Layers

Bounded routing decides whether a learned route may bypass full analysis.

The tetrahedral shape gate decides whether the current structural condition permits that authority.

The scar registry records configurations that had authority and then failed.

Cellular shedding removes the damaged local unit from active authority after failure.

Recovery reconstructs structure after damage.

Lineage inheritance later defines how regenerated cells receive compact rejected-configuration memory without inheriting full history.

These jobs must remain separate.

The router does not perform shedding.

The scar registry does not perform shedding.

The recovery layer does not erase scar evidence.

A regenerated cell does not inherit authority automatically from the removed cell.

## Definitions

A cell is a local structural unit inside the larger tetrahedral recovery architecture.

A cell may be a role-local region, an edge-local relation, a coordinator-bound local configuration, or another declared substructure. The final production scope is not defined here.

A damaged cell is a cell whose current configuration no longer satisfies the declared structural condition required for active authority.

A shed cell is a damaged cell that has been removed from active authority and isolated from route promotion.

A replacement cell is a reconstructed or regenerated cell proposed to take over the structural function of the shed cell.

A shed boundary is the declared local boundary between the removed damaged cell and adjacent structure that remains active.

A load-transfer condition is the evidence that adjacent healthy structure can carry required work while the damaged cell is removed.

A reconstruction proposal is a candidate replacement for the shed cell.

A scar conflict is a match between a reconstruction proposal and a rejected-configuration scar.

## Required Inputs

A cellular shedding decision requires current structural evidence.

The minimum required inputs are:

authorized source identity

observation timestamp

structural epoch

cell identifier

cell scope

cell role or relation

current shape-integrity condition

failure class or failed invariant metadata

adjacent-cell health evidence

applicable scar lookup result

recovery context

route-authority state affected by the cell

Missing, stale, unverifiable, epoch-mismatched, or out-of-scope evidence cannot authorize shedding as a clean recovery action.

When evidence is missing or invalid, the system must fail closed.

## Shedding Trigger

A cell may enter shedding review when a valid structural observation shows that the cell has failed a declared invariant, has become structurally inadmissible, or has betrayed authority after previously being admitted.

A shedding trigger does not automatically approve shedding.

The trigger only starts the review.

The system must determine whether the failure is local enough to isolate, whether adjacent structure can carry the load, whether affected route authority must be revoked, and whether a scar must be written.

## Shedding Decision States

A cell can occupy one of the following states.

ACTIVE means the cell remains authorized and may support route authority.

WARNED means the cell has shown structural stress but has not yet crossed the shedding boundary.

SHEDDING_REVIEW means the cell has triggered review and must not gain new authority until the review resolves.

SHED means the cell has been removed from active authority.

QUARANTINED means the cell remains present for inspection or replay but cannot support active authority.

RECONSTRUCTING means a replacement cell is being proposed or built.

REQUALIFYING means the replacement cell exists but must earn authority through fresh evidence.

RETIRED means the failed cell is no longer eligible for active use.

A shed cell cannot bypass.

A quarantined cell cannot bypass.

A reconstructing cell cannot bypass.

A requalifying replacement cannot bypass until it satisfies the declared requalification process.

## Shedding Boundary

Shedding must be local.

The system must identify what is being removed and what remains active.

The boundary must preserve enough information to answer these questions:

Which cell failed?

Which role, edge, or local relation did it support?

Which routes depended on it?

Which adjacent cells remain healthy?

Which authority states must be revoked?

Which scar records apply?

Which reconstruction proposals are prohibited as-is?

The boundary must not be guessed from route confidence alone.

It must be derived from structural evidence.

## Authority Revocation

When a cell is shed, all route authority depending on that cell must be revoked or suspended.

Historical route confidence cannot preserve authority through a shed boundary.

A route that depended on the shed cell must go through full analysis or declared requalification.

A route that does not depend on the shed cell may remain eligible only if its structural scope can be proven independent of the shed boundary.

If scope cannot be proven, the route fails closed.

## Scar Interaction

The scar registry determines whether the failed configuration or a proposed replacement configuration has already betrayed authority.

A scar may be written when the failed cell had authority and then failed under valid structural evidence.

A scar must not be written for cheap retries, non-admitted candidates, invalid evidence, stale evidence, or out-of-scope evidence.

A hard scar prevents the same configuration from being promoted again as-is.

A soft or restoration scar requires extra proof before promotion.

The scar does not remove the cell.

The scar does not reconstruct the cell.

The scar only constrains what may be trusted again.

## Reconstruction

A replacement cell must be treated as a new authority candidate.

It does not inherit active authority from the shed cell.

It may inherit constraints.

It may inherit applicable scar exclusions.

It may inherit compact lineage evidence in a later lineage layer.

It may not inherit full historical confidence as active authority.

A replacement cell must pass current structural evidence checks before it can support bypass authority.

A replacement cell must not match a hard rejected-configuration scar as-is.

A replacement cell that matches a soft or restoration scar must provide extra proof before promotion.

The extra-proof protocol is not defined in this document.

## Load Transfer

Shedding must not assume that surrounding structure can carry the load.

The system must prove or declare load-transfer conditions.

A valid load-transfer condition should identify which adjacent structure remains active, which responsibilities are temporarily rerouted, which route authorities are blocked, and which operating limits apply during the degraded state.

If load transfer cannot be established, the system must escalate from local shedding to broader recovery.

## Evidence Log

Every shedding event must leave an evidence log.

The log should record:

cell identifier

cell scope

structural epoch

trigger condition

failed invariant metadata

authority state before shedding

routes affected

scar write decision

scar match decision

shed boundary

adjacent-cell health evidence

load-transfer decision

reconstruction status

final cell state

This log is not general memory.

It is a replay record for audit, recovery, and validation.

## Safety Rules

A failed cell cannot preserve authority by remaining physically present.

A replacement cell cannot inherit active authority merely because it occupies the old position.

Route confidence cannot override a shed boundary.

Shape integrity cannot be backfilled from route outcomes.

A scar cannot be ignored when the candidate replacement matches a hard rejected configuration.

A missing scar cannot prove safety.

A missing structural observation cannot prove health.

A local shedding decision cannot authorize unrelated global recovery claims.

## Non-Claims

This document does not prove cellular shedding.

It does not prove lineage inheritance.

It does not define the final production cell schema.

It does not define the final load-transfer formula.

It does not define the extra-proof protocol.

It does not claim that shedding always preserves service.

It does not claim that every failure is locally shed-able.

It does not claim production reliability.

It does not claim that the selected state names are final.

## Validation Direction

The next validation plan should test cellular shedding as a narrow mechanism.

The first test should not attempt full lineage inheritance.

The first test should ask whether the system can detect a local failed cell, revoke only dependent route authority, preserve independent routes when scope is proven independent, write scars only after betrayed authority, reject reconstruction of the same hard-scarred configuration, and force requalification before a replacement cell supports bypass.

A valid first shedding test should include at least these cases:

local failure with dependent routes revoked

local failure with independent routes preserved

uncertain scope causing fail-closed behavior

invalid evidence causing no scar and no clean shedding authorization

hard scar blocking same-configuration reconstruction

soft scar requiring extra proof

replacement cell entering requalification rather than active bypass

load transfer success

load transfer failure escalating to broader recovery

The expected result is not zero failures.

The expected result is bounded local removal without silent preservation of failed authority.

## Next Document

The next document should be:

CELLULAR_SHEDDING_VALIDATION_PLAN_v0_1.md

That plan should freeze the test cases, assertions, output files, and verdict boundary before any simulation script is written.
