"""Data models for AdGuard Home API responses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SafeSearchSettings:
    """AdGuard Home SafeSearch settings with per-engine control."""

    enabled: bool = False
    bing: bool = True
    duckduckgo: bool = True
    google: bool = True
    pixabay: bool = True
    yandex: bool = True
    youtube: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SafeSearchSettings:
        """Create instance from API response dict."""
        return cls(
            enabled=data.get("enabled", False),
            bing=data.get("bing", True),
            duckduckgo=data.get("duckduckgo", True),
            google=data.get("google", True),
            pixabay=data.get("pixabay", True),
            yandex=data.get("yandex", True),
            youtube=data.get("youtube", True),
        )

    def to_dict(self) -> dict[str, bool]:
        """Convert to dict for API request."""
        return {
            "enabled": self.enabled,
            "bing": self.bing,
            "duckduckgo": self.duckduckgo,
            "google": self.google,
            "pixabay": self.pixabay,
            "yandex": self.yandex,
            "youtube": self.youtube,
        }


@dataclass
class AdGuardHomeStatus:
    """AdGuard Home server status."""

    protection_enabled: bool
    running: bool
    safebrowsing_enabled: bool = False
    parental_enabled: bool = False
    safesearch_enabled: bool = False
    dns_addresses: list[str] = field(default_factory=list)
    dns_port: int = 53
    http_port: int = 3000
    version: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdGuardHomeStatus:
        """Create instance from API response dict.

        Note: safesearch in the API response is an object like:
        {"enabled": true, "bing": true, "duckduckgo": true, ...}
        We extract just the 'enabled' field.
        """
        # Handle safesearch which is a nested object in the API response
        safesearch_data = data.get("safesearch", {})
        safesearch_enabled = (
            safesearch_data.get("enabled", False)
            if isinstance(safesearch_data, dict)
            else bool(safesearch_data)
        )

        return cls(
            protection_enabled=data.get("protection_enabled", False),
            running=data.get("running", False),
            safebrowsing_enabled=data.get("safebrowsing_enabled", False),
            parental_enabled=data.get("parental_enabled", False),
            safesearch_enabled=safesearch_enabled,
            dns_addresses=data.get("dns_addresses", []),
            dns_port=data.get("dns_port", 53),
            http_port=data.get("http_port", 3000),
            version=data.get("version", ""),
        )


@dataclass
class AdGuardHomeStats:
    """AdGuard Home statistics."""

    dns_queries: int = 0
    blocked_filtering: int = 0
    replaced_safebrowsing: int = 0
    replaced_parental: int = 0
    replaced_safesearch: int = 0
    avg_processing_time: float = 0.0
    top_queried_domains: list[dict[str, int]] = field(default_factory=list)
    top_blocked_domains: list[dict[str, int]] = field(default_factory=list)
    top_clients: list[dict[str, int]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdGuardHomeStats:
        """Create instance from API response dict."""
        return cls(
            dns_queries=data.get("num_dns_queries", 0),
            blocked_filtering=data.get("num_blocked_filtering", 0),
            replaced_safebrowsing=data.get("num_replaced_safebrowsing", 0),
            replaced_parental=data.get("num_replaced_parental", 0),
            replaced_safesearch=data.get("num_replaced_safesearch", 0),
            avg_processing_time=data.get("avg_processing_time", 0.0),
            top_queried_domains=data.get("top_queried_domains", []),
            top_blocked_domains=data.get("top_blocked_domains", []),
            top_clients=data.get("top_clients", []),
        )


@dataclass
class FilteringStatus:
    """AdGuard Home filtering status."""

    enabled: bool = False
    interval: int = 24
    filters: list[dict[str, Any]] = field(default_factory=list)
    whitelist_filters: list[dict[str, Any]] = field(default_factory=list)
    user_rules: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FilteringStatus:
        """Create instance from API response dict."""
        return cls(
            enabled=data.get("enabled", False),
            interval=data.get("interval", 24),
            filters=data.get("filters", []),
            whitelist_filters=data.get("whitelist_filters", []),
            user_rules=data.get("user_rules", []),
        )


@dataclass
class AdGuardHomeClient:
    """AdGuard Home client configuration."""

    name: str
    ids: list[str] = field(default_factory=list)
    uid: str = ""  # Unique identifier (v0.107.46+)
    use_global_settings: bool = True
    filtering_enabled: bool = True
    parental_enabled: bool = False
    safebrowsing_enabled: bool = False
    safesearch_enabled: bool = False
    use_global_blocked_services: bool = True
    blocked_services: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    upstreams_cache_enabled: bool = True
    upstreams_cache_size: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdGuardHomeClient:
        """Create instance from API response dict."""
        return cls(
            name=data.get("name", ""),
            ids=data.get("ids", []),
            uid=data.get("uid", ""),
            use_global_settings=data.get("use_global_settings", True),
            filtering_enabled=data.get("filtering_enabled", True),
            parental_enabled=data.get("parental_enabled", False),
            safebrowsing_enabled=data.get("safebrowsing_enabled", False),
            safesearch_enabled=data.get("safesearch_enabled", False),
            use_global_blocked_services=data.get("use_global_blocked_services", True),
            blocked_services=data.get("blocked_services", []),
            tags=data.get("tags", []),
            upstreams_cache_enabled=data.get("upstreams_cache_enabled", True),
            upstreams_cache_size=data.get("upstreams_cache_size", 0),
        )


@dataclass
class BlockedService:
    """AdGuard Home blocked service definition."""

    id: str
    name: str
    icon_svg: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlockedService:
        """Create instance from API response dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            icon_svg=data.get("icon_svg", ""),
        )


