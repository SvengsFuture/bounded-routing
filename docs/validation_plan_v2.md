# Bounded Routing — v2 Recovery Requalification Validation Plan

## Status

This plan was written before the v2 simulation run. The mechanism, parameters, expected behavior, and go/no-go criteria are declared in advance and will not be rewritten afterward to match the results.

## Purpose and scope

Bounded routing v1 used a fixed recovery blackout. After a recovery event, bypass was blocked for a set period and then allowed to resume.

That mechanism increased conservative fallback, but it did not establish that routes were safe under the recovered operating conditions. Elapsed time restored execution authority without requiring fresh evidence.

V2 replaces timer-only recovery permission with earned route requalification.

The purpose of v2 is to test whether a learned route can lose bypass authority during recovery, operate only in shadow while full analysis handles live tasks, and regain bypass authority only after producing sufficient current evidence.

V1 remains unchanged as the initial technical record. V2 does not retune or replace the v1 results.

## Experimental arms

The primary v2 recovery experiment uses four arms.

| Arm | Label           | Behavior                                                                   |
| --- | --------------- | -------------------------------------------------------------------------- |
| A   | A_FULL_ANALYSIS | Every task uses full analysis. No learned bypass.                          |
| B   | B_NAIVE_CACHE   | Bypass occurs whenever confidence is above threshold. No recovery control. |
| C   | C_TIMER_BOUND   | Uses the v1 fixed recovery-blackout mechanism.                             |
| D   | D_REQUALIFYING  | Uses post-recovery shadow evaluation and earned requalification.           |

Arm C preserves the timer-based recovery behavior inside the same run. This allows the requalification mechanism to be compared directly with both naive cache and the previous bounded recovery method.

## Shared task manifest

The candidate-route conditions will be generated once before the arms are executed.

The simulation will create a pre-generated task manifest containing the task time, pattern identifier, phase, candidate-route admissibility, candidate-route latency, candidate-route structural cost, and route quality.

All four arms will read the same manifest.

This prevents different arms from receiving different random route conditions and makes the comparison auditable.

## Recovery mechanism change

When a recovery event occurs, every ARD entry in the ACTIVE or WARNED state moves to REQUALIFYING.

A route in REQUALIFYING cannot bypass. The live task is sent through full analysis. At the same time, the candidate learned route is evaluated in shadow against the same task conditions.

Full analysis protects the current task.

Shadow evaluation gathers evidence about whether the candidate route may be trusted for later bypasses.

The shadow result does not control the current live task.

Pre-recovery confidence, observations, and success history do not authorize post-recovery bypass. Requalification uses a separate observation window containing only evidence collected after the recovery event.

## REQUALIFYING state

REQUALIFYING does not mean the route has failed. It means the route lacks current authority to bypass.

The primary state transition is:

```text
ACTIVE or WARNED
        |
        | recovery event
        v
REQUALIFYING
        |
        | K_REQUALIFY consecutive admissible shadow checks
        | fresh confidence >= T_BYPASS
        v
ACTIVE
```

An inadmissible shadow result resets the consecutive clean count to zero and lowers fresh requalification confidence. It does not automatically deprecate the route.

A route moves from REQUALIFYING to DEPRECATED only when its fresh shadow confidence remains below T_DEPRECIATE for the existing depreciation count requirement.

A route that was already DEPRECATED before the recovery event remains DEPRECATED. Recovery does not rehabilitate a route that had already demonstrated sustained failure.

If a route does not gather enough evidence to requalify, it remains REQUALIFYING and continues using full analysis.

## Shadow evaluation definition

A clean shadow check means that the candidate route produces an admissible result under the current task conditions.

Admissibility controls the consecutive K_REQUALIFY count.

Shadow latency, route quality, structural cost, and stability also contribute to the shadow observation’s SMS outcome score.

For every shadow observation:

```text
shadow_outcome_score =
      W_LAT  * shadow_latency_score
    + W_ADM  * shadow_admissibility_score
    + W_DEG  * shadow_degradation_score
    + W_STAB * shadow_stability_score
```

The v1 SMS weights remain unchanged.

Fresh requalification confidence is the mean SMS outcome score in the dedicated post-recovery requalification window.

It is not inherited from the pre-recovery ARD confidence and is not initialized to an arbitrary confidence value.

Promotion to ACTIVE requires both:

```text
requalify_count >= K_REQUALIFY
```

and:

```text
fresh_requalify_confidence >= T_BYPASS
```

When the route returns to ACTIVE, its normal C_success is set to the fresh requalification confidence derived from the current window.

## Primary parameters

| Parameter                            |                               Primary value | Purpose                                       |
| ------------------------------------ | ------------------------------------------: | --------------------------------------------- |
| K_REQUALIFY                          |                                           5 | Consecutive admissible shadow checks required |
| T_BYPASS                             |                                        0.75 | Minimum fresh confidence for promotion        |
| T_DEPRECIATE                         |                                        0.55 | Sustained low-confidence boundary             |
| Requalification window               | Most recent K_REQUALIFY shadow observations | Current evidence only                         |
| Pre-recovery confidence contribution |                                           0 | Stale history cannot restore authority        |
| Recovery blackout timer              |                           Not used by Arm D | Replaced by evidence-based requalification    |

