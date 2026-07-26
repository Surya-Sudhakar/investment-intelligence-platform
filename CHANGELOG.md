# Changelog

All notable project changes are documented in this file.

## Phase 4A — Technical Decision Support — 2026-07-25

### Added

- Daily technical-assessment endpoint
- Assessment health endpoint
- Five technical-outlook classifications
- Technical score from 0 to 100
- Separate confidence score
- Independent risk score and risk level
- Component scoring breakdown
- Supporting and conflicting factors
- Risk and missing-data factors
- Data-quality metadata
- Immutable `technical-v1` scoring methodology
- Phase 4A frontend dashboard
- Backend and frontend assessment tests

### Constraints

- Public assessments support only `interval=1day`.
- The assessment layer consumes one Phase 3 snapshot and never calls a provider directly.
- Assessments are calculated on request and are not persisted.
