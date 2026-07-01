# Tetrahedral Routing Principle

## Governing Relationship Between Bounded Routing and the Tetrahedral Recovery Architecture

---

## Purpose

This document establishes the governing relationship between the bounded routing
mechanism and the tetrahedral recovery architecture. It records the project
principle that emerged from reviewing the v3 simulation results in the context
of the larger system design, and it defines the integration sites where the two
layers must connect.

This document does not design a v4 mechanism, does not select thresholds or
formulas, and does not modify the approved v3 record or verdict.

---

## Controlling principle

Bounded routing is the authority layer for the tetrahedral recovery architecture.
It grants, maintains, and revokes route authority based on route-level evidence
and the continuing structural integrity of the tetrahedral substrate beneath it.

Bounded routing is not a standalone system. It was never intended to operate
independently of the tetrahedral structure and is not a replacement for it. The
router governs movement through the tetrahedral architecture; it does not
substitute for that architecture's own health and recovery mechanisms.

---

## Separation of responsibilities

The system as a whole involves three distinct layers, each with a defined job.

The tetrahedral layer produces role-separated structural state. The three
specialist vertices — Fact, Logic, and Coherence — each maintain an independent
health signal along a distinct dimension of the route's operating context. The
coordinator observes the geometric relationship among these three signals and
produces a measure of the shape they collectively form. This layer does not make
routing decisions. Its job is to maintain the structural invariants and to report
their current condition.

The routing layer governs bypass authority. The router decides, at each task
arrival, whether a learned route is currently admissible. It reads route-level
performance evidence from the ARD and SMS stack, and it reads structural
condition from the tetrahedral layer. It grants, withholds, or revokes bypass
authority. It does not reconstruct the tetrahedral structure when that structure
fails; that is not its job.

The recovery layer reconstructs the tetrahedral structure when its invariants
fail. It responds to structural failures, coordinates role restoration, and
signals when recovery is complete. The router may suspend bypass authority
during recovery and requires evidence of structural restoration before restoring
it — but the reconstruction work belongs to the recovery layer, not the router.

Keeping these responsibilities separate prevents any one layer from absorbing
the functions of the others. The v3 flat harness collapsed this separation by
testing the router without live tetrahedral input, which placed the full burden
of degradation detection on route-level scalar evidence alone. The outcome of
that test is documented in V3_RESULT_AND_VERDICT.md and is not revised here.

---

## Signal provenance and the three named signals

Three signals play distinct roles in the routing decision, and their distinctness
must be preserved through the implementation.

**S_pat** is produced by the Pattern Recognition Engine and identifies what class
of task has arrived and which routing history applies to it. S_pat carries
semantic structure: task type, context class, structural cost estimate, and
recovery-sensitivity flag. It must preserve this task-pattern information without
absorbing or flattening tetrahedral state into it. S_pat is not the right carrier
for live structural health because it is derived from task characteristics, not
from the coordinator's current observation of the substrate.

**C_success** is the route's historical performance confidence, written
exclusively by the Success Measurement System. It reflects how well the learned
route has performed on past tasks, aggregated through an exponentially weighted
moving average. C_success is intentionally slow-moving; it is designed to be
stable under variance. That stability is appropriate for its job but means it
cannot serve as an early-warning signal for structural degradation. C_success
records what the route has done. It does not represent what the substrate
currently looks like.

**shape_integrity** is the provisional name for the live structural condition
of the tetrahedral substrate as observed by the coordinator. It represents
whether the geometric relationship among Fact, Logic, and Coherence currently
satisfies the architectural invariants of the system. The name is provisional
because the final form of this record is an open design question; it is not
necessarily one opaque scalar. What it designates — the current authorized
structural observation of the substrate — is not provisional.

shape_integrity must be produced by the tetrahedral coordinator or another
authorized structural observer. It must not be inferred solely from route
outcomes, latency, or the SMS moving average. Deriving shape_integrity from
route-level evidence would collapse the distinction that makes it useful: a
route can retain high historical performance confidence while the tetrahedral
structure beneath it has already begun to deform, and it is precisely that
divergence that the shape signal exists to detect.

