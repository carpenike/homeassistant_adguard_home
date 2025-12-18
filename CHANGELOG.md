# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.7] - 2025-12-18

### Fixed

- **Per-client settings wiped on toggle** - When toggling per-client switches (filtering, parental, etc.), the `blocked_services_schedule`, `safe_search`, `upstreams`, `ignore_querylog`, and `ignore_statistics` fields were not being preserved. Now all client settings are properly retained when updating any individual setting
- **Filter list names wiped when toggling** - The `set_filter_enabled` API call was missing the required `name` field per the `FilterSetUrlData` schema, causing filter names to be set to empty string when enabling/disabling filter lists
- **Global blocked services schedule wiped on toggle** - When toggling individual blocked service switches, the `blocked_services_schedule` was not being passed to the API, potentially wiping time-based schedules
- **`set_client_blocked_services` service wiped client settings** - The service handler was not preserving `safe_search`, `upstreams`, `blocked_services_schedule`, `upstreams_cache_enabled`, `upstreams_cache_size`, `ignore_querylog`, and `ignore_statistics` fields when updating a client's blocked services
- **`DnsInfo.rate_limit` not populated from API** - Fixed key name mismatch: API returns `ratelimit` but code was looking for `rate_limit`
- **Deprecated blocked services API endpoints** - Updated to use non-deprecated `/control/blocked_services/get` and `/control/blocked_services/update` endpoints instead of `/list` and `/set`
- **Coordinator missing client fields** - Added missing `safe_search`, `blocked_services_schedule`, `upstreams`, `upstreams_cache_enabled`, `upstreams_cache_size`, `ignore_querylog`, and `ignore_statistics` fields to coordinator client data

### Changed

- **Removed `uid` field from `AdGuardHomeClient` model** - The `uid` field exists only in AdGuard Home's config file but is NOT returned by the HTTP API, causing unnecessary empty values
- **Refactored `add_client`/`update_client` to use `to_dict()`** - Cleaner code using the model's serialization method instead of manual dict construction

### Added

- `to_dict()` method to `AdGuardHomeClient` model - Proper serialization for API requests with correct field handling
- `blocked_services_schedule` field to `AdGuardHomeClient` model - Preserves per-client blocked services schedules (required since AdGuard Home v0.107.37)
- `safe_search` field to `AdGuardHomeClient` model - Supports the new safe search settings object (v0.107.52+) with per-engine toggles
- `upstreams` field to `AdGuardHomeClient` model - Preserves per-client custom DNS upstream servers
- `ignore_querylog` and `ignore_statistics` fields to `AdGuardHomeClient` model - Preserves privacy settings for individual clients
- `upstreams_cache_enabled` and `upstreams_cache_size` fields to client API methods - Preserves per-client upstream cache settings
- Optional `name` parameter to `set_filter_enabled()` API method - Allows preserving filter names when toggling
- Tests for `AdGuardHomeClient.to_dict()` method (8 new tests)
- Tests for coordinator client data transformation (2 new tests)
- Tests for new client fields including schedule preservation, safe_search object, and upstreams
- Tests for filter name preservation on toggle
- Tests for blocked services schedule preservation on toggle

## [0.2.6] - 2025-12-18

### Fixed

- **Safe Browsing, Parental Control, and Safe Search switches always show OFF** - The integration incorrectly expected these status fields in the `/control/status` API response, but AdGuard Home returns them from separate endpoints (`/control/safebrowsing/status`, `/control/parental/status`, `/control/safesearch/status`). Now fetches each status from its correct endpoint
- **DNS Cache switch not working on older AdGuard Home versions** - The `cache_enabled` API field only exists in AdGuard Home v0.107.65+. The DNS Cache switch is now hidden on older versions instead of showing with limited functionality
- **Protection toggle shows error toast despite working** - The `/control/protection` endpoint returns `OK` as `text/plain` instead of JSON. The API client now checks the `Content-Type` header before attempting JSON parsing, preventing "Expecting value: line 1 column 1 (char 0)" errors

### Changed

