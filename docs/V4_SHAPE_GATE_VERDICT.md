# V4 Shape-Integrity Gate Verdict

**Document:** `V4_SHAPE_GATE_VERDICT.md`  
**Status:** Supported under frozen synthetic validation plan  
**Related plan:** `TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md`  
**Related script:** `bounded_routing_sim_v4.py`  
**Primary result:** `SUPPORTED`

## Verdict

The V4 experiment supports the narrow claim that an independent tetrahedral shape-integrity gate can withdraw unsafe bypass authority earlier than the inherited flat bounded-routing gate under the frozen matched structural-deformation workload.

The result is not a general proof of the tetrahedral architecture. It is a controlled synthetic validation of one declared mechanism: a live structural signal, derived only from control-plane tetrahedral state, added conjunctively to the existing bounded-routing authority layer.

Under the frozen plan, V4-D changed only one authority variable relative to V4-C. V4-C preserved the inherited flat bounded-routing mechanism. V4-D added the independent shape-integrity gate. All task manifests, deformation schedules, structural inputs, epoch schedules, and comparison keys were pre-generated and shared.

The run produced a `SUPPORTED` verdict with all required assertions passing.

## What Was Tested

The experiment asked whether live tetrahedral structural evidence could detect and revoke unsafe authority earlier than route-confidence decay.

The direct comparison was:

```text
V4-C: flat bounded routing without shape-integrity gate
V4-D: bounded routing with independent tetrahedral shape-integrity gate
```

The structural gate did not replace `C_success`.

It did not blend with `C_success`.

It did not repair route confidence.

It read a structural record carrying source identity, epoch, scope, and role-separated invariant results, which are structurally unavailable to `C_success` by construction.

It acted as an independent conjunctive authority condition. A route could bypass only when both the ordinary routing gates and the shape-integrity gate were admissible.

The first experiment used GLOBAL structural scope:

```text
scope_type = GLOBAL
scope_id = ACTIVE_TETRAHEDRAL_SUBSTRATE
```

This choice was intentionally broad. Any GLOBAL structural failure could deny bypass for the shared substrate. The cost of that broad scope was measured through fallback and lost-bypass-opportunity metrics rather than hidden.

## Frozen Result Summary

```text
Final verdict:                    SUPPORTED
Assertions:                       26/26 passed
Eligible matched instances:        105
V4-C matched wrong bypasses:       404
V4-D matched wrong bypasses:       14
Wrong-bypass reduction:            96.53%
Earlier revocation fraction:       100%
Median revocation lead:            1860 ms
Hard median tasks exposed:         0.0
Soft median tasks exposed:         1.0
Bootstrap 95% CI:                  [365, 416]
Clean suppression check:           passed
D0 clean-control shape denials:    0
D1 transient-soft shape denials:   0
Unnecessary reconstruction:        0
```

The matched wrong-bypass reduction reproduces directly:

```text
1 - (14 / 404) = 0.9653465346534653
```

The bootstrap confidence interval over paired wrong-bypass count differences remained entirely above zero:

```text
paired bootstrap 95% CI over paired wrong-bypass count differences = [365, 416]
```

This satisfies the frozen support requirement that the lower bound be greater than zero. The interval is a count-difference interval, not a millisecond or percentage interval.

## Why The Result Counts

The result counts because the shape gate improved the unsafe-authority outcome without broadly suppressing bypass.

The clean suppression check passed. During structurally healthy periods, V4-D executed nearly the same bypass volume as V4-C:

```text
clean_bypass_ratio_d_over_c = 1.000047
```

That matters because a gate can appear safer simply by turning bypass off. That did not happen here. V4-D preserved ordinary bypass behavior during healthy windows and acted specifically during declared structural deformation, invalidity, restoration, or gate-effective soft degradation.

The hard-failure scenarios showed immediate authority withdrawal. The median number of exposed matched tasks before shape revocation in hard scenarios was:

```text
hard_median_tasks_exposed = 0.0
```

That means the structural gate usually revoked authority before an eligible matched task could execute a wrong bypass after a hard deformation became visible.

The soft-degradation scenarios reflected the declared persistence cost. The median exposure was:

```text
soft_median_tasks_exposed = 1.0
```

That is consistent with the frozen `K_SOFT_PERSIST = 3` rule. The gate did not treat the first raw soft warning as decisive. It waited for persistence, paid the declared delay, then denied bypass. The measured delay remained inside the support boundary.

