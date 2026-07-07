# Bounded Routing

## What This Is

Bounded routing is a route-selection discipline for adaptive systems. It governs when a learned route may bypass full analysis and when the system must fall back.

The governing constraint is admissibility, not speed alone.

A route may bypass only while its confidence, structural cost, recovery context, depreciation state, oscillation behavior, applicable structural conditions, scar status, and local cell authority remain inside declared bounds.

This repository records bounded routing as the authority layer for the tetrahedral recovery architecture. The routing layer grants, maintains, and revokes bypass authority. The tetrahedral substrate supplies live structural state through the Fact, Logic, and Coherence roles and their coordinator. The recovery layer reconstructs the tetrahedral structure when confirmed recovery invariants fail.

Those responsibilities remain separate.

`C_success` records historical route performance.

`shape_integrity` represents the current authorized structural condition of the tetrahedral substrate.

A scar records that an authorized structural configuration failed and should not be promoted again as-is.

Cellular shedding removes a damaged local cell from active authority after failure.

## Current Status

The simulation series now has six main conclusions.

V1 supports the anti-oscillation gate under the tested oscillation workload.

V2 supports removal of stale authority and earned recovery through fresh requalification evidence.

V3 does not support the stronger claim that the flat bounded-routing gate stack revokes unsafe post-promotion authority faster than simpler comparison controls under the tested relapse workload. V3 identified the limit of the flat harness. Route confidence decayed too slowly, and the additional route-level gates did not detect degradation first.

V4 adds an independent tetrahedral shape-integrity gate and supports the narrow claim that live structural evidence can withdraw unsafe bypass authority earlier than the inherited flat gate under the frozen matched structural-deformation workload.

The scar layer adds a minimal rejected-configuration memory primitive. It supports the narrow claim that scars can be written only for betrayed authority, ignored for cheap or invalid failures, matched by exact geometry-only fingerprint, elevated only after the declared threshold, and retired only after declared successful cycles.

Cellular Shedding V1 adds local structural removal after cell failure. It supports the narrow claim that a local failed cell can be removed from active authority while preserving the correct route-authority boundary, scar boundary, replacement boundary, and load-transfer escalation boundary under the frozen synthetic harness.

## V4 Shape Gate Result

The V4 experiment compared:

```text
V4-C: flat bounded routing without shape-integrity gate
V4-D: bounded routing with independent tetrahedral shape-integrity gate
```

The shape gate did not replace `C_success`.

It did not blend with `C_success`.

It did not repair route confidence.

It acted as an independent conjunctive authority condition. A route could bypass only when the ordinary route gates and the shape-integrity gate were both admissible.

The frozen V4 result was:

```text
Final verdict:                 SUPPORTED
Assertions:                    26/26 passed
Eligible matched instances:     105
V4-C matched wrong bypasses:    404
V4-D matched wrong bypasses:    14
Wrong-bypass reduction:         96.53%
Earlier revocation fraction:    100%
Median revocation lead:         1860 ms
Clean suppression check:        passed
```

This result supports only the declared synthetic mechanism. It does not prove production reliability, threshold optimality, route-specific scope, or the complete tetrahedral architecture.

See:

```text
docs/TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1.md
docs/TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md
docs/V4_SHAPE_GATE_VERDICT.md
```

## Scar Layer V1 Result

The rejected-configuration scar layer tests a narrow structural memory primitive.

The governing rule is:

```text
Only betrayed authority creates a scar.
```

A cheap retry does not create a scar.

A non-admitted candidate does not create a scar.

A stale, missing, unverifiable, epoch-mismatched, or out-of-scope record does not create a scar.

A transient soft warning below persistence does not create a scar.

A scar is written only when a configuration had authority and later failed under valid structural evidence.

The scar does not explain why the configuration failed. It is not a diagnostic memory. It is not a semantic record. It is a compact rejected-configuration record that says the same geometry should not be promoted again as-is.

The frozen scar result was:

```text
Final verdict:    SUPPORTED
Assertions:       30/30 passed
Runtime:          0.98 s
stderr:           empty
```

The scar layer validated:

```text
geometry-only fingerprinting
no failed_invariant_class in the hash payload
no scars for cheap or non-admitted failures
no scars for invalid evidence
hard scars returning REJECT_AS_IS
soft and restoration scars returning REQUIRE_EXTRA_PROOF
failure_count incrementing only after repeated trusted failure
elevation only at T_SCAR_ELEVATE = 3
retirement only after T_SCAR_RETIRE_SUCCESS_CYCLES = 5
isolation from shape_integrity and C_success
```

This result does not validate cellular shedding, lineage inheritance, prospective filtering, fuzzy scar matching, or an extra-proof protocol.

See:

```text
docs/REJECTED_CONFIGURATION_SCAR_SPEC_v1_REVISED.md
docs/REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1_FROZEN.md
docs/REJECTED_CONFIGURATION_SCAR_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md
```

## Cellular Shedding V1 Result

