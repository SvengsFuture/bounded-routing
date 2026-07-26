"""
Authority Gate: implements the Ordered Verification Sequence from
Architecture Freeze v0.5, using the encoding/type rules from Harness
Profile v1.6.

Step numbering matches the frozen spec exactly:
  1. Parse transport envelope (syntactic JSON decode only)
  2. Schema validation (types, ranges, enums, duplicates, unknown fields,
     schema_version)
  3. Construct canonical bytes
  4. Resolve key_id via registry; confirm registered to claimed
     observer_id/observer_type
  5. Verify Ed25519 signature against gate-derived canonical bytes
  6. SourceBindingValid
  7. EpochMatch
  8. ScopeMatch
  9. Temporal ordering sanity (source_time <= sign_time <= gate_now)
  10. Atomic replay-state check + commit (SourceReplaySafe AND
      ObserverReplaySafe)
  11. Freshness (0 <= gate_now - source_time <= 2s)
  12. ShapeIntegrity
  13. Combine with RouteAdmissible -> BypassAuthority
"""
import json
import threading
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from canonical import canonical_bytes, FIELD_ORDER, STRING_FIELDS, INT_FIELDS, BOOL_FIELDS
from fixtures import SCHEMA_VERSION, OBSERVER_TYPE_ENUM, SCOPE_TYPE_ENUM, FRESHNESS_WINDOW_NS

IDENTIFIER_RE_ALLOWED = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)
UINT64_MAX = 0xFFFFFFFFFFFFFFFF


class DuplicateKeyError(ValueError):
    pass


def _dup_checking_pairs_hook(pairs):
    """
    Ordered key-pair decode hook (Harness Profile §11): surfaces duplicate
    field names at ANY object level (envelope or payload) as an explicit
    error, rather than letting the default json.loads behavior silently
    collapse them (last-value-wins). This is what makes F2a/F2b real,
    deterministic tests instead of untestable ambiguity.
    """
    seen = set()
    result = {}
    for key, value in pairs:
        if key in seen:
            raise DuplicateKeyError(f"duplicate field name: {key!r}")
        seen.add(key)
        result[key] = value
    return result


class GateResult:
    def __init__(self):
        self.fail_step = None          # int or None (None = fully passed)
        self.structural_authority = False
        self.bypass_authority = False
        self.reason = None
        self.watermarks_advanced = False

    def __repr__(self):
        return (f"GateResult(fail_step={self.fail_step}, SA={self.structural_authority}, "
                f"BA={self.bypass_authority}, wm_advanced={self.watermarks_advanced}, "
                f"reason={self.reason!r})")


def _fail(result, step, reason):
    result.fail_step = step
    result.structural_authority = False
    result.bypass_authority = False
    result.reason = reason
    return result


def _valid_identifier(s):
    return isinstance(s, str) and 1 <= len(s) <= 64 and all(c in IDENTIFIER_RE_ALLOWED for c in s)


def _valid_uint64(v):
    return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= UINT64_MAX


