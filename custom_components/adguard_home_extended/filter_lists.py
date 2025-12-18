"""Filter list switch entities for AdGuard Home Extended."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import AdGuardHomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_filter_unique_id(url: str, whitelist: bool = False) -> str:
    """Generate a unique ID for a filter list based on URL.

    Uses a hash to create a stable, shorter identifier that won't change
    even if the filter name changes.
    """
    prefix = "whitelist_" if whitelist else "filter_"
    return prefix + hashlib.md5(url.encode()).hexdigest()[:8]


class FilterListSwitch(
    CoordinatorEntity[AdGuardHomeDataUpdateCoordinator], SwitchEntity
):
    """Switch to enable/disable a filter list."""

    coordinator: AdGuardHomeDataUpdateCoordinator
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        filter_data: dict[str, Any],
        whitelist: bool = False,
    ) -> None:
        """Initialize the filter list switch."""
        super().__init__(coordinator)
        self._filter_url = filter_data.get("url", "")
        self._filter_name = filter_data.get("name", self._filter_url)
        self._whitelist = whitelist
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_"
            f"{_get_filter_unique_id(self._filter_url, whitelist)}"
        )
        self._attr_device_info = coordinator.device_info

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        prefix = "Whitelist: " if self._whitelist else "Filter: "
        return f"{prefix}{self._filter_name}"

    @property
    def icon(self) -> str:
        """Return the icon for the switch."""
        if self._whitelist:
            return "mdi:format-list-checks"
        return "mdi:filter-outline"

    @property
    def is_on(self) -> bool | None:
        """Return True if the filter is enabled."""
        filter_data = self._get_filter_data()
        if filter_data is None:
            return None
        return bool(filter_data.get("enabled", False))

    @property
    def available(self) -> bool:
        """Return True if the filter exists."""
        return (
            self.coordinator.last_update_success and self._get_filter_data() is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        filter_data = self._get_filter_data()
        if not filter_data:
            return {}

        return {
            "url": filter_data.get("url", ""),
            "name": filter_data.get("name", ""),
            "rules_count": filter_data.get("rules_count", 0),
            "last_updated": filter_data.get("last_updated", ""),
            "whitelist": self._whitelist,
            "filter_id": filter_data.get("id"),
        }

    def _get_filter_data(self) -> dict[str, Any] | None:
        """Get the current filter data from coordinator."""
        if not self.coordinator.data or not self.coordinator.data.filtering:
            return None

        # Search in the appropriate list
        filters = (
            self.coordinator.data.filtering.whitelist_filters
            if self._whitelist
            else self.coordinator.data.filtering.filters
        )

        for filter_data in filters:
            if filter_data.get("url") == self._filter_url:
                return dict(filter_data)

        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the filter list."""
        await self.coordinator.client.set_filter_enabled(
            url=self._filter_url,
            enabled=True,
            whitelist=self._whitelist,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the filter list."""
        await self.coordinator.client.set_filter_enabled(
            url=self._filter_url,
            enabled=False,
            whitelist=self._whitelist,
        )
        await self.coordinator.async_request_refresh()


class FilterListEntityManager:
    """Manage dynamic filter list entities."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Initialize the filter list entity manager."""
        self._coordinator = coordinator
        self._async_add_entities = async_add_entities
        self._tracked_filters: set[str] = set()
        self._unsubscribe: Callable[[], None] | None = None

    async def async_setup(self) -> None:
        """Set up the filter list entity manager."""
        # Create initial entities for existing filters
        await self._async_add_new_filter_entities()

        # Subscribe to coordinator updates
        self._unsubscribe = self._coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator data updates."""
        self._coordinator.hass.async_create_task(self._async_add_new_filter_entities())

    async def _async_add_new_filter_entities(self) -> None:
        """Add entities for any new filter lists."""
        if self._coordinator.data is None or self._coordinator.data.filtering is None:
            return

        new_entities: list[SwitchEntity] = []

        # Process blocklist filters (handle None gracefully)
        filters = self._coordinator.data.filtering.filters or []
        for filter_data in filters:
            url = filter_data.get("url", "")
            filter_key = f"filter_{url}"

            if filter_key not in self._tracked_filters:
                new_entities.append(
                    FilterListSwitch(
                        self._coordinator,
                        filter_data,
                        whitelist=False,
                    )
                )
                self._tracked_filters.add(filter_key)

        # Process whitelist filters (handle None gracefully)
        whitelist_filters = self._coordinator.data.filtering.whitelist_filters or []
        for filter_data in whitelist_filters:
            url = filter_data.get("url", "")
            filter_key = f"whitelist_{url}"

            if filter_key not in self._tracked_filters:
                new_entities.append(
                    FilterListSwitch(
                        self._coordinator,
                        filter_data,
                        whitelist=True,
                    )
                )
                self._tracked_filters.add(filter_key)

        # Add new entities if any
        if new_entities:
            self._async_add_entities(new_entities)

    def async_unsubscribe(self) -> None:
        """Unsubscribe from coordinator updates."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None
