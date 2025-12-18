"""Tests for the AdGuard Home Extended blocked services switches."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.adguard_home_extended.blocked_services import (
    SERVICE_CATEGORIES,
    AdGuardBlockedServiceSwitch,
    async_setup_entry,
)
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData


class TestServiceCategories:
    """Tests for service categories configuration."""

    def test_categories_have_required_fields(self) -> None:
        """Test all categories have required fields."""
        for _cat_id, cat_data in SERVICE_CATEGORIES.items():
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
        assert "claude" in ai["services"]  # v0.107.66+
        assert "deepseek" in ai["services"]  # v0.107.66+
        assert ai["icon"] == "mdi:robot"

    def test_new_video_services(self) -> None:
        """Test video streaming category includes newer services."""
        streaming = SERVICE_CATEGORIES["video_streaming"]
        assert "odysee" in streaming["services"]  # v0.107.66+

    def test_service_categories_are_documentation_only(self) -> None:
        """Test that categories are for icon mapping, not exhaustive lists.

        The actual available services come from the AdGuard Home API
        via GET /control/blocked_services/all. These categories are
        used only for icon selection and grouping in the UI.
        """
        # Just verify the documentation comment exists implicitly
        # by checking that categories exist and have icons
        for cat_id, cat_data in SERVICE_CATEGORIES.items():
            assert "icon" in cat_data, f"Category {cat_id} should have an icon"


class TestBlockedServiceSwitch:
    """Tests for AdGuardBlockedServiceSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        # Mock options.get to return defaults
        coordinator.config_entry.options = {"icon_color": "#44739e"}
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

    def test_entity_picture_with_svg_icon(self, mock_coordinator: MagicMock) -> None:
        """Test entity_picture returns data URL when icon_svg is provided."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
            icon_svg="PHN2Zy8+",  # Base64-encoded SVG
        )

        # entity_picture should return processed SVG as data URL
        assert switch.entity_picture is not None
        assert switch.entity_picture.startswith("data:image/svg+xml;base64,")
        # Should NOT have MDI icon when SVG is provided
        assert not hasattr(switch, "_attr_icon") or switch._attr_icon is None

    def test_entity_picture_none_when_no_svg_icon(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test entity_picture returns None when no icon_svg is provided."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        assert switch.entity_picture is None
        # Should have MDI icon when no SVG
        assert switch._attr_icon == "mdi:account-group"

    def test_entity_picture_empty_string_svg(self, mock_coordinator: MagicMock) -> None:
        """Test entity_picture returns None when icon_svg is empty string."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="unknown_service",
            service_name="Unknown",
            icon_svg="",
        )

        assert switch.entity_picture is None
        # Should fall back to MDI icon
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

    @pytest.mark.asyncio
    async def test_turn_on_preserves_schedule(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turning on preserves the blocked services schedule."""
        # Set up a schedule on the coordinator
        mock_coordinator.data.blocked_services_schedule = {
            "time_zone": "America/New_York",
            "mon": [{"start": "09:00", "end": "17:00"}],
            "tue": [{"start": "09:00", "end": "17:00"}],
        }
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="youtube",
            service_name="YouTube",
        )

        await switch.async_turn_on()

        # Should pass the schedule as the second argument
        mock_coordinator.client.set_blocked_services.assert_called_once()
        call_args = mock_coordinator.client.set_blocked_services.call_args
        # First positional arg is the services list
        services = call_args[0][0]
        assert "youtube" in services
        # Second positional arg is the schedule
        schedule = call_args[0][1]
        assert schedule["time_zone"] == "America/New_York"
        assert "mon" in schedule
        assert "tue" in schedule

    @pytest.mark.asyncio
    async def test_turn_off_preserves_schedule(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turning off preserves the blocked services schedule."""
        # Set up a schedule on the coordinator
        mock_coordinator.data.blocked_services_schedule = {
            "time_zone": "Europe/London",
            "wed": [{"start": "22:00", "end": "06:00"}],
        }
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        await switch.async_turn_off()

        # Should pass the schedule as the second argument
        mock_coordinator.client.set_blocked_services.assert_called_once()
        call_args = mock_coordinator.client.set_blocked_services.call_args
        # First positional arg is the services list
        services = call_args[0][0]
        assert "facebook" not in services
        # Second positional arg is the schedule
        schedule = call_args[0][1]
        assert schedule["time_zone"] == "Europe/London"
        assert "wed" in schedule

    def test_switch_none_data(self, mock_coordinator: MagicMock) -> None:
        """Test switch with None data."""
        mock_coordinator.data = None
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        assert switch.is_on is None

    def test_device_info(self, mock_coordinator: MagicMock) -> None:
        """Test device info property."""
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        device_info = switch.device_info
        assert device_info["name"] == "AdGuard Home"
        assert device_info["manufacturer"] == "AdGuard"
        assert ("adguard_home_extended", "test_entry") in device_info["identifiers"]

    @pytest.mark.asyncio
    async def test_turn_on_when_data_is_none(self, mock_coordinator: MagicMock) -> None:
        """Test turning on when coordinator data is None returns early."""
        mock_coordinator.data = None
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        await switch.async_turn_on()

        # Should not call set_blocked_services
        mock_coordinator.client.set_blocked_services.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_when_data_is_none(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turning off when coordinator data is None returns early."""
        mock_coordinator.data = None
        switch = AdGuardBlockedServiceSwitch(
            coordinator=mock_coordinator,
            service_id="facebook",
            service_name="Facebook",
        )

        await switch.async_turn_off()

        # Should not call set_blocked_services
        mock_coordinator.client.set_blocked_services.assert_not_called()


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_entry_creates_entities(self) -> None:
        """Test setup entry creates entities for available services."""
        coordinator = MagicMock()
        coordinator.data = AdGuardHomeData()
        coordinator.data.available_services = [
            {"id": "facebook", "name": "Facebook"},
            {"id": "youtube", "name": "YouTube"},
        ]
        coordinator.data.blocked_services = []

        entry = MagicMock()
        entry.runtime_data = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        # Should have called async_add_entities with 2 entities
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 2

    @pytest.mark.asyncio
    async def test_setup_entry_no_services(self) -> None:
        """Test setup entry with no available services."""
        coordinator = MagicMock()
        coordinator.data = AdGuardHomeData()
        coordinator.data.available_services = []
        coordinator.data.blocked_services = []

        entry = MagicMock()
        entry.runtime_data = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        # Should have called async_add_entities with empty list
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 0

    @pytest.mark.asyncio
    async def test_setup_entry_with_none_data_calls_refresh(self) -> None:
        """Test setup entry calls refresh when data is None."""
        coordinator = MagicMock()
        coordinator.data = None
        coordinator.async_config_entry_first_refresh = AsyncMock()

        entry = MagicMock()
        entry.runtime_data = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        # Should have called async_config_entry_first_refresh
        coordinator.async_config_entry_first_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_entry_passes_icon_svg_to_entities(self) -> None:
        """Test setup entry passes icon_svg from available_services to entities."""
        coordinator = MagicMock()
        coordinator.data = AdGuardHomeData()
        coordinator.data.available_services = [
            {"id": "facebook", "name": "Facebook", "icon_svg": "PHN2Zy8+"},
            {"id": "youtube", "name": "YouTube", "icon_svg": ""},
        ]
        coordinator.data.blocked_services = []
        # Mock config_entry.options for icon color
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.options = {"icon_color": "#44739e"}

        entry = MagicMock()
        entry.runtime_data = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(MagicMock(), entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 2

        # First entity should have icon_svg and entity_picture
        facebook_entity = entities[0]
        assert facebook_entity._icon_svg == "PHN2Zy8+"
        # entity_picture should be processed SVG as data URL
        assert facebook_entity.entity_picture is not None
        assert facebook_entity.entity_picture.startswith("data:image/svg+xml;base64,")
        # Should NOT have MDI icon when SVG is provided
        assert not hasattr(facebook_entity, "_attr_icon")

        # Second entity should NOT have icon_svg, but should have MDI fallback
        youtube_entity = entities[1]
        assert youtube_entity._icon_svg == ""
        assert youtube_entity.entity_picture is None
        # Should have MDI icon when no SVG
        assert youtube_entity._attr_icon == "mdi:video"
