# V5 Independent Structural Witness — Executable Test Matrix v1.6 (Final, Self-Contained)

Supersedes v1.0–v1.5 in full. Companion: Harness Profile v1.5. Every category reproduced in full — no row references a superseded version.

## Legend

Construction modes (Harness Profile §6): `unsigned`, `payload-tampered`, `signature-corrupted`, `unauthorized-signer`, `valid-resubmit`, `valid-alternate-context`, `fault-injected-signer`, `gate-fault-injected`, `encoder-direct`, `malformed`, `transport-varied`. **Every gate-path test row names its starting fixture** (`UNCONSUMED_BASELINE`, `CONSUMED_BASELINE`, or `E9_SOURCE_BINDING_FIXTURE`). Component-level and construction-level tests that never submit a record through the gate (B-Encoder, L, C, C-Witness, CW, CW-Boundary, G1, I) state `Fixture = N/A`. **SA** = StructuralAuthority, **BA** = BypassAuthority, **Wm** = watermark behavior.

---

## Category A — Signature and Witness Authentication

| ID | Attack | Construction | Fixture | Expected fail step | SA | BA | Wm |
|---|---|---|---|---|---|---|---|
| A1 | No `signature` component at all | unsigned | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| A2 | Signature stripped from an otherwise decodable envelope | unsigned | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| A3 | Well-formed signature field, corrupted bytes (payload untouched) | signature-corrupted | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| A4 | Genuinely valid signature from a second, real, unregistered Ed25519 key pair; payload correctly names its own `key_id="key-2"` (unregistered under the standard baseline) | unauthorized-signer | UNCONSUMED_BASELINE | 4 | 0 | 0 | no-advance |
| A5 | Valid registered key; `observer_id` mismatched to registration | payload-tampered | UNCONSUMED_BASELINE | 4 | 0 | 0 | no-advance |
| A6 | Valid registered key; `observer_type` mismatched to registration | payload-tampered | UNCONSUMED_BASELINE | 4 | 0 | 0 | no-advance |
| A7 | Genuinely-keyed signer signs a record claiming an unbound observer identity | fault-injected-signer | UNCONSUMED_BASELINE | 4 | 0 | 0 | no-advance |

---

## Category B — Gate-Path Field Mutation

| ID | Field altered | Construction | Fixture | Expected fail step | SA | BA | Wm |
|---|---|---|---|---|---|---|---|
| B1 | `fact_evidence` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B2 | `logic_evidence` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B3 | `coherence_evidence` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B4 | `shape_integrity` (flip) | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B5 | `source_id` → schema-valid but unregistered id | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B6 | `source_sequence` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B7 | `source_observation_time_ns` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B8 | `observer_sequence` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B9 | `witness_sign_time_ns` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B10 | `structural_epoch` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B11 | `scope_type` → `"system"` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B12 | `scope_id` | payload-tampered | UNCONSUMED_BASELINE | 5 | 0 | 0 | no-advance |
| B13 | `schema_version` → any value ≠ `"v5.0"` | payload-tampered | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| B14 | `observer_id` → schema-valid but unregistered id | payload-tampered | UNCONSUMED_BASELINE | 4 | 0 | 0 | no-advance |
| B15 | `observer_type` → `"auxiliary_observer"` | payload-tampered | UNCONSUMED_BASELINE | 4 | 0 | 0 | no-advance |
| B16 | `key_id` → schema-valid but unregistered id | payload-tampered | UNCONSUMED_BASELINE | 4 | 0 | 0 | no-advance |

## Category B-Encoder — Canonical Sensitivity (Fixture = N/A, all rows)

| ID | Field | Construction | Expected result |
|---|---|---|---|
| BE1 | `schema_version` | encoder-direct | Different canonical bytes |
| BE2 | `source_id` | encoder-direct | Different canonical bytes |
| BE3 | `observer_id` | encoder-direct | Different canonical bytes |
| BE4 | `observer_type` | encoder-direct | Different canonical bytes |
| BE5 | `key_id` | encoder-direct | Different canonical bytes |
| BE6 | `source_sequence` | encoder-direct | Different canonical bytes |
| BE7 | `source_observation_time_ns` | encoder-direct | Different canonical bytes |
| BE8 | `observer_sequence` | encoder-direct | Different canonical bytes |
| BE9 | `witness_sign_time_ns` | encoder-direct | Different canonical bytes |
| BE10 | `structural_epoch` | encoder-direct | Different canonical bytes |
| BE11 | `scope_type` | encoder-direct | Different canonical bytes |
| BE12 | `scope_id` | encoder-direct | Different canonical bytes |
| BE13 | `fact_evidence` | encoder-direct | Different canonical bytes |
| BE14 | `logic_evidence` | encoder-direct | Different canonical bytes |
| BE15 | `coherence_evidence` | encoder-direct | Different canonical bytes |
| BE16 | `shape_integrity` | encoder-direct | Different canonical bytes |

