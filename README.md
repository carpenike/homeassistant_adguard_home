# AdGuard Home Extended for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration that provides **extended functionality** for AdGuard Home beyond the official core integration. Control DNS filtering, manage blocked services, monitor query statistics, and configure per-client settings—all from Home Assistant.

## Features

### Beyond the Core Integration

This integration provides features not available in the official AdGuard Home integration:

| Feature | Core Integration | This Integration |
|---------|------------------|------------------|
| Protection toggle | ✅ | ✅ |
| Basic sensors | ✅ | ✅ |
| Safe Browsing toggle | ✅ | ✅ |
| Parental Control toggle | ✅ | ✅ |
| Safe Search toggle | ✅ | ✅ |
| **Blocked Services control** | ❌ | ✅ |
| **Per-client filtering** | ❌ | ✅ |
| **Filter list management** | ❌ | ✅ |
| **DNS rewrite management** | ❌ | ✅ |
| **Query log sensors** | ❌ | ✅ |
| **DHCP monitoring** | ❌ | ✅ |
| **Top blocked domains** | ❌ | ✅ |
| **Top clients** | ❌ | ✅ |

### Entities

#### Sensors
- **DNS Queries** - Total DNS queries processed
- **Blocked Queries** - Number of blocked queries
- **Blocked Percentage** - Percentage of queries blocked
- **Average Processing Time** - DNS query processing time
- **Safe Browsing Blocked** - Queries blocked by Safe Browsing
- **Parental Control Blocked** - Queries blocked by Parental Control
- **Top Blocked Domain** - Most blocked domain (with attributes for top 10)
- **Top Client** - Most active client (with attributes for top 10)

#### Switches
- **Protection** - Master protection toggle
- **Filtering** - DNS filtering toggle
- **Safe Browsing** - Malware/phishing protection
- **Parental Control** - Content filtering for children
- **Safe Search** - Enforce safe search on search engines

#### Binary Sensors
- **Running** - AdGuard Home service status
- **Protection Enabled** - Overall protection status
- **DHCP Enabled** - DHCP server status

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add this repository URL: `https://github.com/carpenike/homeassistant_adguard_home`
4. Select **Integration** as the category
5. Click **Add**
6. Search for "AdGuard Home Extended" and install
7. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/adguard_home_extended` folder
2. Copy it to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "AdGuard Home Extended"
4. Enter your AdGuard Home details:
   - **Host**: IP address or hostname
   - **Port**: Default is 3000
   - **Username**: (optional) Admin username
   - **Password**: (optional) Admin password
   - **Use SSL**: Enable if using HTTPS
   - **Verify SSL**: Disable for self-signed certificates

## Services

### `adguard_home_extended.add_filter_url`
Add a new filter list URL.

```yaml
service: adguard_home_extended.add_filter_url
data:
  name: "My Custom Filter"
  url: "https://example.com/filter.txt"
  whitelist: false
```

### `adguard_home_extended.remove_filter_url`
Remove a filter list URL.

### `adguard_home_extended.refresh_filters`
Force refresh all filter lists.

### `adguard_home_extended.set_blocked_services`
Set the list of blocked services.

```yaml
service: adguard_home_extended.set_blocked_services
data:
  services:
    - tiktok
    - instagram
    - facebook
```

## Example Automations

### Block Social Media During Work Hours

```yaml
automation:
  - alias: "Block Social Media 9-5"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: adguard_home_extended.set_blocked_services
        data:
          services:
            - facebook
            - instagram
            - tiktok
            - twitter

  - alias: "Unblock Social Media After Work"
    trigger:
      - platform: time
        at: "17:00:00"
    action:
      - service: adguard_home_extended.set_blocked_services
        data:
          services: []
```

### Notify on High Block Rate

```yaml
automation:
  - alias: "Notify High Block Rate"
    trigger:
      - platform: numeric_state
        entity_id: sensor.adguard_home_blocked_percentage
        above: 50
    action:
      - service: notify.mobile_app
        data:
          message: "AdGuard Home is blocking {{ states('sensor.adguard_home_blocked_percentage') }}% of queries"
```

## Compatibility

*Last verified: December 2025*

### Version Requirements

| Component | Minimum Version | Recommended | Tested |
|-----------|----------------|-------------|--------|
| **Home Assistant** | 2025.1.0 | 2025.12.0+ | ✅ 2025.12 (Dec 3, 2025) |
| **AdGuard Home** | 0.107.30 | 0.107.69+ | ✅ 0.107.69 (Oct 30, 2025) |

### Home Assistant 2025.12 Compatibility

This integration follows current Home Assistant best practices:

- ✅ `DataUpdateCoordinator` with explicit `config_entry` parameter (2025.11 deprecation ready)
- ✅ `entry.runtime_data` pattern for typed coordinator access
- ✅ `_async_setup()` method for one-time coordinator initialization (2024.8+)
- ✅ `CoordinatorEntity` base class for all entities
- ✅ `translation_key` pattern for entity names
- ✅ Proper `unique_id` and `device_info` for device registry

### Feature Availability by AdGuard Home Version

Some features require specific AdGuard Home versions:

| Feature | Required AGH Version | API Endpoint |
|---------|---------------------|--------------|
| Basic protection/filtering | 0.107.0+ | `/control/status`, `/control/protection` |
| Stats and query log config | 0.107.30+ | `/control/stats/config`, `/control/querylog/config` |
| SafeSearch per-engine settings | 0.107.43+ | `/control/safesearch/settings` |
| Ecosia safe search | 0.107.52+ | `/control/safesearch/settings` |
| Blocked services with schedule | 0.107.56+ | `/control/blocked_services/get` |
| Check host with client/qtype | 0.107.58+ | `/control/check_host` |
| DNS cache enable/disable | 0.107.65+ | `/control/dns_config` with `cache_enabled` |
| AI services blocking (ChatGPT, Claude) | 0.107.66+ | `/control/blocked_services/all` |
| DNS rewrite enable/disable | 0.107.68+ | `/control/rewrite/update` with `enabled` |
| Query log response_status filter | 0.107.68+ | `/control/querylog` |

### Integration Version History

| Integration | Min AGH | Min HA | Features Added |
|-------------|---------|--------|----------------|
| 0.1.x | 0.107.30 | 2025.1.0 | Initial release with full API support |

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is a community project and is not affiliated with AdGuard. Use at your own risk.
