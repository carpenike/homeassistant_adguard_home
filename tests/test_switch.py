"""Tests for the AdGuard Home Extended switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStatus,
    DnsInfo,
    DnsRewrite,
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
            version="0.107.43",
        )
        data.filtering = FilteringStatus(enabled=True)
        data.dns_info = DnsInfo(cache_enabled=True)
        # These are now fetched from separate endpoints
        data.safebrowsing_enabled = True
        data.parental_enabled = True
        data.safesearch_enabled = True
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
        )
        data.safebrowsing_enabled = False

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
        )
        data.parental_enabled = False

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
        )
        data.safesearch_enabled = False

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
    """Tests for DNS cache switch (using AdGuardDnsCacheSwitch class)."""

    def test_dns_cache_switch_is_on(self) -> None:
        """Test DNS cache switch is_on when enabled."""
        from custom_components.adguard_home_extended.switch import AdGuardDnsCacheSwitch

        # Create mock coordinator
        mock_coordinator = MagicMock()
        mock_coordinator.config_entry.entry_id = "test_entry"
        mock_coordinator.device_info = {}
        mock_coordinator.data = AdGuardHomeData()
        mock_coordinator.data.dns_info = DnsInfo(cache_enabled=True)

        switch = AdGuardDnsCacheSwitch(mock_coordinator)
        assert switch.is_on is True

    def test_dns_cache_switch_is_off(self) -> None:
        """Test DNS cache switch is_on when disabled."""
        from custom_components.adguard_home_extended.switch import AdGuardDnsCacheSwitch

        mock_coordinator = MagicMock()
        mock_coordinator.config_entry.entry_id = "test_entry"
        mock_coordinator.device_info = {}
        mock_coordinator.data = AdGuardHomeData()
        mock_coordinator.data.dns_info = DnsInfo(cache_enabled=False)

        switch = AdGuardDnsCacheSwitch(mock_coordinator)
        assert switch.is_on is False

    def test_dns_cache_switch_none_dns_info(self) -> None:
        """Test DNS cache switch with None dns_info."""
        from custom_components.adguard_home_extended.switch import AdGuardDnsCacheSwitch

        mock_coordinator = MagicMock()
        mock_coordinator.config_entry.entry_id = "test_entry"
        mock_coordinator.device_info = {}
        mock_coordinator.data = AdGuardHomeData()  # dns_info is None

        switch = AdGuardDnsCacheSwitch(mock_coordinator)
        assert switch.is_on is None

    @pytest.mark.asyncio
    async def test_dns_cache_toggle_supported_version(self) -> None:
        """Test DNS cache switch toggle when version supports cache_enabled."""
        from custom_components.adguard_home_extended.switch import AdGuardDnsCacheSwitch

        mock_coordinator = MagicMock()
        mock_coordinator.config_entry.entry_id = "test_entry"
        mock_coordinator.device_info = {}
        mock_coordinator.data = AdGuardHomeData()
        mock_coordinator.data.dns_info = DnsInfo(cache_enabled=True)
        mock_coordinator.server_version.supports_cache_enabled = True
        mock_coordinator.client.set_dns_cache_enabled = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        switch = AdGuardDnsCacheSwitch(mock_coordinator)

        await switch.async_turn_on()
        mock_coordinator.client.set_dns_cache_enabled.assert_called_with(True)

        await switch.async_turn_off()
        mock_coordinator.client.set_dns_cache_enabled.assert_called_with(False)

    @pytest.mark.asyncio
    async def test_dns_cache_toggle_unsupported_version(self) -> None:
        """Test DNS cache switch toggle when version doesn't support cache_enabled."""
        from custom_components.adguard_home_extended.switch import AdGuardDnsCacheSwitch

        mock_coordinator = MagicMock()
        mock_coordinator.config_entry.entry_id = "test_entry"
        mock_coordinator.device_info = {}
        mock_coordinator.data = AdGuardHomeData()
        mock_coordinator.data.dns_info = DnsInfo(cache_enabled=True, cache_size=4194304)
        mock_coordinator.server_version.supports_cache_enabled = False
        mock_coordinator.client.set_dns_cache_enabled = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        switch = AdGuardDnsCacheSwitch(mock_coordinator)

        # Should not call the API on older versions
        await switch.async_turn_on()
        mock_coordinator.client.set_dns_cache_enabled.assert_not_called()

        await switch.async_turn_off()
        mock_coordinator.client.set_dns_cache_enabled.assert_not_called()

    def test_dns_cache_extra_attributes(self) -> None:
        """Test DNS cache switch extra state attributes."""
        from custom_components.adguard_home_extended.switch import AdGuardDnsCacheSwitch

        mock_coordinator = MagicMock()
        mock_coordinator.config_entry.entry_id = "test_entry"
        mock_coordinator.device_info = {}
        mock_coordinator.data = AdGuardHomeData()
        mock_coordinator.data.dns_info = DnsInfo(
            cache_enabled=True, cache_size=100000000
        )
        mock_coordinator.server_version.supports_cache_enabled = True

        switch = AdGuardDnsCacheSwitch(mock_coordinator)
        attrs = switch.extra_state_attributes

        assert attrs["native_toggle_support"] is True
        assert attrs["cache_size"] == 100000000


