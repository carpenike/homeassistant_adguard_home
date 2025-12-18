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
    DnsInfo,
    DnsRewrite,
    FilteringStatus,
    SafeSearchSettings,
)


class TestSafeSearchSettings:
    """Tests for SafeSearchSettings model."""

    def test_from_dict(self) -> None:
        """Test creating settings from dict."""
        data = {
            "enabled": True,
            "bing": True,
            "duckduckgo": False,
            "ecosia": True,
            "google": True,
            "pixabay": True,
            "yandex": False,
            "youtube": True,
        }
        settings = SafeSearchSettings.from_dict(data)

        assert settings.enabled is True
        assert settings.bing is True
        assert settings.duckduckgo is False
        assert settings.ecosia is True
        assert settings.google is True
        assert settings.yandex is False

    def test_from_dict_defaults(self) -> None:
        """Test creating settings from empty dict uses defaults."""
        settings = SafeSearchSettings.from_dict({})

        assert settings.enabled is False
        assert settings.bing is True  # Default to True for all engines
        assert settings.ecosia is True
        assert settings.google is True
        assert settings.youtube is True

    def test_to_dict(self) -> None:
        """Test converting settings to dict."""
        settings = SafeSearchSettings(
            enabled=True,
            bing=False,
            duckduckgo=True,
            ecosia=False,
            google=True,
            pixabay=False,
            yandex=True,
            youtube=False,
        )
        result = settings.to_dict()

        assert result["enabled"] is True
        assert result["bing"] is False
        assert result["duckduckgo"] is True
        assert result["ecosia"] is False
        assert result["youtube"] is False


class TestDnsInfo:
    """Tests for DnsInfo model."""

    def test_from_dict(self) -> None:
        """Test creating DNS info from dict."""
        data = {
            "cache_enabled": True,
            "cache_size": 8388608,
            "cache_ttl_min": 60,
            "cache_ttl_max": 3600,
            "upstream_dns": ["https://dns.cloudflare.com/dns-query"],
            "bootstrap_dns": ["1.1.1.1"],
            "rate_limit": 50,
            "blocking_mode": "nxdomain",
            "edns_cs_enabled": True,
            "dnssec_enabled": True,
        }
        dns_info = DnsInfo.from_dict(data)

        assert dns_info.cache_enabled is True
        assert dns_info.cache_size == 8388608
        assert dns_info.cache_ttl_min == 60
        assert dns_info.cache_ttl_max == 3600
        assert dns_info.upstream_dns == ["https://dns.cloudflare.com/dns-query"]
        assert dns_info.bootstrap_dns == ["1.1.1.1"]
        assert dns_info.rate_limit == 50
        assert dns_info.blocking_mode == "nxdomain"
        assert dns_info.edns_cs_enabled is True
        assert dns_info.dnssec_enabled is True

    def test_from_dict_defaults(self) -> None:
        """Test creating DNS info from empty dict uses defaults."""
        dns_info = DnsInfo.from_dict({})

        # cache_enabled defaults to True when cache_size defaults to 4194304 > 0
        assert dns_info.cache_enabled is True
        assert dns_info.cache_size == 4194304
        assert dns_info.cache_ttl_min == 0
        assert dns_info.cache_ttl_max == 0
        assert dns_info.upstream_dns == []
        assert dns_info.rate_limit == 20
        assert dns_info.blocking_mode == "default"
        assert dns_info.edns_cs_enabled is False
        assert dns_info.dnssec_enabled is False

    def test_from_dict_cache_enabled_inferred_from_size(self) -> None:
        """Test cache_enabled is inferred from cache_size when field missing (pre-v0.107.65)."""
        # When cache_size > 0, cache is enabled
        data_with_cache = {"cache_size": 100000000}
        dns_info = DnsInfo.from_dict(data_with_cache)
        assert dns_info.cache_enabled is True

        # When cache_size = 0, cache is disabled (old method of disabling)
        data_without_cache = {"cache_size": 0}
        dns_info = DnsInfo.from_dict(data_without_cache)
        assert dns_info.cache_enabled is False

    def test_from_dict_cache_enabled_explicit(self) -> None:
        """Test explicit cache_enabled takes precedence (v0.107.65+)."""
        # Explicit cache_enabled=False with non-zero cache_size
        data = {"cache_enabled": False, "cache_size": 100000000}
        dns_info = DnsInfo.from_dict(data)
        assert dns_info.cache_enabled is False
        assert dns_info.cache_size == 100000000


