"""Switch platform for AdGuard Home Extended."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AdGuardHomeDataUpdateCoordinator, AdGuardHomeData
from .api.client import AdGuardHomeClient


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
        is_on_fn=lambda data: (
            data.status.protection_enabled if data.status else None
        ),
        turn_on_fn=lambda client: client.set_protection(True),
        turn_off_fn=lambda client: client.set_protection(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="filtering",
        translation_key="filtering",
        is_on_fn=lambda data: data.filtering.enabled if data.filtering else None,
        turn_on_fn=lambda client: client.set_protection(True),  # Filtering is tied to protection
        turn_off_fn=lambda client: client.set_protection(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="safe_browsing",
        translation_key="safe_browsing",
        is_on_fn=lambda data: (
            data.status.protection_enabled if data.status else None
        ),  # Will be updated when we can read safebrowsing state
        turn_on_fn=lambda client: client.set_safebrowsing(True),
        turn_off_fn=lambda client: client.set_safebrowsing(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="parental_control",
        translation_key="parental_control",
        is_on_fn=lambda data: (
            data.status.protection_enabled if data.status else None
        ),  # Will be updated when we can read parental state
        turn_on_fn=lambda client: client.set_parental(True),
        turn_off_fn=lambda client: client.set_parental(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="safe_search",
        translation_key="safe_search",
        is_on_fn=lambda data: (
            data.status.protection_enabled if data.status else None
        ),  # Will be updated when we can read safesearch state
        turn_on_fn=lambda client: client.set_safesearch(True),
        turn_off_fn=lambda client: client.set_safesearch(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AdGuard Home switches based on a config entry."""
    coordinator: AdGuardHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SwitchEntity] = [
        AdGuardHomeSwitch(coordinator, description) for description in SWITCH_TYPES
    ]

    # Add per-client switches
    from .client_entities import create_client_entities
    client_entities = await create_client_entities(hass, entry, coordinator)
    entities.extend(client_entities)

    async_add_entities(entities)


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
