# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/carpenike/homeassistant_adguard_home/releases/tag/v0.1.0
