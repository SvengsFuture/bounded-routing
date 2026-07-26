# V5 Harness Profile v1.6 (Final, Self-Contained)

Supersedes v1.0-v1.5 in full. Companion to Architecture Freeze v0.5.

---

## 1. Parsing vs. Schema Validation Boundary (steps 1–2)

**Step 1 (Parse):** decode raw transport bytes into a generic structure via JSON, preserving key order and surfacing duplicate keys rather than silently collapsing them (§11). Asks only whether the bytes are syntactically well-formed JSON. Failure: truncated/invalid syntax, invalid character encoding, unterminated structures.

**Step 2 (Schema validation):** given any successfully decoded JSON value — including a wrong top-level type (array/string/number/null instead of object) — check against the frozen schema: presence of both envelope members, presence of all 16 payload fields, correct types, permitted ranges, absence of duplicates (envelope-level and payload-level, tested separately — see §11), absence of any unrecognized field (§12), and `schema_version` exactly `"v5.0"`.

## 2. Transport Envelope Structure

```
{
  "payload": { ...16 fields, wire order irrelevant... },
  "signature": "<128 lowercase hex characters, see §3a>"
}
```

No other top-level members permitted.

## 3. Field Types and Ranges

### 3a. Signature Encoding

Raw 64-byte Ed25519 signature, represented as exactly 128 lowercase hex characters (`[0-9a-f]{128}`), two hex characters per byte, in the exact byte order the signing operation emits. No prefix, no whitespace, no uppercase. Opaque byte string — no endianness concept applies.

### 3b. Payload Fields

| Field | Type | Constraint |
|---|---|---|
| `schema_version` | string | exactly `"v5.0"` |
| `source_id` | string | ASCII, `^[a-zA-Z0-9_-]{1,64}$` |
| `observer_id` | string | same format |
| `observer_type` | string | exactly one of `{"tetrahedral_coordinator", "auxiliary_observer"}` |
| `key_id` | string | same format as `source_id` |
| `source_sequence` | integer (uint64) | `>= 1` |
| `source_observation_time_ns` | integer (uint64) | `>= 0` |
| `observer_sequence` | integer (uint64) | `>= 1` |
| `witness_sign_time_ns` | integer (uint64) | `>= 0` |
| `structural_epoch` | integer (uint64) | `>= 1` |
| `scope_type` | string | exactly one of `{"route", "system"}` |
| `scope_id` | string | ASCII, same identifier format |
| `fact_evidence` | integer, millionths | `0 <= value <= 1,000,000` |
| `logic_evidence` | integer, millionths | `0 <= value <= 1,000,000` |
| `coherence_evidence` | integer, millionths | `0 <= value <= 1,000,000` |
| `shape_integrity` | boolean | `true`/`false` only |

Every field is submitted, transmitted, and parsed as exactly the stated type — no numeric-string, boolean-as-integer, or float-for-integer substitutes for any field, including evidence.

### 3c. Evidence Encoding

Evidence fields are JSON integers in millionths only. `500000` represents 0.5. No decimal-string form, no JSON fractional-number form, no unit conversion at parse time. A fractional number or string submitted for an evidence field fails step 2 as a type violation.

### 3d. shape_integrity Ownership and Frozen Rule

Not part of the source snapshot — the source provides only `fact_evidence`, `logic_evidence`, `coherence_evidence`. Computed by the Structural Witness. Frozen rule for this harness (fixed; changing it requires a new profile version):

```
shape_integrity = (fact_evidence >= 500,000) AND (logic_evidence >= 500,000) AND (coherence_evidence >= 500,000)
```

Threshold inclusive (`>=`). Conjunction, not disjunction. Tested directly by Category CW-Boundary.

### 3e. Full Integer Boundary Coverage

Zero/negative/overflow testing applies to **every** uint64-typed field, not only the two sequence fields: `source_sequence`, `observer_sequence`, `structural_epoch`, `source_observation_time_ns`, `witness_sign_time_ns`, `fact_evidence`, `logic_evidence`, `coherence_evidence`. Note that `structural_epoch` carries the same `>= 1` floor as the two sequence fields (zero and negative values are both invalid), while the two timestamp fields permit `0` but not negative values. Category K provides this coverage across K6–K8 for sequence fields, K11 for evidence bounds, K16–K18 for structural epoch, and K19–K21 for timestamps.

