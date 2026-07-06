# Cellular Shedding Validation Plan v0.1

Status: Frozen for implementation planning.

## Purpose

This document defines the first validation plan for cellular shedding.

The goal is narrow.

The test should determine whether the system can remove a damaged local cell from active authority without preserving failed authority, without unnecessarily collapsing unrelated healthy routes, and without reconstructing the same rejected configuration as-is.

This plan does not validate lineage inheritance.

This plan does not validate production recovery.

This plan does not validate fuzzy scar matching.

This plan does not validate an extra-proof protocol.

This plan does not prove that all failures are locally shed-able.

## Controlling Question

Can a local damaged cell be shed while the system preserves the correct authority boundaries?

The mechanism is supported only if the harness shows all of the following.

Dependent route authority is revoked when the route depends on the shed cell.

Independent route authority is preserved when independence is proven.

Uncertain scope fails closed.

Invalid evidence does not authorize clean shedding.

Betrayed authority writes a scar.

Cheap or non-admitted failure does not write a scar.

A hard scar blocks reconstruction of the same configuration as-is.

A soft or restoration scar requires extra proof.

A replacement cell enters requalification before supporting bypass.

Load-transfer success preserves bounded degraded operation.

Load-transfer failure escalates to broader recovery.

## Model Boundary

The validation harness should model a small structural substrate with local cells.

Each cell has an identifier, scope, role relation, structural state, authority state, scar status, and dependency list.

Routes depend on one or more cells.

A route may bypass only if all required route gates pass, all dependent cells remain structurally admissible, no dependent cell is shed or quarantined, scope is proven, and no hard scar blocks the proposed configuration.

The test does not need a full tetrahedral physics model.

It only needs enough structure to test authority boundaries.

## Minimal Entities

The harness should define cells.

Each cell should include:

cell_id

cell_scope

structural_epoch

role_relation

shape_status

authority_state

failed_invariant_class

adjacent_cells

load_transfer_status

scar_fingerprint

reconstruction_candidate

Each route should include:

route_id

dependent_cells

independent_cells

c_success

route_authority_state

scope_status

bypass_attempts

fallbacks

wrong_bypasses

Each scar should include:

fingerprint

scar_class

failure_count

elevation_state

retirement_state

metadata

## Cell States

The validation harness should use these states.

ACTIVE means the cell may support route authority.

WARNED means the cell has stress but has not crossed the shedding boundary.

SHEDDING_REVIEW means the cell is under review and must not gain new authority.

SHED means the cell has been removed from active authority.

QUARANTINED means the cell is retained for inspection but cannot support active authority.

RECONSTRUCTING means a replacement is being proposed or built.

REQUALIFYING means a replacement exists but must earn authority through fresh evidence.

RETIRED means the failed cell is no longer eligible for active use.

## Route Authority Rules

A route depending on an ACTIVE cell may bypass only when all ordinary route gates and all structural checks pass.

A route depending on a SHED, QUARANTINED, RECONSTRUCTING, REQUALIFYING, or RETIRED cell must not bypass.

A route with uncertain dependency scope must not bypass.

A route independent of the shed cell may bypass only if independence is explicitly proven.

A route may not bypass through a replacement cell until the replacement completes requalification.

Historical route confidence cannot override any of these rules.

## Scar Rules

A scar is written only when a cell had authority and later failed under valid structural evidence.

A scar is not written for cheap retries.

A scar is not written for non-admitted candidates.

A scar is not written when evidence is missing, stale, unverifiable, epoch-mismatched, or out of scope.

A hard scar blocks the same reconstruction candidate as-is.

A soft scar requires extra proof.

A restoration scar requires extra proof.

A no-match result does not block promotion by itself.

The harness should not implement a full extra-proof protocol. It should only verify that the candidate is routed into REQUIRE_EXTRA_PROOF rather than promoted.

## Load Transfer Rules

A local shedding decision must check whether adjacent healthy structure can carry the required load.

If load transfer succeeds, the system may remain in bounded degraded operation.

If load transfer fails, the system must escalate to broader recovery.

Load transfer must not preserve authority for routes that depend on the shed cell.

Load transfer only preserves operation for routes whose dependencies remain admissible or whose rerouting is explicitly declared valid.

## Test Scenarios

Scenario 1: dependent route revoked.

A cell has valid authority, fails a declared invariant, and is shed.

A route depending on that cell attempts bypass.

Expected result: fallback.

Scenario 2: independent route preserved.

A cell is shed, but another route has proven independent scope and depends only on healthy cells.

Expected result: bypass may remain available if ordinary route gates pass.

Scenario 3: uncertain scope fails closed.

A cell is shed and a route has unknown dependency scope.

Expected result: fallback.

Scenario 4: invalid evidence does not authorize clean shedding.

