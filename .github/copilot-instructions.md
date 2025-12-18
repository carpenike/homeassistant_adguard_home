# AdGuard Home Extended Integration for Home Assistant

## Project Overview
This is a custom Home Assistant integration for HACS (Home Assistant Community Store) that provides extended functionality for AdGuard Home instances beyond the official core integration. The integration communicates with AdGuard Home's REST API to provide granular control over DNS filtering, client management, and network protection features.

## Tech Stack
- **Language**: Python 3.12+
- **Framework**: Home Assistant Custom Component
- **Distribution**: HACS (Home Assistant Community Store)
- **API Communication**: aiohttp (async HTTP client)
- **Testing**: pytest, pytest-asyncio, pytest-homeassistant-custom-component

## Project Structure
```
custom_components/
└── adguard_home_extended/
    ├── __init__.py           # Integration entry point, setup/unload, services
    ├── manifest.json         # Integration metadata (HACS/HA required)
    ├── config_flow.py        # UI configuration wizard + OptionsFlow
    ├── coordinator.py        # DataUpdateCoordinator for API polling
    ├── const.py              # Constants, domain, default values
    ├── version.py            # Version detection utilities
    ├── sensor.py             # Sensor entities (stats, query counts, DHCP)
    ├── switch.py             # Switch entities (protection, DNS config toggles)
    ├── binary_sensor.py      # Binary sensors (status indicators)
    ├── blocked_services.py   # Per-service blocking switches
    ├── client_entities.py    # Per-client filtering switches
    ├── filter_lists.py       # Filter list enable/disable switches
    ├── diagnostics.py        # Diagnostics data for troubleshooting
    ├── services.yaml         # Service definitions
    ├── strings.json          # Translations (en)
    ├── translations/         # Localization files
    │   └── en.json
    └── api/                   # AdGuard Home API client
        ├── __init__.py
        ├── client.py         # Main API client class
        └── models.py         # Data models/types
tests/
└── ...                       # pytest test files
```

## Coding Standards

### Python Style
- Follow PEP 8 and Home Assistant's coding style
- Use type hints for all function signatures
- Use dataclasses or TypedDict for data structures
- Prefer `async`/`await` patterns throughout - NO blocking calls
- Use `aiohttp.ClientSession` for HTTP requests (injected from HA)

### Home Assistant Patterns
- Use `DataUpdateCoordinator` for all polling operations
- Pass `config_entry` parameter to coordinator constructor
- Use `entry.runtime_data` pattern (not `hass.data[DOMAIN]`)
- Entities must have stable `unique_id` based on device identifiers
- Use `_attr_*` class attributes for entity properties
- Implement proper `device_info` returning `DeviceInfo` dataclass
- Use `ConfigEntry` for configuration storage
- Handle `ConfigEntryAuthFailed` for reauthentication flows
- Use `FlowResult` type hint (from `data_entry_flow`) for config flows
- Use `OptionsFlow` base class (not deprecated `OptionsFlowWithConfigEntry`)
- Register services in `async_setup_entry`, unregister in `async_unload_entry`
- Use `EntityCategory.DIAGNOSTIC` for diagnostic sensors
- Support `async_migrate_entry` for config version changes

### Entity Naming
- Use `_attr_has_entity_name = True` for proper name composition
- Entity names should be short and descriptive (e.g., "Protection", "DNS Queries")
- Device names should identify the AdGuard Home instance

### Error Handling
- Catch specific exceptions, not bare `except:`
- Use `UpdateFailed` exception in coordinator's `_async_update_data`
- Log warnings once on connection failure, not repeatedly
- Implement graceful degradation when API is unavailable

## AdGuard Home API Reference

### Authentication
- Basic Auth: `Authorization: Basic <base64(username:password)>`
- All endpoints under `/control/` prefix
- Content-Type: `application/json`

### Key Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/control/status` | GET | Server status, protection state |
| `/control/stats` | GET | DNS statistics (queries, blocked) |
| `/control/querylog` | GET | Query log entries |
| `/control/protection` | POST | Enable/disable protection |
| `/control/safebrowsing/enable` | POST | Toggle safe browsing |
| `/control/safebrowsing/disable` | POST | Toggle safe browsing |
| `/control/parental/enable` | POST | Toggle parental control |
| `/control/parental/disable` | POST | Toggle parental control |
| `/control/safesearch/enable` | POST | Toggle safe search |
| `/control/safesearch/disable` | POST | Toggle safe search |
| `/control/safesearch/settings` | GET/PUT | Per-engine safe search config |
| `/control/filtering/add_url` | POST | Add filter list |
| `/control/filtering/remove_url` | POST | Remove filter list |
| `/control/filtering/set_url` | POST | Update filter list (enable/disable) |
| `/control/clients` | GET | List clients |
| `/control/clients/add` | POST | Add client config |
| `/control/clients/update` | POST | Update client config |
| `/control/clients/search` | GET | Search clients (preferred over /find) |
| `/control/blocked_services/all` | GET | List blockable services |
| `/control/blocked_services/set` | POST | Set blocked services (schedule support) |
| `/control/rewrite/list` | GET | List DNS rewrites |
| `/control/rewrite/add` | POST | Add DNS rewrite rule |
| `/control/rewrite/delete` | POST | Remove DNS rewrite rule |
| `/control/rewrite/update` | POST | Update DNS rewrite rule |
| `/control/dhcp/status` | GET | DHCP status and leases |
| `/control/dns_info` | GET | DNS configuration (cache, upstream) |
| `/control/dns_config` | POST | Update DNS configuration |
| `/control/querylog` | GET | Query log with filters |
| `/control/stats` | GET | DNS statistics |
| `/control/stats/reset` | POST | Reset statistics |
| `/control/querylog/clear` | POST | Clear query log |

## Task Tracking with Beads

This project uses `bd` (beads) for all task tracking. **Do NOT use markdown TODOs or task lists.**

### Workflow
```bash
bd ready                    # Find unblocked work
bd create "Task" -t task    # Create new issue
bd update <id> --status in_progress
bd close <id> --reason "Done"
bd dep add <child> <parent> # Add dependency
```

### Issue Types
- `epic` - Large features with subtasks
- `feature` - New functionality
- `bug` - Something broken
- `task` - Work items (docs, refactoring)
- `chore` - Maintenance

### Priorities
- `0` - Critical (blocking, security)
- `1` - High (major features)
- `2` - Medium (default)
- `3` - Low (polish)
- `4` - Backlog

## Testing Requirements
- All new features require tests
- Use `pytest-homeassistant-custom-component` fixtures
- Mock external API calls
- Test config flow validation
- Test coordinator error handling

## HACS Requirements
- `manifest.json` must include `version` field
- Repository must have GitHub releases
- README must document installation and configuration
- Add to `home-assistant/brands` for icons

## Changelog Management

This project maintains a manual `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

### Workflow
1. **During development**: Add entries under `## [Unreleased]` as changes are made
2. **At release time**: Rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and create a new empty `[Unreleased]` section

### Entry Categories
Use these standard sections under each version:
- `### Added` - New features
- `### Changed` - Changes in existing functionality
- `### Deprecated` - Soon-to-be removed features
- `### Removed` - Now removed features
- `### Fixed` - Bug fixes
- `### Security` - Vulnerability fixes

### Guidelines
- Write entries for users, not developers (focus on impact, not implementation)
- Group related changes together
- Use bullet points with brief, clear descriptions
- Link to issues/PRs when relevant: `([#123](link))`
- The release workflow extracts changelog content for GitHub release notes
