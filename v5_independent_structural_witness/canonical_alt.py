"""
An INDEPENDENTLY-WRITTEN second implementation of the canonical encoder,
used exclusively by the L5 test to provide a genuine cross-check.

This deliberately does NOT import or call anything from canonical.py. If it
did, comparing its output to canonical.py's output would prove nothing
(both would trivially agree, having run identical code) -- this is exactly
the tautology problem identified in review. This module re-derives the
field order, widths, and encoding rules from Harness Profile v1.6 §4 from
scratch, using a different implementation strategy (a builder class
appending to a bytearray field-by-field with inline encoding, rather than
canonical.py's functional encode-and-concatenate style) so that a bug in
one is unlikely to be mirrored by an identical bug in the other.
"""

_FIELD_SPEC = [
    ("schema_version", "str"),
    ("source_id", "str"),
    ("observer_id", "str"),
    ("observer_type", "str"),
    ("key_id", "str"),
    ("source_sequence", "u64"),
    ("source_observation_time_ns", "u64"),
    ("observer_sequence", "u64"),
    ("witness_sign_time_ns", "u64"),
    ("structural_epoch", "u64"),
    ("scope_type", "str"),
    ("scope_id", "str"),
    ("fact_evidence", "u64"),
    ("logic_evidence", "u64"),
    ("coherence_evidence", "u64"),
    ("shape_integrity", "bool"),
]


class _Builder:
    def __init__(self):
        self.buf = bytearray()

    def put_u16(self, n):
        self.buf.append((n >> 8) & 0xFF)
        self.buf.append(n & 0xFF)

    def put_u64(self, n):
        for shift in (56, 48, 40, 32, 24, 16, 8, 0):
            self.buf.append((n >> shift) & 0xFF)

    def put_str(self, s):
        raw = s.encode("ascii")
        self.put_u16(len(raw))
        self.buf.extend(raw)

    def put_bool(self, b):
        self.buf.append(1 if b else 0)


def canonical_bytes_independent(fields: dict) -> bytes:
    b = _Builder()
    for name, kind in _FIELD_SPEC:
        val = fields[name]
        if kind == "str":
            b.put_str(val)
        elif kind == "u64":
            if isinstance(val, bool) or not isinstance(val, int):
                raise ValueError(f"{name} must be int, got {type(val)}")
            b.put_u64(val)
        elif kind == "bool":
            if not isinstance(val, bool):
                raise ValueError(f"{name} must be bool, got {type(val)}")
            b.put_bool(val)
    return bytes(b.buf)
