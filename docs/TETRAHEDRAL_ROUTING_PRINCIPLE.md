# Tetrahedral Routing Principle

## Governing Relationship Between Bounded Routing and the Tetrahedral Recovery Architecture

## Purpose

This document establishes the governing relationship between the bounded routing mechanism and the tetrahedral recovery architecture.

Earlier versions of this document recorded the architectural need for an independent tetrahedral structural signal after the V3 flat-harness result. That need has now been tested in the V4 shape-integrity gate experiment.

This document now records the post-V4 principle: bounded routing is the authority layer, the tetrahedral substrate supplies current structural condition, the recovery layer restores failed structure, and the scar layer records rejected structural configurations after betrayed authority.

This document does not revise the V1, V2, V3, V4, or scar-layer result records. Each result stands on its own. This document records how those results relate architecturally.

## Controlling Principle

Bounded routing is the authority layer for the tetrahedral recovery architecture.

It grants, maintains, and revokes route authority based on route-level evidence and the continuing structural integrity of the tetrahedral substrate beneath it.

Bounded routing is not a standalone system. It governs movement through the tetrahedral architecture. It does not substitute for the architecture's own health, recovery, and rejected-configuration mechanisms.

The V3 flat harness showed the limit of route-level scalar confidence as the sole post-promotion degradation detector.

The V4 shape-gate test showed that an independent structural signal can revoke unsafe bypass authority earlier than the inherited flat gate under the frozen matched structural-deformation workload.

The scar-layer test showed that betrayed structural authority can leave behind a compact rejected-configuration record without turning that record into general memory, diagnosis, shedding, or lineage inheritance.

## Separation of Responsibilities

The system has four distinct layers.

The tetrahedral layer produces role-separated structural state. The three specialist vertices, Fact, Logic, and Coherence, each maintain an independent health signal along a distinct dimension of the route's operating context. The coordinator observes the geometric relationship among these signals and produces the current structural condition. This layer does not make routing decisions. Its job is to maintain structural invariants and report their current condition.

The routing layer governs bypass authority. The router decides, at each task arrival, whether a learned route is currently admissible. It reads route-level performance evidence from the ARD and SMS stack, and it reads structural condition from the tetrahedral layer. It grants, withholds, or revokes bypass authority. It does not reconstruct the tetrahedral structure when that structure fails.

The recovery layer reconstructs the tetrahedral structure when its invariants fail. It responds to structural failures, coordinates role restoration, and signals when recovery is complete. The router may suspend bypass authority during recovery and requires valid structural evidence before restoring it, but reconstruction belongs to the recovery layer.

The scar layer records rejected structural configurations after betrayed authority. A scar says that a configuration had authority, later failed under valid evidence, and should not be promoted again as-is. It does not explain the failure. It does not replace recovery. It does not perform shedding. It does not define lineage inheritance.

Keeping these responsibilities separate prevents any one layer from absorbing the functions of the others.

## Signal Provenance and the Named Signals

Three named signals remain central to the routing decision.

`S_pat` is produced by the Pattern Recognition Engine and identifies what class of task has arrived and which routing history applies to it. It carries task-pattern information. It is not the carrier for live structural health because it is derived from task characteristics, not from the coordinator's current observation of the substrate.

`C_success` is the route's historical performance confidence, written by the Success Measurement System. It reflects how well the learned route has performed on past tasks, aggregated through a moving performance record. It is intentionally slow-moving. It records what the route has done. It does not represent what the substrate currently looks like.

`shape_integrity` is the current authorized structural condition of the tetrahedral substrate as observed by the coordinator or another authorized structural observer. It represents whether the geometric relationship among Fact, Logic, and Coherence currently satisfies the architectural invariants of the system.

These signals must remain separate.

`shape_integrity` must not be inferred solely from route outcomes, latency, or the SMS moving average. Deriving it from route-level evidence would collapse the distinction that makes it useful. A route can retain high historical confidence while the tetrahedral structure beneath it has already begun to deform.

