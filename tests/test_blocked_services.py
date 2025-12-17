"""Tests for the AdGuard Home Extended blocked services switches."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.adguard_home_extended.blocked_services import (
    SERVICE_CATEGORIES,
    AdGuardBlockedServiceSwitch,
)
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData


class TestServiceCategories:
    """Tests for service categories configuration."""

    def test_categories_have_required_fields(self) -> None:
        """Test all categories have required fields."""
        for cat_id, cat_data in SERVICE_CATEGORIES.items():
            assert "name" in cat_data
            assert "icon" in cat_data
            assert "services" in cat_data
            assert isinstance(cat_data["services"], list)
            assert len(cat_data["services"]) > 0

    def test_social_media_category(self) -> None:
        """Test social media category contains expected services."""
        social = SERVICE_CATEGORIES["social_media"]
        assert "facebook" in social["services"]
        assert "instagram" in social["services"]
        assert "tiktok" in social["services"]
        assert social["icon"] == "mdi:account-group"

    def test_video_streaming_category(self) -> None:
        """Test video streaming category contains expected services."""
        streaming = SERVICE_CATEGORIES["video_streaming"]
        assert "youtube" in streaming["services"]
        assert "netflix" in streaming["services"]
        assert streaming["icon"] == "mdi:video"

    def test_ai_services_category(self) -> None:
        """Test AI services category contains expected services."""
        ai = SERVICE_CATEGORIES["ai_services"]
        assert "openai" in ai["services"]
        assert "chatgpt" in ai["services"]
        assert ai["icon"] == "mdi:robot"


class TestBlockedServiceSwitch:
    """Tests for AdGuardBlockedServiceSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.blocked_services = ["facebook", "tiktok"]
        coordinator.data.available_services = [
            {"id": "facebook", "name": "Facebook"},
            {"id": "youtube", "name": "YouTube"},
            {"id": "tiktok", "name": "TikTok"},
        ]
        coordinator.client = AsyncMock()
        coordinator.client.set_blocked_services = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    def test_switch_init(self, mock_coordinator: MagicMock) -> None:
        """Test switch initialization."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        assert switch._service_id == "facebook"
        assert switch._service_name == "Facebook"
        assert "facebook" in switch._attr_unique_id

    def test_switch_name(self, mock_coordinator: MagicMock) -> None:
        """Test switch name."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        assert switch.name == "Block Facebook"

    def test_switch_is_on_when_blocked(self, mock_coordinator: MagicMock) -> None:
        """Test switch is on when service is blocked."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        assert switch.is_on is True

    def test_switch_is_off_when_not_blocked(self, mock_coordinator: MagicMock) -> None:
        """Test switch is off when service is not blocked."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="youtube",
            service_name="YouTube",
        )

        assert switch.is_on is False

    def test_switch_icon_social_media(self, mock_coordinator: MagicMock) -> None:
        """Test switch icon for social media service."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        assert switch._attr_icon == "mdi:account-group"

    def test_switch_icon_streaming(self, mock_coordinator: MagicMock) -> None:
        """Test switch icon for streaming service."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="youtube",
            service_name="YouTube",
        )

        assert switch._attr_icon == "mdi:video"

    def test_switch_icon_unknown(self, mock_coordinator: MagicMock) -> None:
        """Test switch icon for unknown service."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="unknown_service",
            service_name="Unknown",
        )

        assert switch._attr_icon == "mdi:block-helper"

    def test_extra_state_attributes(self, mock_coordinator: MagicMock) -> None:
        """Test switch extra state attributes."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        attrs = switch.extra_state_attributes
        assert attrs["service_id"] == "facebook"
        assert attrs["category"] == "Social Media"

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_coordinator: MagicMock) -> None:
        """Test turning switch on (blocking service)."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="youtube",
            service_name="YouTube",
        )

        await switch.async_turn_on()

        # Should add youtube to blocked services
        mock_coordinator.client.set_blocked_services.assert_called_once()
        call_args = mock_coordinator.client.set_blocked_services.call_args[0][0]
        assert "youtube" in call_args
        assert "facebook" in call_args  # existing
        assert "tiktok" in call_args  # existing
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_coordinator: MagicMock) -> None:
        """Test turning switch off (unblocking service)."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        await switch.async_turn_off()

        # Should remove facebook from blocked services
        mock_coordinator.client.set_blocked_services.assert_called_once()
        call_args = mock_coordinator.client.set_blocked_services.call_args[0][0]
        assert "facebook" not in call_args
        assert "tiktok" in call_args  # still blocked
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_switch_none_data(self, mock_coordinator: MagicMock) -> None:
        """Test switch with None data."""
        mock_coordinator.data = None
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        assert switch.is_on is None