## 4. Canonical Encoding

- Fields ordered in one fixed sequence: `schema_version, source_id, observer_id, observer_type, key_id, source_sequence, source_observation_time_ns, observer_sequence, witness_sign_time_ns, structural_epoch, scope_type, scope_id, fact_evidence, logic_evidence, coherence_evidence, shape_integrity` — regardless of wire order.
- Integer fields (`source_sequence`, `source_observation_time_ns`, `observer_sequence`, `witness_sign_time_ns`, `structural_epoch`, `fact_evidence`, `logic_evidence`, `coherence_evidence`): fixed-width big-endian uint64 (8 bytes each).
- `shape_integrity`: single byte (`0x00`/`0x01`).
- String fields (`schema_version`, `source_id`, `observer_id`, `observer_type`, `key_id`, `scope_type`, `scope_id`): ASCII, 2-byte big-endian length prefix + exact bytes.
- All 16 fields participate; none omitted.

## 5. Baseline Fixture

**Registry:** `source_id="source-1"`; `observer_id="witness-1"`, `observer_type="tetrahedral_coordinator"`, `key_id="key-1"`, bound together and to `source-1`. Deterministic Ed25519 test key pair derived from seed `SHA-256(ASCII("v5-harness-test-key-1"))`.

**Epoch/scope:** `structural_epoch=1`, `scope_type="route"`, `scope_id="route-A"`.

**Baseline clock values** (all test-clock-controlled, never real-time): `source_observation_time_ns=10,000,000,000`; `witness_sign_time_ns=10,100,000,000`; `gate_now_ns=10,200,000,000`. These satisfy the frozen temporal-ordering invariant `source_observation_time_ns <= witness_sign_time_ns <= gate_now_ns` (step 9), which every row that varies clock values must independently continue to satisfy unless the row is specifically testing an ordering violation (F7–F9). `source_age_ns` at baseline = `200,000,000` (well within the 2-second window).

**Evidence:** `fact_evidence=logic_evidence=coherence_evidence=1,000,000` → `shape_integrity=true`.

**Route state:** `RouteAdmissible=true` unless a test deliberately flips it.

**Sequence reset value:** both sequences reset to exactly `1` on epoch transition.

### Named Fixtures

- **UNCONSUMED_BASELINE**: record `source_sequence=10`, `observer_sequence=10`; gate watermarks `9`/`9`.
- **CONSUMED_BASELINE**: same record values; gate watermarks already `10`/`10`.

**Every gate-path test row names its starting fixture.** Tests that do not submit a record through the gate explicitly state `Fixture = N/A`. These include direct encoder tests (BE1–16), the known-answer vector (L1–5), source-interface tests (C1–12), witness-derivation-rule tests (CW1–9), G1, and producer-invariant tests (I1–6), and other rows whose construction ends before gate submission. G2 and J1 are gate-path tests and use `UNCONSUMED_BASELINE`.

### 5a. E9-Specific Registry Fixture

The standard baseline registry (one witness, one key, one source, all mutually bound) cannot construct E9's intended scenario — a registered source presented through a registered witness that is *not* bound to it — because no second registered witness exists to be legitimately unbound. E9 uses a dedicated fixture, **E9_SOURCE_BINDING_FIXTURE**, which extends the registry with:

- `observer_id="witness-2"`, `observer_type="tetrahedral_coordinator"`, `key_id="key-2"` — a second, fully registered witness/key pair
- `source_id="source-1"` remains bound only to `witness-1`, exactly as in the standard baseline

The test record is genuinely signed with `key-2`, correctly claiming `observer_id="witness-2"` and `source_id="source-1"`. Step 4 passes (key-2 correctly resolves to witness-2). Step 5 passes (the signature is genuine). Step 6 fails, because `source-1` is bound to `witness-1`, not `witness-2` — `SourceBindingValid` is false.

## 6. Construction Modes (corrected and complete)

