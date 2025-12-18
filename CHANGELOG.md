# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/carpenike/homeassistant_adguard_home/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/carpenike/homeassistant_adguard_home/releases/tag/v0.1.0
