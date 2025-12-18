# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/carpenike/homeassistant_adguard_home/releases/tag/v0.1.0