---

## Provenance, freshness, and epoch integrity of structural observations

Every structural observation that participates in a bypass decision must carry,
at minimum, an authorized source identity, an observation timestamp, and a
structural or recovery epoch identifier. The source identity establishes that
the observation was produced by an authorized structural observer — the
tetrahedral coordinator or a designated equivalent — and not inferred from route
outcomes or reconstructed from stale evidence. The timestamp records when the
observation was made. The epoch identifier establishes which structural or
recovery cycle the observation belongs to.

A shape observation from an earlier epoch must not authorize bypass in the
current epoch. After a recovery event, structural realignment, or role
replacement, the previous epoch's observations are no longer valid evidence
about the current condition of the substrate, regardless of how healthy they
appeared at the time. The router must treat epoch-mismatched structural state
as unavailable rather than as carry-forward authorization.

Missing, stale, unverifiable, or epoch-mismatched structural state cannot be
interpreted as healthy. The router must fail closed to the non-bypass path until
a current, authorized structural observation is available. This is a
provenance requirement, not a performance preference. The cost of occasionally
withholding bypass authority on a healthy route is lower than the cost of
executing bypass on a route whose substrate has deformed and whose structural
record cannot confirm otherwise. The appropriate freshness duration for a
structural observation is not chosen in this document; that choice requires
architecture-level design work on the coordinator's observation cadence and the
router's tolerance for observation lag.

---

## The form of shape_integrity

shape_integrity is the provisional name for a structural record or gate
condition, not necessarily a single opaque scalar. The coordinator may derive a
bounded pass/fail gate result or a compact integrity measure that the router
reads directly. Producing a single scalar as a gate output is acceptable, but
only if it is a derived output and does not replace or erase the underlying
role-separated structural record from which it was computed.

The system must preserve enough role-separated and geometric evidence to
identify the source of deformation after the fact. A scalar that compresses
Fact, Logic, and Coherence health into one number without retaining the
components makes audit, diagnosis, and recovery guidance impossible: a failing
gate result cannot indicate which role is deforming or which edge has collapsed.
At minimum, future schema work on the structural record must consider the
individual Fact, Logic, and Coherence health values; coordinator-derived
geometric measures such as angular distortion, role imbalance, or edge
condition; the authorized source identity; the observation timestamp; and the
structural epoch. The final schema is not determined here. The constraint is that
whatever form the structural record takes, the underlying evidence must be
preserved and attributable, not compressed away in the gate result.

---

## Scope and applicability of structural conditions

The future architecture must determine whether structural integrity is global to
the tetrahedral substrate, route-specific according to which roles or edges a
particular route depends on, or a combination of both. A route that passes
through only two of the three specialist vertices may be affected differently by
role-specific deformation than a route that engages all three. A regional failure
in one part of the substrate may not invalidate routes that do not depend on
that region.

This document does not decide the question of scope. It does require that the
provenance and applicability of every structural condition be explicit in the
schema and the gate logic. A healthy observation of an unrelated region of the
substrate cannot authorize a route through a deformed one. The gate must be able
to identify whether the structural observation it is reading applies to the route
being evaluated at that moment. If that applicability cannot be established, the
router must fail closed.

---

## Why Fact, Logic, and Coherence must not be blended

The independence of the three specialist signals is the source of the early
deformation signal. A route may still appear factually correct while logical
consistency is falling. It may still appear fast and admissible while coherence
is breaking. A single blended average hides this divergence because the
deteriorating dimension is diluted by the dimensions that remain healthy.

Fact, Logic, and Coherence must therefore not be collapsed into another scalar
confidence score before they reach the routing decision. Doing so would recreate
the same problem that v3 identified with C_success: a slow-moving average that
detects degradation only after it has progressed far enough to dominate the
blend. The coordinator's job is to measure the geometric relationship among the
three signals and produce a shape measure that reflects their current agreement
or divergence. That shape measure is what shape_integrity carries. The
separation is the value; destroying it in the aggregation step would make the
tetrahedral layer redundant.

