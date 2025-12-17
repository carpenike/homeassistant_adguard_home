"""Blocked services switch platform for AdGuard Home Extended."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AdGuardHomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Popular service categories for organization
SERVICE_CATEGORIES = {
    "social_media": {
        "name": "Social Media",
        "icon": "mdi:account-group",
        "services": [
            "facebook", "instagram", "twitter", "tiktok", "snapchat",
            "pinterest", "linkedin", "reddit", "tumblr", "vk",
            "ok", "weibo", "qq", "wechat"
        ],
    },
    "video_streaming": {
        "name": "Video Streaming",
        "icon": "mdi:video",
        "services": [
            "youtube", "netflix", "amazon_video", "disneyplus", "hulu",
            "hbomax", "peacock", "paramount_plus", "twitch", "vimeo",
            "dailymotion", "9gag", "iqiyi", "bilibili"
        ],
    },
    "messaging": {
        "name": "Messaging",
        "icon": "mdi:message",
        "services": [
            "whatsapp", "telegram", "signal", "viber", "discord",
            "skype", "slack", "teams", "zoom", "line"
        ],
    },
    "gaming": {
        "name": "Gaming",
        "icon": "mdi:gamepad-variant",
        "services": [
            "steam", "epicgames", "origin", "ubisoft", "roblox",
            "minecraft", "playstation", "xbox", "nintendo", "twitch"
        ],
    },
    "ai_services": {
        "name": "AI Services",
        "icon": "mdi:robot",
        "services": [
            "openai", "chatgpt", "claude", "bard", "bing_ai",
            "midjourney", "copilot", "perplexity"
        ],
    },
    "adult": {
        "name": "Adult Content",
        "icon": "mdi:alert-circle",
        "services": ["pornhub", "xvideos", "xnxx", "xhamster"],
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up blocked services switches."""
    coordinator: AdGuardHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SwitchEntity] = []

    # Wait for coordinator data to be available
    if coordinator.data is None:
        await coordinator.async_config_entry_first_refresh()

    # Create a switch for each available service
    if coordinator.data and coordinator.data.available_services:
        for service in coordinator.data.available_services:
            entities.append(
                AdGuardBlockedServiceSwitch(
                    coordinator=coordinator,
                    service_id=service["id"],
                    service_name=service["name"],
                )
            )

    async_add_entities(entities)


class AdGuardBlockedServiceSwitch(
    CoordinatorEntity[AdGuardHomeDataUpdateCoordinator], SwitchEntity
):
    """Switch to toggle blocking of a specific service."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AdGuardHomeDataUpdateCoordinator,
        service_id: str,
        service_name: str,
    ) -> None:
        """Initialize the blocked service switch."""
        super().__init__(coordinator)
        self._service_id = service_id
        self._service_name = service_name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_blocked_{service_id}"
        self._attr_translation_key = "blocked_service"
        self._attr_translation_placeholders = {"service_name": service_name}

        # Find icon based on category
        self._attr_icon = self._get_service_icon(service_id)

    def _get_service_icon(self, service_id: str) -> str:
        """Get the icon for a service based on its category."""
        for category_data in SERVICE_CATEGORIES.values():
            if service_id in category_data["services"]:
                return category_data["icon"]
        return "mdi:block-helper"

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"Block {self._service_name}"

    @property
    def is_on(self) -> bool | None:
        """Return true if service is blocked."""
        if self.coordinator.data is None:
            return None
        return self._service_id in self.coordinator.data.blocked_services

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "AdGuard Home",
            "manufacturer": "AdGuard",
            "model": "AdGuard Home",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        category = None
        for cat_id, cat_data in SERVICE_CATEGORIES.items():
            if self._service_id in cat_data["services"]:
                category = cat_data["name"]
                break

        return {
            "service_id": self._service_id,
            "category": category,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Block the service."""
        if self.coordinator.data is None:
            return

        current_blocked = set(self.coordinator.data.blocked_services)
        current_blocked.add(self._service_id)

        await self.coordinator.client.set_blocked_services(list(current_blocked))
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unblock the service."""
        if self.coordinator.data is None:
            return

        current_blocked = set(self.coordinator.data.blocked_services)
        current_blocked.discard(self._service_id)

        await self.coordinator.client.set_blocked_services(list(current_blocked))
        await self.coordinator.async_request_refresh()
