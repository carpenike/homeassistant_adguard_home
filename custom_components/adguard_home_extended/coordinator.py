"""DataUpdateCoordinator for AdGuard Home Extended."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.client import (
    AdGuardHomeAuthError,
    AdGuardHomeClient,
    AdGuardHomeConnectionError,
)
from .api.models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
    DhcpStatus,
    DnsInfo,
    DnsRewrite,
    FilteringStatus,
)
from .const import (
    CONF_QUERY_LOG_LIMIT,
    DEFAULT_QUERY_LOG_LIMIT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .version import AdGuardHomeVersion, parse_version

if TYPE_CHECKING:  # pragma: no cover
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class AdGuardHomeData:
    """Class to hold AdGuard Home data."""

    def __init__(self) -> None:
        """Initialize the data container."""
        self.status: AdGuardHomeStatus | None = None
        self.stats: AdGuardHomeStats | None = None
        self.filtering: FilteringStatus | None = None
        self.dns_info: DnsInfo | None = None
        self.blocked_services: list[str] = []
        self.blocked_services_schedule: dict[str, Any] | None = None
        self.available_services: list[dict[str, Any]] = []
        self.clients: list[dict[str, Any]] = []
        self.dhcp: DhcpStatus | None = None
        self.rewrites: list[DnsRewrite] = []
        self.query_log: list[dict[str, Any]] = []
        self.stats_config: dict[str, Any] | None = None
        self.querylog_config: dict[str, Any] | None = None

    @property
    def version(self) -> AdGuardHomeVersion:
        """Get parsed version from status."""
        version_str = self.status.version if self.status else ""
        return parse_version(version_str)


class AdGuardHomeDataUpdateCoordinator(DataUpdateCoordinator[AdGuardHomeData]):
    """Class to manage fetching AdGuard Home data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: AdGuardHomeClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        # Get scan interval from options, falling back to default
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.client = client
        # Will be populated in _async_setup
        self._available_services: list[dict[str, Any]] = []
        self._server_version: AdGuardHomeVersion | None = None

    async def _async_setup(self) -> None:
        """Set up the coordinator - called once during first refresh.

        This method is called once during the first coordinator refresh
        (Home Assistant 2024.8+). Use it for one-time initialization that
        shouldn't be repeated on every update.
        """
        try:
            # Fetch server version - rarely changes
            status = await self.client.get_status()
            self._server_version = parse_version(status.version)
            _LOGGER.debug("AdGuard Home version detected: %s", self._server_version)

            # Fetch available blocked services - static per installation
            # This only changes when AdGuard Home is upgraded
            services = await self.client.get_all_blocked_services()
            self._available_services = [
                {"id": svc.id, "name": svc.name} for svc in services
            ]
            _LOGGER.debug(
                "Loaded %d available blocked services", len(self._available_services)
            )
        except AdGuardHomeAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed during setup: {err}"
            ) from err
        except AdGuardHomeConnectionError as err:
            raise UpdateFailed(f"Error during coordinator setup: {err}") from err

    async def _async_update_data(self) -> AdGuardHomeData:
        """Fetch data from AdGuard Home."""
        data = AdGuardHomeData()

        try:
            # Fetch status - required
            data.status = await self.client.get_status()

            # Fetch stats - required
            data.stats = await self.client.get_stats()

            # Fetch filtering status
            try:
                data.filtering = await self.client.get_filtering_status()
            except AdGuardHomeConnectionError as err:
                _LOGGER.debug("Failed to fetch filtering status: %s", err)

            # Fetch DNS info (cache settings, etc.)
            try:
                dns_info_data = await self.client.get_dns_info()
                data.dns_info = DnsInfo.from_dict(dns_info_data)
            except AdGuardHomeConnectionError as err:
                _LOGGER.debug("Failed to fetch DNS info: %s", err)

            # Fetch blocked services (with schedule for v0.107.56+)
            try:
                blocked_data = await self.client.get_blocked_services_with_schedule()
                data.blocked_services = blocked_data.get("ids", [])
                data.blocked_services_schedule = blocked_data.get("schedule")
                # Use cached available services from _async_setup
                data.available_services = self._available_services
            except AdGuardHomeConnectionError as err:
                _LOGGER.debug("Failed to fetch blocked services: %s", err)

            # Fetch clients
            try:
                clients = await self.client.get_clients()
                data.clients = [
                    {
                        "name": c.name,
                        "ids": c.ids,
                        "use_global_settings": c.use_global_settings,
                        "filtering_enabled": c.filtering_enabled,
                        "parental_enabled": c.parental_enabled,
                        "safebrowsing_enabled": c.safebrowsing_enabled,
                        "safesearch_enabled": c.safesearch_enabled,
                        "use_global_blocked_services": c.use_global_blocked_services,
                        "blocked_services": c.blocked_services or [],
                        "tags": c.tags or [],
                    }
                    for c in clients
                ]
            except AdGuardHomeConnectionError as err:
                _LOGGER.debug("Failed to fetch clients: %s", err)

            # Fetch DHCP status
            try:
                data.dhcp = await self.client.get_dhcp_status()
            except AdGuardHomeConnectionError as err:
                _LOGGER.debug("Failed to fetch DHCP status: %s", err)

            # Fetch DNS rewrites
            try:
                data.rewrites = await self.client.get_rewrites()
            except AdGuardHomeConnectionError as err:
                _LOGGER.debug("Failed to fetch DNS rewrites: %s", err)

            # Fetch query log (limit is configurable via options)
            query_log_limit = self.config_entry.options.get(
                CONF_QUERY_LOG_LIMIT, DEFAULT_QUERY_LOG_LIMIT
            )
            try:
                data.query_log = await self.client.get_query_log(limit=query_log_limit)
            except AdGuardHomeConnectionError as err:
                _LOGGER.debug("Failed to fetch query log: %s", err)

            # Fetch stats config (v0.107.30+) - only if version supports it
            if self._server_version and self._server_version.supports_stats_config:
                try:
                    data.stats_config = await self.client.get_stats_config()
                except AdGuardHomeConnectionError as err:
                    _LOGGER.debug("Failed to fetch stats config: %s", err)

            # Fetch query log config (v0.107.30+) - only if version supports it
            if self._server_version and self._server_version.supports_querylog_config:
                try:
                    data.querylog_config = await self.client.get_querylog_config()
                except AdGuardHomeConnectionError as err:
                    _LOGGER.debug("Failed to fetch query log config: %s", err)

        except AdGuardHomeAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for AdGuard Home: {err}"
            ) from err
        except AdGuardHomeConnectionError as err:
            raise UpdateFailed(f"Error communicating with AdGuard Home: {err}") from err

        return data

    @property
    def server_version(self) -> AdGuardHomeVersion:
        """Return the cached server version.

        This version is detected during _async_setup and can be used by
        entities to gate feature usage based on API availability.
        """
        return self._server_version or parse_version("")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this AdGuard Home instance."""
        version = "unknown"
        if self.data and self.data.status:
            version = self.data.status.version

        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=f"AdGuard Home ({self.config_entry.data.get('host', 'unknown')})",
            manufacturer="AdGuard",
            model="AdGuard Home",
            sw_version=version,
        )
