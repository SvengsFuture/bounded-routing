EABC Implementation Profile
Bounded Routing V5 — Independent Structural Witness
Profile ID: EABC-IP-BR-V5-001
Profile Version: 1.0
Profile Status: Frozen
Mapped Implementation: Bounded Routing V5 — Independent Structural Witness
EABC Architecture: Stanislav Levarsky
Bounded Routing V5 Architecture: Stephen Gettel
Implementation Profile: Joint architectural mapping by Stanislav Levarsky and Stephen Gettel

Frozen V5 Implementation Reference: 154b389af2d3ec54f50ae7216dea35c2c065b39b
Profile Content SHA-256: b87df53bd45f9d5ea296efb1cb93292b9d41fe115f02c8cde1484f55eb9b90c4

1. Status and Scope
This document is an EABC Implementation Profile describing how the existing Bounded Routing V5 implementation maps against the EABC property model.

The profile is descriptive of the existing Bounded Routing V5 implementation.

It:

does not modify Bounded Routing V5;
does not add EABC mechanisms to Bounded Routing;
does not reinterpret unsupported V5 capabilities as present;
preserves the original V5 implementation boundary;
preserves the mapping statuses Conditional, Partial, Satisfied, and Not Claimed;
does not constitute a claim of full EABC conformance.
The purpose of this profile is to record an independent architectural mapping between an existing implementation and the EABC execution-authority property model.

2. Introduction
Bounded Routing was independently developed around execution-time route admissibility under live structural constraints.

V5 introduces independently produced and cryptographically authenticated structural evidence outside the governed routed-agent process.

The resulting V5 architecture provides a chain of:

Trusted Structural Source
↓
Independent Structural Witness
↓
Signed Structural Record
↓
Authority Gate
↓
Structural Authority
↓
Route Admissibility
↓
Bypass Authority

Bounded Routing V5 was not designed as an implementation of EABC.

The EABC mapping was performed against the existing V5 architecture after both architectural models existed independently.

The mapping therefore evaluates observable properties and boundaries rather than assuming architectural equivalence.

3. Architectural Overview
The V5 execution-authority path is bounded as follows:

a trusted structural source provides structural observations;
an independent structural witness observes and records the relevant structural state;
the witness produces a signed structural record;
the authority gate verifies the record and applicable structural conditions;
structural authority is established or refused;
route admissibility is evaluated;
bypass authority is granted or refused.
The V5 boundary terminates at execution eligibility / bypass authority.

V5 does not model the externally effective execution of an action after bypass authority has been established.

4. Execution Authority Boundary
For purposes of this profile, the V5 authority boundary terminates at the point where the system establishes or refuses authority for the governed route to proceed.

This distinction is normative for the mapping:

Structural observation
↓
Signed structural evidence
↓
Verified authority decision
↓
Route admissibility
↓
Bypass authority
↓
[ V5 boundary terminates ]
↓
External execution
↓
Externally effective commit

The final two stages are not modeled by frozen V5.

Therefore:

Bypass authority is not proof of execution and is not equivalent to an externally effective execution commit.

5. Terminology Note: V5 Internal Commit vs EABC Execution Commit
V5 contains an internal atomic commit associated with replay and watermark state.

That internal commit establishes the state transition required for the V5 gate's replay/watermark processing.

It is not an externally effective execution commit in the EABC sense.

The two concepts must not be conflated:

V5 internal replay/watermark commit
≠
EABC externally effective execution commit

This distinction is preserved throughout the mapping.

6. EABC Property Mapping
Each EABC property is mapped using the common profile structure:

Property / Claim → Mapping → Assumptions → Gap → Evidence

P1 — Independent Execution Authority
Property / Claim
Execution authority must be established independently of the governed initiator such that the initiator cannot manufacture, alter, widen, substitute, or replay the authority evidence used to establish permission.

Mapping
Status: Conditional

V5 separates the structural witness and signing authority from the governed routed-agent process.

Under the declared V5 threat model, the routed agent cannot manufacture, alter, widen, substitute, or replay a structural record accepted by the authority gate.

This establishes an independent authority path at the software/process level.

Assumptions
The mapping assumes that the witness process, signing authority, and verification authority remain outside the routed agent's compromise domain.

V5 does not claim hardware-enforced trust-domain isolation.

V5 also does not claim that the witness or signing authority remains trustworthy after compromise of its host or signing authority itself.

Gap
The V5 implementation does not establish the stronger EABC property of hardware-enforced independence or continued authority integrity after compromise of the witness host or signing authority.

