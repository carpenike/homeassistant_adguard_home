"""Tests for the AdGuard Home Extended sensor platform."""
from __future__ import annotations

import pytest

from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
    DnsRewrite,
)
from custom_components.adguard_home_extended.const import (
    DEFAULT_ATTR_LIST_LIMIT,
    DEFAULT_ATTR_TOP_ITEMS_LIMIT,
)
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData


class TestSensorEntityDescriptions:
    """Tests for sensor entity descriptions."""

    @pytest.fixture
    def data_with_stats(self) -> AdGuardHomeData:
        """Return data with stats."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            version="0.107.43",
        )
        data.stats = AdGuardHomeStats(
            dns_queries=12345,
            blocked_filtering=1234,
            replaced_safebrowsing=10,
            replaced_parental=5,
            replaced_safesearch=2,
            avg_processing_time=0.0155,  # 15.5ms in seconds (API returns seconds)
            top_queried_domains=[{"example.com": 100}],
            top_blocked_domains=[{"ads.example.com": 50}],
            top_clients=[{"192.168.1.100": 500}],
        )
        return data

    def test_dns_queries_value(self, data_with_stats: AdGuardHomeData) -> None:
        """Test DNS queries sensor value extraction."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        dns_queries_desc = next(d for d in SENSOR_TYPES if d.key == "dns_queries")
        value = dns_queries_desc.value_fn(data_with_stats)
        assert value == 12345

    def test_blocked_queries_value(self, data_with_stats: AdGuardHomeData) -> None:
        """Test blocked queries sensor value extraction."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        blocked_desc = next(d for d in SENSOR_TYPES if d.key == "blocked_queries")
        value = blocked_desc.value_fn(data_with_stats)
        assert value == 1234

    def test_blocked_percentage_value(self, data_with_stats: AdGuardHomeData) -> None:
        """Test blocked percentage calculation."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        percentage_desc = next(d for d in SENSOR_TYPES if d.key == "blocked_percentage")
        value = percentage_desc.value_fn(data_with_stats)
        # 1234 / 12345 * 100 ≈ 9.99...
        assert value is not None
        assert 9.9 < value < 10.1

    def test_blocked_percentage_zero_queries(self) -> None:
        """Test blocked percentage with zero queries."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        data = AdGuardHomeData()
        data.stats = AdGuardHomeStats(dns_queries=0, blocked_filtering=0)

        percentage_desc = next(d for d in SENSOR_TYPES if d.key == "blocked_percentage")
        value = percentage_desc.value_fn(data)
        assert value == 0

    def test_avg_processing_time_value(self, data_with_stats: AdGuardHomeData) -> None:
        """Test average processing time sensor value extraction."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        avg_time_desc = next(d for d in SENSOR_TYPES if d.key == "avg_processing_time")
        value = avg_time_desc.value_fn(data_with_stats)
        assert value == 15.5

    def test_top_blocked_domain_value(self, data_with_stats: AdGuardHomeData) -> None:
        """Test top blocked domain sensor value extraction."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        top_blocked_desc = next(
            d for d in SENSOR_TYPES if d.key == "top_blocked_domain"
        )
        value = top_blocked_desc.value_fn(data_with_stats)
        assert value == "ads.example.com"

    def test_top_blocked_domain_empty(self) -> None:
        """Test top blocked domain with no data."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        data = AdGuardHomeData()
        data.stats = AdGuardHomeStats(top_blocked_domains=[])

        top_blocked_desc = next(
            d for d in SENSOR_TYPES if d.key == "top_blocked_domain"
        )
        value = top_blocked_desc.value_fn(data)
        assert value is None

    def test_top_client_value(self, data_with_stats: AdGuardHomeData) -> None:
        """Test top client sensor value extraction."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        top_client_desc = next(d for d in SENSOR_TYPES if d.key == "top_client")
        value = top_client_desc.value_fn(data_with_stats)
        assert value == "192.168.1.100"

    def test_all_sensors_have_required_fields(self) -> None:
        """Test all sensors have required fields."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        for sensor in SENSOR_TYPES:
            assert sensor.key is not None
            assert sensor.translation_key is not None
            assert callable(sensor.value_fn)