- Removed obsolete `safebrowsing_enabled`, `parental_enabled`, `safesearch_enabled` fields from `AdGuardHomeStatus` model since they were never returned by the API
- Added `safebrowsing_enabled`, `parental_enabled`, `safesearch_enabled` fields to `AdGuardHomeData` coordinator data class
- Added `get_safebrowsing_status()` and `get_parental_status()` methods to API client
- Added `supports_cache_enabled` version feature flag (v0.107.65+)
- DNS Cache switch is now filtered out on AdGuard Home versions < v0.107.65
- Query Logging and Statistics switches are now filtered out on AdGuard Home versions < v0.107.30 (these features require API endpoints that don't exist in older versions)

## [0.2.5] - 2025-12-18

### Fixed

- **405 Method Not Allowed on Safe Search toggle** - Use correct endpoint `/control/safesearch/status` for GET requests (not `/settings` which only supports PUT). The global Safe Search toggle now works properly

## [0.2.4] - 2025-12-18

### Fixed

- **Parental/Safe Browsing toggles fail on AdGuard Home v0.107.62** - aiohttp still sends `Content-Type: application/octet-stream` for empty POST bodies even with `skip_auto_headers`. Now skip both `Content-Type` and `Content-Length` headers to ensure truly empty requests

## [0.2.3] - 2025-12-18

### Fixed

- **415 Unsupported Media Type error (aiohttp fix)** - Use `skip_auto_headers={"Content-Type"}` to prevent aiohttp from auto-adding Content-Type header on POST requests without a body. This is the correct solution per aiohttp documentation
- **400 Bad Request on client update** - Fixed `/control/clients/update` API payload to include all required Client schema fields and `blocked_services_schedule` when using per-client blocked services (required since AdGuard Home v0.107.37)
- **Sensor state_class warnings** - Changed `dns_queries`, `blocked_queries`, `safe_browsing_blocked`, and `parental_blocked` sensors from `SensorStateClass.TOTAL_INCREASING` to `SensorStateClass.TOTAL` since AdGuard Home statistics can be reset manually or periodically

### Added

- Tests for `skip_auto_headers` usage on no-body POST requests
- Tests for `blocked_services_schedule` handling in `add_client` and `update_client`
- Tests verifying sensor state_class configuration for resettable statistics

## [0.2.2] - 2025-12-18

### Added

- **Configured Clients sensor** - New sensor that exposes all configured AdGuard Home clients with their settings including `blocked_services`, enabling templates to access per-client blocked service data

### Fixed

- **NoneType error on startup** - Fixed `'NoneType' object is not iterable` error when AdGuard Home API returns `null` for `filters` or `whitelist_filters` arrays in the filtering status. Now handles null values gracefully by treating them as empty lists
- **Invalid unit for DNS Cache Size sensor** - Changed native unit from `bytes` to `B` to comply with Home Assistant's `DATA_SIZE` device class requirements

## [0.2.1] - 2025-12-18

### Fixed

- **415 Unsupported Media Type error (complete fix)** - Fixed API client to completely omit the `json` parameter when making POST requests without a body, rather than passing `json=None`. This fully resolves the 415 error on endpoints like `/control/parental/enable` and `/control/safebrowsing/enable`

### Added

- Additional regression tests for API request parameter handling

## [0.2.0] - 2025-12-17

### Added

- Per-client blocked service switches for granular control (e.g., block YouTube for specific clients)
  - Individual switch for each service per client
  - Automatically unavailable when client uses global blocked services setting
  - Organized under EntityCategory.CONFIG
- Debug logging when switches become unavailable due to missing data
- New tests for switch availability and API Content-Type handling (10 new tests)

### Fixed

- **415 Unsupported Media Type error** - Fixed API client sending `Content-Type: application/json` header on POST requests without a body (e.g., `/control/parental/enable`), which caused all entities to become unavailable on newer AdGuard Home versions
- Switch entities now properly report unavailable state when required data is missing (e.g., stats_config on older AdGuard Home versions)

## [0.1.1] - 2025-12-17

### Added

- Support for entering full URLs in config flow (e.g., `https://adguard.local:8443`)
  - Automatically extracts host, sets SSL, and configures port from URL scheme
  - Supports `http://` and `https://` prefixes
  - Extracts custom ports from URL (e.g., `:8443`)

## [0.1.0] - 2025-12-17

### Added

- Initial release
- **Sensors**
  - DNS Queries count
  - Blocked Queries count
  - Blocked Percentage
  - Average Processing Time
  - Safe Browsing Blocked count
  - Parental Control Blocked count
  - Top Blocked Domain (with top 10 in attributes)
  - Top Client (with top 10 in attributes)
  - DNS Rewrites count (with rules in attributes)
  - DHCP Leases count (with lease details in attributes)
  - DHCP Static Leases count
  - Recent Queries count (with query details in attributes)

- **Switches**
  - Protection toggle
  - Filtering toggle
  - Safe Browsing toggle
  - Parental Control toggle
  - Safe Search toggle
  - Per-service blocked service toggles (Facebook, TikTok, YouTube, etc.)
  - Per-client filtering switches (6 switches per client)

- **Binary Sensors**
  - Running status
  - Protection Enabled status
  - DHCP Enabled status

- **Services**
  - `add_filter_url` - Add filter list URL
  - `remove_filter_url` - Remove filter list URL
  - `refresh_filters` - Refresh all filter lists
  - `set_blocked_services` - Set globally blocked services
  - `set_client_blocked_services` - Set per-client blocked services
  - `add_dns_rewrite` - Add DNS rewrite rule
  - `remove_dns_rewrite` - Remove DNS rewrite rule

- **Other**
  - Config flow with UI configuration
  - Reauthentication support
  - Diagnostics support with sensitive data redaction
  - Full test coverage (114 tests)

[Unreleased]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.7...HEAD
[0.2.7]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.6...v0.2.7
[0.2.6]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.5...v0.2.6
[0.2.5]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/carpenike/homeassistant_adguard_home/releases/tag/v0.1.0
