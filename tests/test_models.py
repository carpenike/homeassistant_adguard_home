"""Tests for the AdGuard Home Extended data models."""
from __future__ import annotations

from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeClient as ClientConfig,
)
from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
    BlockedService,
    DhcpStatus,
    DnsRewrite,
    FilteringStatus,
)


class TestAdGuardHomeStatus:
    """Tests for AdGuardHomeStatus model."""

    def test_from_dict(self) -> None:
        """Test creating status from dict."""
        data = {
            "protection_enabled": True,
            "running": True,
            "safebrowsing_enabled": True,
            "parental_enabled": True,
            "safesearch": {"enabled": True, "bing": True, "duckduckgo": True},
            "dns_addresses": ["192.168.1.1", "192.168.1.2"],
            "dns_port": 53,
            "http_port": 3000,
            "version": "0.107.43",
        }
        status = AdGuardHomeStatus.from_dict(data)

        assert status.protection_enabled is True
        assert status.running is True
        assert status.safebrowsing_enabled is True
        assert status.parental_enabled is True
        assert status.safesearch_enabled is True
        assert status.dns_addresses == ["192.168.1.1", "192.168.1.2"]
        assert status.dns_port == 53
        assert status.http_port == 3000
        assert status.version == "0.107.43"

    def test_from_dict_defaults(self) -> None:
        """Test creating status from dict with defaults."""
        status = AdGuardHomeStatus.from_dict({})

        assert status.protection_enabled is False
        assert status.running is False
        assert status.safebrowsing_enabled is False
        assert status.parental_enabled is False
        assert status.safesearch_enabled is False
        assert status.dns_addresses == []
        assert status.dns_port == 53
        assert status.http_port == 3000
        assert status.version == ""

    def test_from_dict_safesearch_disabled(self) -> None:
        """Test parsing safesearch when disabled."""
        data = {
            "protection_enabled": True,
            "running": True,
            "safesearch": {"enabled": False},
        }
        status = AdGuardHomeStatus.from_dict(data)

        assert status.safesearch_enabled is False

    def test_from_dict_safesearch_legacy_format(self) -> None:
        """Test parsing safesearch when it's a boolean (legacy format)."""
        data = {
            "protection_enabled": True,
            "running": True,
            "safesearch": True,
        }
        status = AdGuardHomeStatus.from_dict(data)

        assert status.safesearch_enabled is True


class TestAdGuardHomeStats:
    """Tests for AdGuardHomeStats model."""

    def test_from_dict(self) -> None:
        """Test creating stats from dict."""
        data = {
            "num_dns_queries": 12345,
            "num_blocked_filtering": 1234,
            "num_replaced_safebrowsing": 10,
            "num_replaced_parental": 5,
            "num_replaced_safesearch": 2,
            "avg_processing_time": 15.5,
            "top_queried_domains": [{"example.com": 100}],
            "top_blocked_domains": [{"ads.example.com": 50}],
            "top_clients": [{"192.168.1.100": 500}],
        }
        stats = AdGuardHomeStats.from_dict(data)

        assert stats.dns_queries == 12345
        assert stats.blocked_filtering == 1234
        assert stats.replaced_safebrowsing == 10
        assert stats.replaced_parental == 5
        assert stats.replaced_safesearch == 2
        assert stats.avg_processing_time == 15.5
        assert len(stats.top_queried_domains) == 1
        assert len(stats.top_blocked_domains) == 1
        assert len(stats.top_clients) == 1

    def test_from_dict_defaults(self) -> None:
        """Test creating stats from dict with defaults."""
        stats = AdGuardHomeStats.from_dict({})

        assert stats.dns_queries == 0
        assert stats.blocked_filtering == 0
        assert stats.avg_processing_time == 0.0
        assert stats.top_queried_domains == []