Evidence
V5's independent witness architecture, signed structural records, authority gate verification, and declared threat model establish the claimed separation within the modeled boundary.

P2 — Complete Mediation
Property / Claim
Every execution path capable of producing the protected effect must be subject to the applicable authority boundary.

Mapping
Status: Conditional

Within the bounded routing model, bypass authority is mediated by the authority gate.

Invalid, missing, stale, replayed, source-invalid, scope-invalid, epoch-invalid, or structurally invalid evidence cannot produce valid bypass authority through the modeled gate.

Assumptions
The mapping applies to the paths represented by the Bounded Routing model.

Gap
The repository does not establish that every possible path to an externally effective consequence in a real deployment necessarily crosses the V5 authority gate.

Therefore, V5 does not establish universal mediation of all external effect paths.

Evidence
The V5 authority gate controls the modeled route-admissibility and bypass-authority decision and rejects invalid authority conditions.

P3 — Deterministic Commit Semantics
Property / Claim
The authority boundary must have deterministic semantics for accepting or rejecting the transition presented to it.

Mapping
Status: Satisfied within the modeled authority boundary; external execution commit semantics not claimed.

V5 defines deterministic processing for structural observation, authority evaluation, route admissibility, bypass authority, and rejection conditions.

The V5 architecture also models authority state, failure, revocation, and recovery behavior.

Assumptions
The claim is limited to the modeled V5 authority boundary.

Gap
V5 does not model the externally effective execution commit.

Its internal replay/watermark atomic commit is an authority-state transition and must not be interpreted as the commit of an external protected effect.

Evidence
The V5 gate's defined verification sequence, deterministic failure conditions, replay/watermark state transition, route admissibility decision, and bypass-authority outcome provide evidence within the modeled authority boundary.

P4 — Context Binding
Property / Claim
Authority evidence must be bound to the relevant execution context so that evidence from another context cannot be substituted for the applicable context.

Mapping
Status: Satisfied within the V5 boundary

The signed structural record binds relevant contextual information including:

source identity;
observer identity and type;
signing key identity;
source sequence;
source observation time;
observer sequence;
signing time;
structural epoch;
scope type;
scope identifier;
structural evidence;
shape integrity.
The authority gate verifies the applicable identity, epoch, scope, temporal, replay, freshness, structural, and route conditions.

Assumptions
The mapping relies on the V5 cryptographic and authority-verification assumptions.

Gap
No additional gap is identified within the V5 modeled boundary.

Evidence
The signed structural record and gate verification logic bind the authority decision to the relevant source, scope, epoch, sequence, timing, and structural context.

P5 — State Binding
Property / Claim
The authority decision must remain bound to the state for which authority was established through the point at which the protected effect becomes effective.

Mapping
Status: Partial

V5 strongly binds the authority decision to the structural state observed by the independent witness.

The chain established by V5 is:

Observed structural state
↓
Signed structural evidence
↓
Verified authority decision

This is a strong state-binding property within the V5 authority boundary.

Assumptions
The mapping assumes the V5 source and witness provide truthful structural observations within their declared trust model.

V5 does not claim physical sensor fidelity or independent proof that asserted source inputs correspond to physical reality.

Gap
V5 does not establish the second half of the EABC state-binding requirement:

Verified authority decision
↓
Externally effective commit
↓
Proof that the same authorized state still governed the consequence

There is no V5 commit-time mechanism proving that the state governing the eventual external consequence remained the state against which authority was granted.

The key distinction is:

A witnessed and authorized state is not equivalent to proven commit-time state.

Evidence
Source sequence, observer sequence, structural epoch, structural evidence, shape integrity, observation timing, and signing timing provide strong binding between observed state and the V5 authority decision.

The missing evidence is the commit-time binding to an externally effective consequence.

P6 — Evidence Integrity
Property / Claim
Evidence used to establish authority must be integrity-protected and verifiable under the declared trust model.

Mapping
Status: Satisfied under declared V5 cryptographic assumptions

V5 uses canonical encoding and Ed25519-signed structural records.

Independent canonical encoding verification and known-answer validation support deterministic verification of the signed evidence.

Assumptions
The mapping assumes that:

the witness signing authority is outside the governed agent's compromise domain;
the signing authority remains uncompromised;
the verifier correctly implements the specified verification process.
Gap
No additional cryptographic integrity gap is identified within the declared V5 threat model.

The broader limitation remains that cryptographic integrity of an asserted source observation does not establish physical truth of that observation.

Evidence
Canonical encoding, Ed25519 signatures, signature verification, and V5 validation behavior provide the relevant evidence-integrity mechanism.

