# AdGuard Home Extended for Home Assistant

<p align="center">
  <img src="images/logo.png" alt="AdGuard Home Extended Logo" width="200">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Badge"></a>
  <a href="https://github.com/carpenike/homeassistant_adguard_home/releases"><img src="https://img.shields.io/github/release/carpenike/homeassistant_adguard_home.svg" alt="GitHub Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/carpenike/homeassistant_adguard_home.svg" alt="License"></a>
</p>

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
| **Per-service blocking switches** | ❌ | ✅ |
| **Per-client filtering controls** | ❌ | ✅ |
| **Filter list management** | ❌ | ✅ |
| **DNS rewrite management** | ❌ | ✅ |
| **DNS configuration controls** | ❌ | ✅ |
| **Query log services** | ❌ | ✅ |
| **DHCP monitoring** | ❌ | ✅ |
| **Top blocked domains/clients** | ❌ | ✅ |
| **Diagnostics support** | ❌ | ✅ |

### Entities

#### Sensors

| Sensor | Description | Attributes |
|--------|-------------|------------|
| **DNS Queries** | Total DNS queries processed | - |
| **Blocked Queries** | Number of blocked queries | - |
| **Blocked Percentage** | Percentage of queries blocked | - |
| **Average Processing Time** | DNS query processing time (ms) | - |
| **Safe Browsing Blocked** | Queries blocked by Safe Browsing | - |
| **Parental Control Blocked** | Queries blocked by Parental Control | - |
| **Top Blocked Domain** | Most blocked domain | `top_blocked_domains` (top N list) |
| **Top Client** | Most active client | `top_clients` (top N list) |
| **DNS Rewrites** | Number of DNS rewrite rules | `rewrites` (domain/answer pairs) |
| **DHCP Leases** | Active DHCP leases count | `leases` (mac, ip, hostname, expires) |
| **DHCP Static Leases** | Static DHCP reservations count | `static_leases` (mac, ip, hostname) |
| **Recent Queries** | Recent query log entries count | `recent_queries` (domain, client, reason) |
| **Upstream DNS Servers** | Number of upstream DNS servers | `upstream_servers` list |
| **Bootstrap DNS Servers** | Number of bootstrap DNS servers | `bootstrap_servers` list |
| **DNS Cache Size** | DNS cache size in bytes | - |
| **DNS Rate Limit** | DNS rate limit (req/s) | - |
| **DNS Blocking Mode** | Current blocking mode | - |

#### Switches

**Global Protection Switches:**

| Switch | Description |
|--------|-------------|
| **Protection** | Master protection toggle |
| **Filtering** | DNS filtering toggle |
| **Safe Browsing** | Malware/phishing protection |
| **Parental Control** | Content filtering for children |
| **Safe Search** | Enforce safe search on search engines |

**DNS Configuration Switches:**

| Switch | Description |
|--------|-------------|
| **DNS Cache** | Enable/disable DNS caching |
| **DNSSEC** | Enable/disable DNSSEC validation |
| **EDNS Client Subnet** | Enable/disable EDNS Client Subnet |
| **Query Logging** | Enable/disable query logging |
| **Statistics Collection** | Enable/disable statistics collection |

**Dynamic Switches (auto-created):**

| Switch Type | Description |
|-------------|-------------|
| **Block [Service]** | One switch per blockable service (Facebook, YouTube, TikTok, etc.) |
| **Filter: [Name]** | One switch per filter list to enable/disable |
| **Whitelist: [Name]** | One switch per whitelist to enable/disable |
| **DNS Rewrite: [Domain]** | One switch per DNS rewrite rule to enable/disable |

#### Per-Client Switches

For each client configured in AdGuard Home, the integration creates:

| Switch | Description |
|--------|-------------|
| **[Client] Filtering** | Enable/disable filtering for this client |
| **[Client] Parental Control** | Enable/disable parental control for this client |
| **[Client] Safe Browsing** | Enable/disable safe browsing for this client |
| **[Client] Safe Search** | Enable/disable safe search for this client |
| **[Client] Use Global Settings** | Use global settings vs client-specific |
| **[Client] Use Global Blocked Services** | Use global blocked services vs client-specific |

#### Binary Sensors

| Binary Sensor | Description |
|---------------|-------------|
| **Running** | AdGuard Home service status |
| **Protection Enabled** | Overall protection status |
| **DHCP Enabled** | DHCP server status |

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