class TestAdGuardHomeStatus:
    """Tests for AdGuardHomeStatus model."""

    def test_from_dict(self) -> None:
        """Test creating status from dict with all OpenAPI schema fields."""
        data = {
            "protection_enabled": True,
            "running": True,
            "dns_addresses": ["192.168.1.1", "192.168.1.2"],
            "dns_port": 53,
            "http_port": 3000,
            "version": "0.107.43",
            "language": "en",
            "protection_disabled_until": "2024-12-31T23:59:59Z",
            "protection_disabled_duration": 3600000,
            "dhcp_available": True,
            "start_time": 1700000000000,
        }
        status = AdGuardHomeStatus.from_dict(data)

        assert status.protection_enabled is True
        assert status.running is True
        assert status.dns_addresses == ["192.168.1.1", "192.168.1.2"]
        assert status.dns_port == 53
        assert status.http_port == 3000
        assert status.version == "0.107.43"
        assert status.language == "en"
        assert status.protection_disabled_until == "2024-12-31T23:59:59Z"
        assert status.protection_disabled_duration == 3600000
        assert status.dhcp_available is True
        assert status.start_time == 1700000000000

    def test_from_dict_defaults(self) -> None:
        """Test creating status from dict with defaults."""
        status = AdGuardHomeStatus.from_dict({})

        assert status.protection_enabled is False
        assert status.running is False
        assert status.dns_addresses == []
        assert status.dns_port == 53
        assert status.http_port == 3000
        assert status.version == ""
        assert status.language == "en"
        assert status.protection_disabled_until is None
        assert status.protection_disabled_duration == 0
        assert status.dhcp_available is False
        assert status.start_time == 0.0