class TestSensorValues:
    """Tests for sensor value handling edge cases."""

    def test_none_data(self) -> None:
        """Test sensor with None data."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        data = AdGuardHomeData()  # All fields are None

        for sensor in SENSOR_TYPES:
            # Should not raise an exception
            try:
                _ = sensor.value_fn(data)
                # Value can be None for missing data
            except Exception as e:
                pytest.fail(f"Sensor {sensor.key} raised exception with None data: {e}")


class TestSensorAttributeLimits:
    """Tests for sensor attribute list truncation limits."""

    @pytest.fixture
    def data_with_many_items(self) -> AdGuardHomeData:
        """Return data with many items for limit testing."""
        data = AdGuardHomeData()
        data.stats = AdGuardHomeStats(
            dns_queries=1000,
            blocked_filtering=100,
            # Create 30 items to test limit truncation
            top_blocked_domains=[{f"domain{i}.com": i} for i in range(30)],
            top_clients=[{f"192.168.1.{i}": i * 10} for i in range(30)],
        )
        # Create 30 rewrites
        data.rewrites = [
            DnsRewrite(domain=f"rewrite{i}.local", answer=f"10.0.0.{i}")
            for i in range(30)
        ]
        # Create 30 query log entries
        data.query_log = [
            {"QH": f"query{i}.com", "IP": f"192.168.1.{i}"} for i in range(30)
        ]
        return data

    def test_top_blocked_domains_respects_limit(
        self, data_with_many_items: AdGuardHomeData
    ) -> None:
        """Test top blocked domains attribute respects top_limit."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        top_blocked_desc = next(
            d for d in SENSOR_TYPES if d.key == "top_blocked_domain"
        )

        # Test with default limit
        attrs = top_blocked_desc.attributes_fn(
            data_with_many_items, DEFAULT_ATTR_TOP_ITEMS_LIMIT, DEFAULT_ATTR_LIST_LIMIT
        )
        assert len(attrs["top_blocked_domains"]) == DEFAULT_ATTR_TOP_ITEMS_LIMIT

        # Test with custom limit
        attrs = top_blocked_desc.attributes_fn(data_with_many_items, 5, 20)
        assert len(attrs["top_blocked_domains"]) == 5

    def test_top_clients_respects_limit(
        self, data_with_many_items: AdGuardHomeData
    ) -> None:
        """Test top clients attribute respects top_limit."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        top_client_desc = next(d for d in SENSOR_TYPES if d.key == "top_client")

        # Test with custom limit
        attrs = top_client_desc.attributes_fn(data_with_many_items, 7, 20)
        assert len(attrs["top_clients"]) == 7

    def test_rewrites_respects_limit(
        self, data_with_many_items: AdGuardHomeData
    ) -> None:
        """Test rewrites attribute respects list_limit."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        rewrites_desc = next(d for d in SENSOR_TYPES if d.key == "dns_rewrites_count")

        # Test with default limit
        attrs = rewrites_desc.attributes_fn(
            data_with_many_items, DEFAULT_ATTR_TOP_ITEMS_LIMIT, DEFAULT_ATTR_LIST_LIMIT
        )
        assert len(attrs["rewrites"]) == DEFAULT_ATTR_LIST_LIMIT

        # Test with custom limit
        attrs = rewrites_desc.attributes_fn(data_with_many_items, 10, 15)
        assert len(attrs["rewrites"]) == 15

    def test_recent_queries_respects_limit(
        self, data_with_many_items: AdGuardHomeData
    ) -> None:
        """Test recent queries attribute respects top_limit."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        queries_desc = next(d for d in SENSOR_TYPES if d.key == "recent_queries")

        # Test with custom limit
        attrs = queries_desc.attributes_fn(data_with_many_items, 8, 20)
        assert len(attrs["recent_queries"]) == 8

    def test_attributes_with_fewer_items_than_limit(self) -> None:
        """Test attributes when data has fewer items than limit."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        data = AdGuardHomeData()
        data.stats = AdGuardHomeStats(
            dns_queries=100,
            blocked_filtering=10,
            top_blocked_domains=[{"example.com": 5}],  # Only 1 item
        )

        top_blocked_desc = next(
            d for d in SENSOR_TYPES if d.key == "top_blocked_domain"
        )
        attrs = top_blocked_desc.attributes_fn(data, 10, 20)
        # Should return all available items (1) without error
        assert len(attrs["top_blocked_domains"]) == 1


