# AdGuard Home Extended Integration for Home Assistant

## Project Overview
This is a custom Home Assistant integration for HACS (Home Assistant Community Store) that provides extended functionality for AdGuard Home instances beyond the official core integration. The integration communicates with AdGuard Home's REST API to provide granular control over DNS filtering, client management, and network protection features.

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: Home Assistant Custom Component
- **Distribution**: HACS (Home Assistant Community Store)
- **API Communication**: aiohttp (async HTTP client)
- **Testing**: pytest, pytest-asyncio, pytest-homeassistant-custom-component

## Project Structure
```
custom_components/
└── adguard_home_extended/
    ├── __init__.py           # Integration entry point, setup/unload
    ├── manifest.json         # Integration metadata (HACS/HA required)
    ├── config_flow.py        # UI configuration wizard
    ├── coordinator.py        # DataUpdateCoordinator for API polling
    ├── const.py              # Constants, domain, default values
    ├── sensor.py             # Sensor entities (stats, query counts)
    ├── switch.py             # Switch entities (protection toggles)
    ├── binary_sensor.py      # Binary sensors (status indicators)
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
- Entities must have stable `unique_id` based on device identifiers
- Use `_attr_*` class attributes for entity properties
- Implement proper `device_info` for device registry
- Use `ConfigEntry` for configuration storage
- Handle `ConfigEntryAuthFailed` for reauthentication flows

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
| `/control/filtering/add_url` | POST | Add filter list |
| `/control/filtering/remove_url` | POST | Remove filter list |
| `/control/clients` | GET | List clients |
| `/control/clients/add` | POST | Add client config |
| `/control/clients/update` | POST | Update client config |
| `/control/blocked_services/all` | GET | List blockable services |
| `/control/blocked_services/set` | POST | Set blocked services |
| `/control/rewrite/list` | GET | List DNS rewrites |
| `/control/dhcp/status` | GET | DHCP status and leases |

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
