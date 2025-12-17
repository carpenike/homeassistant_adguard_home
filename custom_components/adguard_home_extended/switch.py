"""Switch platform for AdGuard Home Extended."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api.client import AdGuardHomeClient
from .const import DOMAIN
from .coordinator import AdGuardHomeData, AdGuardHomeDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class AdGuardHomeSwitchEntityDescription(SwitchEntityDescription):
    """Describes AdGuard Home switch entity."""

    is_on_fn: Callable[[AdGuardHomeData], bool | None]
    turn_on_fn: Callable[[AdGuardHomeClient], Coroutine[Any, Any, None]]
    turn_off_fn: Callable[[AdGuardHomeClient], Coroutine[Any, Any, None]]


SWITCH_TYPES: tuple[AdGuardHomeSwitchEntityDescription, ...] = (
    AdGuardHomeSwitchEntityDescription(
        key="protection",
        translation_key="protection",
        icon="mdi:shield-check",
        is_on_fn=lambda data: (data.status.protection_enabled if data.status else None),
        turn_on_fn=lambda client: client.set_protection(True),
        turn_off_fn=lambda client: client.set_protection(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="filtering",
        translation_key="filtering",
        icon="mdi:filter",
        is_on_fn=lambda data: data.filtering.enabled if data.filtering else None,
        turn_on_fn=lambda client: client.set_filtering(True),
        turn_off_fn=lambda client: client.set_filtering(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="safe_browsing",
        translation_key="safe_browsing",
        icon="mdi:shield-lock",
        is_on_fn=lambda data: (
            data.status.safebrowsing_enabled if data.status else None
        ),
        turn_on_fn=lambda client: client.set_safebrowsing(True),
        turn_off_fn=lambda client: client.set_safebrowsing(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="parental_control",
        translation_key="parental_control",
        icon="mdi:account-child",
        is_on_fn=lambda data: (data.status.parental_enabled if data.status else None),
        turn_on_fn=lambda client: client.set_parental(True),
        turn_off_fn=lambda client: client.set_parental(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="safe_search",
        translation_key="safe_search",
        icon="mdi:magnify-scan",
        is_on_fn=lambda data: (data.status.safesearch_enabled if data.status else None),
        turn_on_fn=lambda client: client.set_safesearch(True),
        turn_off_fn=lambda client: client.set_safesearch(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="dns_cache",
        translation_key="dns_cache",
        icon="mdi:cached",
        is_on_fn=lambda data: data.dns_info.cache_enabled if data.dns_info else None,
        turn_on_fn=lambda client: client.set_dns_cache_enabled(True),
        turn_off_fn=lambda client: client.set_dns_cache_enabled(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AdGuard Home switches based on a config entry."""
    coordinator: AdGuardHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Add global switches
    entities: list[SwitchEntity] = [
        AdGuardHomeSwitch(coordinator, description) for description in SWITCH_TYPES
    ]
    async_add_entities(entities)

    # Set up dynamic client entity manager
    client_manager = ClientEntityManager(coordinator, async_add_entities)
    await client_manager.async_setup()

    # Store manager reference for cleanup
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "client_managers" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["client_managers"] = {}
    hass.data[DOMAIN]["client_managers"][entry.entry_id] = client_manager


class ClientEntityManager:
    """Manage dynamic client entities."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Initialize the client entity manager."""
        self._coordinator = coordinator
        self._async_add_entities = async_add_entities
        self._tracked_clients: set[str] = set()
        self._unsubscribe: Callable[[], None] | None = None

    async def async_setup(self) -> None:
        """Set up the client entity manager."""
        # Create initial entities for existing clients
        await self._async_add_new_client_entities()

        # Subscribe to coordinator updates
        self._unsubscribe = self._coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator data updates."""
        # Schedule the async entity check
        self._coordinator.hass.async_create_task(self._async_add_new_client_entities())

    async def _async_add_new_client_entities(self) -> None:
        """Add entities for any new clients."""
        if self._coordinator.data is None or not self._coordinator.data.clients:
            return

        from .api.models import AdGuardHomeClient as ClientConfig
        from .client_entities import (
            AdGuardClientFilteringSwitch,
            AdGuardClientParentalSwitch,
            AdGuardClientSafeBrowsingSwitch,
            AdGuardClientSafeSearchSwitch,
            AdGuardClientUseGlobalBlockedServicesSwitch,
            AdGuardClientUseGlobalSettingsSwitch,
        )

        new_entities: list[SwitchEntity] = []
        current_clients: set[str] = set()

        for client_data in self._coordinator.data.clients:
            client = ClientConfig.from_dict(client_data)
            current_clients.add(client.name)

            # Skip if we already have entities for this client
            if client.name in self._tracked_clients:
                continue

            # Create all entity types for the new client
            new_entities.extend(
                [
                    AdGuardClientFilteringSwitch(self._coordinator, client.name),
                    AdGuardClientParentalSwitch(self._coordinator, client.name),
                    AdGuardClientSafeBrowsingSwitch(self._coordinator, client.name),
                    AdGuardClientSafeSearchSwitch(self._coordinator, client.name),
                    AdGuardClientUseGlobalSettingsSwitch(
                        self._coordinator, client.name
                    ),
                    AdGuardClientUseGlobalBlockedServicesSwitch(
                        self._coordinator, client.name
                    ),
                ]
            )

            self._tracked_clients.add(client.name)

        # Add new entities if any
        if new_entities:
            self._async_add_entities(new_entities)

        # Note: Removed clients will have their entities become unavailable
        # (handled by available property checking _get_client_data())

    def async_unsubscribe(self) -> None:
        """Unsubscribe from coordinator updates."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None


class AdGuardHomeSwitch(
    CoordinatorEntity[AdGuardHomeDataUpdateCoordinator], SwitchEntity
):
    """Representation of an AdGuard Home switch."""

    entity_description: AdGuardHomeSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        description: AdGuardHomeSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.entity_description.turn_on_fn(self.coordinator.client)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.entity_description.turn_off_fn(self.coordinator.client)
        await self.coordinator.async_request_refresh()