@dataclass
class DnsRewrite:
    """AdGuard Home DNS rewrite rule."""

    domain: str
    answer: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DnsRewrite:
        """Create instance from API response dict."""
        return cls(
            domain=data.get("domain", ""),
            answer=data.get("answer", ""),
        )


@dataclass
class DhcpLease:
    """AdGuard Home DHCP lease."""

    mac: str
    ip: str
    hostname: str
    expires: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DhcpLease:
        """Create instance from API response dict."""
        return cls(
            mac=data.get("mac", ""),
            ip=data.get("ip", ""),
            hostname=data.get("hostname", ""),
            expires=data.get("expires", ""),
        )


@dataclass
class DhcpV4Config:
    """AdGuard Home DHCP v4 configuration."""

    gateway_ip: str = ""
    subnet_mask: str = ""
    range_start: str = ""
    range_end: str = ""
    lease_duration: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DhcpV4Config:
        """Create instance from API response dict."""
        return cls(
            gateway_ip=data.get("gateway_ip", ""),
            subnet_mask=data.get("subnet_mask", ""),
            range_start=data.get("range_start", ""),
            range_end=data.get("range_end", ""),
            lease_duration=data.get("lease_duration", 0),
        )


@dataclass
class DhcpV6Config:
    """AdGuard Home DHCP v6 configuration."""

    range_start: str = ""
    lease_duration: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DhcpV6Config:
        """Create instance from API response dict."""
        return cls(
            range_start=data.get("range_start", ""),
            lease_duration=data.get("lease_duration", 0),
        )


@dataclass
class DhcpStatus:
    """AdGuard Home DHCP status."""

    enabled: bool = False
    interface_name: str = ""
    v4: DhcpV4Config | None = None
    v6: DhcpV6Config | None = None
    leases: list[DhcpLease] = field(default_factory=list)
    static_leases: list[DhcpLease] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DhcpStatus:
        """Create instance from API response dict."""
        v4_data = data.get("v4")
        v6_data = data.get("v6")
        return cls(
            enabled=data.get("enabled", False),
            interface_name=data.get("interface_name", ""),
            v4=DhcpV4Config.from_dict(v4_data) if v4_data else None,
            v6=DhcpV6Config.from_dict(v6_data) if v6_data else None,
            leases=[DhcpLease.from_dict(lease) for lease in data.get("leases", [])],
            static_leases=[
                DhcpLease.from_dict(lease) for lease in data.get("static_leases", [])
            ],
        )
