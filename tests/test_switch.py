"""Tests for the AdGuard Home Extended switch platform."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStatus,
    FilteringStatus,
)


class TestSwitchEntityDescriptions:
    """Tests for switch entity descriptions."""

    @pytest.fixture
    def data_with_status(self) -> AdGuardHomeData:
        """Return data with status."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            version="0.107.43",
        )
        data.filtering = FilteringStatus(enabled=True)
        return data

    def test_protection_switch_is_on(self, data_with_status: AdGuardHomeData) -> None:
        """Test protection switch is_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        protection_desc = next(
            d for d in SWITCH_TYPES if d.key == "protection"
        )
        is_on = protection_desc.is_on_fn(data_with_status)
        assert is_on is True

    def test_protection_switch_is_off(self) -> None:
        """Test protection switch when off."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=False,
            running=True,
        )

        protection_desc = next(
            d for d in SWITCH_TYPES if d.key == "protection"
        )
        is_on = protection_desc.is_on_fn(data)
        assert is_on is False

    def test_filtering_switch_is_on(self, data_with_status: AdGuardHomeData) -> None:
        """Test filtering switch is_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        filtering_desc = next(
            d for d in SWITCH_TYPES if d.key == "filtering"
        )
        is_on = filtering_desc.is_on_fn(data_with_status)
        assert is_on is True

    def test_all_switches_have_required_fields(self) -> None:
        """Test all switches have required fields."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        for switch in SWITCH_TYPES:
            assert switch.key is not None
            assert switch.translation_key is not None
            assert callable(switch.is_on_fn)
            assert callable(switch.turn_on_fn)
            assert callable(switch.turn_off_fn)

    @pytest.mark.asyncio
    async def test_protection_turn_on(self) -> None:
        """Test protection switch turn_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_protection = AsyncMock()

        protection_desc = next(
            d for d in SWITCH_TYPES if d.key == "protection"
        )
        await protection_desc.turn_on_fn(mock_client)

        mock_client.set_protection.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_protection_turn_off(self) -> None:
        """Test protection switch turn_off function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_protection = AsyncMock()

        protection_desc = next(
            d for d in SWITCH_TYPES if d.key == "protection"
        )
        await protection_desc.turn_off_fn(mock_client)

        mock_client.set_protection.assert_called_once_with(False)

    @pytest.mark.asyncio
    async def test_safe_browsing_toggle(self) -> None:
        """Test safe browsing switch toggle functions."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_safebrowsing = AsyncMock()

        safe_browsing_desc = next(
            d for d in SWITCH_TYPES if d.key == "safe_browsing"
        )

        await safe_browsing_desc.turn_on_fn(mock_client)
        mock_client.set_safebrowsing.assert_called_with(True)

        await safe_browsing_desc.turn_off_fn(mock_client)
        mock_client.set_safebrowsing.assert_called_with(False)

    @pytest.mark.asyncio
    async def test_parental_toggle(self) -> None:
        """Test parental control switch toggle functions."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_parental = AsyncMock()

        parental_desc = next(
            d for d in SWITCH_TYPES if d.key == "parental_control"
        )

        await parental_desc.turn_on_fn(mock_client)
        mock_client.set_parental.assert_called_with(True)

        await parental_desc.turn_off_fn(mock_client)
        mock_client.set_parental.assert_called_with(False)

    @pytest.mark.asyncio
    async def test_safe_search_toggle(self) -> None:
        """Test safe search switch toggle functions."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_safesearch = AsyncMock()

        safe_search_desc = next(
            d for d in SWITCH_TYPES if d.key == "safe_search"
        )

        await safe_search_desc.turn_on_fn(mock_client)
        mock_client.set_safesearch.assert_called_with(True)

        await safe_search_desc.turn_off_fn(mock_client)
        mock_client.set_safesearch.assert_called_with(False)


class TestSwitchNoneHandling:
    """Tests for switch handling of None data."""

    def test_protection_switch_none_status(self) -> None:
        """Test protection switch with None status."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()  # status is None

        protection_desc = next(
            d for d in SWITCH_TYPES if d.key == "protection"
        )
        is_on = protection_desc.is_on_fn(data)
        assert is_on is None

    def test_filtering_switch_none_filtering(self) -> None:
        """Test filtering switch with None filtering status."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()  # filtering is None

        filtering_desc = next(
            d for d in SWITCH_TYPES if d.key == "filtering"
        )
        is_on = filtering_desc.is_on_fn(data)
        assert is_on is None