class TestDnssecSwitch:
    """Tests for DNSSEC switch."""

    def test_dnssec_switch_is_on(self) -> None:
        """Test DNSSEC switch is_on function when enabled."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.dns_info = DnsInfo(dnssec_enabled=True)

        dnssec_desc = next(d for d in SWITCH_TYPES if d.key == "dnssec")
        is_on = dnssec_desc.is_on_fn(data)
        assert is_on is True

    def test_dnssec_switch_is_off(self) -> None:
        """Test DNSSEC switch is_on function when disabled."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.dns_info = DnsInfo(dnssec_enabled=False)

        dnssec_desc = next(d for d in SWITCH_TYPES if d.key == "dnssec")
        is_on = dnssec_desc.is_on_fn(data)
        assert is_on is False

    def test_dnssec_switch_none_dns_info(self) -> None:
        """Test DNSSEC switch with None dns_info."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()  # dns_info is None

        dnssec_desc = next(d for d in SWITCH_TYPES if d.key == "dnssec")
        is_on = dnssec_desc.is_on_fn(data)
        assert is_on is None

    @pytest.mark.asyncio
    async def test_dnssec_toggle(self) -> None:
        """Test DNSSEC switch toggle functions."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_dnssec_enabled = AsyncMock()

        dnssec_desc = next(d for d in SWITCH_TYPES if d.key == "dnssec")

        await dnssec_desc.turn_on_fn(mock_client)
        mock_client.set_dnssec_enabled.assert_called_with(True)

        await dnssec_desc.turn_off_fn(mock_client)
        mock_client.set_dnssec_enabled.assert_called_with(False)


class TestEdnsClientSubnetSwitch:
    """Tests for EDNS Client Subnet switch."""

    def test_edns_cs_switch_is_on(self) -> None:
        """Test EDNS CS switch is_on function when enabled."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.dns_info = DnsInfo(edns_cs_enabled=True)

        edns_desc = next(d for d in SWITCH_TYPES if d.key == "edns_client_subnet")
        is_on = edns_desc.is_on_fn(data)
        assert is_on is True

    def test_edns_cs_switch_is_off(self) -> None:
        """Test EDNS CS switch is_on function when disabled."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.dns_info = DnsInfo(edns_cs_enabled=False)

        edns_desc = next(d for d in SWITCH_TYPES if d.key == "edns_client_subnet")
        is_on = edns_desc.is_on_fn(data)
        assert is_on is False

    def test_edns_cs_switch_none_dns_info(self) -> None:
        """Test EDNS CS switch with None dns_info."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()  # dns_info is None

        edns_desc = next(d for d in SWITCH_TYPES if d.key == "edns_client_subnet")
        is_on = edns_desc.is_on_fn(data)
        assert is_on is None

    @pytest.mark.asyncio
    async def test_edns_cs_toggle(self) -> None:
        """Test EDNS CS switch toggle functions."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_edns_cs_enabled = AsyncMock()

        edns_desc = next(d for d in SWITCH_TYPES if d.key == "edns_client_subnet")

        await edns_desc.turn_on_fn(mock_client)
        mock_client.set_edns_cs_enabled.assert_called_with(True)

        await edns_desc.turn_off_fn(mock_client)
        mock_client.set_edns_cs_enabled.assert_called_with(False)


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

    def test_dns_rewrite_switch_data_is_none(self) -> None:
        """Test DNS rewrite switch when coordinator.data is None."""
        from unittest.mock import MagicMock

        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}
        coordinator.data = None

        switch = AdGuardDnsRewriteSwitch(coordinator, "ads.example.com", "0.0.0.0")

        # _get_rewrite_data should return None when data is None
        assert switch._get_rewrite_data() is None
        assert switch.is_on is None
        assert switch.available is False

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