---

## Integration sites

Five specific sites in the existing routing stack require attention when the
tetrahedral layer is connected to the router. These are not design decisions
about how the connection is made; they are identifications of where flattening
currently occurs or where new architectural joints are needed.

**1. PRE — Pattern Recognition Engine**

PRE must preserve task-pattern information in S_pat without absorbing tetrahedral
state into it. S_pat is derived from the arriving task, not from the current
structural condition of the substrate. If PRE begins encoding coordinator output
or role health into S_pat, it conflates the identity of the task with the current
condition of the architecture, which are independent facts. The tetrahedral state
does not change which pattern class a task belongs to; it changes whether the
route for that pattern class is currently trustworthy. Those are different
questions and must remain separate.

**2. ARD entry — Adaptive Routing Database**

The ARD entry must carry a live structural field, provisionally named
shape_integrity, alongside the existing route-level fields. This field has
different provenance from C_success: it is written by the tetrahedral coordinator
or recovery layer, not by SMS. It carries an observation timestamp and epoch
identifier reflecting when the coordinator last observed the substrate and under
which structural cycle, not when the last route outcome was recorded. The ARD
entry already distinguishes between fields with different update cadences and
sources — p_opt is updated by full analysis, C_success by SMS, depreciation
state by the state machine. shape_integrity is a peer field with its own source,
its own write policy, and its own epoch binding. That provenance must be explicit
in any future ARD schema revision.

**3. SMS — Success Measurement System**

SMS continues to calculate route-level performance evidence and updates C_success
accordingly. It must not absorb shape_integrity into C_success. The SMS outcome
formula combines latency, admissibility, degradation, and stability into a single
route-performance score, and this is appropriate for what SMS is measuring. But
structural condition is not route performance. Feeding shape_integrity into the
SMS blend would cause the slow ALPHA decay to attenuate the structural signal
before it reaches the gate, which defeats the purpose of having it. SMS and the
coordinator are parallel observers reporting different things; the router needs
to read both, not merge them before reading.

**4. IBM — Intelligent Bypass Mechanism**

The IBM gate stack currently has four peer authority conditions: confidence,
structural cost, recovery context, and anti-oscillation. A fifth peer condition
— the structural integrity of the tetrahedral substrate — belongs in this stack.
The gate reads shape_integrity from the ARD entry and withholds bypass authority
if the structural observation is absent, epoch-mismatched, or outside declared
bounds. This gate is a peer, not a modifier to an existing gate, because the
condition it enforces is architecturally independent: a route may pass all four
existing gates while the substrate is deforming, and a route may fail the shape
gate while its confidence is high and its latency is within bounds. The
independence of the conditions is what gives each gate its meaning.

The architectural reason for this gate is direct. A route may retain high
historical confidence while the tetrahedral structure beneath it has already
begun to deform. C_success accumulates evidence slowly by design, and the SMS
stability score measures route-outcome variance rather than structural divergence
among roles. The shape gate exists to revoke bypass authority before slow scalar
confidence decay detects the problem. Without it, the router cannot act on early
structural warning; it can only respond after degradation has propagated far
enough into route outcomes to drain C_success below T_bypass.

**5. Recovery context**

The current recovery context gate reads elapsed time relative to a declared
recovery event. It was redesigned in v2 to require earned requalification rather
than a fixed blackout timer, which was a meaningful improvement. But neither the
timer nor the requalification mechanism responds to structural deformation in
real time. The recovery context layer must be capable of responding to structural
deformation as a trigger condition, not only to elapsed time or a previously
declared recovery event. Structural deformation detected by the coordinator
should be able to initiate a recovery-sensitive state in the routing layer
without waiting for the recovery event to be formally declared and timestamped.
The mechanism for that connection is not specified here; establishing it requires
architecture-level design work on both the recovery layer and the router.

---