class TestFilteringStatus:
    """Tests for FilteringStatus model."""

    def test_from_dict(self) -> None:
        """Test creating filtering status from dict."""
        data = {
            "enabled": True,
            "interval": 12,
            "filters": [{"id": 1, "name": "Test Filter", "enabled": True}],
            "whitelist_filters": [],
            "user_rules": ["||example.com^"],
        }
        status = FilteringStatus.from_dict(data)

        assert status.enabled is True
        assert status.interval == 12
        assert len(status.filters) == 1
        assert status.filters[0]["name"] == "Test Filter"
        assert len(status.user_rules) == 1

    def test_from_dict_defaults(self) -> None:
        """Test creating filtering status from dict with defaults."""
        status = FilteringStatus.from_dict({})

        assert status.enabled is False
        assert status.interval == 24
        assert status.filters == []


class TestClientConfig:
    """Tests for ClientConfig model."""

    def test_from_dict(self) -> None:
        """Test creating client config from dict."""
        data = {
            "name": "Kids Tablet",
            "ids": ["192.168.1.100", "AA:BB:CC:DD:EE:FF"],
            "use_global_settings": False,
            "filtering_enabled": True,
            "parental_enabled": True,
            "safebrowsing_enabled": True,
            "safesearch_enabled": True,
            "use_global_blocked_services": False,
            "blocked_services": ["tiktok", "youtube"],
            "tags": ["device:tablet", "user:child"],
        }
        client = ClientConfig.from_dict(data)

        assert client.name == "Kids Tablet"
        assert len(client.ids) == 2
        assert client.use_global_settings is False
        assert client.filtering_enabled is True
        assert client.parental_enabled is True
        assert client.safebrowsing_enabled is True
        assert client.safesearch_enabled is True
        assert client.use_global_blocked_services is False
        assert client.blocked_services == ["tiktok", "youtube"]
        assert len(client.tags) == 2

    def test_from_dict_defaults(self) -> None:
        """Test creating client config from dict with defaults."""
        client = ClientConfig.from_dict({"name": "Test"})

        assert client.name == "Test"
        assert client.ids == []
        assert client.use_global_settings is True
        assert client.filtering_enabled is True
        assert client.parental_enabled is False
        assert client.use_global_blocked_services is True
        assert client.blocked_services == []


class TestBlockedService:
    """Tests for BlockedService model."""

    def test_from_dict(self) -> None:
        """Test creating blocked service from dict."""
        data = {
            "id": "facebook",
            "name": "Facebook",
            "icon_svg": "<svg>...</svg>",
        }
        service = BlockedService.from_dict(data)

        assert service.id == "facebook"
        assert service.name == "Facebook"
        assert service.icon_svg == "<svg>...</svg>"

    def test_from_dict_defaults(self) -> None:
        """Test creating blocked service from dict with defaults."""
        service = BlockedService.from_dict({})

        assert service.id == ""
        assert service.name == ""
        assert service.icon_svg == ""


class TestDnsRewrite:
    """Tests for DnsRewrite model."""

    def test_from_dict(self) -> None:
        """Test creating DNS rewrite from dict."""
        data = {
            "domain": "local.example.com",
            "answer": "192.168.1.50",
        }
        rewrite = DnsRewrite.from_dict(data)

        assert rewrite.domain == "local.example.com"
        assert rewrite.answer == "192.168.1.50"


class TestDhcpStatus:
    """Tests for DhcpStatus model."""

    def test_from_dict(self) -> None:
        """Test creating DHCP status from dict."""
        data = {
            "enabled": True,
            "static_leases": [
                {
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "ip": "192.168.1.100",
                    "hostname": "device1",
                }
            ],
            "leases": [
                {
                    "mac": "11:22:33:44:55:66",
                    "ip": "192.168.1.101",
                    "hostname": "device2",
                }
            ],
        }
        status = DhcpStatus.from_dict(data)

        assert status.enabled is True
        assert len(status.leases) == 1

    def test_from_dict_defaults(self) -> None:
        """Test creating DHCP status from dict with defaults."""
        status = DhcpStatus.from_dict({})

        assert status.enabled is False
        assert status.leases == []