class AuthorityGate:
    def __init__(self, registry, structural_epoch, scope_type, scope_id, clock,
                 gate_fault_hook=None, contention_hook=None):
        self.registry = registry
        self.current_epoch = structural_epoch
        self.current_scope_type = scope_type
        self.current_scope_id = scope_id
        self._clock = clock  # SAME TrustedClock instance as source and witness
        # Single composite replay-state object. Never mutated in place --
        # every update replaces this reference with a new, fully-built
        # candidate object in one assignment, so a failure at any point
        # before that final assignment leaves this reference, and everything
        # it points to, completely untouched. See step 10 below.
        self._replay_state = {"source": {}, "observer": {}}
        self._replay_lock = threading.Lock()
        self.gate_fault_hook = gate_fault_hook
        self.contention_hook = contention_hook

    def seed_watermark(self, source_id, observer_id, epoch, source_seq, observer_seq):
        """Set up CONSUMED_BASELINE-style pre-accepted watermark state."""
        with self._replay_lock:
            candidate = {
                "source": dict(self._replay_state["source"]),
                "observer": dict(self._replay_state["observer"]),
            }
            candidate["source"][(source_id, epoch)] = source_seq
            candidate["observer"][(observer_id, epoch)] = observer_seq
            self._replay_state = candidate

    def watermark_snapshot(self):
        with self._replay_lock:
            state = self._replay_state
            return (dict(state["source"]), dict(state["observer"]))

    def verify(self, raw_transport_bytes: bytes, route_admissible: bool) -> GateResult:
        gate_now_ns = self._clock.now_ns()
        result = GateResult()

        # ---- Step 1: parse transport envelope (syntactic decode only) ----
        try:
            envelope = json.loads(raw_transport_bytes, object_pairs_hook=_dup_checking_pairs_hook)
        except DuplicateKeyError as e:
            # Per Profile §11: duplicate field names are classified as a
            # step-2 schema failure (absence-of-duplicates check), even
            # though detection happens during the step-1 decode pass.
            return _fail(result, 2, f"step2: {e}")
        except Exception as e:
            return _fail(result, 1, f"step1: JSON decode failure: {e}")

        # ---- Step 2: schema validation ----
        if not isinstance(envelope, dict):
            return _fail(result, 2, "step2: top-level value is not an object")
        if set(envelope.keys()) != {"payload", "signature"}:
            return _fail(result, 2, f"step2: envelope must have exactly payload+signature, got {set(envelope.keys())}")

        payload = envelope["payload"]
        signature_hex = envelope["signature"]

        if not isinstance(payload, dict):
            return _fail(result, 2, "step2: payload is not an object")
        if not isinstance(signature_hex, str):
            return _fail(result, 2, "step2: signature is not a string")
        if len(signature_hex) != 128:
            return _fail(result, 2, "step2: signature wrong length")
        if any(c not in "0123456789abcdef" for c in signature_hex):
            return _fail(result, 2, "step2: signature contains non-lowercase-hex characters")

        if set(payload.keys()) != set(FIELD_ORDER):
            missing = set(FIELD_ORDER) - set(payload.keys())
            extra = set(payload.keys()) - set(FIELD_ORDER)
            return _fail(result, 2, f"step2: payload field set mismatch (missing={missing}, extra={extra})")

        # Type/range/enum checks per Profile §3b/§3e
        for f in STRING_FIELDS:
            if not isinstance(payload[f], str):
                return _fail(result, 2, f"step2: {f} must be a string")
        for f in INT_FIELDS:
            v = payload[f]
            if isinstance(v, bool) or not isinstance(v, int):
                return _fail(result, 2, f"step2: {f} must be an integer (K14/K22 class failure)")
        if not isinstance(payload["shape_integrity"], bool):
            return _fail(result, 2, "step2: shape_integrity must be a boolean (K15)")

        if payload["schema_version"] != SCHEMA_VERSION:
            return _fail(result, 2, "step2: unsupported schema_version (B13/F3)")
        if not _valid_identifier(payload["source_id"]):
            return _fail(result, 2, "step2: source_id invalid format (K9)")
        if not _valid_identifier(payload["observer_id"]):
            return _fail(result, 2, "step2: observer_id invalid format (K9)")
        if not _valid_identifier(payload["key_id"]):
            return _fail(result, 2, "step2: key_id invalid format (K9)")
        if not _valid_identifier(payload["scope_id"]):
            return _fail(result, 2, "step2: scope_id invalid format (K9)")
        if payload["observer_type"] not in OBSERVER_TYPE_ENUM:
            return _fail(result, 2, "step2: observer_type outside frozen enum (K10)")
        if payload["scope_type"] not in SCOPE_TYPE_ENUM:
            return _fail(result, 2, "step2: scope_type outside frozen enum (K10)")

        if not _valid_uint64(payload["source_sequence"]) or payload["source_sequence"] < 1:
            return _fail(result, 2, "step2: source_sequence must be uint64 >= 1 (K6/K7/K8)")
        if not _valid_uint64(payload["observer_sequence"]) or payload["observer_sequence"] < 1:
            return _fail(result, 2, "step2: observer_sequence must be uint64 >= 1 (K6/K7/K8)")
        if not _valid_uint64(payload["structural_epoch"]) or payload["structural_epoch"] < 1:
            return _fail(result, 2, "step2: structural_epoch must be uint64 >= 1 (K16/K17/K18)")
        if not _valid_uint64(payload["source_observation_time_ns"]):
            return _fail(result, 2, "step2: source_observation_time_ns must be uint64 >= 0 (K19/K21)")
        if not _valid_uint64(payload["witness_sign_time_ns"]):
            return _fail(result, 2, "step2: witness_sign_time_ns must be uint64 >= 0 (K20/K21)")

        for f in ("fact_evidence", "logic_evidence", "coherence_evidence"):
            v = payload[f]
            if not (0 <= v <= 1_000_000):
                return _fail(result, 2, f"step2: {f} out of [0, 1000000] range (K11)")

        # ---- Step 3: construct canonical bytes ----
        try:
            canon = canonical_bytes(payload)
        except Exception as e:
            return _fail(result, 2, f"step2: payload failed canonical construction: {e}")

        # ---- Step 4: resolve key_id, confirm registered to claimed identity ----
        entry = self.registry.resolve_key(payload["key_id"])
        if entry is None:
            return _fail(result, 4, "step4: key_id not registered")
        pub, reg_observer_id, reg_observer_type = entry
        if payload["observer_id"] != reg_observer_id or payload["observer_type"] != reg_observer_type:
            return _fail(result, 4, "step4: key not registered to claimed observer_id/observer_type")

        # ---- Step 5: verify Ed25519 signature against gate-derived canonical bytes ----
        try:
            pub.verify(bytes.fromhex(signature_hex), canon)
        except InvalidSignature:
            return _fail(result, 5, "step5: signature verification failed")
        except Exception as e:
            return _fail(result, 5, f"step5: signature verification error: {e}")

        # ---- Step 6: SourceBindingValid ----
        bound_observer = self.registry.source_bound_to(payload["source_id"])
        if bound_observer is None:
            return _fail(result, 6, "step6: source_id not registered")
        if bound_observer != payload["observer_id"]:
            return _fail(result, 6, "step6: source not bound to signing witness identity")

        # ---- Step 7: EpochMatch ----
        if payload["structural_epoch"] != self.current_epoch:
            return _fail(result, 7, "step7: structural_epoch does not match gate's current epoch")

        # ---- Step 8: ScopeMatch ----
        if payload["scope_type"] != self.current_scope_type or payload["scope_id"] != self.current_scope_id:
            return _fail(result, 8, "step8: scope does not match gate's current authority context")

        # ---- Step 9: temporal ordering sanity ----
        st = payload["source_observation_time_ns"]
        wt = payload["witness_sign_time_ns"]
        if not (st <= wt <= gate_now_ns):
            return _fail(result, 9, "step9: temporal ordering violated (source_time <= sign_time <= gate_now)")

        # ---- Step 10: atomic replay-state check + commit ----
        if self.contention_hook is not None:
            self.contention_hook()

        with self._replay_lock:
            current_state = self._replay_state
            src_key = (payload["source_id"], payload["structural_epoch"])
            obs_key = (payload["observer_id"], payload["structural_epoch"])
            src_wm = current_state["source"].get(src_key, 0)
            obs_wm = current_state["observer"].get(obs_key, 0)

            source_replay_safe = payload["source_sequence"] > src_wm
            observer_replay_safe = payload["observer_sequence"] > obs_wm

            if not (source_replay_safe and observer_replay_safe):
                reason = f"step10: replay check failed (SourceReplaySafe={source_replay_safe}, ObserverReplaySafe={observer_replay_safe})"
                return _fail(result, 10, reason)

            # Build the ENTIRE new state as a fully-formed candidate object
            # before touching self._replay_state at all. Nothing below this
            # point can leave a partial update visible: either the
            # candidate is built completely and the single reference
            # reassignment at the end executes, or something raises first
            # and self._replay_state is untouched -- still pointing at the
            # exact object it pointed at before this call began.
            candidate = {
                "source": dict(current_state["source"]),
                "observer": dict(current_state["observer"]),
            }
            candidate["source"][src_key] = payload["source_sequence"]
            candidate["observer"][obs_key] = payload["observer_sequence"]

            # Fault hook for gate-fault-injected (J1): runs after the
            # candidate is fully built but before the single replacement.
            # If it raises, self._replay_state still refers to current_state,
            # completely unchanged -- not merely "hard to observe changed",
            # genuinely never modified.
            if self.gate_fault_hook is not None:
                try:
                    self.gate_fault_hook()
                except Exception as e:
                    return _fail(result, 10, f"step10: gate-fault-injected interruption before commit: {e}")

            # Single reference reassignment -- the only line that can
            # possibly make the new state visible, and it cannot partially
            # apply: either this executes and the whole candidate becomes
            # the new state, or it doesn't run at all.
            self._replay_state = candidate
            result.watermarks_advanced = True

        # ---- Step 11: freshness ----
        source_age = gate_now_ns - st
        if not (0 <= source_age <= FRESHNESS_WINDOW_NS):
            return _fail(result, 11, "step11: source evidence stale (freshness window exceeded)")

        # ---- Step 12: ShapeIntegrity ----
        if payload["shape_integrity"] is not True:
            return _fail(result, 12, "step12: shape_integrity is false")

        # All structural conditions passed.
        result.fail_step = None
        result.structural_authority = True

        # ---- Step 13: combine with RouteAdmissible ----
        if route_admissible is not True and route_admissible is not False:
            # A non-Boolean input is a caller/integration error, not a
            # legitimate "route is admissible" signal. StructuralAuthority
            # (already determined above) stands on its own merits, but
            # BypassAuthority must fail closed rather than coerce an
            # arbitrary truthy value (e.g. the string "false", which is
            # non-empty and would otherwise evaluate as True).
            # fail_step is set explicitly here: leaving it at None would
            # claim "fully passed" while simultaneously reporting an error
            # in `reason` and forcing bypass_authority False -- a
            # self-contradictory result.
            result.fail_step = 13
            result.bypass_authority = False
            result.reason = f"step13: route_admissible must be a bool, got {type(route_admissible).__name__}: {route_admissible!r}"
            return result
        result.bypass_authority = route_admissible
        result.reason = "accepted"
        return result