P7 — Evidence Correlation
Property / Claim
Evidence must support deterministic reconstruction of a completed protected operation across the relevant authority and execution lifecycle.

Mapping
Status: Partial

V5 contains substantial evidence covering:

structural observations;
signed witness records;
authority-gate evaluation;
route authority;
failure conditions;
revocation;
scar state;
cell state;
recovery.
The structural provenance path is therefore substantial.

Assumptions
The mapping considers the evidence actually represented by the frozen V5 architecture and does not infer an external execution lifecycle that V5 does not model.

Gap
V5 does not contain an intrinsically protected identifier chain that allows one completed external operation to be mechanically traversed as:

External effect
↓
Execution commit
↓
Gate decision
↓
Signed witness record
↓
Originating observation

In particular, V5 does not establish a complete integrity-protected lifecycle/command/execution identifier or equivalent correlation mechanism joining the entire chain.

The external effect commit is outside the V5 execution model.

Therefore, a complete EABC evidence chain would require inference across the V5 boundary rather than deterministic traversal from intrinsically correlated evidence.

Evidence
V5 provides protected identity, sequence, epoch, scope, timing, structural evidence, witness records, gate outcomes, and related authority/failure state.

These establish substantial provenance within the structural authorization path but do not constitute a complete protected effect-to-observation correlation chain.

P8 — Failure Semantics
Property / Claim
Invalid, missing, stale, conflicting, or otherwise insufficient authority evidence must not be interpreted as successful authority.

Mapping
Status: Satisfied

V5 fails closed with respect to invalid authority conditions.

Missing, invalid, stale, replayed, mismatched, structurally invalid, or otherwise failed evidence does not become successful bypass authority.

V5 distinguishes evidence invalidity, revocation, structural failure, and recovery behavior.

Assumptions
The mapping applies to the failure conditions represented by the frozen V5 authority model.

Gap
No additional gap is identified within the modeled V5 authority boundary.

Evidence
The authority gate produces explicit failed conditions and prevents bypass authority when required verification conditions are not satisfied.

Missing evidence is not treated as successful execution authority.

P9 — Implementation Neutrality
Property / Claim
The EABC property model must be evaluable against an implementation without requiring that implementation to adopt EABC's internal architecture or terminology.

Mapping
Status: Satisfied as an independent mapping result

Bounded Routing V5 was independently developed and does not depend on EABC terminology or architecture.

The observable V5 behavior can therefore be evaluated against EABC properties without requiring architectural equivalence.

The mapping records where each EABC property is supported, conditional, partial, or not claimed.

Assumptions
This result is limited to the independence of the architectural models and the ability to evaluate their observable properties.

Gap
No architectural equivalence between EABC and Bounded Routing is implied.

Evidence
The independent origin of Bounded Routing V5 and the property-by-property mapping demonstrate that the EABC property model can be evaluated against an independently developed implementation without requiring that implementation to reproduce EABC architecture.

P10 — Extensible Profiles
Property / Claim
The implementation should support explicit profiles that define applicable execution-authority properties without requiring the core architecture to be redesigned.

Mapping
Status: Not Claimed

Frozen V5 does not contain an EABC profile and was not designed around EABC profile semantics.

This document is a new external mapping artifact.

Its existence does not retroactively establish profile extensibility as a native V5 capability.

Assumptions
The assessment is against the frozen V5 implementation, not against possible future extensions.

Gap
No native V5 capability corresponding to the EABC profile mechanism is claimed.

Evidence
The frozen V5 architecture does not define an EABC profile mechanism.

7. Evidence Mapping
EABC Evidence Category	V5 Evidence
Identity	Source identity, observer identity/type, signing-key identity
State	Source sequence, observer sequence, structural epoch, structural evidence, shape integrity, source observation time, witness signing time
Context	Scope type and scope identifier, together with identity and epoch
Integrity	Canonical signed records using Ed25519 under the declared threat model
Authority	Gate-produced structural-authority and bypass-authority outcomes, including failure step/reason
Execution	Frozen V5 does not evidence an external effect being attempted or committed
Correlation	Protected identity, sequence, epoch, scope, and timing provide provenance within the structural path, but not a complete external-effect-to-observation lifecycle
External Commit	Not modeled by frozen V5
Important: bypass authority MUST NOT be interpreted as execution evidence.

8. Execution Semantics
The modeled V5 lifecycle is:

Structural observation
↓
Witness construction
↓
Signed structural record
↓
Gate verification
↓
Structural authority
↓
Route admissibility
↓
Bypass authority / refusal