1. Download the `custom_components/adguard_home_extended` folder from the [latest release](https://github.com/carpenike/homeassistant_adguard_home/releases)
2. Copy it to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

### Initial Setup

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

### Options

After setup, you can configure additional options via the integration's **Configure** button:

| Option | Description | Default |
|--------|-------------|---------|
| **Scan Interval** | How often to poll AdGuard Home (seconds) | 30 |
| **Query Log Limit** | Max query log entries to fetch | 100 |
| **Top Items Limit** | Max items in top clients/domains attributes | 10 |
| **List Items Limit** | Max items in rewrite/lease list attributes | 20 |

## Services

### `adguard_home_extended.set_blocked_services`

Set the list of services to block globally with optional schedule.

```yaml
service: adguard_home_extended.set_blocked_services
data:
  services:
    - tiktok
    - instagram
    - facebook
  # Optional: schedule (v0.107.56+)
  schedule:
    time_zone: "Local"
    mon:
      start: 32400000    # 9:00 AM in ms
      end: 61200000      # 5:00 PM in ms
```

### `adguard_home_extended.set_client_blocked_services`

Set blocked services for a specific client.

```yaml
service: adguard_home_extended.set_client_blocked_services
data:
  client_name: "Kids Tablet"
  services:
    - tiktok
    - youtube
    - instagram
```

### `adguard_home_extended.add_filter_url`

Add a new filter list URL.

```yaml
service: adguard_home_extended.add_filter_url
data:
  name: "My Custom Filter"
  url: "https://example.com/filter.txt"
  whitelist: false  # true for allowlist
```

### `adguard_home_extended.remove_filter_url`

Remove a filter list URL.

```yaml
service: adguard_home_extended.remove_filter_url
data:
  url: "https://example.com/filter.txt"
  whitelist: false
```

### `adguard_home_extended.refresh_filters`

Force refresh all filter lists.

```yaml
service: adguard_home_extended.refresh_filters
```

### `adguard_home_extended.add_dns_rewrite`

Add a DNS rewrite rule.

```yaml
service: adguard_home_extended.add_dns_rewrite
data:
  domain: "ads.example.com"
  answer: "0.0.0.0"  # or another domain/IP
```

### `adguard_home_extended.remove_dns_rewrite`

Remove a DNS rewrite rule.

```yaml
service: adguard_home_extended.remove_dns_rewrite
data:
  domain: "ads.example.com"
  answer: "0.0.0.0"
```

### `adguard_home_extended.check_host`

Check how a domain would be filtered.

```yaml
service: adguard_home_extended.check_host
data:
  domain: "doubleclick.net"
  # Optional (v0.107.58+):
  client: "192.168.1.100"
  qtype: "A"  # A, AAAA, CNAME, MX, TXT, etc.
```

**Response** is returned as a service response containing:
- `reason`: Why the domain was filtered
- `rules`: Matching filter rules
- `service_name`: Blocked service name (if applicable)

### `adguard_home_extended.get_query_log`

Retrieve DNS query log entries.

```yaml
service: adguard_home_extended.get_query_log
data:
  limit: 100
  offset: 0
  search: "google.com"  # optional domain filter
  response_status: "all"  # or "filtered" for blocked only
```

### `adguard_home_extended.clear_query_log`

Clear all query log entries (cannot be undone).

```yaml
service: adguard_home_extended.clear_query_log
```

### `adguard_home_extended.reset_stats`

Reset all statistics counters (cannot be undone).

```yaml
service: adguard_home_extended.reset_stats
```

### Multiple Instances

When multiple AdGuard Home instances are configured, add `entry_id` to specify which instance:

```yaml
service: adguard_home_extended.set_blocked_services
data:
  entry_id: "abc123..."  # Get from integration page
  services:
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

### Block Services for Kids at Bedtime

```yaml
automation:
  - alias: "Kids Bedtime Blocking"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: adguard_home_extended.set_client_blocked_services
        data:
          client_name: "Kids Tablet"
          services:
            - youtube
            - tiktok
            - twitch
            - netflix
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

### Dynamic DNS Rewrite for Development

```yaml
automation:
  - alias: "Enable Dev DNS Override"
    trigger:
      - platform: state
        entity_id: input_boolean.development_mode
        to: "on"
    action:
      - service: adguard_home_extended.add_dns_rewrite
        data:
          domain: "api.myapp.com"
          answer: "192.168.1.100"

  - alias: "Disable Dev DNS Override"
    trigger:
      - platform: state
        entity_id: input_boolean.development_mode
        to: "off"
    action:
      - service: adguard_home_extended.remove_dns_rewrite
        data:
          domain: "api.myapp.com"
          answer: "192.168.1.100"
```

## Diagnostics

This integration supports Home Assistant's diagnostics feature. To download diagnostics:

1. Go to **Settings** → **Devices & Services**
2. Click on the AdGuard Home Extended integration
3. Click the three dots menu → **Download diagnostics**

Diagnostics include (with sensitive data redacted):
- Configuration entry details
- Coordinator status and update times
- AdGuard Home version and feature flags
- Statistics and filtering status
- Client and DHCP information (IPs/MACs redacted)

## Compatibility

*Last verified: December 2025*

### Version Requirements

| Component | Minimum Version | Recommended | Tested |
|-----------|----------------|-------------|--------|
| **Home Assistant** | 2025.1.0 | 2025.12.0+ | ✅ 2025.12 |
| **AdGuard Home** | 0.107.30 | 0.107.69+ | ✅ 0.107.69 |

### Home Assistant Compatibility

This integration follows current Home Assistant best practices:

- ✅ `DataUpdateCoordinator` with explicit `config_entry` parameter
- ✅ `entry.runtime_data` pattern for typed coordinator access
- ✅ `_async_setup()` method for one-time coordinator initialization
- ✅ `CoordinatorEntity` base class for all entities
- ✅ `translation_key` pattern for entity names
- ✅ Proper `unique_id` and `device_info` for device registry
- ✅ Options flow for runtime configuration
- ✅ DHCP discovery support
- ✅ Re-authentication flow for credential updates
- ✅ Diagnostics support

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

## Troubleshooting

### Common Issues

**"Cannot connect to AdGuard Home"**
- Verify the host and port are correct
- Check if AdGuard Home is running
- Ensure no firewall is blocking the connection
- If using SSL, verify certificate settings

**"Invalid authentication"**
- Check username and password
- Ensure the account has admin privileges
- Try re-authenticating via the integration's Configure menu

**Entities show "Unavailable"**
- Check the AdGuard Home service status
- Review Home Assistant logs for connection errors
- Try reloading the integration

**Missing blocked services**
- Available services are fetched dynamically from AdGuard Home
- Newer services (ChatGPT, Claude, etc.) require AdGuard Home v0.107.66+
- Check your AdGuard Home version for service availability

### Debug Logging

Enable debug logging by adding to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.adguard_home_extended: debug
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is a community project and is not affiliated with AdGuard. Use at your own risk.
