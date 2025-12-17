"""Tests for DNS rewrite and query log features."""
from __future__ import annotations

from custom_components.adguard_home_extended.api.models import DnsRewrite
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
from custom_components.adguard_home_extended.sensor import SENSOR_TYPES


class TestDnsRewriteSensor:
    """Test DNS rewrites sensor."""

    def test_dns_rewrites_count_sensor_exists(self) -> None:
        """Test that DNS rewrites count sensor is defined."""
        sensor_keys = [s.key for s in SENSOR_TYPES]
        assert "dns_rewrites_count" in sensor_keys

    def test_dns_rewrites_count_value(self) -> None:
        """Test DNS rewrites count value function."""
        data = AdGuardHomeData()
        data.rewrites = [
            DnsRewrite(domain="ads.example.com", answer="0.0.0.0"),
            DnsRewrite(domain="tracker.example.com", answer="0.0.0.0"),
            DnsRewrite(domain="custom.local", answer="192.168.1.100"),
        ]

        sensor = next(s for s in SENSOR_TYPES if s.key == "dns_rewrites_count")
        assert sensor.value_fn(data) == 3

    def test_dns_rewrites_count_empty(self) -> None:
        """Test DNS rewrites count with no rewrites."""
        data = AdGuardHomeData()

        sensor = next(s for s in SENSOR_TYPES if s.key == "dns_rewrites_count")
        assert sensor.value_fn(data) == 0

    def test_dns_rewrites_attributes(self) -> None:
        """Test DNS rewrites attributes function."""
        data = AdGuardHomeData()
        data.rewrites = [
            DnsRewrite(domain="ads.example.com", answer="0.0.0.0"),
            DnsRewrite(domain="tracker.example.com", answer="127.0.0.1"),
        ]

        sensor = next(s for s in SENSOR_TYPES if s.key == "dns_rewrites_count")
        attrs = sensor.attributes_fn(data)

        assert "rewrites" in attrs
        assert len(attrs["rewrites"]) == 2
        assert attrs["rewrites"][0]["domain"] == "ads.example.com"
        assert attrs["rewrites"][0]["answer"] == "0.0.0.0"


class TestDhcpSensors:
    """Test DHCP sensors."""

    def test_dhcp_leases_sensor_exists(self) -> None:
        """Test that DHCP leases sensor is defined."""
        sensor_keys = [s.key for s in SENSOR_TYPES]
        assert "dhcp_leases_count" in sensor_keys

    def test_dhcp_static_leases_sensor_exists(self) -> None:
        """Test that DHCP static leases sensor is defined."""
        sensor_keys = [s.key for s in SENSOR_TYPES]
        assert "dhcp_static_leases_count" in sensor_keys

    def test_dhcp_leases_count(self) -> None:
        """Test DHCP leases count."""
        from custom_components.adguard_home_extended.api.models import (
            DhcpLease,
            DhcpStatus,
        )

        data = AdGuardHomeData()
        data.dhcp = DhcpStatus(
            enabled=True,
            interface_name="eth0",
            leases=[
                DhcpLease(
                    mac="aa:bb:cc:dd:ee:ff",
                    ip="192.168.1.10",
                    hostname="device1",
                    expires="2024-01-01",
                ),
                DhcpLease(
                    mac="11:22:33:44:55:66",
                    ip="192.168.1.11",
                    hostname="device2",
                    expires="2024-01-02",
                ),
            ],
            static_leases=[],
        )

        sensor = next(s for s in SENSOR_TYPES if s.key == "dhcp_leases_count")
        assert sensor.value_fn(data) == 2

    def test_dhcp_static_leases_count(self) -> None:
        """Test DHCP static leases count."""
        from custom_components.adguard_home_extended.api.models import (
            DhcpLease,
            DhcpStatus,
        )

        data = AdGuardHomeData()
        data.dhcp = DhcpStatus(
            enabled=True,
            interface_name="eth0",
            leases=[],
            static_leases=[
                DhcpLease(
                    mac="aa:bb:cc:dd:ee:ff",
                    ip="192.168.1.50",
                    hostname="server",
                    expires="",
                ),
            ],
        )

        sensor = next(s for s in SENSOR_TYPES if s.key == "dhcp_static_leases_count")
        assert sensor.value_fn(data) == 1

    def test_dhcp_sensors_none_data(self) -> None:
        """Test DHCP sensors with no DHCP data."""
        data = AdGuardHomeData()

        leases_sensor = next(s for s in SENSOR_TYPES if s.key == "dhcp_leases_count")
        static_sensor = next(
            s for s in SENSOR_TYPES if s.key == "dhcp_static_leases_count"
        )

        assert leases_sensor.value_fn(data) == 0
        assert static_sensor.value_fn(data) == 0