class TestAdGuardHomeStats:
    """Tests for AdGuardHomeStats model."""

    def test_from_dict(self) -> None:
        """Test creating stats from dict with all OpenAPI schema fields."""
        data = {
            "time_units": "hours",
            "num_dns_queries": 12345,
            "num_blocked_filtering": 1234,
            "num_replaced_safebrowsing": 10,
            "num_replaced_parental": 5,
            "num_replaced_safesearch": 2,
            "avg_processing_time": 15.5,
            "top_queried_domains": [{"example.com": 100}],
            "top_blocked_domains": [{"ads.example.com": 50}],
            "top_clients": [{"192.168.1.100": 500}],
            # v0.107.36+ fields
            "top_upstreams_responses": [{"1.1.1.1": 1000}],
            "top_upstreams_avg_time": [{"1.1.1.1": 0.025}],
            # Time-series arrays
            "dns_queries": [100, 150, 200],
            "blocked_filtering": [10, 15, 20],
            "replaced_safebrowsing": [1, 2, 1],
            "replaced_parental": [0, 1, 0],
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
        # v0.107.36+ fields
        assert stats.time_units == "hours"
        assert len(stats.top_upstreams_responses) == 1
        assert stats.top_upstreams_responses[0] == {"1.1.1.1": 1000}
        assert len(stats.top_upstreams_avg_time) == 1
        assert stats.top_upstreams_avg_time[0] == {"1.1.1.1": 0.025}
        # Time-series arrays
        assert stats.dns_queries_series == [100, 150, 200]
        assert stats.blocked_filtering_series == [10, 15, 20]
        assert stats.replaced_safebrowsing_series == [1, 2, 1]
        assert stats.replaced_parental_series == [0, 1, 0]

    def test_from_dict_defaults(self) -> None:
        """Test creating stats from dict with defaults."""
        stats = AdGuardHomeStats.from_dict({})

        assert stats.dns_queries == 0
        assert stats.blocked_filtering == 0
        assert stats.avg_processing_time == 0.0
        assert stats.top_queried_domains == []
        assert stats.time_units == "hours"
        assert stats.top_upstreams_responses == []
        assert stats.top_upstreams_avg_time == []
        assert stats.dns_queries_series == []
        assert stats.blocked_filtering_series == []


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

    def test_from_dict_with_null_filters(self) -> None:
        """Test creating filtering status when API returns null for filters."""
        # AdGuard Home API can return null for filters/whitelist_filters arrays
        data = {
            "enabled": True,
            "interval": 12,
            "filters": None,
            "whitelist_filters": None,
            "user_rules": None,
        }
        status = FilteringStatus.from_dict(data)

        assert status.enabled is True
        assert status.interval == 12
        assert status.filters == []
        assert status.whitelist_filters == []
        assert status.user_rules == []


class TestClientConfig:
    """Tests for ClientConfig model."""

    def test_from_dict(self) -> None:
        """Test creating client config from dict."""
        data = {
            "name": "Kids Tablet",
            "ids": ["192.168.1.100", "AA:BB:CC:DD:EE:FF"],
            "uid": "client-abc123",
            "use_global_settings": False,
            "filtering_enabled": True,
            "parental_enabled": True,
            "safebrowsing_enabled": True,
            "safesearch_enabled": True,
            "safe_search": {
                "enabled": True,
                "bing": True,
                "duckduckgo": True,
                "google": True,
                "youtube": False,
            },
            "use_global_blocked_services": False,
            "blocked_services": ["tiktok", "youtube"],
            "blocked_services_schedule": {
                "time_zone": "America/New_York",
                "mon": {"start": 0, "end": 86400000},
            },
            "upstreams": ["https://family.cloudflare-dns.com/dns-query"],
            "tags": ["device:tablet", "user:child"],
            "upstreams_cache_enabled": False,
            "upstreams_cache_size": 8192,
            "ignore_querylog": True,
            "ignore_statistics": True,
        }
        client = ClientConfig.from_dict(data)

        assert client.name == "Kids Tablet"
        assert len(client.ids) == 2
        assert client.uid == "client-abc123"
        assert client.use_global_settings is False
        assert client.filtering_enabled is True
        assert client.parental_enabled is True
        assert client.safebrowsing_enabled is True
        assert client.safesearch_enabled is True
        # Test safe_search parsing
        assert client.safe_search is not None
        assert client.safe_search.enabled is True
        assert client.safe_search.youtube is False
        assert client.use_global_blocked_services is False
        assert client.blocked_services == ["tiktok", "youtube"]
        # Test blocked_services_schedule
        assert client.blocked_services_schedule is not None
        assert client.blocked_services_schedule["time_zone"] == "America/New_York"
        # Test upstreams
        assert client.upstreams == ["https://family.cloudflare-dns.com/dns-query"]
        assert len(client.tags) == 2
        assert client.upstreams_cache_enabled is False
        assert client.upstreams_cache_size == 8192
        assert client.ignore_querylog is True
        assert client.ignore_statistics is True

    def test_from_dict_defaults(self) -> None:
        """Test creating client config from dict with defaults."""
        client = ClientConfig.from_dict({"name": "Test"})

        assert client.name == "Test"
        assert client.ids == []
        assert client.uid == ""
        assert client.use_global_settings is True
        assert client.filtering_enabled is True
        assert client.parental_enabled is False
        assert client.use_global_blocked_services is True
        assert client.blocked_services == []
        assert client.blocked_services_schedule is None
        assert client.upstreams == []
        assert client.safe_search is None
        assert client.upstreams_cache_enabled is True
        assert client.upstreams_cache_size == 0
        assert client.ignore_querylog is False
        assert client.ignore_statistics is False


class TestBlockedService:
    """Tests for BlockedService model."""

    def test_from_dict(self) -> None:
        """Test creating blocked service from dict with all schema fields."""
        data = {
            "id": "facebook",
            "name": "Facebook",
            "icon_svg": "<svg>...</svg>",
            "rules": ["||facebook.com^", "||fbcdn.net^"],
            "group_id": "social",
        }
        service = BlockedService.from_dict(data)

        assert service.id == "facebook"
        assert service.name == "Facebook"
        assert service.icon_svg == "<svg>...</svg>"
        assert service.rules == ["||facebook.com^", "||fbcdn.net^"]
        assert service.group_id == "social"

    def test_from_dict_defaults(self) -> None:
        """Test creating blocked service from dict with defaults."""
        service = BlockedService.from_dict({})

        assert service.id == ""
        assert service.name == ""
        assert service.icon_svg == ""
        assert service.rules == []
        assert service.group_id == ""

    def test_from_dict_minimal(self) -> None:
        """Test creating blocked service with only required fields."""
        data = {
            "id": "youtube",
            "name": "YouTube",
            "icon_svg": "<svg></svg>",
            "rules": ["||youtube.com^"],
        }
        service = BlockedService.from_dict(data)

        assert service.id == "youtube"
        assert service.name == "YouTube"
        assert service.rules == ["||youtube.com^"]
        assert service.group_id == ""  # Optional field defaults to empty


class TestDnsRewrite:
    """Tests for DnsRewrite model."""

    def test_from_dict(self) -> None:
        """Test creating DNS rewrite from dict with all OpenAPI schema fields."""
        data = {
            "domain": "local.example.com",
            "answer": "192.168.1.50",
            "enabled": True,
        }
        rewrite = DnsRewrite.from_dict(data)

        assert rewrite.domain == "local.example.com"
        assert rewrite.answer == "192.168.1.50"
        assert rewrite.enabled is True

    def test_from_dict_defaults(self) -> None:
        """Test creating DNS rewrite with defaults (enabled defaults to True)."""
        data = {
            "domain": "test.example.com",
            "answer": "10.0.0.1",
        }
        rewrite = DnsRewrite.from_dict(data)

        assert rewrite.domain == "test.example.com"
        assert rewrite.answer == "10.0.0.1"
        assert rewrite.enabled is True  # Default for backwards compatibility

    def test_from_dict_disabled(self) -> None:
        """Test creating disabled DNS rewrite (v0.107.68+)."""
        data = {
            "domain": "disabled.example.com",
            "answer": "0.0.0.0",
            "enabled": False,
        }
        rewrite = DnsRewrite.from_dict(data)

        assert rewrite.domain == "disabled.example.com"
        assert rewrite.enabled is False

    def test_to_dict(self) -> None:
        """Test converting DNS rewrite to dict for API request."""
        rewrite = DnsRewrite(
            domain="api.example.com",
            answer="192.168.1.100",
            enabled=True,
        )
        result = rewrite.to_dict()

        assert result["domain"] == "api.example.com"
        assert result["answer"] == "192.168.1.100"
        assert result["enabled"] is True


class TestDhcpStatus:
    """Tests for DhcpStatus model."""

    def test_from_dict(self) -> None:
        """Test creating DHCP status from dict.

        Per OpenAPI DhcpStatus schema, DhcpLease requires: mac, ip, hostname, expires.
        DhcpStaticLease requires: mac, ip, hostname.
        """
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
                    "expires": "2024-12-31T23:59:59Z",
                }
            ],
        }
        status = DhcpStatus.from_dict(data)

        assert status.enabled is True
        assert len(status.leases) == 1
        assert status.leases[0].expires == "2024-12-31T23:59:59Z"

    def test_from_dict_defaults(self) -> None:
        """Test creating DHCP status from dict with defaults."""
        status = DhcpStatus.from_dict({})

        assert status.enabled is False
        assert status.leases == []
        assert status.v4 is None
        assert status.v6 is None

    def test_from_dict_with_v4_config(self) -> None:
        """Test creating DHCP status with v4 configuration."""
        from custom_components.adguard_home_extended.api.models import DhcpV4Config

        data = {
            "enabled": True,
            "interface_name": "eth0",
            "v4": {
                "gateway_ip": "192.168.1.1",
                "subnet_mask": "255.255.255.0",
                "range_start": "192.168.1.100",
                "range_end": "192.168.1.200",
                "lease_duration": 86400,
            },
            "leases": [],
            "static_leases": [],
        }
        status = DhcpStatus.from_dict(data)

        assert status.enabled is True
        assert status.interface_name == "eth0"
        assert status.v4 is not None
        assert isinstance(status.v4, DhcpV4Config)
        assert status.v4.gateway_ip == "192.168.1.1"
        assert status.v4.subnet_mask == "255.255.255.0"
        assert status.v4.range_start == "192.168.1.100"
        assert status.v4.range_end == "192.168.1.200"
        assert status.v4.lease_duration == 86400

    def test_from_dict_with_v6_config(self) -> None:
        """Test creating DHCP status with v6 configuration."""
        from custom_components.adguard_home_extended.api.models import DhcpV6Config

        data = {
            "enabled": True,
            "v6": {
                "range_start": "2001:db8::100",
                "lease_duration": 43200,
            },
            "leases": [],
            "static_leases": [],
        }
        status = DhcpStatus.from_dict(data)

        assert status.v6 is not None
        assert isinstance(status.v6, DhcpV6Config)
        assert status.v6.range_start == "2001:db8::100"
        assert status.v6.lease_duration == 43200