Cellular Shedding V1 tests local structural removal after a damaged cell loses authority.

The governing rule is:

```text
Do not preserve failed authority through continuity of form.
```

A shed cell cannot support bypass authority.

A quarantined cell cannot support bypass authority.

A reconstructing cell cannot support bypass authority.

A requalifying replacement cell cannot support bypass authority until it earns fresh authority under the declared process.

The frozen shedding validation tested dependent-route revocation, independent-route preservation, uncertain-scope fail-closed behavior, invalid-evidence exclusion, betrayed-authority scar writing, cheap retry exclusion, non-admitted candidate exclusion, hard scar reconstruction blocking, soft and restoration scar extra-proof routing, replacement-cell requalification, load-transfer success, load-transfer failure, and replay-log coverage.

The frozen shedding result was:

```text
Final verdict:       SUPPORTED
Assertions:          22/22 passed
Document integrity:  OK
Script filename:     cellular_shedding_sim_v1_REVIEWED.py
```

The run record verified the frozen document hashes:

```text
Specification SHA-256:      8aaf925877d5bde60826a4a7ae3075d6177afaf41151e9d3a185bd4a1a27f512
Validation plan SHA-256:    4c073e5cdef9cd1e1812088bbf490775a658900cf790d87d632c049a4d821ae4
```

Cellular Shedding V1 supports the narrow claim that a local failed cell can be removed from active authority while preserving the correct route-authority boundary, scar boundary, replacement boundary, and load-transfer escalation boundary under the frozen synthetic harness.

It does not validate lineage inheritance. It does not validate fuzzy scar matching. It does not validate prospective filtering. It does not validate production recovery. It does not validate a full extra-proof protocol. It does not prove that every structural failure is locally shed-able. It does not prove uninterrupted service. It does not prove production reliability.

See:

```text
docs/CELLULAR_SHEDDING_SPEC_v1_FROZEN.md
docs/CELLULAR_SHEDDING_VALIDATION_PLAN_v1_FROZEN.md
docs/CELLULAR_SHEDDING_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md
```

## Simulation Series

### V1 Initial Harness

V1 compared full analysis, naive confidence-based bypass, and bounded routing with the full gate stack across stable, drift, fault, recovery, and oscillation phases.

The clearest V1 result occurred during route oscillation.

```text
Naive confidence cache wrong bypasses: 64
Bounded routing wrong bypasses:       0
```

V1 supports the anti-oscillation gate under the tested workload.

### V2 Recovery Requalification

V2 replaced timer-only restoration with earned route requalification.

A recovery event removes bypass authority. The current task goes through full analysis. The candidate learned route is evaluated in shadow on the same task, but that evidence applies only to future bypass authority.

Pre-recovery confidence cannot restore the route.

The primary V2 test required five consecutive admissible shadow checks and fresh confidence of at least 0.75.

The requalifying arm produced zero wrong bypasses in the primary recovery test while allowing eligible routes to earn authority back.

### V3 Post-Authority Relapse

V3 created the harder matched workload identified after V2. Borderline routes were allowed to requalify and then degrade after bypass authority had been restored.

The primary V3 matched results were:

```text
Naive cache wrong bypasses:           105
Timer-bound recovery wrong bypasses:  123
Requalifying recovery wrong bypasses: 126
```

V3 did not support the stronger claim that the flat bounded-routing gate stack revoked unsafe post-promotion authority faster than the comparison arms.

The first blocking gate was the confidence gate in all eligible borderline route instances.

V3 identified the need for an independent structural signal.

### V4 Shape Integrity

V4 tested that independent structural signal.

V4-D added the tetrahedral shape-integrity gate to the inherited flat bounded-routing mechanism. Under the frozen V4 plan, the direct comparison changed only one authority variable: whether the independent shape gate was consumed.

The V4 result was SUPPORTED.

### Scar Layer V1

The scar layer sits after the shape-gate work. It defines what kind of compact structural record is left when an authorized configuration fails.

The scar result was SUPPORTED.

The scar layer is intentionally narrow. It is a rejected-configuration registry, not a general memory system.

### Cellular Shedding V1

Cellular shedding sits after the scar-layer work. It defines how a damaged local cell is removed from active authority after failure.

The shedding result was SUPPORTED.

The shedding layer is intentionally narrow. It is local authority removal and boundary preservation, not lineage inheritance, production recovery, fuzzy matching, or extra-proof behavior.

## Repository Structure