The lifecycle terminates at execution eligibility.

Frozen V5 does not model:

external execution attempt;
external execution commit;
proof of externally effective consequence;
commit-time revalidation of the structural state;
evidence that the authorized state remained applicable at the external commit.
9. Failure Semantics
V5 uses fail-closed authority semantics.

Failure of required verification conditions prevents the establishment of bypass authority.

Relevant failure classes include:

invalid evidence;
missing evidence;
stale evidence;
replay;
source mismatch;
scope mismatch;
epoch mismatch;
structural invalidity;
revocation;
structural failure;
recovery conditions.
A failed verification condition does not become successful authority.

This is distinct from proving that no external effect occurred after a failed authority decision; that latter property lies outside the frozen V5 execution model.

10. Conformance Statement
This profile establishes substantial correspondence between the frozen Bounded Routing V5 implementation and the EABC property model.

It does not establish full EABC conformance.

The resulting status is:

Property	Status
P1 — Independent Execution Authority	Conditional
P2 — Complete Mediation	Conditional
P3 — Deterministic Commit Semantics	Satisfied within the modeled authority boundary
P4 — Context Binding	Satisfied within V5 boundary
P5 — State Binding	Partial
P6 — Evidence Integrity	Satisfied under declared V5 cryptographic assumptions
P7 — Evidence Correlation	Partial
P8 — Failure Semantics	Satisfied
P9 — Implementation Neutrality	Satisfied as an independent mapping result
P10 — Extensible Profiles	Not Claimed
11. Known Limitations and Assumptions
The mapping preserves the following limitations of frozen V5:

No hardware-enforced trust-domain isolation is claimed.
No resistance to compromise of the witness host or signing authority is claimed.
Universal mediation of every possible real-world path to an external effect is not established.
External effective execution commit is outside the V5 model.
V5 does not prove that the authorized state remains applicable at the external commit.
V5 does not provide a complete intrinsically protected correlation chain from external effect through execution commit, gate decision, witness record, and originating observation.
V5 evidence and state are memory-resident within the frozen harness and are not claimed to provide restart persistence.
Structural source evidence represents asserted inputs; V5 does not claim independent physical sensing fidelity.
These limitations are intentionally preserved rather than being normalized away through the EABC mapping.

12. Mapping Result
The purpose of this profile is not to demonstrate that Bounded Routing V5 reproduces EABC.

The result is that an independently developed architecture can be meaningfully evaluated against the EABC property model without changing either architecture.

The most significant boundaries identified by the mapping are:

P5 — State Binding
V5 establishes a strong relationship:

Observed structural state
↓
Signed evidence
↓
Verified authority decision

but does not establish:

Verified authority decision
↓
Externally effective commit
↓
Proof of same governing state

These are therefore the clearest boundaries between the V5 authority model and the execution-authority boundary described by EABC.

P7 — Evidence Correlation
V5 provides substantial authority and provenance evidence, but does not establish an intrinsically protected complete lifecycle correlation:

External effect
↓
Execution commit
↓
Gate decision
↓
Signed witness
↓
Originating observation

The mapping intentionally preserves these boundaries.

13. Cross-Repository Provenance
This profile is intended to exist as corresponding copies in the Bounded Routing and EABC repositories.

The copies are identified by the stable profile identity:

Profile ID: EABC-IP-BR-V5-001
Profile Version: 1.0

The profile content may additionally be identified by its SHA-256 digest:

Profile Content SHA-256: b87df53bd45f9d5ea296efb1cb93292b9d41fe115f02c8cde1484f55eb9b90c4

The frozen Bounded Routing implementation is independently identified by:

Frozen V5 Implementation Reference:
154b389af2d3ec54f50ae7216dea35c2c065b39b

The repository copies should be referenced by repository path and profile identity rather than by mutually dependent commit hashes.

This avoids a circular provenance dependency in which the Bounded Routing copy would need to contain the final EABC-repository commit hash while the EABC copy simultaneously needs to contain the final Bounded Routing commit hash.

Final repository commit identifiers may be recorded separately as release provenance after both repository copies have been committed.

14. Freeze Statement
Once the frozen V5 implementation reference and profile content digest are populated, this document represents the frozen EABC Implementation Profile for:

Bounded Routing V5 — Independent Structural Witness

The technical mapping, property statuses, identified gaps, and stated limitations are not to be changed merely to improve the apparent conformance result.

Any future changes to either implementation or mapping should produce a new profile version or an explicitly versioned amendment.

