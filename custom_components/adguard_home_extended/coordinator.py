"""DataUpdateCoordinator for AdGuard Home Extended."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api.client import (
    AdGuardHomeClient,
    AdGuardHomeConnectionError,
    AdGuardHomeAuthError,
)
from .api.models import (
    AdGuardHomeStatus,
    AdGuardHomeStats,
    FilteringStatus,
    DhcpStatus,
)
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class AdGuardHomeData:
    """Class to hold AdGuard Home data."""

    def __init__(self) -> None:
        """Initialize the data container."""
        self.status: AdGuardHomeStatus | None = None
        self.stats: AdGuardHomeStats | None = None
        self.filtering: FilteringStatus | None = None
        self.blocked_services: list[str] = []
        self.available_services: list[dict[str, Any]] = []
        self.clients: list[dict[str, Any]] = []
        self.dhcp: DhcpStatus | None = None


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
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.config_entry = entry

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

            # Fetch blocked services
            try:
                data.blocked_services = await self.client.get_blocked_services()
                services = await self.client.get_all_blocked_services()
                data.available_services = [
                    {"id": svc.id, "name": svc.name} for svc in services
                ]
            except AdGuardHomeConnectionError as err:
                _LOGGER.debug("Failed to fetch blocked services: %s", err)

            # Fetch clients
            try:
                clients = await self.client.get_clients()
                data.clients = [
                    {
                        "name": c.name,
                        "ids": c.ids,
                        "filtering_enabled": c.filtering_enabled,
                        "parental_enabled": c.parental_enabled,
                        "safebrowsing_enabled": c.safebrowsing_enabled,
                        "safesearch_enabled": c.safesearch_enabled,
                        "blocked_services": c.blocked_services,
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

        except AdGuardHomeAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for AdGuard Home: {err}"
            ) from err
        except AdGuardHomeConnectionError as err:
            raise UpdateFailed(f"Error communicating with AdGuard Home: {err}") from err

        return data

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for this AdGuard Home instance."""
        version = "unknown"
        if self.data and self.data.status:
            version = self.data.status.version

        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": f"AdGuard Home ({self.config_entry.data.get('host', 'unknown')})",
            "manufacturer": "AdGuard",
            "model": "AdGuard Home",
            "sw_version": version,
        }
