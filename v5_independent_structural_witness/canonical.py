"""
Canonical payload encoder, per V5 Harness Profile v1.6 §4.

Field order, widths, and string length-prefix rule are frozen. This module
is the single source of truth for canonical bytes on both the witness
(signing) side and the gate (verifying) side -- they must import this same
module rather than each implementing their own encoder, or the whole point
of the known-answer vector (Category L) is defeated.
"""
import struct

FIELD_ORDER = [
    "schema_version", "source_id", "observer_id", "observer_type", "key_id",
    "source_sequence", "source_observation_time_ns", "observer_sequence",
    "witness_sign_time_ns", "structural_epoch", "scope_type", "scope_id",
    "fact_evidence", "logic_evidence", "coherence_evidence", "shape_integrity",
]

STRING_FIELDS = {
    "schema_version", "source_id", "observer_id", "observer_type",
    "key_id", "scope_type", "scope_id",
}
INT_FIELDS = {
    "source_sequence", "source_observation_time_ns", "observer_sequence",
    "witness_sign_time_ns", "structural_epoch",
    "fact_evidence", "logic_evidence", "coherence_evidence",
}
BOOL_FIELDS = {"shape_integrity"}


def _enc_str(s: str) -> bytes:
    b = s.encode("ascii")
    if len(b) > 0xFFFF:
        raise ValueError("string field exceeds 2-byte length prefix capacity")
    return struct.pack(">H", len(b)) + b


def _enc_u64(n: int) -> bytes:
    if not (0 <= n <= 0xFFFFFFFFFFFFFFFF):
        raise ValueError(f"value {n} out of uint64 range")
    return struct.pack(">Q", n)


def _enc_bool(b: bool) -> bytes:
    if b is not True and b is not False:
        raise ValueError("shape_integrity must be a Python bool, not %r" % (b,))
    return b"\x01" if b else b"\x00"


def canonical_bytes(fields: dict) -> bytes:
    """
    Build canonical bytes from a fully-typed, already-schema-validated
    field dict. This function does NOT perform schema validation (that is
    step 2's job, done separately) -- it assumes it is being called with
    values that are already the correct Python type (str/int/bool) and in
    range. Calling it with the wrong type is a caller bug, not a step-2
    schema rejection, and will raise here.
    """
    missing = [f for f in FIELD_ORDER if f not in fields]
    if missing:
        raise ValueError(f"canonical_bytes called with missing fields: {missing}")

    out = bytearray()
    for name in FIELD_ORDER:
        val = fields[name]
        if name in STRING_FIELDS:
            if not isinstance(val, str):
                raise ValueError(f"{name} must be str, got {type(val)}")
            out += _enc_str(val)
        elif name in INT_FIELDS:
            # Explicit bool rejection: in Python, bool is a subclass of int,
            # so isinstance(True, int) is True. Reject booleans explicitly
            # here so the encoder never silently accepts K22-class input.
            if isinstance(val, bool) or not isinstance(val, int):
                raise ValueError(f"{name} must be int (not bool), got {type(val)}")
            out += _enc_u64(val)
        elif name in BOOL_FIELDS:
            if not isinstance(val, bool):
                raise ValueError(f"{name} must be bool, got {type(val)}")
            out += _enc_bool(val)
        else:
            raise AssertionError(f"unclassified field {name}")
    return bytes(out)
