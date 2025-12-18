"""Switch platform for AdGuard Home Extended."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api.client import AdGuardHomeClient
from .api.models import DnsRewrite
from .const import DOMAIN
from .coordinator import AdGuardHomeData, AdGuardHomeDataUpdateCoordinator

if TYPE_CHECKING:  # pragma: no cover
    from . import AdGuardHomeConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AdGuardHomeSwitchEntityDescription(SwitchEntityDescription):  # type: ignore[override]
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
    AdGuardHomeSwitchEntityDescription(
        key="dnssec",
        translation_key="dnssec",
        icon="mdi:shield-key",
        is_on_fn=lambda data: data.dns_info.dnssec_enabled if data.dns_info else None,
        turn_on_fn=lambda client: client.set_dnssec_enabled(True),
        turn_off_fn=lambda client: client.set_dnssec_enabled(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="edns_client_subnet",
        translation_key="edns_client_subnet",
        icon="mdi:map-marker-radius",
        is_on_fn=lambda data: data.dns_info.edns_cs_enabled if data.dns_info else None,
        turn_on_fn=lambda client: client.set_edns_cs_enabled(True),
        turn_off_fn=lambda client: client.set_edns_cs_enabled(False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="query_logging",
        translation_key="query_logging",
        icon="mdi:text-box-search",
        is_on_fn=lambda data: (
            data.querylog_config.get("enabled") if data.querylog_config else None
        ),
        turn_on_fn=lambda client: client.set_querylog_config(enabled=True),
        turn_off_fn=lambda client: client.set_querylog_config(enabled=False),
    ),
    AdGuardHomeSwitchEntityDescription(
        key="statistics",
        translation_key="statistics",
        icon="mdi:chart-bar",
        is_on_fn=lambda data: (
            data.stats_config.get("enabled") if data.stats_config else None
        ),
        turn_on_fn=lambda client: client.set_stats_config(enabled=True),
        turn_off_fn=lambda client: client.set_stats_config(enabled=False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AdGuardHomeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AdGuard Home switches based on a config entry."""
    coordinator = entry.runtime_data

    # Add global switches
    entities: list[SwitchEntity] = [
        AdGuardHomeSwitch(coordinator, description) for description in SWITCH_TYPES
    ]
    async_add_entities(entities)

    # Set up dynamic client entity manager
    client_manager = ClientEntityManager(coordinator, async_add_entities)
    await client_manager.async_setup()

    # Set up dynamic DNS rewrite entity manager
    rewrite_manager = DnsRewriteEntityManager(coordinator, async_add_entities)
    await rewrite_manager.async_setup()

    # Set up dynamic filter list entity manager
    from .filter_lists import FilterListEntityManager

    filter_manager = FilterListEntityManager(coordinator, async_add_entities)
    await filter_manager.async_setup()

    # Store manager references for cleanup
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "client_managers" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["client_managers"] = {}
    hass.data[DOMAIN]["client_managers"][entry.entry_id] = client_manager

    if "rewrite_managers" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["rewrite_managers"] = {}
    hass.data[DOMAIN]["rewrite_managers"][entry.entry_id] = rewrite_manager

    if "filter_managers" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["filter_managers"] = {}
    hass.data[DOMAIN]["filter_managers"][entry.entry_id] = filter_manager


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

    coordinator: AdGuardHomeDataUpdateCoordinator
    entity_description: AdGuardHomeSwitchEntityDescription
    _attr_has_entity_name = True
    _logged_unavailable: bool = False  # Track if we've logged unavailability

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
    def available(self) -> bool:
        """Return True if entity is available.

        The entity is unavailable if the coordinator failed to update
        OR if the required data for this switch is not present (e.g.,
        stats_config/querylog_config on older AdGuard Home versions).
        """
        if not super().available:
            return False
        # If is_on_fn returns None, the required data is missing
        data_available = (
            self.entity_description.is_on_fn(self.coordinator.data) is not None
        )
        if not data_available and not self._logged_unavailable:
            _LOGGER.debug(
                "Switch '%s' unavailable: required data not present "
                "(feature may not be supported by this AdGuard Home version)",
                self.entity_description.key,
            )
            self._logged_unavailable = True
        elif data_available and self._logged_unavailable:
            # Reset flag when data becomes available again
            self._logged_unavailable = False
        return data_available

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


def _get_rewrite_unique_id(domain: str, answer: str) -> str:
    """Generate a unique ID for a DNS rewrite rule.

    Uses a hash of domain+answer to create a stable, URL-safe unique ID.
    """
    key = f"{domain}:{answer}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