class TestDnsConfigSensors:
    """Tests for DNS configuration sensors."""

    @pytest.fixture
    def data_with_dns_info(self) -> AdGuardHomeData:
        """Return data with DNS info."""
        from custom_components.adguard_home_extended.api.models import DnsInfo

        data = AdGuardHomeData()
        data.dns_info = DnsInfo(
            cache_enabled=True,
            cache_size=8388608,  # 8MB
            rate_limit=30,
            blocking_mode="nxdomain",
            upstream_dns=["https://dns.cloudflare.com/dns-query", "8.8.8.8"],
            bootstrap_dns=["1.1.1.1", "8.8.4.4"],
            edns_cs_enabled=True,
            dnssec_enabled=True,
        )
        return data

    def test_upstream_dns_servers_count(
        self, data_with_dns_info: AdGuardHomeData
    ) -> None:
        """Test upstream DNS servers count."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        desc = next(d for d in SENSOR_TYPES if d.key == "upstream_dns_servers")
        value = desc.value_fn(data_with_dns_info)
        assert value == 2

    def test_upstream_dns_servers_attributes(
        self, data_with_dns_info: AdGuardHomeData
    ) -> None:
        """Test upstream DNS servers attributes."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        desc = next(d for d in SENSOR_TYPES if d.key == "upstream_dns_servers")
        attrs = desc.attributes_fn(data_with_dns_info, 10, 20)
        assert "upstream_servers" in attrs
        assert len(attrs["upstream_servers"]) == 2
        assert "https://dns.cloudflare.com/dns-query" in attrs["upstream_servers"]

    def test_bootstrap_dns_servers_count(
        self, data_with_dns_info: AdGuardHomeData
    ) -> None:
        """Test bootstrap DNS servers count."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        desc = next(d for d in SENSOR_TYPES if d.key == "bootstrap_dns_servers")
        value = desc.value_fn(data_with_dns_info)
        assert value == 2

    def test_bootstrap_dns_servers_attributes(
        self, data_with_dns_info: AdGuardHomeData
    ) -> None:
        """Test bootstrap DNS servers attributes."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        desc = next(d for d in SENSOR_TYPES if d.key == "bootstrap_dns_servers")
        attrs = desc.attributes_fn(data_with_dns_info, 10, 20)
        assert "bootstrap_servers" in attrs
        assert "1.1.1.1" in attrs["bootstrap_servers"]

    def test_dns_cache_size_value(self, data_with_dns_info: AdGuardHomeData) -> None:
        """Test DNS cache size sensor value."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        desc = next(d for d in SENSOR_TYPES if d.key == "dns_cache_size")
        value = desc.value_fn(data_with_dns_info)
        assert value == 8388608

    def test_dns_rate_limit_value(self, data_with_dns_info: AdGuardHomeData) -> None:
        """Test DNS rate limit sensor value."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        desc = next(d for d in SENSOR_TYPES if d.key == "dns_rate_limit")
        value = desc.value_fn(data_with_dns_info)
        assert value == 30

    def test_dns_blocking_mode_value(self, data_with_dns_info: AdGuardHomeData) -> None:
        """Test DNS blocking mode sensor value."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        desc = next(d for d in SENSOR_TYPES if d.key == "dns_blocking_mode")
        value = desc.value_fn(data_with_dns_info)
        assert value == "nxdomain"

    def test_dns_sensors_none_dns_info(self) -> None:
        """Test DNS sensors with None dns_info."""
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        data = AdGuardHomeData()  # dns_info is None

        upstream_desc = next(d for d in SENSOR_TYPES if d.key == "upstream_dns_servers")
        assert upstream_desc.value_fn(data) == 0

        bootstrap_desc = next(
            d for d in SENSOR_TYPES if d.key == "bootstrap_dns_servers"
        )
        assert bootstrap_desc.value_fn(data) == 0

        cache_desc = next(d for d in SENSOR_TYPES if d.key == "dns_cache_size")
        assert cache_desc.value_fn(data) is None

        rate_desc = next(d for d in SENSOR_TYPES if d.key == "dns_rate_limit")
        assert rate_desc.value_fn(data) is None

        mode_desc = next(d for d in SENSOR_TYPES if d.key == "dns_blocking_mode")
        assert mode_desc.value_fn(data) is None

    def test_upstream_servers_respects_limit(self) -> None:
        """Test upstream servers attribute respects list_limit."""
        from custom_components.adguard_home_extended.api.models import DnsInfo
        from custom_components.adguard_home_extended.sensor import SENSOR_TYPES

        data = AdGuardHomeData()
        data.dns_info = DnsInfo(upstream_dns=[f"dns{i}.example.com" for i in range(30)])

        desc = next(d for d in SENSOR_TYPES if d.key == "upstream_dns_servers")
        attrs = desc.attributes_fn(data, 10, 15)
        assert len(attrs["upstream_servers"]) == 15
