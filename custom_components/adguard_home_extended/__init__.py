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

ATTR_SERVICES = "services"
ATTR_NAME = "name"
ATTR_URL = "url"
ATTR_WHITELIST = "whitelist"


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

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