## Three-Way Classification Result

The experiment preserved the v1.1 distinction among three non-admissible states.

Evidence invalidity denied bypass without declaring tetrahedral collapse. Stale records, missing records, failed verification, epoch mismatch, and scope mismatch failed closed. They did not trigger reconstruction by themselves.

Confirmed hard structural failure revoked authority immediately from valid structural evidence. Hard role absence, angular compression, coverage loss, coordinator offset, and role dominance all triggered the expected hard-failure behavior.

Soft structural degradation became gate-effective only after the frozen persistence rule was satisfied. The transient D1 soft imbalance crossed a soft bound but cleared before persistence, producing no shape-caused denial. The persistent soft cases crossed the same kind of boundary and then became gate-effective as declared.

This is the core architectural result. The gate did not treat every non-admissible condition as the same thing.

## Leakage And Isolation Result

All 26 assertions passed.

The run preserved the required isolation. Manifests were generated before arm execution. The structural observer did not consume route correctness, wrong-bypass labels, `C_success`, task-processing latency, arm identity, or evaluator-only ground-truth labels. The shape-record stream was replay-verifiable from the saved structural manifest. The corrected A7 and A25 assertions checked replay determinism and record immutability rather than comparing objects to themselves.

V4-C and V4-D were route-mechanically identical until the shape gate became non-admissible. The shape gate was the isolated authority change.

## What This Result Supports

This result supports the following narrow claim:

Under the frozen V4 synthetic workload, an independent tetrahedral shape-integrity gate withdrew unsafe bypass authority earlier than the inherited flat bounded-routing gate, sharply reduced matched wrong bypasses, and did so without broad bypass suppression or route-outcome leakage.

The supported result is strongest in the hard-deformation cases, where the structural signal revoked authority before confidence decay could accumulate enough evidence to block the route.

The persistent soft-degradation cases also support the mechanism, but they include the expected cost of `K_SOFT_PERSIST`. That cost is not a defect. It was declared in the plan and measured in the result.

## What This Result Does Not Claim

This result does not prove that the selected thresholds are optimal.

It does not prove that GLOBAL scope is the right deployment scope.

It does not prove production reliability.

It does not prove that all tetrahedral failures can be captured by the selected structural formulas.

It does not prove that the coordinator design is complete.

It does not prove that route-specific or regional scope will behave the same way.

It does not overturn the v3 result. V3 remains the flat bounded-routing baseline. V3 showed that the flat confidence-decay mechanism did not withdraw authority fast enough under the tested relapse workload. V4 tested what v3 showed was missing: a structural signal that acts before confidence decay.

V4 adds an independent structural gate and tests a different mechanism.

## Technical Interpretation

The important result is not that V4-D had fewer wrong bypasses in the abstract.

The important result is that the reduction came from a separate live structural authority signal, not from historical route confidence, not from outcome leakage, and not from suppressing bypass everywhere.

`C_success` answers whether a route has performed well over time.

`shape_integrity` answers whether the tetrahedral substrate is currently intact enough to permit bypass authority.

The V4 result shows that those two questions can be kept separate in a simulation harness and that the structural question can provide an earlier withdrawal signal under matched deformation.

That is the technical value of the run.

## Repo Placement

Recommended placement:

```text
docs/V4_SHAPE_GATE_VERDICT.md
```

Recommended supporting files:

```text
docs/TETRAHEDRAL_SHAPE_INTEGRITY_SPEC_v1_1.md
docs/TETRAHEDRAL_SHAPE_INTEGRITY_VALIDATION_PLAN_v1.md
scripts/bounded_routing_sim_v4.py
data/bounded_routing_v4_summary.csv
data/bounded_routing_v4_verdict.csv
data/bounded_routing_v4_assertions.csv
data/bounded_routing_v4_matched_comparison.csv
plots/v4_revocation_timeline.png
plots/v4_wrong_bypass_matched.png
plots/v4_clean_suppression_check.png
plots/v4_global_scope_cost.png
```

The complete raw-manifest package should be retained as evidence, but the repo can expose a compact result set unless the goal is full replay from source artifacts.

## Final Status

The V4 shape-integrity gate is supported under the frozen synthetic validation plan.

The next technical step is not another architecture revision. The next step is packaging the result cleanly into the project record and deciding which result files belong in the public repository.
