"""Binary sensor platform for AdGuard Home Extended."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AdGuardHomeData, AdGuardHomeDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class AdGuardHomeBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes AdGuard Home binary sensor entity."""

    is_on_fn: Callable[[AdGuardHomeData], bool | None]


BINARY_SENSOR_TYPES: tuple[AdGuardHomeBinarySensorEntityDescription, ...] = (
    AdGuardHomeBinarySensorEntityDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=lambda data: data.status.running if data.status else None,
    ),
    AdGuardHomeBinarySensorEntityDescription(
        key="protection_enabled",
        translation_key="protection_enabled",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=lambda data: (data.status.protection_enabled if data.status else None),
    ),
    AdGuardHomeBinarySensorEntityDescription(
        key="dhcp_enabled",
        translation_key="dhcp_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.dhcp.enabled if data.dhcp else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AdGuard Home binary sensors based on a config entry."""
    coordinator: AdGuardHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AdGuardHomeBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_TYPES
    )


class AdGuardHomeBinarySensor(
    CoordinatorEntity[AdGuardHomeDataUpdateCoordinator], BinarySensorEntity
):
    """Representation of an AdGuard Home binary sensor."""

    entity_description: AdGuardHomeBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        description: AdGuardHomeBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)