- **`unsigned`**: no `signature` component in the envelope, or present but empty/null.
- **`payload-tampered`**: start from a validly signed baseline record (real key, real values, real signature). Mutate exactly one payload field in the transport-level representation. Resubmit without re-signing, retaining the original now-mismatched signature. This is what was previously called just `tampered`; renamed for clarity now that a second tampering mode exists.
- **`signature-corrupted`**: start from a validly signed baseline record with an unmodified, schema-valid payload. Corrupt the signature bytes themselves via a **same-length** corruption only — e.g. a one-bit flip within the existing 128-hex-character string. A wrong-length signature is a step-2 schema failure (covered by K3), not a step-5 cryptographic failure, so it does not belong to this mode; this mode exists specifically to reach step 5 with everything upstream of it intact.
- **`unauthorized-signer`**: generate a second, genuinely valid Ed25519 key pair never registered with the gate. Sign a payload whose `key_id` field names this unregistered key's own identifier (e.g. `"key-2"`) — not `"key-1"`. If the payload instead claimed `key_id="key-1"` while being signed by the wrong key, step 4 would resolve `"key-1"` successfully and the failure would only surface at step 5 as a signature mismatch.
- **`valid-resubmit`**: submit a genuinely, validly signed record — real key, real values, real signature — manipulating only delivery (timing, order, repetition, concurrency). No tampering with signed bytes.
- **`valid-alternate-context`**: a normally-operating source and witness produce a genuine, honestly-signed record for another valid epoch or scope value — nothing about the signing itself is anomalous. The Agent Domain then presents that legitimately-signed record against a gate context that doesn't match it. Distinct from `valid-resubmit`, which manipulates delivery of a single existing record instance; this mode involves a second, independently produced record. Used for E6/E7.
- **`fault-injected-signer`**: harness-controlled signing capability produces a genuinely, correctly signed record whose content an honestly-operating witness — reading from its one bound source through its normal pipeline, obeying its own sequence-monotonicity invariants — would never naturally produce: impossible timestamp orderings (F7–F9), an observer identity the signing key isn't registered against (A7), a `source_id` not in the gate's registry (E8), or a resurrected/reused sequence value the witness could not have honestly produced (D3–D5, D7, H6's second record). The signature is always genuine; what makes the record anomalous is its *content*, not its authenticity. Rejection may occur either before signature verification (e.g. A7 fails at step 4's registry-binding check, before step 5 is ever reached) or after it (e.g. F7–F9 fail at step 9, after the genuine signature has already verified) — which step depends entirely on which predicate the test targets, not on any fixed relationship to step 5.
- **`gate-fault-injected`**: distinct from `fault-injected-signer` — here, the submitted record is completely normal (genuinely signed, honestly produced, otherwise fully accept-eligible), and the fault is injected inside the **gate's own internal processing**, specifically interrupting the atomic replay-state commit at step 10 after both comparisons have passed but before the composite object is written. Used for J1. Nothing about the record or the signer is anomalous; the defect is purely in the gate's execution.
- **Duplicate-record generation hook**: a shared harness utility that takes one source snapshot and produces two independently, genuinely signed witness records from it, differing only in `observer_sequence`. Used by D2, D6, D8a, and D8b.
- **`encoder-direct`**: bypasses gate and transport layer; constructs two internal payloads differing in exactly one field, runs both through the canonical encoder directly, asserts differing byte output.
- **`malformed`**: bytes that either fail to decode as JSON at all (step-1 failure) or decode but violate schema-level structure — wrong top-level type, duplicate fields, unsupported version, missing fields, unknown fields (step-2 failures). Each `malformed` row states explicitly which of these two failure classes it targets.
- **`transport-varied`**: start from a genuinely valid, validly signed record. Re-serialize the transport envelope with different but meaning-preserving JSON formatting — reordered keys, different whitespace — without altering any structured field value. Used exclusively for the F6 positive control; the resulting record must still verify successfully, since canonical encoding is derived from parsed structured values, not wire bytes.

## 7. Producer Invariants

- Source's `source_sequence` strictly increasing within an epoch (not necessarily contiguous); resets to exactly `1` on epoch change, and only then.
- Witness's `observer_sequence` obeys the same two rules independently per `observer_id`.
- Neither generator repeats or decreases within an epoch, verified across an extended/randomized run.
- Witness's `shape_integrity` computation (§3d) is deterministic across repeated runs on identical evidence.

