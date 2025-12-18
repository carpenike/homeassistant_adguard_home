"""AdGuard Home Extended integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

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
SERVICE_CHECK_HOST = "check_host"
SERVICE_GET_QUERY_LOG = "get_query_log"

ATTR_SERVICES = "services"
ATTR_SCHEDULE = "schedule"
ATTR_NAME = "name"
ATTR_URL = "url"
ATTR_WHITELIST = "whitelist"
ATTR_CLIENT_NAME = "client_name"
ATTR_DOMAIN = "domain"
ATTR_ANSWER = "answer"
ATTR_ENTRY_ID = "entry_id"
ATTR_CLIENT = "client"
ATTR_QTYPE = "qtype"
ATTR_LIMIT = "limit"
ATTR_OFFSET = "offset"
ATTR_SEARCH = "search"
ATTR_RESPONSE_STATUS = "response_status"


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


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry to new version.

    This function is called when a config entry's version is lower than the current
    VERSION in the config flow. It provides a migration path for existing users when
    the config schema changes.
    """
    _LOGGER.debug(
        "Migrating AdGuard Home config entry from version %s", config_entry.version
    )

    if config_entry.version > 1:
        # Can't migrate from a future version
        _LOGGER.error(
            "Cannot migrate from version %s to version 1", config_entry.version
        )
        return False

    if config_entry.version == 1:
        # Current version, no migration needed
        # Future migrations from v1 -> v2 would go here
        pass

    _LOGGER.debug("Migration successful")
    return True


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

    # Register services before platforms to avoid race condition
    # Services should be available when entities are created
    if not hass.services.has_service(DOMAIN, SERVICE_SET_BLOCKED_SERVICES):
        await _async_setup_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
        schedule = call.data.get(ATTR_SCHEDULE)
        await coordinator.client.set_blocked_services(services, schedule)
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

    async def handle_check_host(call: ServiceCall) -> dict[str, Any]:
        """Handle the check_host service call.

        Check how a domain would be filtered, optionally for a specific client
        and query type (v0.107.58+).

        Returns:
            dict: Filtering result with reason, matching rules, etc.
        """
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        domain = call.data[ATTR_DOMAIN]
        client = call.data.get(ATTR_CLIENT)
        qtype = call.data.get(ATTR_QTYPE)

        result = await coordinator.client.check_host(
            name=domain,
            client=client,
            qtype=qtype,
        )

        # Fire an event with the result for automations
        hass.bus.async_fire(
            f"{DOMAIN}_check_host_result",
            {
                "domain": domain,
                "client": client,
                "qtype": qtype,
                "result": result,
            },
        )

        return result

    async def handle_get_query_log(call: ServiceCall) -> dict[str, Any]:
        """Handle the get_query_log service call.

        Retrieve paginated query log entries with optional filtering.

        Returns:
            dict: Query log entries with pagination metadata.
        """
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        limit = call.data.get(ATTR_LIMIT, 100)
        offset = call.data.get(ATTR_OFFSET, 0)
        search = call.data.get(ATTR_SEARCH)
        response_status = call.data.get(ATTR_RESPONSE_STATUS)

        entries = await coordinator.client.get_query_log(
            limit=limit,
            offset=offset,
            search=search,
            response_status=response_status,
        )

        return {
            "entries": entries,
            "count": len(entries),
            "limit": limit,
            "offset": offset,
            "search": search,
            "response_status": response_status,
        }

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

    hass.services.async_register(
        DOMAIN,
        SERVICE_CHECK_HOST,
        handle_check_host,
        schema=vol.Schema(
            {
                vol.Required(ATTR_DOMAIN): cv.string,
                vol.Optional(ATTR_CLIENT): cv.string,
                vol.Optional(ATTR_QTYPE): cv.string,
                **entry_id_schema,
            }
        ),
        supports_response=True,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_QUERY_LOG,
        handle_get_query_log,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_LIMIT, default=100): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=5000)
                ),
                vol.Optional(ATTR_OFFSET, default=0): vol.All(
                    vol.Coerce(int), vol.Range(min=0)
                ),
                vol.Optional(ATTR_SEARCH): cv.string,
                vol.Optional(ATTR_RESPONSE_STATUS): vol.In(["all", "filtered"]),
                **entry_id_schema,
            }
        ),
        supports_response=True,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Clean up ClientEntityManager if it exists
    if (
        "client_managers" in hass.data.get(DOMAIN, {})
        and entry.entry_id in hass.data[DOMAIN]["client_managers"]
    ):
        client_manager = hass.data[DOMAIN]["client_managers"].pop(entry.entry_id)
        client_manager.async_unsubscribe()

    # Clean up DnsRewriteEntityManager if it exists
    if (
        "rewrite_managers" in hass.data.get(DOMAIN, {})
        and entry.entry_id in hass.data[DOMAIN]["rewrite_managers"]
    ):
        rewrite_manager = hass.data[DOMAIN]["rewrite_managers"].pop(entry.entry_id)
        rewrite_manager.async_unsubscribe()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

        # Clean up empty client_managers dict
        if (
            "client_managers" in hass.data.get(DOMAIN, {})
            and not hass.data[DOMAIN]["client_managers"]
        ):
            hass.data[DOMAIN].pop("client_managers", None)

        # Clean up empty rewrite_managers dict
        if (
            "rewrite_managers" in hass.data.get(DOMAIN, {})
            and not hass.data[DOMAIN]["rewrite_managers"]
        ):
            hass.data[DOMAIN].pop("rewrite_managers", None)

        # Unregister services when last instance is removed
        # Check if there are no more coordinator entries (only managers might remain)
        remaining_entries = {
            k
            for k in hass.data.get(DOMAIN, {}).keys()
            if k not in ("client_managers", "rewrite_managers")
        }
        if not remaining_entries:
            for service in [
                SERVICE_SET_BLOCKED_SERVICES,
                SERVICE_ADD_FILTER_URL,
                SERVICE_REMOVE_FILTER_URL,
                SERVICE_REFRESH_FILTERS,
                SERVICE_SET_CLIENT_BLOCKED_SERVICES,
                SERVICE_ADD_DNS_REWRITE,
                SERVICE_REMOVE_DNS_REWRITE,
                SERVICE_CHECK_HOST,
                SERVICE_GET_QUERY_LOG,
            ]:
                hass.services.async_remove(DOMAIN, service)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of a config entry.

    This is called after async_unload_entry has been called.
    Any cleanup of persistent data (like stored credentials, files, etc.) should be done here.
    """
    _LOGGER.debug("Removing AdGuard Home config entry: %s", entry.entry_id)

    # Clean up any remaining domain data
    if DOMAIN in hass.data:
        # Remove entry from domain data if somehow still present
        hass.data[DOMAIN].pop(entry.entry_id, None)

        # Remove from client_managers if still present
        if "client_managers" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["client_managers"].pop(entry.entry_id, None)
            if not hass.data[DOMAIN]["client_managers"]:
                del hass.data[DOMAIN]["client_managers"]

        # Remove from rewrite_managers if still present
        if "rewrite_managers" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["rewrite_managers"].pop(entry.entry_id, None)
            if not hass.data[DOMAIN]["rewrite_managers"]:
                del hass.data[DOMAIN]["rewrite_managers"]

        # Clean up domain data if completely empty
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]