The V4 shape-gate result depends on this separation. The shape gate acted as an independent conjunctive authority condition. It did not replace `C_success`, blend with `C_success`, or repair route confidence.

## Provenance, Freshness, and Epoch Integrity

Every structural observation that participates in a bypass decision must carry an authorized source identity, an observation timestamp, and a structural or recovery epoch identifier.

The source identity establishes that the observation was produced by an authorized structural observer, not inferred from route outcomes or reconstructed from stale evidence.

The timestamp records when the observation was made.

The epoch identifier establishes which structural or recovery cycle the observation belongs to.

A shape observation from an earlier epoch must not authorize bypass in the current epoch. After a recovery event, structural realignment, or role replacement, the previous epoch's observations are no longer valid evidence about the current condition of the substrate.

Missing, stale, unverifiable, epoch-mismatched, or out-of-scope structural state cannot be interpreted as healthy. The router must fail closed to the non-bypass path until current authorized structural evidence is available.

This is a provenance requirement, not a performance preference.

## The Form of shape_integrity

shape_integrity is a structural record or gate condition, not necessarily one opaque scalar.

The coordinator may derive a bounded pass/fail gate result or compact integrity measure that the router reads directly. A single gate output is acceptable only if it does not erase the underlying role-separated structural record from which it was computed.

The system must preserve enough role-separated and geometric evidence to support audit, diagnosis, and recovery guidance.

At minimum, future schema work should preserve the individual Fact, Logic, and Coherence health values; coordinator-derived geometric measures such as angular distortion, role imbalance, or edge condition; the authorized source identity; the observation timestamp; the structural epoch; and the route scope to which the observation applies.

The V4 result supports the gate behavior under the frozen synthetic workload. It does not prove that one final production shape formula has been selected.

## Scope and Applicability

The architecture must determine whether structural integrity is global to the tetrahedral substrate, route-specific according to which roles or edges a particular route depends on, or a combination of both.

A route that depends on only part of the substrate may be affected differently by role-specific deformation than a route that engages all three specialist vertices.

A healthy observation of an unrelated region of the substrate cannot authorize a route through a deformed one.

The gate must be able to identify whether the structural observation it is reading applies to the route being evaluated at that moment. If applicability cannot be established, the router must fail closed.

The V4 result does not settle final route scope. It supports the narrow claim that the independent shape gate can revoke unsafe bypass authority earlier under the declared matched deformation workload.

## Why Fact, Logic, and Coherence Must Not Be Blended Away

The independence of the three specialist signals is the source of the early deformation signal.

A route may still appear factually correct while logical consistency is falling. It may still appear fast and admissible while coherence is breaking. A single blended average can hide this divergence because the deteriorating dimension is diluted by the dimensions that remain healthy.

Fact, Logic, and Coherence must therefore not be collapsed into another scalar confidence score before they reach the routing decision.

Doing so would recreate the problem V3 identified with C_success: a slow-moving average that detects degradation only after it has progressed far enough to dominate the blend.

The coordinator's job is to measure the geometric relationship among the three signals and produce a structural condition that reflects their current agreement or divergence.

The separation is the value.

## Integration Sites

The existing routing stack has five primary integration sites.

The Pattern Recognition Engine must preserve task-pattern information in S_pat without absorbing tetrahedral state into it. The tetrahedral state does not change which pattern class a task belongs to. It changes whether the route for that pattern class is currently trustworthy.

The Adaptive Routing Database must carry structural condition alongside route-level fields. The structural field has different provenance from C_success. It is written by the tetrahedral coordinator or another authorized structural observer, not by SMS. It carries its own source, timestamp, epoch, and scope.

The Success Measurement System continues to calculate route-level performance evidence and update C_success. It must not absorb shape_integrity into C_success. SMS and the coordinator are parallel observers reporting different things. The router needs to read both, not merge them before reading.

