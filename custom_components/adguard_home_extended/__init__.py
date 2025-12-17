"""AdGuard Home Extended integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import AdGuardHomeDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]

# Service constants
SERVICE_SET_BLOCKED_SERVICES = "set_blocked_services"
SERVICE_ADD_FILTER_URL = "add_filter_url"
SERVICE_REMOVE_FILTER_URL = "remove_filter_url"
SERVICE_REFRESH_FILTERS = "refresh_filters"
SERVICE_SET_CLIENT_BLOCKED_SERVICES = "set_client_blocked_services"
SERVICE_ADD_DNS_REWRITE = "add_dns_rewrite"
SERVICE_REMOVE_DNS_REWRITE = "remove_dns_rewrite"

ATTR_SERVICES = "services"
ATTR_NAME = "name"
ATTR_URL = "url"
ATTR_WHITELIST = "whitelist"
ATTR_CLIENT_NAME = "client_name"
ATTR_DOMAIN = "domain"
ATTR_ANSWER = "answer"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AdGuard Home Extended from a config entry."""
    # Import here to avoid circular imports
    from .api.client import AdGuardHomeClient

    session = async_get_clientsession(hass, verify_ssl=entry.data.get(CONF_VERIFY_SSL, True))

    client = AdGuardHomeClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        username=entry.data.get(CONF_USERNAME),
        password=entry.data.get(CONF_PASSWORD),
        use_ssl=entry.data.get(CONF_SSL, False),
        session=session,
    )

    coordinator = AdGuardHomeDataUpdateCoordinator(hass, client, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_setup_services(hass, coordinator)

    return True


async def _async_setup_services(
    hass: HomeAssistant, coordinator: AdGuardHomeDataUpdateCoordinator
) -> None:
    """Set up services for AdGuard Home Extended."""

    async def handle_set_blocked_services(call: ServiceCall) -> None:
        """Handle the set_blocked_services service call."""
        services = call.data.get(ATTR_SERVICES, [])
        await coordinator.client.set_blocked_services(services)
        await coordinator.async_request_refresh()

    async def handle_add_filter_url(call: ServiceCall) -> None:
        """Handle the add_filter_url service call."""
        name = call.data[ATTR_NAME]
        url = call.data[ATTR_URL]
        whitelist = call.data.get(ATTR_WHITELIST, False)
        await coordinator.client.add_filter_url(name, url, whitelist)
        await coordinator.async_request_refresh()

    async def handle_remove_filter_url(call: ServiceCall) -> None:
        """Handle the remove_filter_url service call."""
        url = call.data[ATTR_URL]
        whitelist = call.data.get(ATTR_WHITELIST, False)
        await coordinator.client.remove_filter_url(url, whitelist)
        await coordinator.async_request_refresh()

    async def handle_refresh_filters(call: ServiceCall) -> None:
        """Handle the refresh_filters service call."""
        await coordinator.client.refresh_filters()
        await coordinator.async_request_refresh()

    async def handle_set_client_blocked_services(call: ServiceCall) -> None:
        """Handle the set_client_blocked_services service call."""
        from .api.models import AdGuardHomeClient as ClientConfig
        
        client_name = call.data[ATTR_CLIENT_NAME]
        services = call.data.get(ATTR_SERVICES, [])
        
        # Find the client in coordinator data
        if coordinator.data is None:
            return
        
        for client_data in coordinator.data.clients:
            if client_data.get("name") == client_name:
                # Build updated client config with new blocked services
                updated_client = ClientConfig(
                    name=client_data.get("name", ""),
                    ids=client_data.get("ids", []),
                    use_global_settings=client_data.get("use_global_settings", True),
                    filtering_enabled=client_data.get("filtering_enabled", True),
                    parental_enabled=client_data.get("parental_enabled", False),
                    safebrowsing_enabled=client_data.get("safebrowsing_enabled", False),
                    safesearch_enabled=client_data.get("safesearch_enabled", False),
                    use_global_blocked_services=False,  # Disable global when setting per-client
                    blocked_services=services,
                    tags=client_data.get("tags", []),
                )
                await coordinator.client.update_client(client_name, updated_client)
                await coordinator.async_request_refresh()
                return

    async def handle_add_dns_rewrite(call: ServiceCall) -> None:
        """Handle the add_dns_rewrite service call."""
        domain = call.data[ATTR_DOMAIN]
        answer = call.data[ATTR_ANSWER]
        await coordinator.client.add_rewrite(domain, answer)
        await coordinator.async_request_refresh()

    async def handle_remove_dns_rewrite(call: ServiceCall) -> None:
        """Handle the remove_dns_rewrite service call."""
        domain = call.data[ATTR_DOMAIN]
        answer = call.data[ATTR_ANSWER]
        await coordinator.client.delete_rewrite(domain, answer)
        await coordinator.async_request_refresh()

    # Only register once
    if not hass.services.has_service(DOMAIN, SERVICE_SET_BLOCKED_SERVICES):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BLOCKED_SERVICES,
            handle_set_blocked_services,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_SERVICES): vol.All(
                        cv.ensure_list, [cv.string]
                    ),
                }
            ),
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_ADD_FILTER_URL,
            handle_add_filter_url,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_NAME): cv.string,
                    vol.Required(ATTR_URL): cv.url,
                    vol.Optional(ATTR_WHITELIST, default=False): cv.boolean,
                }
            ),
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_REMOVE_FILTER_URL,
            handle_remove_filter_url,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_URL): cv.url,
                    vol.Optional(ATTR_WHITELIST, default=False): cv.boolean,
                }
            ),
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_FILTERS,
            handle_refresh_filters,
            schema=vol.Schema({}),
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_CLIENT_BLOCKED_SERVICES,
            handle_set_client_blocked_services,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_CLIENT_NAME): cv.string,
                    vol.Required(ATTR_SERVICES): vol.All(
                        cv.ensure_list, [cv.string]
                    ),
                }
            ),
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_ADD_DNS_REWRITE,
            handle_add_dns_rewrite,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_DOMAIN): cv.string,
                    vol.Required(ATTR_ANSWER): cv.string,
                }
            ),
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_REMOVE_DNS_REWRITE,
            handle_remove_dns_rewrite,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_DOMAIN): cv.string,
                    vol.Required(ATTR_ANSWER): cv.string,
                }
            ),
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