## Category L — Canonical Known-Answer Vector (Fixture = N/A, all rows)

Independently verified: both reviewer and author recomputed the seed digest, derived Ed25519 public key, 140-byte canonical payload, its SHA-256 digest, and the signature, and all values matched.

| ID | Check | Expected value (Harness Profile §13) |
|---|---|---|
| L1 | Seed → derived Ed25519 public key | Matches frozen reference exactly |
| L2 | Baseline record → canonical payload length | Exactly 140 bytes |
| L3 | Baseline record → canonical payload SHA-256 | Matches frozen reference digest exactly |
| L4 | Canonical payload signed with derived private key → signature | Matches frozen reference signature exactly |
| L5 | Witness-side encoder and gate-side encoder, run independently on the same baseline field values | Byte-identical canonical output |

---

## Category C — Source Snapshot Integrity (Fixture = N/A, all rows)

| ID | Attack | Expected outcome |
|---|---|---|
| C1 | Direct write attempt to the source snapshot | Refused at interface level |
| C2 | Acquire/duplicate the source writer endpoint | Acquisition fails |
| C3 | Replace the witness's read endpoint | No effect |
| C4 | Influence via shared mutable state | No effect on any of the 9 source fields |
| C5 | Influence via route outcomes | No effect |
| C6 | Influence via task latency | No effect |
| C7 | Influence via route confidence / SMS state | No effect |
| C8 | Influence via environment variables | No effect |
| C9 | Influence via file writes / temp files | No effect |
| C10 | Influence via command-line arguments | No effect |
| C11 | Historical read-back attempt | No mechanism exists; fails structurally |
| C12 | Torn-snapshot under concurrent update | Witness never observes a mixed-sequence snapshot |

## Category C-Witness — shape_integrity Derivation Isolation (Fixture = N/A, all rows)

| ID | Attack | Expected outcome |
|---|---|---|
| CW1 | Vary route outcomes, hold evidence fixed | Unchanged |
| CW2 | Vary task latency, hold evidence fixed | Unchanged |
| CW3 | Vary route confidence/SMS state, hold evidence fixed | Unchanged |
| CW4 | Vary env/file/args, hold evidence fixed | Unchanged |
| CW5 | Determinism: identical evidence, repeated computation | Identical output every time |

## Category CW-Boundary — Frozen Rule Threshold Tests (Fixture = N/A, all rows)

| ID | Setup | Expected `shape_integrity` |
|---|---|---|
| CW6 | All three evidence fields exactly `500,000` | `true` (inclusive `>=`) |
| CW7 | `fact_evidence=499,999`, others `1,000,000` | `false` |
| CW8 | `logic_evidence=499,999`, others `1,000,000` | `false` |
| CW9 | `coherence_evidence=499,999`, others `1,000,000` | `false` |

---

## Category D — Replay and Sequence Manipulation (constructions corrected)

