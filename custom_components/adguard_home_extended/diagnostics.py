"""Diagnostics support for AdGuard Home Extended."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

if TYPE_CHECKING:
    from . import AdGuardHomeConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME}

# Redact sensitive info from clients (IPs, MACs, hostnames)
TO_REDACT_NESTED = {"ids", "mac", "ip", "hostname", "IP"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: AdGuardHomeConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    data = coordinator.data

    diagnostics_data: dict[str, Any] = {
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "data": {},
    }

    if data:
        # Status
        if data.status:
            diagnostics_data["data"]["status"] = {
                "protection_enabled": data.status.protection_enabled,
                "running": data.status.running,
                "dns_port": data.status.dns_port,
                "http_port": data.status.http_port,
                "version": data.status.version,
                # Redact DNS addresses as they may reveal network info
                "dns_addresses": "**REDACTED**",
            }

        # Stats
        if data.stats:
            diagnostics_data["data"]["stats"] = {
                "dns_queries": data.stats.dns_queries,
                "blocked_filtering": data.stats.blocked_filtering,
                "replaced_safebrowsing": data.stats.replaced_safebrowsing,
                "replaced_parental": data.stats.replaced_parental,
                "replaced_safesearch": data.stats.replaced_safesearch,
                "avg_processing_time": data.stats.avg_processing_time,
                # Don't include top domains/clients as they may be sensitive
                "top_queried_domains_count": len(data.stats.top_queried_domains),
                "top_blocked_domains_count": len(data.stats.top_blocked_domains),
                "top_clients_count": len(data.stats.top_clients),
            }

        # Filtering
        if data.filtering:
            diagnostics_data["data"]["filtering"] = {
                "enabled": data.filtering.enabled,
                "interval": data.filtering.interval,
                "filters_count": len(data.filtering.filters),
                "whitelist_filters_count": len(data.filtering.whitelist_filters),
                "user_rules_count": len(data.filtering.user_rules),
            }

        # Blocked services
        diagnostics_data["data"]["blocked_services"] = {
            "blocked_count": len(data.blocked_services),
            "blocked_services": data.blocked_services,
            "available_services_count": len(data.available_services),
        }

        # Clients (redact sensitive info)
        diagnostics_data["data"]["clients"] = {
            "count": len(data.clients),
            "clients": [
                {
                    "name": c.get("name"),
                    "filtering_enabled": c.get("filtering_enabled"),
                    "parental_enabled": c.get("parental_enabled"),
                    "safebrowsing_enabled": c.get("safebrowsing_enabled"),
                    "safesearch_enabled": c.get("safesearch_enabled"),
                    "blocked_services_count": len(c.get("blocked_services", [])),
                    # Redact IDs as they contain IPs/MACs
                    "ids": "**REDACTED**",
                }
                for c in data.clients
            ],
        }

        # DHCP
        if data.dhcp:
            diagnostics_data["data"]["dhcp"] = {
                "enabled": data.dhcp.enabled,
                "interface_name": data.dhcp.interface_name,
                "leases_count": len(data.dhcp.leases),
                "static_leases_count": len(data.dhcp.static_leases),
                # Don't include actual lease data as it contains IPs/MACs
            }

        # DNS Rewrites
        diagnostics_data["data"]["rewrites"] = {
            "count": len(data.rewrites),
            # Include rewrite domains but not answers (may be IPs)
            "domains": [r.domain for r in data.rewrites[:20]],
        }

        # Query log summary
        diagnostics_data["data"]["query_log"] = {
            "entries_fetched": len(data.query_log),
            # Don't include actual queries as they may be sensitive
        }

    return diagnostics_data