The declared sensitivity sweep uses:

```text
K_REQUALIFY = 3, 5, 8
```

The primary reported run uses K_REQUALIFY = 5.

No separate C_REQUALIFY_INIT parameter is used.

## Requalification gate reasons

The requalification_gate_reason field uses only these values:

```text
REQUALIFYING_COUNT
REQUALIFYING_CONFIDENCE
DEPRECATED
TIMER
NONE
```

REQUALIFYING_COUNT means the route has not yet accumulated the required clean shadow checks.

REQUALIFYING_CONFIDENCE means the clean count has been reached, but fresh confidence remains below T_BYPASS.

DEPRECATED means the route is not eligible for requalification.

TIMER applies only to Arm C while the fixed blackout remains active.

NONE means bypass was permitted.

## New raw-data fields

The v2 raw CSV adds these fields:

| Field                       | Meaning                                                |
| --------------------------- | ------------------------------------------------------ |
| time_since_recovery_ms      | Time elapsed since the recovery signal                 |
| requalification_state       | Current ARD state for the route                        |
| requalify_count             | Current consecutive clean shadow count                 |
| shadow_route_admissible     | Whether the candidate route would have been admissible |
| shadow_latency_ms           | Modeled latency of the candidate route                 |
| shadow_structural_cost      | Structural cost of the candidate route                 |
| shadow_outcome_score        | SMS score produced by the shadow result                |
| fresh_requalify_confidence  | Confidence built only from the requalification window  |
| requalified_at_ms           | Time when the route regained ACTIVE status             |
| bypass_post_requalify       | Whether a bypass occurred after requalification        |
| requalification_gate_reason | Reason bypass authority was withheld or permitted      |

## Summary metrics

The v2 summary reports the existing v1 metrics plus:

```text
mean_time_to_requalify_ms
patterns_requalified
patterns_remaining_requalifying
patterns_deprecated_during_requalification
shadow_checks_total
shadow_checks_admissible
post_requalify_bypasses
post_requalify_wrong_bypasses
post_requalify_wrong_bypass_rate
wrong_bypasses_by_recovery_time_bin
fallback_rate_by_recovery_time_bin
```

Recovery time bins will be reported separately so early and late behavior are not hidden inside one phase average.

## Expected result shape

Arm B is expected to bypass immediately after recovery because its pre-recovery confidence remains authoritative.

Arm C is expected to block bypass during the fixed timer and restore bypass authority when the timer expires.

Arm D is expected to begin recovery with high fallback because routes are REQUALIFYING.

Patterns should regain authority at different times as they collect fresh shadow evidence. Fallback should decline pattern by pattern rather than ending at one global timestamp.

The important result is not merely that Arm D produces fewer total bypasses.

The important result is whether bypasses made after requalification are cleaner than immediate naive bypasses and cleaner than bypasses restored by timer expiration alone.

V2 may fail to show this advantage.

If Arm D only appears safer because it rarely or never requalifies, the mechanism has not demonstrated useful bounded routing.

## Required plots

The v2 package should generate:

```text
recovery_wrong_bypass_timeseries_v2.png
recovery_fallback_timeseries_v2.png
requalification_by_pattern_v2.png
post_requalification_safety_v2.png
requalification_sensitivity_v2.png
```

The recovery wrong-bypass plot should show when violations accumulate after the recovery signal.

The fallback plot should show whether Arm D gradually restores bypass rather than behaving like permanent full analysis.

The pattern plot should show when individual routes requalify.

The post-requalification safety plot should compare Arms B, C, and D using bypasses that occur after Arm D begins restoring authority.

The sensitivity plot should compare K_REQUALIFY values of 3, 5, and 8.

## Go/no-go criteria

Every Arm D bypass must be blocked while its route is REQUALIFYING.

Every promotion to ACTIVE must be preceded by at least K_REQUALIFY consecutive admissible shadow checks and fresh confidence at or above T_BYPASS.

No pre-recovery observation may contribute to fresh requalification confidence.

A DEPRECATED route may not return to ACTIVE merely because a recovery event occurred.

The mechanism supports the recovery claim if Arm D produces a lower post-requalification wrong-bypass rate than Arm B without remaining in near-permanent fallback.

The mechanism improves on timer-only recovery if Arm D restores bypass authority through evidence and produces cleaner post-restoration bypasses than Arm C.

The result is no-go if Arm D obtains lower violation counts only by suppressing nearly all bypasses, if routes are promoted without the declared evidence, or if the result depends on one favorable value of K_REQUALIFY.

## What v2 does not test

V2 does not test automatic discovery of a replacement route for a DEPRECATED entry.

The current harness does not genuinely model full analysis identifying and naming a new route. Replacement-route nomination is deferred until the simulation includes explicit route identities and can verify that a proposed replacement differs from the failed P_opt.

V2 does not establish real-world latency, optimal parameter values, production reliability, or correctness of the PRE pattern signature.

The v2 claim remains narrow.

Recovery removes execution authority. Full analysis protects live work. Shadow evaluation gathers current evidence. A learned route regains bypass authority only after that evidence satisfies the declared requalification bounds.