## 8. Concurrency Model

**Sequential:** submissions processed one at a time to completion.

**Concurrent:** synchronization barrier immediately before the gate's atomic replay-comparison-and-commit (step 10); two submissions from the same source snapshot released simultaneously; exactly one completes the atomic operation and is accepted (subject to remaining predicates); the other observes an already-advanced watermark and is rejected. The test asserts only that exactly one wins, not which one.

## 9. Atomic Failure Injection

Replay state is one composite object, updated under a single lock/transactional commit. Fault injection interrupts after both replay comparisons pass but before the single commit. Assertion: the composite object observed after the fault is byte-for-byte identical to its pre-submission value.

## 10. Source Interface Direct Tests

- **Historical read-back attempt:** no API surface exists to request a past `source_sequence` through the authority-producing path; attempt fails structurally.
- **Torn-snapshot test:** a source update triggered mid-read by the witness never produces a snapshot mixing fields from two different `source_sequence` values.

## 11. Duplicate Field Detection

The step-1 parser uses an ordered key-pair decode (or equivalent hook) that surfaces duplicate field names rather than silently collapsing them. Duplicate detection is tested **at two independent levels**, since they are structurally different failure sites:

- **Envelope-level duplicates:** more than one `payload` or `signature` top-level key.
- **Payload-level duplicates:** more than one occurrence of the same field name inside the `payload` object.

Both classes are classified as step-2 schema failures (absence-of-duplicates check), regardless of which structural level the duplication occurs at.

## 12. Unknown Field Rejection

The schema rejects **every** field not in the frozen 16-field payload list or the 2-member envelope list — no distinction between "authority-relevant" and other fields. Any unrecognized field, at any level, fails step 2.

## 13. Canonical Known-Answer Vector

This section freezes concrete, independently reproducible values so that a witness-side encoder and a gate-side encoder built from this profile can be verified to agree — proving the canonical encoding rules in §4 are actually implemented as specified, not merely that changing a field changes *some* output (which BE1–BE16 already show, but which two independently-buggy-in-the-same-way encoders could still pass).

All values below were generated with a Python reference implementation (Python `cryptography` library, Ed25519) built directly from this profile's §4 encoding rules, and independently re-verified for correct byte length before being recorded here.

**Seed** (`SHA-256(ASCII("v5-harness-test-key-1"))`, 32 bytes, the raw Ed25519 private seed):
`957eba143691d419a813315baa86b8dd0df3aa7af1770a2b2ddf720c7d50dfe8`

**Derived Ed25519 public key** (32 bytes, raw, hex):
`ef5f63d3671be7b17daef2431d77c00af615f17fc79bc26f4909374656349005`

**Baseline canonical payload** (UNCONSUMED_BASELINE healthy record: `source_sequence=10`, `source_observation_time_ns=10,000,000,000`, `observer_sequence=10`, `witness_sign_time_ns=10,100,000,000`, `structural_epoch=1`, `scope_type="route"`, `scope_id="route-A"`, all evidence `1,000,000`, `shape_integrity=true`):

- Canonical payload length: **140 bytes**
- Canonical payload SHA-256 (32 bytes, hex): `66e4a1e1159e3e036966797a8daa81f36ea68711832f5a849c1557fbd0580a43`

**Baseline signature** (64 bytes, hex, produced by signing the canonical payload above with the derived private key, self-verified against the derived public key):
`b87269a046160c69c2a8a630d15569c06be75b7542b0cc4076058874988fa4deab7e8fefab4105185ea13463cbb82d7ef81db2fb2f10d673b1774df587820106`

**Implementation note:** this vector is a starting reference, not a substitute for the harness's own verification step. Whoever implements the harness must run their own encoder over these same baseline field values and confirm it reproduces the same 140-byte canonical length and the same SHA-256 digest before treating agreement with this vector as established. A length or digest mismatch on independent recomputation means the implementation's encoder disagrees with §4 — it is not evidence that this reference vector is wrong, since this vector was itself independently regenerated and character-verified (not hand-transcribed) before being recorded above.
