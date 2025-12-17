"""Sensor platform for AdGuard Home Extended."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ATTR_LIST_LIMIT,
    CONF_ATTR_TOP_ITEMS_LIMIT,
    DEFAULT_ATTR_LIST_LIMIT,
    DEFAULT_ATTR_TOP_ITEMS_LIMIT,
    DOMAIN,
)
from .coordinator import AdGuardHomeData, AdGuardHomeDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class AdGuardHomeSensorEntityDescription(SensorEntityDescription):
    """Describes AdGuard Home sensor entity."""

    value_fn: Callable[[AdGuardHomeData], Any]
    attributes_fn: Callable[[AdGuardHomeData, int, int], dict[str, Any]] | None = None


SENSOR_TYPES: tuple[AdGuardHomeSensorEntityDescription, ...] = (
    AdGuardHomeSensorEntityDescription(
        key="dns_queries",
        translation_key="dns_queries",
        native_unit_of_measurement="queries",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.stats.dns_queries if data.stats else None,
    ),
    AdGuardHomeSensorEntityDescription(
        key="blocked_queries",
        translation_key="blocked_queries",
        native_unit_of_measurement="queries",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.stats.blocked_filtering if data.stats else None,
    ),
    AdGuardHomeSensorEntityDescription(
        key="blocked_percentage",
        translation_key="blocked_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (
            round((data.stats.blocked_filtering / data.stats.dns_queries) * 100, 1)
            if data.stats and data.stats.dns_queries > 0
            else 0
        ),
    ),
    AdGuardHomeSensorEntityDescription(
        key="avg_processing_time",
        translation_key="avg_processing_time",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (
            round(data.stats.avg_processing_time * 1000, 2) if data.stats else None
        ),
    ),
    AdGuardHomeSensorEntityDescription(
        key="safe_browsing_blocked",
        translation_key="safe_browsing_blocked",
        native_unit_of_measurement="queries",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: (
            data.stats.replaced_safebrowsing if data.stats else None
        ),
    ),
    AdGuardHomeSensorEntityDescription(
        key="parental_blocked",
        translation_key="parental_blocked",
        native_unit_of_measurement="queries",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.stats.replaced_parental if data.stats else None,
    ),
    AdGuardHomeSensorEntityDescription(
        key="top_blocked_domain",
        translation_key="top_blocked_domain",
        value_fn=lambda data: (
            list(data.stats.top_blocked_domains[0].keys())[0]
            if data.stats and data.stats.top_blocked_domains
            else None
        ),
        attributes_fn=lambda data, top_limit, list_limit: (
            {"top_blocked_domains": data.stats.top_blocked_domains[:top_limit]}
            if data.stats
            else {}
        ),
    ),
    AdGuardHomeSensorEntityDescription(
        key="top_client",
        translation_key="top_client",
        value_fn=lambda data: (
            list(data.stats.top_clients[0].keys())[0]
            if data.stats and data.stats.top_clients
            else None
        ),
        attributes_fn=lambda data, top_limit, list_limit: (
            {"top_clients": data.stats.top_clients[:top_limit]} if data.stats else {}
        ),
    ),
    # DNS Rewrites sensor
    AdGuardHomeSensorEntityDescription(
        key="dns_rewrites_count",
        translation_key="dns_rewrites_count",
        native_unit_of_measurement="rules",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: len(data.rewrites) if data.rewrites else 0,
        attributes_fn=lambda data, top_limit, list_limit: (
            {
                "rewrites": [
                    {"domain": r.domain, "answer": r.answer}
                    for r in data.rewrites[:list_limit]
                ]
            }
            if data.rewrites
            else {}
        ),
    ),
    # DHCP sensors
    AdGuardHomeSensorEntityDescription(
        key="dhcp_leases_count",
        translation_key="dhcp_leases_count",
        native_unit_of_measurement="leases",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: len(data.dhcp.leases) if data.dhcp else 0,
        attributes_fn=lambda data, top_limit, list_limit: (
            {
                "leases": [
                    {
                        "mac": lease.mac,
                        "ip": lease.ip,
                        "hostname": lease.hostname,
                        "expires": lease.expires,
                    }
                    for lease in data.dhcp.leases[:list_limit]
                ]
            }
            if data.dhcp
            else {}
        ),
    ),
    AdGuardHomeSensorEntityDescription(
        key="dhcp_static_leases_count",
        translation_key="dhcp_static_leases_count",
        native_unit_of_measurement="leases",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: len(data.dhcp.static_leases) if data.dhcp else 0,
        attributes_fn=lambda data, top_limit, list_limit: (
            {
                "static_leases": [
                    {
                        "mac": lease.mac,
                        "ip": lease.ip,
                        "hostname": lease.hostname,
                    }
                    for lease in data.dhcp.static_leases[:list_limit]
                ]
            }
            if data.dhcp
            else {}
        ),
    ),
    # Query log sensor
    AdGuardHomeSensorEntityDescription(
        key="recent_queries",
        translation_key="recent_queries",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: len(data.query_log) if data.query_log else 0,
        attributes_fn=lambda data, top_limit, list_limit: (
            {
                "recent_queries": [
                    {
                        "domain": q.get("question", {}).get("name", "")
                        if isinstance(q.get("question"), dict)
                        else q.get("QH", ""),  # Fallback for older API format
                        "client": q.get("client", q.get("IP", "")),
                        "answer": q.get("answer", []),
                        "reason": q.get("reason", q.get("Reason", "")),
                        "time": q.get("time", ""),
                    }
                    for q in data.query_log[:top_limit]
                ]
            }
            if data.query_log
            else {}
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AdGuard Home sensors based on a config entry."""
    coordinator: AdGuardHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AdGuardHomeSensor(coordinator, description) for description in SENSOR_TYPES
    )


class AdGuardHomeSensor(
    CoordinatorEntity[AdGuardHomeDataUpdateCoordinator], SensorEntity
):
    """Representation of an AdGuard Home sensor."""

    entity_description: AdGuardHomeSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        description: AdGuardHomeSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.attributes_fn:
            # Get attribute limits from options
            options = self.coordinator.config_entry.options
            top_limit = options.get(
                CONF_ATTR_TOP_ITEMS_LIMIT, DEFAULT_ATTR_TOP_ITEMS_LIMIT
            )
            list_limit = options.get(CONF_ATTR_LIST_LIMIT, DEFAULT_ATTR_LIST_LIMIT)
            return self.entity_description.attributes_fn(
                self.coordinator.data, top_limit, list_limit
            )
        return None