class TestQueryLogSensor:
    """Test query log sensor."""

    def test_recent_queries_sensor_exists(self) -> None:
        """Test that recent queries sensor is defined."""
        sensor_keys = [s.key for s in SENSOR_TYPES]
        assert "recent_queries" in sensor_keys

    def test_recent_queries_count(self) -> None:
        """Test recent queries count."""
        data = AdGuardHomeData()
        data.query_log = [
            {
                "question": {"name": "example.com"},
                "client": "192.168.1.10",
                "reason": "",
            },
            {
                "question": {"name": "google.com"},
                "client": "192.168.1.11",
                "reason": "",
            },
            {
                "question": {"name": "blocked.com"},
                "client": "192.168.1.10",
                "reason": "FilteredBlackList",
            },
        ]

        sensor = next(s for s in SENSOR_TYPES if s.key == "recent_queries")
        assert sensor.value_fn(data) == 3

    def test_recent_queries_empty(self) -> None:
        """Test recent queries with empty log."""
        data = AdGuardHomeData()

        sensor = next(s for s in SENSOR_TYPES if s.key == "recent_queries")
        assert sensor.value_fn(data) == 0

    def test_recent_queries_attributes(self) -> None:
        """Test recent queries attributes with new API format."""
        data = AdGuardHomeData()
        data.query_log = [
            {
                "question": {"name": "example.com"},
                "client": "192.168.1.10",
                "reason": "",
                "answer": [{"value": "93.184.216.34"}],
                "time": "2024-01-01T12:00:00Z",
            },
        ]

        sensor = next(s for s in SENSOR_TYPES if s.key == "recent_queries")
        attrs = sensor.attributes_fn(data)

        assert "recent_queries" in attrs
        assert len(attrs["recent_queries"]) == 1
        assert attrs["recent_queries"][0]["domain"] == "example.com"
        assert attrs["recent_queries"][0]["client"] == "192.168.1.10"
        assert attrs["recent_queries"][0]["time"] == "2024-01-01T12:00:00Z"

    def test_recent_queries_attributes_legacy_format(self) -> None:
        """Test recent queries attributes with legacy API format."""
        data = AdGuardHomeData()
        data.query_log = [
            {
                "QH": "example.com",
                "IP": "192.168.1.10",
                "Reason": "",
                "Answer": "93.184.216.34",
            },
        ]

        sensor = next(s for s in SENSOR_TYPES if s.key == "recent_queries")
        attrs = sensor.attributes_fn(data)

        assert "recent_queries" in attrs
        assert len(attrs["recent_queries"]) == 1
        assert attrs["recent_queries"][0]["domain"] == "example.com"
        assert attrs["recent_queries"][0]["client"] == "192.168.1.10"


class TestDnsRewriteModel:
    """Test DNS rewrite model."""

    def test_dns_rewrite_from_dict(self) -> None:
        """Test DnsRewrite creation from dict."""
        data = {
            "domain": "ads.example.com",
            "answer": "0.0.0.0",
        }
        rewrite = DnsRewrite.from_dict(data)

        assert rewrite.domain == "ads.example.com"
        assert rewrite.answer == "0.0.0.0"

    def test_dns_rewrite_defaults(self) -> None:
        """Test DnsRewrite with missing fields."""
        rewrite = DnsRewrite.from_dict({})

        assert rewrite.domain == ""
        assert rewrite.answer == ""
