"""AdGuard Home Extended integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
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
from homeassistant.exceptions import HomeAssistantError
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
ATTR_ENTRY_ID = "entry_id"


def _get_coordinator(
    hass: HomeAssistant, entry_id: str | None
) -> AdGuardHomeDataUpdateCoordinator:
    """Get coordinator for the given entry_id or the only one if not specified."""
    coordinators = hass.data.get(DOMAIN, {})

    if not coordinators:
        raise HomeAssistantError("No AdGuard Home instances configured")

    if entry_id:
        if entry_id not in coordinators:
            raise HomeAssistantError(f"AdGuard Home instance {entry_id} not found")
        return coordinators[entry_id]

    # If only one instance, use it; otherwise require entry_id
    if len(coordinators) == 1:
        return next(iter(coordinators.values()))

    raise HomeAssistantError(
        "Multiple AdGuard Home instances configured. Please specify entry_id."
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AdGuard Home Extended from a config entry."""
    # Import here to avoid circular imports
    from .api.client import AdGuardHomeClient

    session = async_get_clientsession(
        hass, verify_ssl=entry.data.get(CONF_VERIFY_SSL, True)
    )

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

    # Register services only once (first entry)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_BLOCKED_SERVICES):
        await _async_setup_services(hass)

    # Add update listener for options changes
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update - reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for AdGuard Home Extended."""

    async def handle_set_blocked_services(call: ServiceCall) -> None:
        """Handle the set_blocked_services service call."""
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        services = call.data.get(ATTR_SERVICES, [])
        await coordinator.client.set_blocked_services(services)
        await coordinator.async_request_refresh()

    async def handle_add_filter_url(call: ServiceCall) -> None:
        """Handle the add_filter_url service call."""
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        name = call.data[ATTR_NAME]
        url = call.data[ATTR_URL]
        whitelist = call.data.get(ATTR_WHITELIST, False)
        await coordinator.client.add_filter_url(name, url, whitelist)
        await coordinator.async_request_refresh()

    async def handle_remove_filter_url(call: ServiceCall) -> None:
        """Handle the remove_filter_url service call."""
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        url = call.data[ATTR_URL]
        whitelist = call.data.get(ATTR_WHITELIST, False)
        await coordinator.client.remove_filter_url(url, whitelist)
        await coordinator.async_request_refresh()

    async def handle_refresh_filters(call: ServiceCall) -> None:
        """Handle the refresh_filters service call."""
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        await coordinator.client.refresh_filters()
        await coordinator.async_request_refresh()

    async def handle_set_client_blocked_services(call: ServiceCall) -> None:
        """Handle the set_client_blocked_services service call."""
        from .api.models import AdGuardHomeClient as ClientConfig

        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        client_name = call.data[ATTR_CLIENT_NAME]
        services = call.data.get(ATTR_SERVICES, [])

        # Find the client in coordinator data
        if coordinator.data is None:
            raise HomeAssistantError("No data available from AdGuard Home")

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

        raise HomeAssistantError(f"Client '{client_name}' not found")

    async def handle_add_dns_rewrite(call: ServiceCall) -> None:
        """Handle the add_dns_rewrite service call."""
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        domain = call.data[ATTR_DOMAIN]
        answer = call.data[ATTR_ANSWER]
        await coordinator.client.add_rewrite(domain, answer)
        await coordinator.async_request_refresh()

    async def handle_remove_dns_rewrite(call: ServiceCall) -> None:
        """Handle the remove_dns_rewrite service call."""
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        domain = call.data[ATTR_DOMAIN]
        answer = call.data[ATTR_ANSWER]
        await coordinator.client.delete_rewrite(domain, answer)
        await coordinator.async_request_refresh()

    # Schema with optional entry_id for multi-instance support
    entry_id_schema = {vol.Optional(ATTR_ENTRY_ID): cv.string}

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BLOCKED_SERVICES,
        handle_set_blocked_services,
        schema=vol.Schema(
            {
                vol.Required(ATTR_SERVICES): vol.All(cv.ensure_list, [cv.string]),
                **entry_id_schema,
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
                **entry_id_schema,
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
                **entry_id_schema,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_FILTERS,
        handle_refresh_filters,
        schema=vol.Schema({**entry_id_schema}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CLIENT_BLOCKED_SERVICES,
        handle_set_client_blocked_services,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CLIENT_NAME): cv.string,
                vol.Required(ATTR_SERVICES): vol.All(cv.ensure_list, [cv.string]),
                **entry_id_schema,
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
                **entry_id_schema,
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
                **entry_id_schema,
            }
        ),
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Unregister services when last instance is removed
        if not hass.data[DOMAIN]:
            for service in [
                SERVICE_SET_BLOCKED_SERVICES,
                SERVICE_ADD_FILTER_URL,
                SERVICE_REMOVE_FILTER_URL,
                SERVICE_REFRESH_FILTERS,
                SERVICE_SET_CLIENT_BLOCKED_SERVICES,
                SERVICE_ADD_DNS_REWRITE,
                SERVICE_REMOVE_DNS_REWRITE,
            ]:
                hass.services.async_remove(DOMAIN, service)

    return unload_ok
