"""Tests for the AdGuard Home Extended switch platform."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStatus,
    DnsInfo,
    FilteringStatus,
)
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData


class TestSwitchEntityDescriptions:
    """Tests for switch entity descriptions."""

    @pytest.fixture
    def data_with_status(self) -> AdGuardHomeData:
        """Return data with status."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            safebrowsing_enabled=True,
            parental_enabled=True,
            safesearch_enabled=True,
            version="0.107.43",
        )
        data.filtering = FilteringStatus(enabled=True)
        data.dns_info = DnsInfo(cache_enabled=True)
        return data

    def test_protection_switch_is_on(self, data_with_status: AdGuardHomeData) -> None:
        """Test protection switch is_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        protection_desc = next(d for d in SWITCH_TYPES if d.key == "protection")
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

        protection_desc = next(d for d in SWITCH_TYPES if d.key == "protection")
        is_on = protection_desc.is_on_fn(data)
        assert is_on is False

    def test_filtering_switch_is_on(self, data_with_status: AdGuardHomeData) -> None:
        """Test filtering switch is_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        filtering_desc = next(d for d in SWITCH_TYPES if d.key == "filtering")
        is_on = filtering_desc.is_on_fn(data_with_status)
        assert is_on is True

    def test_safe_browsing_switch_is_on(
        self, data_with_status: AdGuardHomeData
    ) -> None:
        """Test safe browsing switch is_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        safe_browsing_desc = next(d for d in SWITCH_TYPES if d.key == "safe_browsing")
        is_on = safe_browsing_desc.is_on_fn(data_with_status)
        assert is_on is True

    def test_safe_browsing_switch_is_off(self) -> None:
        """Test safe browsing switch when off."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            safebrowsing_enabled=False,
        )

        safe_browsing_desc = next(d for d in SWITCH_TYPES if d.key == "safe_browsing")
        is_on = safe_browsing_desc.is_on_fn(data)
        assert is_on is False

    def test_parental_control_switch_is_on(
        self, data_with_status: AdGuardHomeData
    ) -> None:
        """Test parental control switch is_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        parental_desc = next(d for d in SWITCH_TYPES if d.key == "parental_control")
        is_on = parental_desc.is_on_fn(data_with_status)
        assert is_on is True

    def test_parental_control_switch_is_off(self) -> None:
        """Test parental control switch when off."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            parental_enabled=False,
        )

        parental_desc = next(d for d in SWITCH_TYPES if d.key == "parental_control")
        is_on = parental_desc.is_on_fn(data)
        assert is_on is False

    def test_safe_search_switch_is_on(self, data_with_status: AdGuardHomeData) -> None:
        """Test safe search switch is_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        safe_search_desc = next(d for d in SWITCH_TYPES if d.key == "safe_search")
        is_on = safe_search_desc.is_on_fn(data_with_status)
        assert is_on is True

    def test_safe_search_switch_is_off(self) -> None:
        """Test safe search switch when off."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            safesearch_enabled=False,
        )

        safe_search_desc = next(d for d in SWITCH_TYPES if d.key == "safe_search")
        is_on = safe_search_desc.is_on_fn(data)
        assert is_on is False

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

        protection_desc = next(d for d in SWITCH_TYPES if d.key == "protection")
        await protection_desc.turn_on_fn(mock_client)

        mock_client.set_protection.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_protection_turn_off(self) -> None:
        """Test protection switch turn_off function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_protection = AsyncMock()

        protection_desc = next(d for d in SWITCH_TYPES if d.key == "protection")
        await protection_desc.turn_off_fn(mock_client)

        mock_client.set_protection.assert_called_once_with(False)

    @pytest.mark.asyncio
    async def test_safe_browsing_toggle(self) -> None:
        """Test safe browsing switch toggle functions."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_safebrowsing = AsyncMock()

        safe_browsing_desc = next(d for d in SWITCH_TYPES if d.key == "safe_browsing")

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

        parental_desc = next(d for d in SWITCH_TYPES if d.key == "parental_control")

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

        safe_search_desc = next(d for d in SWITCH_TYPES if d.key == "safe_search")

        await safe_search_desc.turn_on_fn(mock_client)
        mock_client.set_safesearch.assert_called_with(True)

        await safe_search_desc.turn_off_fn(mock_client)
        mock_client.set_safesearch.assert_called_with(False)

    @pytest.mark.asyncio
    async def test_filtering_toggle(self) -> None:
        """Test filtering switch toggle functions."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_filtering = AsyncMock()

        filtering_desc = next(d for d in SWITCH_TYPES if d.key == "filtering")

        await filtering_desc.turn_on_fn(mock_client)
        mock_client.set_filtering.assert_called_with(True)

        await filtering_desc.turn_off_fn(mock_client)
        mock_client.set_filtering.assert_called_with(False)


class TestSwitchNoneHandling:
    """Tests for switch handling of None data."""

    def test_protection_switch_none_status(self) -> None:
        """Test protection switch with None status."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()  # status is None

        protection_desc = next(d for d in SWITCH_TYPES if d.key == "protection")
        is_on = protection_desc.is_on_fn(data)
        assert is_on is None

    def test_filtering_switch_none_filtering(self) -> None:
        """Test filtering switch with None filtering status."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()  # filtering is None

        filtering_desc = next(d for d in SWITCH_TYPES if d.key == "filtering")
        is_on = filtering_desc.is_on_fn(data)
        assert is_on is None


class TestDnsCacheSwitch:
    """Tests for DNS cache switch."""

    def test_dns_cache_switch_is_on(self) -> None:
        """Test DNS cache switch is_on function when enabled."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.dns_info = DnsInfo(cache_enabled=True)

        dns_cache_desc = next(d for d in SWITCH_TYPES if d.key == "dns_cache")
        is_on = dns_cache_desc.is_on_fn(data)
        assert is_on is True

    def test_dns_cache_switch_is_off(self) -> None:
        """Test DNS cache switch is_on function when disabled."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.dns_info = DnsInfo(cache_enabled=False)

        dns_cache_desc = next(d for d in SWITCH_TYPES if d.key == "dns_cache")
        is_on = dns_cache_desc.is_on_fn(data)
        assert is_on is False

    def test_dns_cache_switch_none_dns_info(self) -> None:
        """Test DNS cache switch with None dns_info."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()  # dns_info is None

        dns_cache_desc = next(d for d in SWITCH_TYPES if d.key == "dns_cache")
        is_on = dns_cache_desc.is_on_fn(data)
        assert is_on is None

    @pytest.mark.asyncio
    async def test_dns_cache_toggle(self) -> None:
        """Test DNS cache switch toggle functions."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_dns_cache_enabled = AsyncMock()

        dns_cache_desc = next(d for d in SWITCH_TYPES if d.key == "dns_cache")

        await dns_cache_desc.turn_on_fn(mock_client)
        mock_client.set_dns_cache_enabled.assert_called_with(True)

        await dns_cache_desc.turn_off_fn(mock_client)
        mock_client.set_dns_cache_enabled.assert_called_with(False)


class TestDnsRewriteSwitch:
    """Tests for DNS rewrite switch entities."""

    def test_get_rewrite_unique_id(self) -> None:
        """Test unique ID generation for DNS rewrites."""
        from custom_components.adguard_home_extended.switch import (
            _get_rewrite_unique_id,
        )

        # Same inputs should produce same ID
        id1 = _get_rewrite_unique_id("example.com", "192.168.1.1")
        id2 = _get_rewrite_unique_id("example.com", "192.168.1.1")
        assert id1 == id2

        # Different inputs should produce different IDs
        id3 = _get_rewrite_unique_id("other.com", "192.168.1.1")
        assert id1 != id3

        id4 = _get_rewrite_unique_id("example.com", "192.168.1.2")
        assert id1 != id4

    def test_dns_rewrite_switch_init(self) -> None:
        """Test DNS rewrite switch initialization."""
        from unittest.mock import MagicMock

        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
            _get_rewrite_unique_id,
        )

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {"identifiers": {("adguard_home_extended", "test")}}

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        expected_unique_id = (
            f"test_entry_123_rewrite_"
            f"{_get_rewrite_unique_id('ads.example.com', '0.0.0.0')}"
        )
        assert switch._attr_unique_id == expected_unique_id
        assert switch._domain == "ads.example.com"
        assert switch._answer == "0.0.0.0"

    def test_dns_rewrite_switch_name(self) -> None:
        """Test DNS rewrite switch name."""
        from unittest.mock import MagicMock

        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        assert switch.name == "Rewrite ads.example.com"

    def test_dns_rewrite_switch_extra_attributes(self) -> None:
        """Test DNS rewrite switch extra state attributes."""
        from unittest.mock import MagicMock

        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        attrs = switch.extra_state_attributes
        assert attrs["domain"] == "ads.example.com"
        assert attrs["answer"] == "0.0.0.0"

    def test_dns_rewrite_switch_is_on_enabled(self) -> None:
        """Test DNS rewrite switch is_on when enabled."""
        from unittest.mock import MagicMock

        from custom_components.adguard_home_extended.api.models import DnsRewrite
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        data = AdGuardHomeData()
        data.rewrites = [
            DnsRewrite(domain="ads.example.com", answer="0.0.0.0", enabled=True),
        ]

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}
        coordinator.data = data

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        assert switch.is_on is True
        assert switch.available is True

    def test_dns_rewrite_switch_is_on_disabled(self) -> None:
        """Test DNS rewrite switch is_on when disabled."""
        from unittest.mock import MagicMock

        from custom_components.adguard_home_extended.api.models import DnsRewrite
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        data = AdGuardHomeData()
        data.rewrites = [
            DnsRewrite(domain="ads.example.com", answer="0.0.0.0", enabled=False),
        ]

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}
        coordinator.data = data

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        assert switch.is_on is False
        assert switch.available is True

    def test_dns_rewrite_switch_not_available_when_missing(self) -> None:
        """Test DNS rewrite switch unavailable when rewrite is deleted."""
        from unittest.mock import MagicMock

        from custom_components.adguard_home_extended.api.models import DnsRewrite
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        data = AdGuardHomeData()
        data.rewrites = [
            DnsRewrite(domain="other.example.com", answer="0.0.0.0", enabled=True),
        ]

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}
        coordinator.data = data

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        assert switch.available is False
        assert switch.is_on is None

    @pytest.mark.asyncio
    async def test_dns_rewrite_switch_turn_on(self) -> None:
        """Test DNS rewrite switch turn_on."""
        from unittest.mock import AsyncMock, MagicMock

        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}
        coordinator.client = MagicMock()
        coordinator.client.set_rewrite_enabled = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        await switch.async_turn_on()

        coordinator.client.set_rewrite_enabled.assert_called_once_with(
            "ads.example.com", "0.0.0.0", True
        )
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_dns_rewrite_switch_turn_off(self) -> None:
        """Test DNS rewrite switch turn_off."""
        from unittest.mock import AsyncMock, MagicMock

        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}
        coordinator.client = MagicMock()
        coordinator.client.set_rewrite_enabled = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        await switch.async_turn_off()

        coordinator.client.set_rewrite_enabled.assert_called_once_with(
            "ads.example.com", "0.0.0.0", False
        )
        coordinator.async_request_refresh.assert_called_once()
