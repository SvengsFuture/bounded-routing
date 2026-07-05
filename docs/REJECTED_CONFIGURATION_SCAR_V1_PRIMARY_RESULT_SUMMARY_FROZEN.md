# Rejected Configuration Scar V1 Primary Run Result Summary

**Document:** `REJECTED_CONFIGURATION_SCAR_V1_PRIMARY_RESULT_SUMMARY.md`  
**Script:** `rejected_configuration_scar_sim_v1_REVIEWED.py`  
**Validation plan:** `REJECTED_CONFIGURATION_SCAR_VALIDATION_PLAN_v1_FROZEN.md`  
**Scar spec:** `REJECTED_CONFIGURATION_SCAR_SPEC_v1_REVISED.md`  
**Run type:** Formal primary run  
**Status:** Frozen after external result review  
**Verdict:** `SUPPORTED`  
**Reason:** `all 30 assertions passed`  

## Result

The reviewed scar validation harness completed the formal primary run with:

```text
assertions_passed = 30
assertions_total  = 30
verdict           = SUPPORTED
runtime_s         = 0.98
stderr            = empty
```

The run supports the narrow v1 claim that the rejected-configuration scar layer enforces the frozen boundary under the synthetic scenario suite.

## What This Run Supports

This primary run supports the following limited claims.

The fingerprint mechanism behaved as frozen. Near-identical float drift matched, geometry beyond the quantization boundary did not match, the same geometry with different `failed_invariant_class` matched the same fingerprint, and missing required geometry produced no fingerprint and no scar.

The authority boundary behaved as frozen. Non-admitted candidates, cheap retry failures, invalid evidence, authorized-but-not-completed operations, and transient soft warnings below persistence wrote no scar.

Scar writes behaved as frozen. Authorized hard structural failure wrote a scar with `REJECT_AS_IS`. Authorized gate-effective soft degradation and authorized restoration failure wrote scars with `REQUIRE_EXTRA_PROOF`.

Scar matching behaved as frozen. The same hard-failed geometry was rejected as-is, the soft scar required extra proof, similar but non-identical geometry did not match under v1 exact policy, and the same geometry with a different first-failed invariant still matched the same scar.

Failure counts, elevation, and retirement behaved as frozen. Repeated trusted failure incremented `failure_count`, cheap rejected repeats did not, elevation fired only at `T_SCAR_ELEVATE = 3`, idle time alone did not retire a scar, successful cycles retired a scar at `T_SCAR_RETIRE_SUCCESS_CYCLES = 5`, and a new trusted failure reset retirement progress.

The separation assertions passed. The scar registry was not readable by the structural observer, did not alter live shape-integrity classification, did not update `C_success`, did not leak forbidden fields into the fingerprint payload, and every written scar came from the scar-eligible write path.

## What This Run Does Not Support

This run does not validate cellular shedding.

It does not validate lineage inheritance.

It does not validate prospective filtering.

It does not validate fuzzy scar matching.

It does not validate an extra-proof protocol.

It does not prove that the system knows why a configuration failed.

It validates only the v1 rejected-configuration scar boundary.

## Run Integrity

```text
run_start_timestamp      = 2026-07-05T14:08:13.128146+00:00
run_completion_timestamp = 2026-07-05T14:08:14.107467+00:00
script_sha256            = eb69c2d5bb885eb327f098a7aba454f09dbe73bde032abf0453d161c2cb0d11c
validation_plan_sha256   = bc85989023352f37ceb77a92bd611f50ce5b5bb647ae3ac1d2a5705cfa1ed186
scar_spec_sha256         = 028eea341c56a6d6118c7d3738bc0eaa00acfb0318ff5003558decec377aa8a9
```

The run record includes Python, OpenSSL, numpy, pandas, and matplotlib version information.

## Required Outputs Present

```text
data/rejected_configuration_scar_v1_raw.csv
data/rejected_configuration_scar_v1_summary.csv
data/rejected_configuration_scar_v1_scenario_summary.csv
data/rejected_configuration_scar_v1_scar_registry.csv
data/rejected_configuration_scar_v1_assertions.csv
data/rejected_configuration_scar_v1_verdict.csv
data/rejected_configuration_scar_v1_run_record.txt
plots/scar_v1_assertion_status.png
plots/scar_v1_write_boundary.png
plots/scar_v1_match_behavior.png
plots/scar_v1_elevation_retirement.png
```

## External Result Review

External review confirmed that the result document is accurate and internally consistent.

The review confirmed:

```text
verdict = SUPPORTED
assertions = 30/30
stderr = empty
runtime_s = 0.98
```

The review also confirmed that the scar registry contents, summary metrics, run integrity fields, and output package contents are consistent with the frozen validation plan.

The result is ready for repo placement.

## Conclusion

`SUPPORTED`.

The formal primary run passed all 30 frozen assertions. The scar layer behaved as a minimal rejected-configuration registry: it wrote scars only for betrayed authority, ignored cheap or invalid failures, matched geometry-only fingerprints exactly, separated hard and soft responses, elevated only after the declared threshold, retired only after successful cycles, and remained isolated from live shape observation and route-confidence scoring.