class TestQueryLoggingAndStatsSwitch:
    """Tests for query logging and statistics switches."""

    def test_query_logging_is_on_when_enabled(self) -> None:
        """Test query logging switch is_on_fn when enabled."""
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.querylog_config = {"enabled": True}

        desc = next(d for d in SWITCH_TYPES if d.key == "query_logging")
        assert desc.is_on_fn(data) is True

    def test_query_logging_is_off_when_disabled(self) -> None:
        """Test query logging switch is_on_fn when disabled."""
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.querylog_config = {"enabled": False}

        desc = next(d for d in SWITCH_TYPES if d.key == "query_logging")
        assert desc.is_on_fn(data) is False

    def test_query_logging_is_none_when_no_config(self) -> None:
        """Test query logging switch is_on_fn when config unavailable."""
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.querylog_config = None

        desc = next(d for d in SWITCH_TYPES if d.key == "query_logging")
        assert desc.is_on_fn(data) is None

    @pytest.mark.asyncio
    async def test_query_logging_turn_on(self) -> None:
        """Test query logging switch turn_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_querylog_config = AsyncMock()

        desc = next(d for d in SWITCH_TYPES if d.key == "query_logging")
        await desc.turn_on_fn(mock_client)

        mock_client.set_querylog_config.assert_called_once_with(enabled=True)

    @pytest.mark.asyncio
    async def test_query_logging_turn_off(self) -> None:
        """Test query logging switch turn_off function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_querylog_config = AsyncMock()

        desc = next(d for d in SWITCH_TYPES if d.key == "query_logging")
        await desc.turn_off_fn(mock_client)

        mock_client.set_querylog_config.assert_called_once_with(enabled=False)

    def test_statistics_is_on_when_enabled(self) -> None:
        """Test statistics switch is_on_fn when enabled."""
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.stats_config = {"enabled": True}

        desc = next(d for d in SWITCH_TYPES if d.key == "statistics")
        assert desc.is_on_fn(data) is True

    def test_statistics_is_off_when_disabled(self) -> None:
        """Test statistics switch is_on_fn when disabled."""
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.stats_config = {"enabled": False}

        desc = next(d for d in SWITCH_TYPES if d.key == "statistics")
        assert desc.is_on_fn(data) is False

    def test_statistics_is_none_when_no_config(self) -> None:
        """Test statistics switch is_on_fn when config unavailable."""
        from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        data = AdGuardHomeData()
        data.stats_config = None

        desc = next(d for d in SWITCH_TYPES if d.key == "statistics")
        assert desc.is_on_fn(data) is None

    @pytest.mark.asyncio
    async def test_statistics_turn_on(self) -> None:
        """Test statistics switch turn_on function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_stats_config = AsyncMock()

        desc = next(d for d in SWITCH_TYPES if d.key == "statistics")
        await desc.turn_on_fn(mock_client)

        mock_client.set_stats_config.assert_called_once_with(enabled=True)

    @pytest.mark.asyncio
    async def test_statistics_turn_off(self) -> None:
        """Test statistics switch turn_off function."""
        from custom_components.adguard_home_extended.switch import SWITCH_TYPES

        mock_client = AsyncMock()
        mock_client.set_stats_config = AsyncMock()

        desc = next(d for d in SWITCH_TYPES if d.key == "statistics")
        await desc.turn_off_fn(mock_client)

        mock_client.set_stats_config.assert_called_once_with(enabled=False)


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_creates_switches(self) -> None:
        """Test that async_setup_entry creates all switch entities."""
        from custom_components.adguard_home_extended.switch import async_setup_entry

        # Mock Home Assistant
        mock_hass = MagicMock()
        mock_hass.data = {}

        # Mock config entry
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_123"

        # Mock coordinator with data
        mock_coordinator = MagicMock()
        mock_coordinator.data = AdGuardHomeData()
        mock_coordinator.data.clients = []
        mock_coordinator.data.rewrites = []
        mock_coordinator.async_add_listener = MagicMock(return_value=lambda: None)
        mock_entry.runtime_data = mock_coordinator

        # Track added entities
        added_entities = []

        def capture_entities(entities):
            added_entities.extend(entities)

        mock_async_add_entities = MagicMock(side_effect=capture_entities)

        # Patch filter manager in filter_lists module where it's defined
        with patch(
            "custom_components.adguard_home_extended.filter_lists.FilterListEntityManager"
        ) as mock_filter_manager:
            mock_filter_manager.return_value.async_setup = AsyncMock()
            await async_setup_entry(mock_hass, mock_entry, mock_async_add_entities)

        # Should have created 10 global switches
        assert len(added_entities) == 10
        # Verify managers are stored
        assert "client_managers" in mock_hass.data["adguard_home_extended"]
        assert "rewrite_managers" in mock_hass.data["adguard_home_extended"]


class TestAdGuardHomeSwitch:
    """Tests for AdGuardHomeSwitch entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {"identifiers": {("adguard_home_extended", "test")}}
        coordinator.data = AdGuardHomeData()
        coordinator.client = MagicMock()
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    def test_switch_initialization(self, mock_coordinator: MagicMock) -> None:
        """Test AdGuardHomeSwitch initialization."""
        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        description = next(d for d in SWITCH_TYPES if d.key == "protection")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        assert switch._attr_unique_id == "test_entry_123_protection"
        assert switch.entity_description == description

    def test_switch_is_on_property(self, mock_coordinator: MagicMock) -> None:
        """Test AdGuardHomeSwitch is_on property."""
        from custom_components.adguard_home_extended.api.models import AdGuardHomeStatus
        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        mock_coordinator.data.status = AdGuardHomeStatus(
            protection_enabled=True, running=True
        )

        description = next(d for d in SWITCH_TYPES if d.key == "protection")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        assert switch.is_on is True

    @pytest.mark.asyncio
    async def test_switch_async_turn_on(self, mock_coordinator: MagicMock) -> None:
        """Test AdGuardHomeSwitch async_turn_on method."""
        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        mock_coordinator.client.set_protection = AsyncMock()

        description = next(d for d in SWITCH_TYPES if d.key == "protection")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        await switch.async_turn_on()

        mock_coordinator.client.set_protection.assert_called_once_with(True)
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_switch_async_turn_off(self, mock_coordinator: MagicMock) -> None:
        """Test AdGuardHomeSwitch async_turn_off method."""
        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        mock_coordinator.client.set_protection = AsyncMock()

        description = next(d for d in SWITCH_TYPES if d.key == "protection")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        await switch.async_turn_off()

        mock_coordinator.client.set_protection.assert_called_once_with(False)
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_switch_available_when_data_present(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test AdGuardHomeSwitch available when required data is present."""
        from custom_components.adguard_home_extended.api.models import AdGuardHomeStatus
        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        # Set up coordinator as available with valid data
        mock_coordinator.last_update_success = True
        mock_coordinator.data.status = AdGuardHomeStatus(
            protection_enabled=True, running=True
        )

        description = next(d for d in SWITCH_TYPES if d.key == "protection")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        assert switch.available is True

    def test_switch_unavailable_when_data_missing(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test AdGuardHomeSwitch unavailable when required data is None."""
        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        # Set up coordinator as available but data.status is None
        mock_coordinator.last_update_success = True
        mock_coordinator.data.status = None

        description = next(d for d in SWITCH_TYPES if d.key == "protection")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        assert switch.available is False

    def test_switch_unavailable_when_stats_config_missing(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test statistics switch unavailable when stats_config is None."""
        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        # Set up coordinator as available but stats_config is None
        mock_coordinator.last_update_success = True
        mock_coordinator.data.stats_config = None

        description = next(d for d in SWITCH_TYPES if d.key == "statistics")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        assert switch.available is False

    def test_switch_available_when_stats_config_present(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test statistics switch available when stats_config is present."""
        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        # Set up coordinator as available with stats_config
        mock_coordinator.last_update_success = True
        mock_coordinator.data.stats_config = {"enabled": True, "interval": 86400000}

        description = next(d for d in SWITCH_TYPES if d.key == "statistics")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        assert switch.available is True

    def test_switch_logs_unavailability_once(
        self, mock_coordinator: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that switch logs unavailability only once."""
        import logging

        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        mock_coordinator.last_update_success = True
        mock_coordinator.data.stats_config = None

        description = next(d for d in SWITCH_TYPES if d.key == "statistics")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        with caplog.at_level(logging.DEBUG):
            # First check - should log
            _ = switch.available
            # Second check - should NOT log again
            _ = switch.available
            # Third check - should NOT log again
            _ = switch.available

        # Should only have one log message about unavailability
        unavailable_logs = [
            r for r in caplog.records if "unavailable" in r.message.lower()
        ]
        assert len(unavailable_logs) == 1
        assert "statistics" in unavailable_logs[0].message

    def test_switch_resets_unavailability_flag_when_data_returns(
        self, mock_coordinator: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that switch resets log flag when data becomes available again."""
        import logging

        from custom_components.adguard_home_extended.switch import (
            SWITCH_TYPES,
            AdGuardHomeSwitch,
        )

        mock_coordinator.last_update_success = True
        mock_coordinator.data.stats_config = None

        description = next(d for d in SWITCH_TYPES if d.key == "statistics")
        switch = AdGuardHomeSwitch(mock_coordinator, description)

        with caplog.at_level(logging.DEBUG):
            # First check - unavailable, logs
            assert switch.available is False
            assert switch._logged_unavailable is True

            # Data becomes available
            mock_coordinator.data.stats_config = {"enabled": True}
            assert switch.available is True
            assert switch._logged_unavailable is False

            # Data goes away again - should log again
            mock_coordinator.data.stats_config = None
            assert switch.available is False

        # Should have two log messages (once for each unavailability)
        unavailable_logs = [
            r for r in caplog.records if "unavailable" in r.message.lower()
        ]
        assert len(unavailable_logs) == 2


class TestClientEntityManager:
    """Tests for ClientEntityManager."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = MagicMock()
        coordinator.hass.async_create_task = MagicMock()
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = []
        coordinator.async_add_listener = MagicMock(return_value=lambda: None)
        return coordinator

    @pytest.mark.asyncio
    async def test_manager_setup_no_clients(self, mock_coordinator: MagicMock) -> None:
        """Test ClientEntityManager setup with no clients."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = ClientEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        # No entities should be added when no clients
        assert len(added_entities) == 0
        # Listener should be registered
        mock_coordinator.async_add_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_setup_with_clients(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test ClientEntityManager setup with existing clients."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        mock_coordinator.data.clients = [
            {
                "name": "laptop",
                "ids": ["192.168.1.100"],
                "use_global_settings": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            }
        ]

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = ClientEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        # Should add 6 entities per client
        assert len(added_entities) == 6

    @pytest.mark.asyncio
    async def test_manager_handles_new_clients(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test ClientEntityManager adds entities for new clients."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = ClientEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        # Initial: no clients
        assert len(added_entities) == 0

        # Add a client
        mock_coordinator.data.clients = [
            {
                "name": "laptop",
                "ids": ["192.168.1.100"],
                "use_global_settings": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            }
        ]

        # Simulate coordinator update
        await manager._async_add_new_client_entities()

        # Should have added 6 entities
        assert len(added_entities) == 6

    @pytest.mark.asyncio
    async def test_manager_skips_existing_clients(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test ClientEntityManager doesn't duplicate entities for existing clients."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        mock_coordinator.data.clients = [
            {
                "name": "laptop",
                "ids": ["192.168.1.100"],
                "use_global_settings": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            }
        ]

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = ClientEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        initial_count = len(added_entities)

        # Call again - should not add duplicates
        await manager._async_add_new_client_entities()

        assert len(added_entities) == initial_count

    def test_manager_unsubscribe(self, mock_coordinator: MagicMock) -> None:
        """Test ClientEntityManager unsubscribe."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        unsubscribe_called = []
        mock_coordinator.async_add_listener = MagicMock(
            return_value=lambda: unsubscribe_called.append(True)
        )

        manager = ClientEntityManager(mock_coordinator, MagicMock())
        manager._unsubscribe = mock_coordinator.async_add_listener()

        manager.async_unsubscribe()

        assert len(unsubscribe_called) == 1
        assert manager._unsubscribe is None

    def test_manager_handle_coordinator_update(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test ClientEntityManager coordinator update callback."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        manager = ClientEntityManager(mock_coordinator, MagicMock())

        # Should schedule async task
        manager._handle_coordinator_update()

        mock_coordinator.hass.async_create_task.assert_called_once()


class TestDnsRewriteEntityManager:
    """Tests for DnsRewriteEntityManager."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}
        coordinator.hass = MagicMock()
        coordinator.hass.async_create_task = MagicMock()
        coordinator.data = AdGuardHomeData()
        coordinator.data.rewrites = []
        coordinator.async_add_listener = MagicMock(return_value=lambda: None)
        return coordinator

    @pytest.mark.asyncio
    async def test_manager_setup_no_rewrites(self, mock_coordinator: MagicMock) -> None:
        """Test DnsRewriteEntityManager setup with no rewrites."""
        from custom_components.adguard_home_extended.switch import (
            DnsRewriteEntityManager,
        )

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = DnsRewriteEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        assert len(added_entities) == 0
        mock_coordinator.async_add_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_setup_with_rewrites(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test DnsRewriteEntityManager setup with existing rewrites."""
        from custom_components.adguard_home_extended.api.models import DnsRewrite
        from custom_components.adguard_home_extended.switch import (
            DnsRewriteEntityManager,
        )

        mock_coordinator.data.rewrites = [
            DnsRewrite(domain="ads.example.com", answer="0.0.0.0", enabled=True),
            DnsRewrite(domain="local.home", answer="192.168.1.1", enabled=True),
        ]

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = DnsRewriteEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        assert len(added_entities) == 2

    @pytest.mark.asyncio
    async def test_manager_handles_new_rewrites(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test DnsRewriteEntityManager adds entities for new rewrites."""
        from custom_components.adguard_home_extended.api.models import DnsRewrite
        from custom_components.adguard_home_extended.switch import (
            DnsRewriteEntityManager,
        )

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = DnsRewriteEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        # Add a rewrite
        mock_coordinator.data.rewrites = [
            DnsRewrite(domain="new.example.com", answer="127.0.0.1", enabled=True),
        ]

        await manager._async_add_new_rewrite_entities()

        assert len(added_entities) == 1

    @pytest.mark.asyncio
    async def test_manager_skips_existing_rewrites(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test DnsRewriteEntityManager doesn't duplicate existing rewrites."""
        from custom_components.adguard_home_extended.api.models import DnsRewrite
        from custom_components.adguard_home_extended.switch import (
            DnsRewriteEntityManager,
        )

        mock_coordinator.data.rewrites = [
            DnsRewrite(domain="ads.example.com", answer="0.0.0.0", enabled=True),
        ]

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = DnsRewriteEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        initial_count = len(added_entities)

        # Call again - should not add duplicates
        await manager._async_add_new_rewrite_entities()

        assert len(added_entities) == initial_count

    def test_manager_unsubscribe(self, mock_coordinator: MagicMock) -> None:
        """Test DnsRewriteEntityManager unsubscribe."""
        from custom_components.adguard_home_extended.switch import (
            DnsRewriteEntityManager,
        )

        unsubscribe_called = []
        mock_coordinator.async_add_listener = MagicMock(
            return_value=lambda: unsubscribe_called.append(True)
        )

        manager = DnsRewriteEntityManager(mock_coordinator, MagicMock())
        manager._unsubscribe = mock_coordinator.async_add_listener()

        manager.async_unsubscribe()

        assert len(unsubscribe_called) == 1
        assert manager._unsubscribe is None

    def test_manager_handle_coordinator_update(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test DnsRewriteEntityManager coordinator update callback."""
        from custom_components.adguard_home_extended.switch import (
            DnsRewriteEntityManager,
        )

        manager = DnsRewriteEntityManager(mock_coordinator, MagicMock())

        manager._handle_coordinator_update()

        mock_coordinator.hass.async_create_task.assert_called_once()


class TestDnsRewriteSwitchVersionGating:
    """Tests for version-gated DNS rewrite switch behavior."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {}
        coordinator.client = MagicMock()
        coordinator.async_request_refresh = AsyncMock()

        # Setup data with a rewrite
        data = AdGuardHomeData()
        data.rewrites = [
            DnsRewrite(domain="ads.example.com", answer="0.0.0.0", enabled=True),
        ]
        coordinator.data = data

        return coordinator

    def test_extra_attributes_with_version_support(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test extra_state_attributes includes native toggle support info."""
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        mock_coordinator.server_version = MagicMock()
        mock_coordinator.server_version.supports_rewrite_enabled = True

        switch = AdGuardDnsRewriteSwitch(mock_coordinator, "ads.example.com", "0.0.0.0")

        attrs = switch.extra_state_attributes
        assert attrs["native_toggle_support"] is True

    def test_is_on_older_version_always_true(self, mock_coordinator: MagicMock) -> None:
        """Test is_on returns True for older versions without enabled field support."""
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        mock_coordinator.server_version = MagicMock()
        mock_coordinator.server_version.supports_rewrite_enabled = False

        switch = AdGuardDnsRewriteSwitch(mock_coordinator, "ads.example.com", "0.0.0.0")

        # Even if the rewrite has enabled=False, older versions report True
        assert switch.is_on is True

    @pytest.mark.asyncio
    async def test_turn_on_older_version_no_action(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turn_on does nothing for older versions."""
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        mock_coordinator.server_version = MagicMock()
        mock_coordinator.server_version.supports_rewrite_enabled = False
        mock_coordinator.client.set_rewrite_enabled = AsyncMock()

        switch = AdGuardDnsRewriteSwitch(mock_coordinator, "ads.example.com", "0.0.0.0")

        await switch.async_turn_on()

        # Should not call API for older versions
        mock_coordinator.client.set_rewrite_enabled.assert_not_called()
        # Should still refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_older_version_logs_warning(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turn_off logs warning for older versions."""
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        mock_coordinator.server_version = MagicMock()
        mock_coordinator.server_version.supports_rewrite_enabled = False
        mock_coordinator.client.set_rewrite_enabled = AsyncMock()

        switch = AdGuardDnsRewriteSwitch(mock_coordinator, "ads.example.com", "0.0.0.0")

        with patch(
            "custom_components.adguard_home_extended.switch._LOGGER"
        ) as mock_logger:
            await switch.async_turn_off()

            mock_logger.warning.assert_called_once()
            assert "Cannot disable" in mock_logger.warning.call_args[0][0]

        # Should not call API
        mock_coordinator.client.set_rewrite_enabled.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_newer_version_calls_api(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turn_on calls API for newer versions."""
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        mock_coordinator.server_version = MagicMock()
        mock_coordinator.server_version.supports_rewrite_enabled = True
        mock_coordinator.client.set_rewrite_enabled = AsyncMock()

        switch = AdGuardDnsRewriteSwitch(mock_coordinator, "ads.example.com", "0.0.0.0")

        await switch.async_turn_on()

        mock_coordinator.client.set_rewrite_enabled.assert_called_once_with(
            "ads.example.com", "0.0.0.0", True
        )

    @pytest.mark.asyncio
    async def test_turn_off_newer_version_calls_api(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turn_off calls API for newer versions."""
        from custom_components.adguard_home_extended.switch import (
            AdGuardDnsRewriteSwitch,
        )

        mock_coordinator.server_version = MagicMock()
        mock_coordinator.server_version.supports_rewrite_enabled = True
        mock_coordinator.client.set_rewrite_enabled = AsyncMock()

        switch = AdGuardDnsRewriteSwitch(mock_coordinator, "ads.example.com", "0.0.0.0")

        await switch.async_turn_off()

        mock_coordinator.client.set_rewrite_enabled.assert_called_once_with(
            "ads.example.com", "0.0.0.0", False
        )