```text
bounded-routing/
|-- README.md
|-- ROUTING_VERDICT.md
|-- FILE_MAP.md
|-- docs/
|   |-- bounded_routing_mechanism.md
|   |-- ard_sms_bypass.md
|   |-- validation_plan.md
|   |-- validation_plan_v2.md
|   |-- validation_plan_v3.md
|   |-- V3_RESULT_AND_VERDICT.md
|   |-- TETRAHEDRAL_ROUTING_PRINCIPLE.md
|   |-- TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1.md
|   |-- TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md
|   |-- V4_SHAPE_GATE_VERDICT.md
|   |-- REJECTED_CONFIGURATION_SCAR_SPEC_v1_REVISED.md
|   |-- REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1_FROZEN.md
|   |-- REJECTED_CONFIGURATION_SCAR_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md
|   |-- CELLULAR_SHEDDING_SPEC_v1_FROZEN.md
|   |-- CELLULAR_SHEDDING_VALIDATION_PLAN_v1_FROZEN.md
|   |-- CELLULAR_SHEDDING_V1_PRIMARY_RESULT_SUMMARY_FROZEN.md
|-- scripts/
|   |-- bounded_routing_sim_v1.py
|   |-- bounded routing sim v2.py
|   |-- bounded routing sim v3.py
|   |-- rejected_configuration_scar_sim_v1_REVIEWED.py
|   |-- cellular_shedding_sim_v1_REVIEWED.py
|-- data/
|   |-- bounded_routing_v1_raw.csv
|   |-- bounded_routing_v1_summary.csv
|   |-- bounded routing v2 recovery summary.csv
|   |-- bounded routing v2 sensitivity summary.csv
|   |-- bounded_routing_v3_raw.csv
|   |-- bounded_routing_v3_summary.csv
|   |-- bounded_routing_v3_recovery_summary.csv
|   |-- bounded_routing_v3_sensitivity_summary.csv
|   |-- bounded_routing_v3_matched_comparison.csv
|   |-- bounded_routing_v3_per_route_instance.csv
|   |-- bounded_routing_v3_aggregate_metrics.csv
|   |-- bounded_routing_v3_run_record.txt
|   |-- rejected_configuration_scar_v1_raw.csv
|   |-- rejected_configuration_scar_v1_summary.csv
|   |-- rejected_configuration_scar_v1_scenario_summary.csv
|   |-- rejected_configuration_scar_v1_scar_registry.csv
|   |-- rejected_configuration_scar_v1_assertions.csv
|   |-- rejected_configuration_scar_v1_verdict.csv
|   |-- rejected_configuration_scar_v1_run_record.txt
|   |-- cellular_shedding_v0_1_raw.csv
|   |-- cellular_shedding_v0_1_summary.csv
|   |-- cellular_shedding_v0_1_cell_states.csv
|   |-- cellular_shedding_v0_1_route_authority.csv
|   |-- cellular_shedding_v0_1_scar_events.csv
|   |-- cellular_shedding_v0_1_load_transfer.csv
|   |-- cellular_shedding_v0_1_assertions.csv
|   |-- cellular_shedding_v0_1_verdict.csv
|   |-- cellular_shedding_v0_1_run_record.txt
|-- plots/
|   |-- latency_by_phase_v1.png
|   |-- safety_metrics_v1.png
|   |-- cost_fallback_v1.png
|   |-- oscillation_wrong_bypass_v1.png
|   |-- latency_timeseries_v1.png
|   |-- recovery_wrong_bypass_timeseries_v3.png
|   |-- recovery_fallback_timeseries_v3.png
|   |-- requalification_by_pattern_v3.png
|   |-- post_requalification_matched_v3.png
|   |-- revocation_timeline_v3.png
|   |-- requalification_sensitivity_v3.png
|   |-- scar_v1_assertion_status.png
|   |-- scar_v1_write_boundary.png
|   |-- scar_v1_match_behavior.png
|   |-- scar_v1_elevation_retirement.png
```

## Running the Simulations

Run V1 with:

```bash
python scripts/bounded_routing_sim_v1.py
```

Run V2 with:

```bash
python "scripts/bounded routing sim v2.py"
```

Run V3 with:

```bash
python "scripts/bounded routing sim v3.py"
```

Run the scar validation with:

```bash
python scripts/rejected_configuration_scar_sim_v1_REVIEWED.py
```

Run the cellular shedding validation with:

```bash
python scripts/cellular_shedding_sim_v1_REVIEWED.py
```

The V4 shape-gate result is recorded in the V4 docs listed above.

## What This Does Not Claim

This project does not claim zero wrong bypasses under every condition.

It does not claim that the selected thresholds are optimal.

It does not claim production reliability.

It does not claim that GLOBAL scope is the correct deployment scope.

It does not prove the complete tetrahedral architecture.

It does not prove that every successfully requalified route will remain safe under later degradation.

It does not prove lineage inheritance, prospective filtering, fuzzy scar matching, or extra-proof recovery.

It does not prove that the system knows why a structural configuration failed.

It does not prove that every structural failure can be locally shed.

It does not prove uninterrupted service during shedding.

Full analysis remains the safety baseline and the correct fallback whenever bypass authority is not earned or required structural evidence is absent.

## Next Architectural Work

The next layer is lineage inheritance.

The scar layer defines what record is left behind when an authorized structural configuration fails.

Shedding defines how a damaged cell is cut away, how its authority is removed, and how adjacent healthy structure carries the load.

Lineage must define how a regenerated cell inherits a compact rejected-configuration list without inheriting the full history or old active authority.