| ID | Attack | Construction | Fixture | Expected fail step | Failing predicate | SA | BA | Wm |
|---|---|---|---|---|---|---|---|---|
| D1 | Exact replay of accepted record | valid-resubmit | CONSUMED_BASELINE | 10 | SourceReplaySafe AND ObserverReplaySafe | 0 | 0 | no-advance |
| D2 | Same `source_sequence`, new `observer_sequence` — duplicate-record pair generated via the shared hook (Profile §6) from one snapshot | fault-injected-signer (duplicate-record hook) | CONSUMED_BASELINE | 10 | SourceReplaySafe | 0 | 0 | no-advance |
| D3 | Same `observer_sequence`, new `source_sequence` — witness reusing an observer_sequence for a new snapshot violates its own strict-increase invariant; not naturally producible | fault-injected-signer | CONSUMED_BASELINE | 10 | ObserverReplaySafe | 0 | 0 | no-advance |
| D4 | Lower `source_sequence` (requires re-signing historical source content the witness cannot retrieve), new/valid `observer_sequence` | fault-injected-signer | CONSUMED_BASELINE | 10 | SourceReplaySafe | 0 | 0 | no-advance |
| D5 | Lower `observer_sequence` (violates witness's own monotonicity), new/valid `source_sequence` | fault-injected-signer | CONSUMED_BASELINE | 10 | ObserverReplaySafe | 0 | 0 | no-advance |
| D6 | Fresh `observer_sequence` wrapping consumed source content — duplicate-record pair via the shared hook | fault-injected-signer (duplicate-record hook) | CONSUMED_BASELINE | 10 | SourceReplaySafe | 0 | 0 | no-advance |
| D7 | Fresh `source_sequence` paired with reused `observer_sequence` — violates witness monotonicity; not naturally producible | fault-injected-signer | CONSUMED_BASELINE | 10 | ObserverReplaySafe | 0 | 0 | no-advance |
| D8a | Two signed records from one snapshot via the duplicate-record hook, submitted sequentially | fault-injected-signer (duplicate-record hook) | UNCONSUMED_BASELINE (first) → CONSUMED_BASELINE-equivalent (second) | second: 10 | SourceReplaySafe (second) | first: 1 / second: 0 | per route / 0 | first: advance, second: no-advance |
| D8b | Two signed records from one snapshot via the duplicate-record hook, concurrent, barrier before step 10 | fault-injected-signer (duplicate-record hook) | UNCONSUMED_BASELINE | loser: 10 | SourceReplaySafe (loser) | exactly one: 1, other: 0 | winner's route-dependent / loser: 0 | exactly one advance |

**Note on this category's revised constructions:** none of these weaken the tests — they correctly reclassify D3–D7 and H6's second record as gate defenses against *authentic but defective witness output* (a compromised or buggy witness signing anomalous content) rather than ordinary Agent Domain replay of otherwise-normal records. D1 remains the one pure case of straightforward exact replay.

---

## Category E — Delivery Order, Staleness, Scope/Epoch

| ID | Attack | Construction | Fixture | Expected fail step | Failing predicate | SA | BA | Wm |
|---|---|---|---|---|---|---|---|---|
| E1 | Out-of-order delivery of two honestly-produced records (an honest witness reading an honestly-advancing single source necessarily moves both sequences together, so the earlier record is lower on both) | valid-resubmit | CONSUMED_BASELINE | 10 | SourceReplaySafe AND ObserverReplaySafe (both fail together — isolating either predicate alone requires the fault-injected constructions in D4/D5, not ordinary out-of-order delivery) | 0 | 0 | no-advance (rejected one) |
| E2 | Same as E1 — retained as a distinct row for traceability to the "observer sequence" phrasing in the frozen attack classes, but mechanically identical to E1 under honest single-source/single-witness operation | valid-resubmit | CONSUMED_BASELINE | 10 | SourceReplaySafe AND ObserverReplaySafe | 0 | 0 | no-advance (rejected one) |
| E3 | Retain-and-release earlier snapshot | — | N/A | N/A — collapses to C1–C3, C11 | — | — | — | — |
| E4 | Fresh sign time, stale source time (injected clock) | valid-resubmit | UNCONSUMED_BASELINE | 11 | Fresh | 0 | 0 | advance |
| E5 | Prior-epoch replay | valid-resubmit | UNCONSUMED_BASELINE (new epoch) | 7 | EpochMatch | 0 | 0 | no-advance |
| E6 | A second, genuinely and honestly produced record for `scope_id="route-B"`, presented against a gate context currently requesting `scope_id="route-A"` | valid-alternate-context | UNCONSUMED_BASELINE | 8 | ScopeMatch | 0 | 0 | no-advance |
| E7 | A genuinely signed `scope_type="route"` record presented as `scope_type="system"` authority | valid-alternate-context | UNCONSUMED_BASELINE | 8 | ScopeMatch | 0 | 0 | no-advance |
| E8 | A genuinely signed record whose `source_id` names a source not in the gate's registry | fault-injected-signer | UNCONSUMED_BASELINE | 6 | SourceBindingValid | 0 | 0 | no-advance |
| E9 | A registered source (`source-1`) presented through a registered but unbound witness (`witness-2`/`key-2`) | fault-injected-signer + E9_SOURCE_BINDING_FIXTURE | E9_SOURCE_BINDING_FIXTURE | 6 | SourceBindingValid | 0 | 0 | no-advance |

---

## Category F — Schema, Encoding, Temporal Sanity

| ID | Attack | Construction | Fixture | Expected fail step | SA | BA | Wm |
|---|---|---|---|---|---|---|---|
| F1 | Bytes that do not decode as JSON syntax at all | malformed (step-1) | UNCONSUMED_BASELINE | 1 | 0 | 0 | no-advance |
| F2a | Duplicate top-level envelope key | malformed (step-2) | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| F2b | Duplicate field name inside `payload` | malformed (step-2) | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| F3 | Unsupported `schema_version` | malformed (step-2) | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| F4 | Required field missing | malformed (step-2) | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| F5 | Any unrecognized field, envelope or payload level | malformed (step-2) | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| F6 | Meaning-preserving transport variance: reordered keys, whitespace | transport-varied | UNCONSUMED_BASELINE | none — must pass | 1 | per route | advance |
| F7 | `source_observation_time_ns` later than `witness_sign_time_ns` | fault-injected-signer | UNCONSUMED_BASELINE | 9 | 0 | 0 | no-advance |
| F8 | `witness_sign_time_ns` future relative to gate clock | fault-injected-signer | UNCONSUMED_BASELINE | 9 | 0 | 0 | no-advance |
| F9 | `source_observation_time_ns` future relative to gate clock | fault-injected-signer | UNCONSUMED_BASELINE | 9 | 0 | 0 | no-advance |
| F10 | `source_age_ns > 2s`, otherwise valid | valid-resubmit | UNCONSUMED_BASELINE | 11 | 0 | 0 | advance |

---

## Category K — Type and Boundary Strictness

All rows: construction `malformed` (step-2 class), fixture `UNCONSUMED_BASELINE`, `BA=0`, `Wm=no-advance`, stated per row.

| ID | Attack | Fixture | Expected fail step | SA | BA | Wm |
|---|---|---|---|---|---|---|
| K1 | Top-level JSON value wrong type | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K2 | `signature` field wrong JSON type | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K3 | `signature` string incorrect length | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K4 | `signature` string non-hex characters | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K5 | `signature` string uppercase hex | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K6 | `source_sequence`/`observer_sequence` = zero | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K7 | `source_sequence`/`observer_sequence` negative | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K8 | `source_sequence`/`observer_sequence` exceeding uint64 | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K9 | Identifier field format/length violation | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K10 | `observer_type`/`scope_type` outside frozen enum | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K11 | Evidence field below 0 or above 1,000,000 | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K12 | Evidence field as JSON fractional number | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K13 | Evidence field as JSON string | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K14 | Any integer-typed field — **`source_sequence`, `observer_sequence`, `structural_epoch`, `source_observation_time_ns`, `witness_sign_time_ns`, `fact_evidence`, `logic_evidence`, or `coherence_evidence`** — submitted as a JSON float | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K15 | `shape_integrity` as non-boolean | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K16 (new) | `structural_epoch = 0` | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K17 (new) | `structural_epoch` negative | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K18 (new) | `structural_epoch` exceeding uint64 range | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K19 (new) | `source_observation_time_ns` negative | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K20 (new) | `witness_sign_time_ns` negative | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K21 (new) | Either timestamp field exceeding uint64 range | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |
| K22 (new) | Any integer-typed field submitted as JSON `true`/`false` instead of an integer — particularly important to test explicitly since some implementation languages (e.g. Python, where `bool` subclasses `int`) can silently let a boolean pass an integer type check | UNCONSUMED_BASELINE | 2 | 0 | 0 | no-advance |

**Note on K16–K18 vs. K19–K21:** `structural_epoch` shares the same `>= 1` floor as the sequence fields (both zero and negative values are invalid), while the two timestamp fields permit `0` but not negative values — reflected in the separate zero-case row existing only for epoch (K16), not duplicated for timestamps.

## Category KF — Freshness Boundary Controls

| ID | `source_observation_time_ns` | `witness_sign_time_ns` | `gate_now_ns` | `source_age_ns` | Fixture | Expected SA | Expected BA | Watermarks |
|---|---|---|---|---|---|---|---|---|
| KF1 | 10,200,000,000 | 10,200,000,000 | 10,200,000,000 | 0 | UNCONSUMED_BASELINE | 1 | 1 | advance |
| KF2 | 8,200,000,000 | 10,100,000,000 | 10,200,000,000 | 2,000,000,000 | UNCONSUMED_BASELINE | 1 | 1 | advance |
| KF3 | 8,199,999,999 | 10,100,000,000 | 10,200,000,000 | 2,000,000,001 | UNCONSUMED_BASELINE | 0 | 0 | advance |

---

## Category G — Availability

| ID | Attack | Construction | Fixture | Expected SA/BA | Watermarks | Classification |
|---|---|---|---|---|---|---|
| G1 | Suppress source delivery entirely — no record is ever produced, so nothing reaches the gate | — | N/A | 0 / 0 | no-advance (nothing to advance) | Availability failure — logged separately from integrity results |
| G2 | Delay delivery so the record reaches the gate only after the freshness window has elapsed — this is a genuine gate-path submission of an otherwise-valid record, mechanically identical to F10/KF3: it passes the step-10 replay commit (novel sequence pair) before failing freshness at step 11 | valid-resubmit | UNCONSUMED_BASELINE | 0 / 0 | advance | Availability-driven, but processed and rejected as an ordinary staleness failure — not a special case at the gate level |

---

## Category H — Positive and Negative Controls

| ID | Setup | Construction | Fixture | Expected SA | Expected BA | Watermarks |
|---|---|---|---|---|---|---|
| H1 | Fully authentic, fresh, correct scope/epoch, healthy evidence | valid-resubmit | UNCONSUMED_BASELINE | 1 | = RouteAdmissible | advance |
| H2 | Fully authentic and fresh, genuinely unhealthy evidence (`fact_evidence=499,999`, others `1,000,000`) | valid-resubmit | UNCONSUMED_BASELINE | 0 | 0 | advance |
| H3 | Valid SA=1, RouteAdmissible=0 | valid-resubmit | UNCONSUMED_BASELINE | 1 | 0 | advance |
| H4 | Authentic except `source_age_ns > 2s` | valid-resubmit | UNCONSUMED_BASELINE | 0 | 0 | advance |
| H5 | No snapshot produced | — | N/A | no record | 0 | no-advance |
| H6 | First record: unhealthy, `source_sequence=N`, `observer_sequence=N` (accepted, advances both watermarks to N). Second record: healthy, `source_sequence=N-1`, `observer_sequence=N+1` — this combination requires resurrecting old source content the witness cannot retrieve, so it cannot arise from the frozen normal pipeline | first: valid-resubmit / second: fault-injected-signer | UNCONSUMED_BASELINE (first) → CONSUMED_BASELINE-equivalent at N (second) | first: 0 / second: 0 | first: 0 / second: 0 | first: advance to N/N; second: SourceReplaySafe=0, ObserverReplaySafe=1, StructuralAuthority=0 |

---

## Category I — Producer Invariants (Fixture = N/A, all rows)

| ID | Test | Expected result |
|---|---|---|
| I1 | `source_sequence` strictly increasing within an epoch | Pass |
| I2 | `source_sequence` resets to exactly `1` on epoch change | Pass |
| I3 | `observer_sequence` strictly increasing within an epoch | Pass |
| I4 | `observer_sequence` resets to exactly `1` on epoch change | Pass |
| I5 | Neither generator repeats/decreases within an epoch | Pass |
| I6 | Witness `shape_integrity` computation deterministic | Pass |

## Category J — Atomic Replay-State Failure

| ID | Attack | Construction | Fixture | Expected SA | Expected BA | Watermarks |
|---|---|---|---|---|---|---|
| J1 | Submit an otherwise fully accept-eligible record; inject a fault after both replay comparisons pass but before the single composite-state commit at step 10 | gate-fault-injected | UNCONSUMED_BASELINE | 0 | 0 | no-advance — composite replay-state object observed after the fault is byte-for-byte identical to its pre-submission value |

---

## Resolution Status

This revision resolves: E1/E2's predicate expectation (both `SourceReplaySafe` and `ObserverReplaySafe` fail together under honest out-of-order delivery from a single source/witness — isolating either predicate alone remains D4/D5's job, via fault injection), G2's and J1's misclassification as component-level/N/A tests when both are genuine gate-path submissions (G2 now `valid-resubmit`/`UNCONSUMED_BASELINE` with SA=0/BA=0/advance; J1 now `gate-fault-injected`/`UNCONSUMED_BASELINE` with SA=0/BA=0/no-advance), the missing `## 4. Canonical Encoding` heading in the Harness Profile (restored — a real editing artifact from an earlier revision, not a content gap), two construction-mode definitions tightened (`fault-injected-signer` now correctly allows rejection either before or after step 5 depending on the targeted predicate, since A7 fails at step 4; `signature-corrupted` now restricted to same-length corruption only, since wrong-length signatures are K3's job at step 2), and K22 added for boolean-as-integer type confusion.

Architecture Freeze v0.5 has required no changes across six rounds of review. Harness Profile v1.5 and this Test Matrix v1.6 are synchronized, self-contained, and — per this round's disposition — ready to serve as the implementation baseline.