A cell appears failed, but evidence is stale, missing, unverifiable, epoch-mismatched, or out of scope.

Expected result: no clean shedding authorization, no scar write, route authority fails closed.

Scenario 5: betrayed authority writes scar.

A cell had authority and later fails under valid evidence.

Expected result: scar written.

Scenario 6: cheap retry does not write scar.

A cheap retry fails before authority is granted.

Expected result: no scar.

Scenario 7: non-admitted candidate does not write scar.

A candidate never receives authority and fails.

Expected result: no scar.

Scenario 8: hard scar blocks same reconstruction as-is.

A replacement candidate matches a hard scar.

Expected result: REJECT_AS_IS.

Scenario 9: soft scar requires extra proof.

A replacement candidate matches a soft scar.

Expected result: REQUIRE_EXTRA_PROOF.

Scenario 10: replacement enters requalification.

A replacement candidate does not match a hard scar and has valid structural evidence.

Expected result: REQUALIFYING, not ACTIVE bypass.

Scenario 11: load transfer succeeds.

A cell is shed and adjacent healthy structure can carry the declared degraded load.

Expected result: bounded degraded operation continues for admissible independent or rerouted work.

Scenario 12: load transfer fails.

A cell is shed and adjacent structure cannot carry the declared load.

Expected result: escalation to broader recovery.

## Assertions

A1: Dependent routes cannot bypass after their required cell is shed.

A2: Independent routes may remain eligible only when independence is proven.

A3: Unknown route scope fails closed.

A4: Invalid evidence does not authorize clean shedding.

A5: Invalid evidence does not write a scar.

A6: Betrayed authority writes a scar.

A7: Cheap retry failure does not write a scar.

A8: Non-admitted candidate failure does not write a scar.

A9: Hard scar match returns REJECT_AS_IS.

A10: Soft scar match returns REQUIRE_EXTRA_PROOF.

A11: Restoration scar match returns REQUIRE_EXTRA_PROOF.

A12: No-match candidate is not blocked by scar status alone.

A13: Replacement cell enters REQUALIFYING before active bypass.

A14: Replacement cell does not inherit active authority from the shed cell.

A15: Historical route confidence does not override a shed boundary.

A16: Historical route confidence does not override a hard scar.

A17: Load-transfer success preserves only declared admissible work.

A18: Load-transfer failure escalates to broader recovery.

A19: Scar matching remains isolated from shape_integrity.

A20: Scar matching remains isolated from C_success.

A21: Shedding event log contains cell_id, epoch, trigger, authority state, route impacts, scar decision, boundary, load-transfer decision, and final state.

A22: The harness produces a deterministic final verdict from the assertion results.

## Output Files

The validation run should produce:

cellular_shedding_v0_1_raw.csv

cellular_shedding_v0_1_summary.csv

cellular_shedding_v0_1_cell_states.csv

cellular_shedding_v0_1_route_authority.csv

cellular_shedding_v0_1_scar_events.csv

cellular_shedding_v0_1_load_transfer.csv

cellular_shedding_v0_1_assertions.csv

cellular_shedding_v0_1_verdict.csv

cellular_shedding_v0_1_run_record.txt

The validation run should also produce plots only after the data output is stable.

Suggested plots:

shedding_assertion_status.png

shedding_route_authority.png

shedding_scar_boundary.png

shedding_load_transfer.png

shedding_cell_state_timeline.png

## Verdict Boundary

The result is SUPPORTED only if all declared assertions pass.

The result is PARTIAL SUPPORT if authority revocation and scar rules pass, but load transfer or independent-route preservation fails.

The result is NOT SUPPORTED if dependent routes can bypass through a shed cell, hard scars can be overridden, invalid evidence writes scars, or replacements inherit active authority from removed cells.

The result is INCONCLUSIVE if the harness does not exercise dependent routes, independent routes, invalid evidence, scar conflicts, replacement requalification, and load-transfer outcomes.

## Required Run Record

The run record should include:

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

## Non-Claims

This validation plan does not prove production reliability.

It does not prove optimal thresholds.

It does not prove full recovery.

It does not prove lineage inheritance.

It does not prove fuzzy scar matching.

It does not prove prospective filtering.

It does not prove an extra-proof protocol.

It does not prove that every structural failure can be handled locally.

It does not prove that service remains uninterrupted during shedding.

## Freeze Criteria

Before implementation, this plan should be reviewed for three questions.

First, does the plan test the narrow shedding mechanism without accidentally claiming lineage inheritance?

Second, does the plan preserve the distinction among route confidence, shape integrity, scar matching, recovery, and shedding?

Third, does the verdict boundary punish the exact failures that would silently preserve failed authority?

Once those questions are answered, this plan can be frozen as:

CELLULAR_SHEDDING_VALIDATION_PLAN_v1_FROZEN.md
