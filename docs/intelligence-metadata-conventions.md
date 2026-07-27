# Intelligence response metadata conventions

These conventions define the canonical metadata vocabulary for new intelligence modules,
starting with Phase 8. They do not replace or break the existing Phase 3 through Phase 7
response contracts.

## Canonical top-level fields

New independent intelligence responses should use:

| Field | Meaning |
|---|---|
| `provider` | Normalized provider identifier responsible for the primary source data. |
| `methodology_version` | Immutable identifier for the rules that produced the response. |
| `confidence` | Integer from 0 through 100 measuring evidence quality, coverage and freshness; it is not directional strength or probability of correctness. |
| `source_timestamp` | Timestamp of the source observation, or a structured unavailable value when no source timestamp exists. |
| `generated_at` | UTC time when the API response was calculated. |
| `evaluated_at` | UTC time at which a status or freshness rule was evaluated, when different from `generated_at`. |
| `warnings` | Human-readable, non-secret explanations of partial, stale, proxy-based or degraded results. |
| `partial_data_status` | `complete`, `partial`, or `unavailable`. |

All timestamps are timezone-aware ISO 8601 values normalized to UTC at the API boundary.

## Availability

`AvailableValue[T]` is the canonical wrapper for optional intelligence fields:

```json
{
  "status": "unavailable",
  "value": null,
  "reason": "The provider did not supply an authoritative benchmark.",
  "alignment": null
}
```

Allowed states:

- `available`: the value is present and usable under the documented methodology.
- `unavailable`: the concept applies, but reliable input is missing or insufficient.
- `not_applicable`: the concept does not apply to the selected asset or response.
- `planned_phase8`: the field is intentionally reserved for Phase 8 and no value has been
  calculated. Future modules should use a correspondingly explicit planned state only when a
  field is already published before its implementation.

Every non-available field must include a specific reason. Missing numerical data must never be
converted to zero or a neutral classification.

## Partial-data status

- `complete`: every component required by that module's declared methodology is available.
- `partial`: a valid result exists, but one or more eligible inputs are unavailable, stale,
  delayed, proxy-based or otherwise degraded.
- `unavailable`: the module cannot produce its primary result.

Warnings should explain why a response is partial. HTTP 200 remains appropriate for a valid
partial response. Invalid symbols, invalid requests, authentication failures, provider outages
and similar request-level failures continue to use the standard error envelope.

## Freshness

Modules may require different time bands, but freshness objects should consistently expose:

- `state`
- source age in a documented unit
- source timestamp
- `evaluated_at`
- a reason

State names should use the smallest applicable subset of:

- `CURRENT` or `LIVE`
- `RECENT` or `DELAYED`
- `STALE`
- `UNKNOWN`
- `UNAVAILABLE` or `DISCONNECTED`

Existing module-specific enums remain supported. New modules must document how their states map
to these meanings rather than silently reusing thresholds from another data domain.

## Confidence

Confidence is always independent from directional classification.

- It is an integer from 0 through 100.
- It measures input coverage, data freshness, source quality and rule-specific agreement.
- Missing or stale inputs reduce confidence.
- Confidence is not a forecast probability.
- A score of 80 does not mean an 80 percent chance of a market outcome.
- Each module must publish its confidence formula and methodology version.

## Provider and source attribution

`provider` identifies the primary normalized provider. When multiple sources are introduced,
new modules should add a source-attribution collection without changing the meaning of the
existing provider field.

References and proxies must include:

- symbol or source identifier
- human-readable name
- reference kind
- whether it is a proxy

A proxy must never be labelled as an authoritative index or benchmark.

## Alignment metadata

Comparative time-series fields may add:

- `actual_overlap_count`
- `aligned_start_timestamp`
- `aligned_end_timestamp`
- `requested_lookback`
- `minimum_required`
- `alignment_sufficient`

Returns must be calculated from the same common start and end dates. Observation counts alone
must not be described as overlap.

## Migration guidance

Existing endpoints remain backward compatible:

- Phase 3 retains `FreshnessMetadata` and `timestamp`.
- Phase 4A retains `confidence_score`, `scoring_version` and `snapshot_timestamp`.
- Phase 5 retains boolean `AssetAvailability`.
- Phase 6 retains `NewsFreshnessMetadata` and its existing confidence fields.
- Phase 7 retains its structured availability fields and now reuses the canonical availability
  types internally.

New fields may be added compatibly, but existing fields must not be renamed or removed without a
new API version. A future orchestration layer should translate legacy metadata into the
canonical convention instead of forcing domain services to depend on one another.
