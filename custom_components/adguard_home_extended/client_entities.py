"""Per-client filtering entities for AdGuard Home Extended."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api.models import AdGuardHomeClient as ClientConfig
from .const import DOMAIN
from .coordinator import AdGuardHomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def create_client_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: AdGuardHomeDataUpdateCoordinator,
) -> list[SwitchEntity]:
    """Create per-client filtering entities."""
    entities: list[SwitchEntity] = []

    # Wait for coordinator data to be available
    if coordinator.data is None:
        return entities

    # Create entities for each configured client
    if coordinator.data.clients:
        for client_data in coordinator.data.clients:
            client = ClientConfig.from_dict(client_data)

            # Client filtering switch
            entities.append(AdGuardClientFilteringSwitch(coordinator, client.name))

            # Client parental control switch
            entities.append(AdGuardClientParentalSwitch(coordinator, client.name))

            # Client safe browsing switch
            entities.append(AdGuardClientSafeBrowsingSwitch(coordinator, client.name))

            # Client safe search switch
            entities.append(AdGuardClientSafeSearchSwitch(coordinator, client.name))

            # Client use global settings switch
            entities.append(
                AdGuardClientUseGlobalSettingsSwitch(coordinator, client.name)
            )

            # Client use global blocked services switch
            entities.append(
                AdGuardClientUseGlobalBlockedServicesSwitch(coordinator, client.name)
            )

    return entities


class AdGuardClientBaseSwitch(CoordinatorEntity, SwitchEntity):
    """Base class for per-client switches."""

    coordinator: AdGuardHomeDataUpdateCoordinator

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        client_name: str,
        switch_type: str,
        icon: str,
    ) -> None:
        """Initialize the per-client switch."""
        super().__init__(coordinator)
        self._client_name = client_name
        self._switch_type = switch_type
        self._attr_icon = icon
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_client_{client_name}_{switch_type}"
        )

    def _get_client_data(self) -> dict[str, Any] | None:
        """Get client data from coordinator."""
        if self.coordinator.data is None:
            return None

        for client in self.coordinator.data.clients:
            if client.get("name") == self._client_name:
                return dict(client)
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this client."""
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{self.coordinator.config_entry.entry_id}_{self._client_name}",
                )
            },
            name=f"AdGuard Client: {self._client_name}",
            manufacturer="AdGuard",
            model="Client",
            via_device=(DOMAIN, self.coordinator.config_entry.entry_id),
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self._get_client_data() is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        client_data = self._get_client_data()
        if client_data is None:
            return {}

        return {
            "client_name": self._client_name,
            "client_ids": client_data.get("ids", []),
            "tags": client_data.get("tags", []),
        }

    async def _async_update_client(self, **kwargs: Any) -> None:
        """Update client settings."""
        client_data = self._get_client_data()
        if client_data is None:
            return

        # Build updated client config
        updated_client = ClientConfig(
            name=client_data.get("name", ""),
            ids=client_data.get("ids", []),
            use_global_settings=kwargs.get(
                "use_global_settings", client_data.get("use_global_settings", True)
            ),
            filtering_enabled=kwargs.get(
                "filtering_enabled", client_data.get("filtering_enabled", True)
            ),
            parental_enabled=kwargs.get(
                "parental_enabled", client_data.get("parental_enabled", False)
            ),
            safebrowsing_enabled=kwargs.get(
                "safebrowsing_enabled", client_data.get("safebrowsing_enabled", False)
            ),
            safesearch_enabled=kwargs.get(
                "safesearch_enabled", client_data.get("safesearch_enabled", False)
            ),
            use_global_blocked_services=kwargs.get(
                "use_global_blocked_services",
                client_data.get("use_global_blocked_services", True),
            ),
            blocked_services=kwargs.get(
                "blocked_services", client_data.get("blocked_services", [])
            ),
            tags=client_data.get("tags", []),
        )

        await self.coordinator.client.update_client(self._client_name, updated_client)
        await self.coordinator.async_request_refresh()


