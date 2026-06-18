"""Binary sensor platform for AdGuard Home Extended."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import AdGuardHomeData, AdGuardHomeDataUpdateCoordinator

if TYPE_CHECKING:  # pragma: no cover
    from . import AdGuardHomeConfigEntry

# Read-only platform; coordinator handles all polling.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class AdGuardHomeBinarySensorEntityDescription(BinarySensorEntityDescription):  # type: ignore[override]
    """Describes AdGuard Home binary sensor entity."""

    is_on_fn: Callable[[AdGuardHomeData], bool | None]


BINARY_SENSOR_TYPES: tuple[AdGuardHomeBinarySensorEntityDescription, ...] = (
    AdGuardHomeBinarySensorEntityDescription(
        key="running",
        translation_key="running",
        icon="mdi:check-network",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=lambda data: data.status.running if data.status else None,
    ),
    AdGuardHomeBinarySensorEntityDescription(
        key="protection_enabled",
        translation_key="protection_enabled",
        icon="mdi:shield",
        # Note: Do NOT use BinarySensorDeviceClass.SAFETY here - it has inverted
        # semantics (True=Unsafe, False=Safe) which is backwards for protection status
        is_on_fn=lambda data: (data.status.protection_enabled if data.status else None),
    ),
    AdGuardHomeBinarySensorEntityDescription(
        key="dhcp_enabled",
        translation_key="dhcp_enabled",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.dhcp.enabled if data.dhcp else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AdGuardHomeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AdGuard Home binary sensors based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        AdGuardHomeBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_TYPES
    )


class AdGuardHomeBinarySensor(
    CoordinatorEntity[AdGuardHomeDataUpdateCoordinator], BinarySensorEntity
):
    """Representation of an AdGuard Home binary sensor."""

    coordinator: AdGuardHomeDataUpdateCoordinator
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
    def available(self) -> bool:
        """Return True if entity is available.

        Falls back to unavailable when the underlying data for this sensor
        is missing (e.g. DHCP status when the DHCP endpoint is unreachable)
        even if the coordinator update otherwise succeeded.
        """
        if not super().available:
            return False
        return self.entity_description.is_on_fn(self.coordinator.data) is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)
