"""Data models for AdGuard Home API responses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdGuardHomeStatus:
    """AdGuard Home server status."""

    protection_enabled: bool
    running: bool
    dns_addresses: list[str] = field(default_factory=list)
    dns_port: int = 53
    http_port: int = 3000
    version: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdGuardHomeStatus:
        """Create instance from API response dict."""
        return cls(
            protection_enabled=data.get("protection_enabled", False),
            running=data.get("running", False),
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
    use_global_settings: bool = True
    filtering_enabled: bool = True
    parental_enabled: bool = False
    safebrowsing_enabled: bool = False
    safesearch_enabled: bool = False
    use_global_blocked_services: bool = True
    blocked_services: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdGuardHomeClient:
        """Create instance from API response dict."""
        return cls(
            name=data.get("name", ""),
            ids=data.get("ids", []),
            use_global_settings=data.get("use_global_settings", True),
            filtering_enabled=data.get("filtering_enabled", True),
            parental_enabled=data.get("parental_enabled", False),
            safebrowsing_enabled=data.get("safebrowsing_enabled", False),
            safesearch_enabled=data.get("safesearch_enabled", False),
            use_global_blocked_services=data.get("use_global_blocked_services", True),
            blocked_services=data.get("blocked_services", []),
            tags=data.get("tags", []),
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
class DhcpStatus:
    """AdGuard Home DHCP status."""

    enabled: bool = False
    interface_name: str = ""
    leases: list[DhcpLease] = field(default_factory=list)
    static_leases: list[DhcpLease] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DhcpStatus:
        """Create instance from API response dict."""
        return cls(
            enabled=data.get("enabled", False),
            interface_name=data.get("interface_name", ""),
            leases=[DhcpLease.from_dict(lease) for lease in data.get("leases", [])],
            static_leases=[DhcpLease.from_dict(lease) for lease in data.get("static_leases", [])],
        )
