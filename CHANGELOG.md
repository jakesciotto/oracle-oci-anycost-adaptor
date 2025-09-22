# Changelog

## [1.0.0] - 2025-09-22

### Added
- Oracle OCI Usage API integration
- Daily automation script (`daily_sync.py`)
- CBF format transformation with CloudZero validation
- 5MB API limit handling with automatic batching
- Production-ready OCI to CloudZero cost sync

### Changed
- Field names: `billing/quantity` → `usage/amount`, `resource/compartment` → `resource/tag:compartment`
- Decimal formatting to avoid scientific notation
- Clean, minimal README for production use