class DnsRewriteEntityManager:
    """Manage dynamic DNS rewrite switch entities."""

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Initialize the DNS rewrite entity manager."""
        self._coordinator = coordinator
        self._async_add_entities = async_add_entities
        self._tracked_rewrites: set[str] = set()  # Set of unique_ids
        self._unsubscribe: Callable[[], None] | None = None

    async def async_setup(self) -> None:
        """Set up the DNS rewrite entity manager."""
        # Create initial entities for existing rewrites
        await self._async_add_new_rewrite_entities()

        # Subscribe to coordinator updates
        self._unsubscribe = self._coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator data updates."""
        # Schedule the async entity check
        self._coordinator.hass.async_create_task(self._async_add_new_rewrite_entities())

    async def _async_add_new_rewrite_entities(self) -> None:
        """Add entities for any new DNS rewrites."""
        if self._coordinator.data is None or not self._coordinator.data.rewrites:
            return

        new_entities: list[SwitchEntity] = []

        for rewrite in self._coordinator.data.rewrites:
            unique_id = _get_rewrite_unique_id(rewrite.domain, rewrite.answer)

            # Skip if we already have an entity for this rewrite
            if unique_id in self._tracked_rewrites:
                continue

            new_entities.append(
                AdGuardDnsRewriteSwitch(
                    self._coordinator,
                    rewrite.domain,
                    rewrite.answer,
                )
            )
            self._tracked_rewrites.add(unique_id)

        # Add new entities if any
        if new_entities:
            self._async_add_entities(new_entities)

    def async_unsubscribe(self) -> None:
        """Unsubscribe from coordinator updates."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None


class AdGuardDnsRewriteSwitch(
    CoordinatorEntity[AdGuardHomeDataUpdateCoordinator], SwitchEntity
):
    """Switch to enable/disable a DNS rewrite rule (v0.107.68+).

    For AdGuard Home versions < 0.107.68, this switch uses a fallback
    mechanism of deleting and re-adding the rewrite rule.
    """

    coordinator: AdGuardHomeDataUpdateCoordinator
    _attr_has_entity_name = True
    _attr_icon = "mdi:dns"

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        domain: str,
        answer: str,
    ) -> None:
        """Initialize the DNS rewrite switch."""
        super().__init__(coordinator)
        self._domain = domain
        self._answer = answer
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_rewrite_"
            f"{_get_rewrite_unique_id(domain, answer)}"
        )
        self._attr_device_info = coordinator.device_info

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"Rewrite {self._domain}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs: dict[str, Any] = {
            "domain": self._domain,
            "answer": self._answer,
        }
        # Include version-gating info
        if self.coordinator.server_version:
            attrs["native_toggle_support"] = (
                self.coordinator.server_version.supports_rewrite_enabled
            )
        return attrs

    def _get_rewrite_data(self) -> DnsRewrite | None:
        """Get the rewrite data from coordinator."""
        if self.coordinator.data is None:
            return None

        for rewrite in self.coordinator.data.rewrites:
            if rewrite.domain == self._domain and rewrite.answer == self._answer:
                return rewrite
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._get_rewrite_data() is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if the DNS rewrite is enabled."""
        rewrite = self._get_rewrite_data()
        if rewrite is None:
            return None
        # For older versions without enabled field, always report as enabled
        if not self.coordinator.server_version.supports_rewrite_enabled:
            return True
        return rewrite.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the DNS rewrite rule."""
        if self.coordinator.server_version.supports_rewrite_enabled:
            # v0.107.68+: Use native enable/disable API
            await self.coordinator.client.set_rewrite_enabled(
                self._domain, self._answer, True
            )
        else:
            # Older versions: Delete and re-add (rewrite is already "on" if it exists)
            # No action needed for turn_on in older versions
            pass
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the DNS rewrite rule."""
        if self.coordinator.server_version.supports_rewrite_enabled:
            # v0.107.68+: Use native enable/disable API
            await self.coordinator.client.set_rewrite_enabled(
                self._domain, self._answer, False
            )
        else:
            # Older versions: No native disable - rewrite can only exist as enabled
            # User should use delete_rewrite service instead
            _LOGGER.warning(
                "Cannot disable rewrite %s -> %s on AGH < v0.107.68. "
                "Use delete_rewrite service instead",
                self._domain,
                self._answer,
            )
        await self.coordinator.async_request_refresh()