The Intelligent Bypass Mechanism must consume the shape gate as a peer authority condition. The route may pass confidence, structural cost, recovery context, and anti-oscillation gates while still failing shape integrity. A failed, missing, stale, epoch-mismatched, or out-of-scope shape observation withholds bypass authority.

The recovery context must be able to respond to structural deformation as a trigger condition, not only to elapsed time or a previously declared recovery event. Structural deformation detected by the coordinator should be able to initiate a recovery-sensitive state in the routing layer without waiting for ordinary route confidence to decay.

## What V3 Established

V3 tested the bounded routing mechanism in a flat harness without live tetrahedral structural input.

The four arms operated on a synthetic task stream with route quality encoded directly in the manifest. No coordinator produced a shape measure. No role-separated signals fed the routing decision. The router had access only to route-level confidence, latency, cost, and the requalification state machine.

V3 found that scalar confidence decay did not revoke unsafe post-promotion authority faster than the simpler comparison arms.

In all eligible borderline route instances, the first gate to block bypass after degradation onset was the confidence gate. The depreciation, cost, anti-oscillation, and cooldown gates did not fire first.

V3 did not test whether tetrahedral deformation can provide an earlier revocation signal. It showed what happens when the router operates without the structural substrate it was designed to sit on.

The V3 NOT SUPPORTED verdict remains unchanged.

## What V4 Established

V4 tested an independent tetrahedral shape-integrity gate under a frozen matched structural-deformation workload.

The comparison changed one authority variable: whether the independent shape-integrity gate was consumed.

The primary V4 result was SUPPORTED.

The V4 run passed 26 of 26 assertions.

The matched wrong bypass count fell from 404 in the flat V4-C arm to 14 in the V4-D shape-gated arm.

That is a 96.53 percent reduction under the frozen workload.

Earlier revocation occurred in 100 percent of eligible matched instances.

The median revocation lead was 1860 milliseconds.

The clean suppression check passed.

V4 supports the narrow claim that live structural evidence can revoke unsafe bypass authority earlier than the inherited flat route gate under the declared synthetic deformation workload.

V4 does not prove production reliability, threshold optimality, final route scope, or the complete tetrahedral architecture.

## What the Scar Layer Established

The scar layer tested a narrow rejected-configuration registry.

The governing rule is: only betrayed authority creates a scar.

A cheap retry does not create a scar.

A non-admitted candidate does not create a scar.

Invalid evidence does not create a scar.

A scar is written only when a configuration had authority and then failed under valid evidence.

The frozen scar run passed 30 of 30 assertions and returned a SUPPORTED verdict.

The test supports geometry-only fingerprinting, hard scar rejection, soft and restoration scar extra-proof requirements, elevation only at the declared threshold, retirement only after declared successful cycles, and isolation from shape_integrity and C_success.

The scar layer does not validate cellular shedding, lineage inheritance, prospective filtering, fuzzy matching, or an extra-proof protocol.

## Design Constraints Going Forward

No route-authority mechanism may treat shape_integrity as merely another weighted SMS component. It must reach the bypass gate as its own condition, readable and enforceable independently of the confidence gate.

No future experiment may claim to test tetrahedral routing unless live role-separated or coordinator-derived structural state actually participates in the bypass decision.

No stale or missing shape observation may preserve bypass authority.

No scalar gate result may erase the underlying structural evidence from which it was derived.

No structural condition may authorize a route unless its scope applies to that route.

No scar may be written without betrayed authority.

No scar match may mutate shape_integrity or C_success.

No scar-layer result may be treated as validation of shedding or lineage inheritance.

## Next Architectural Work

The next architectural layer is cellular shedding.

The scar layer records that an authorized configuration failed and should not be promoted again as-is.

Shedding must define how a damaged cell is cut away, how its authority is removed, how adjacent healthy structure carries the load, and how the system prevents the damaged configuration from being reconstructed unchanged.

Lineage inheritance comes after shedding. It must define how a regenerated cell inherits a compact rejected-configuration list without inheriting full history and without turning the scar registry into general memory.