class AdGuardClientFilteringSwitch(AdGuardClientBaseSwitch):
    """Switch to toggle filtering for a specific client."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        client_name: str,
    ) -> None:
        """Initialize the client filtering switch."""
        super().__init__(coordinator, client_name, "filtering", "mdi:filter")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Filtering"

    @property
    def is_on(self) -> bool | None:
        """Return true if filtering is enabled for this client."""
        client_data = self._get_client_data()
        if client_data is None:
            return None
        return bool(client_data.get("filtering_enabled", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable filtering for this client."""
        await self._async_update_client(filtering_enabled=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable filtering for this client."""
        await self._async_update_client(filtering_enabled=False)


class AdGuardClientParentalSwitch(AdGuardClientBaseSwitch):
    """Switch to toggle parental control for a specific client."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        client_name: str,
    ) -> None:
        """Initialize the client parental control switch."""
        super().__init__(coordinator, client_name, "parental", "mdi:account-child")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Parental Control"

    @property
    def is_on(self) -> bool | None:
        """Return true if parental control is enabled for this client."""
        client_data = self._get_client_data()
        if client_data is None:
            return None
        return bool(client_data.get("parental_enabled", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable parental control for this client."""
        await self._async_update_client(parental_enabled=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable parental control for this client."""
        await self._async_update_client(parental_enabled=False)


class AdGuardClientSafeBrowsingSwitch(AdGuardClientBaseSwitch):
    """Switch to toggle safe browsing for a specific client."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        client_name: str,
    ) -> None:
        """Initialize the client safe browsing switch."""
        super().__init__(coordinator, client_name, "safebrowsing", "mdi:shield-check")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Safe Browsing"

    @property
    def is_on(self) -> bool | None:
        """Return true if safe browsing is enabled for this client."""
        client_data = self._get_client_data()
        if client_data is None:
            return None
        return bool(client_data.get("safebrowsing_enabled", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable safe browsing for this client."""
        await self._async_update_client(safebrowsing_enabled=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable safe browsing for this client."""
        await self._async_update_client(safebrowsing_enabled=False)


class AdGuardClientSafeSearchSwitch(AdGuardClientBaseSwitch):
    """Switch to toggle safe search for a specific client."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        client_name: str,
    ) -> None:
        """Initialize the client safe search switch."""
        super().__init__(coordinator, client_name, "safesearch", "mdi:magnify-close")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Safe Search"

    @property
    def is_on(self) -> bool | None:
        """Return true if safe search is enabled for this client."""
        client_data = self._get_client_data()
        if client_data is None:
            return None
        return bool(client_data.get("safesearch_enabled", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable safe search for this client."""
        await self._async_update_client(safesearch_enabled=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable safe search for this client."""
        await self._async_update_client(safesearch_enabled=False)


class AdGuardClientUseGlobalSettingsSwitch(AdGuardClientBaseSwitch):
    """Switch to toggle use of global settings for a specific client."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        client_name: str,
    ) -> None:
        """Initialize the client use global settings switch."""
        super().__init__(coordinator, client_name, "use_global", "mdi:earth")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Use Global Settings"

    @property
    def is_on(self) -> bool | None:
        """Return true if using global settings for this client."""
        client_data = self._get_client_data()
        if client_data is None:
            return None
        return bool(client_data.get("use_global_settings", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable global settings for this client."""
        await self._async_update_client(use_global_settings=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable global settings for this client."""
        await self._async_update_client(use_global_settings=False)


class AdGuardClientUseGlobalBlockedServicesSwitch(AdGuardClientBaseSwitch):
    """Switch to toggle use of global blocked services for a specific client."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        client_name: str,
    ) -> None:
        """Initialize the client use global blocked services switch."""
        super().__init__(
            coordinator, client_name, "use_global_blocked", "mdi:earth-box"
        )

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Use Global Blocked Services"

    @property
    def is_on(self) -> bool | None:
        """Return true if using global blocked services for this client."""
        client_data = self._get_client_data()
        if client_data is None:
            return None
        return bool(client_data.get("use_global_blocked_services", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable global blocked services for this client."""
        await self._async_update_client(use_global_blocked_services=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable global blocked services for this client."""
        await self._async_update_client(use_global_blocked_services=False)