## What v3 established

V3 tested the bounded routing mechanism in a flat harness without live
tetrahedral structural input. The four arms operated on a synthetic task stream
with route quality encoded directly in the manifest. No coordinator produced a
shape measure. No role-separated signals fed the routing decision. The router
had access only to route-level confidence, latency, cost, and the requalification
state machine.

V3 found that scalar confidence decay did not revoke unsafe post-promotion
authority faster than the simpler comparison arms. In all 15 eligible borderline
route instances, the first gate to block bypass after degradation onset was the
confidence gate. The depreciation, cost, anti-oscillation, and cooldown gates
did not fire first in any instance. Arm D accumulated 126 matched wrong bypasses
in the primary window, compared with 105 for Arm B and 123 for Arm C. The
pre-declared verdict condition was not met.

V3 did not test whether tetrahedral deformation can provide an earlier revocation
signal. The flat harness had no mechanism by which role-separated structural
information could reach the bypass gate. The test was a valid and necessary
isolation of the router on its own, and it identified the specific limitation of
scalar confidence as the sole detection mechanism. It was not a test of the full
architecture described in this document.

The v3 NOT SUPPORTED verdict remains unchanged. Nothing in this document revises
or reframes that result. V3 showed what happens when the router operates without
the structural substrate it was designed to sit on. It did not show that the
tetrahedral structure is unnecessary; it showed what is missing when it is
absent.

---

## Design constraints for future work

These constraints apply to any mechanism that claims to implement tetrahedral
routing. They are stated in advance, before any v4 design work begins, to prevent
future experiments from repeating the structural problem v3 identified.

No future route-authority mechanism may treat shape_integrity as merely another
weighted SMS component. If shape_integrity enters the SMS blend and is compressed
into C_success, the independence that gives it value is destroyed. The constraint
is not about the weight assigned; it is about the architecture. shape_integrity
must reach the IBM gate as its own condition, readable and enforceable
independently of the confidence gate.

No future experiment may claim to test tetrahedral routing unless live
role-separated or coordinator-derived structural state actually participates in
the bypass decision. A simulation that encodes structural health only in route
quality — as v3's manifest did — is a flat harness, however the parameters are
labeled. The participation of actual Fact, Logic, Coherence, and coordinator
signals in the gate decision is the defining feature of a tetrahedral routing
test, not the number of patterns or the shape of the degradation schedule.

No threshold, shape formula, or deformation metric is approved by this document.
The right values for an integrity bound, the method by which angular distortion
or role imbalance is quantified, and the relationship between coordinator output
and the binary bypass condition are all open design questions. Choosing them
requires architecture-level work that has not yet been done.

A stale or missing shape observation may never preserve bypass authority. The
router must fail closed when the structural record is absent, unverifiable,
epoch-mismatched, or beyond its valid freshness window. Absence of a current
structural observation is not evidence of a healthy substrate; it is an unknown,
and the router treats unknowns as non-bypass conditions.

A scalar gate result may not erase the underlying structural evidence from which
it was derived. If the coordinator computes a pass/fail or compact integrity
measure for the router's use, the role-separated and geometric evidence that
produced it must be retained in a form sufficient for audit, diagnosis, and
recovery guidance. A scalar output that has discarded the Fact, Logic, and
Coherence components cannot identify which role is deforming or inform the
recovery layer about where reconstruction is needed.

No structural condition may authorize a route unless its scope applies to that
route. A structural observation covering a region of the substrate that the
route in question does not depend on cannot serve as authorization for that
route. The gate logic must be able to verify applicability, not only validity,
of every structural condition it reads.

The next step after this document is an architecture-level definition of
candidate tetrahedral deformation measures: what the coordinator observes, how
it computes a shape condition from role-separated signals, and how that condition
is expressed in a form the router can read and act on. That definition precedes
any simulation implementation. No v4 harness should be written until the
deformation measure has a declared form, the scope and applicability rules have
been specified, and the integration sites in this document have been addressed
at the schema level.
