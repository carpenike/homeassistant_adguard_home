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
    ecosia: bool = True  # Added in AdGuard Home v0.107.52
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
            ecosia=data.get("ecosia", True),
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
            "ecosia": self.ecosia,
            "google": self.google,
            "pixabay": self.pixabay,
            "yandex": self.yandex,
            "youtube": self.youtube,
        }


@dataclass
class AdGuardHomeStatus:
    """AdGuard Home server status.

    Per OpenAPI ServerStatus schema, required fields are:
    dns_addresses, dns_port, http_port, protection_enabled,
    protection_disabled_until (nullable), running, version, language.

    Note: safebrowsing_enabled, parental_enabled, and safesearch_enabled
    are NOT returned by the /control/status endpoint. They must be fetched
    from separate endpoints: /control/safebrowsing/status,
    /control/parental/status, and /control/safesearch/status.
    """

    protection_enabled: bool
    running: bool
    dns_addresses: list[str] = field(default_factory=list)
    dns_port: int = 53
    http_port: int = 3000
    version: str = ""
    language: str = "en"
    protection_disabled_until: str | None = None
    protection_disabled_duration: int = 0
    dhcp_available: bool = False
    start_time: float = 0.0

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
            language=data.get("language", "en"),
            protection_disabled_until=data.get("protection_disabled_until"),
            protection_disabled_duration=data.get("protection_disabled_duration", 0),
            dhcp_available=data.get("dhcp_available", False),
            start_time=data.get("start_time", 0.0),
        )


@dataclass
class AdGuardHomeStats:
    """AdGuard Home statistics.

    Per OpenAPI Stats schema, includes time_units (hours/days enum),
    num_* counters, avg_processing_time, top_* arrays, and time-series
    arrays. Fields added in v0.107.36: top_upstreams_responses, top_upstreams_avg_time.
    """

    dns_queries: int = 0
    blocked_filtering: int = 0
    replaced_safebrowsing: int = 0
    replaced_parental: int = 0
    replaced_safesearch: int = 0
    avg_processing_time: float = 0.0
    top_queried_domains: list[dict[str, int]] = field(default_factory=list)
    top_blocked_domains: list[dict[str, int]] = field(default_factory=list)
    top_clients: list[dict[str, int]] = field(default_factory=list)
    # Added in v0.107.36
    top_upstreams_responses: list[dict[str, int]] = field(default_factory=list)
    top_upstreams_avg_time: list[dict[str, float]] = field(default_factory=list)
    time_units: str = "hours"
    # Time-series arrays for graphing
    dns_queries_series: list[int] = field(default_factory=list)
    blocked_filtering_series: list[int] = field(default_factory=list)
    replaced_safebrowsing_series: list[int] = field(default_factory=list)
    replaced_parental_series: list[int] = field(default_factory=list)

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
            # v0.107.36+ fields
            top_upstreams_responses=data.get("top_upstreams_responses", []),
            top_upstreams_avg_time=data.get("top_upstreams_avg_time", []),
            time_units=data.get("time_units", "hours"),
            # Time-series arrays
            dns_queries_series=data.get("dns_queries", []),
            blocked_filtering_series=data.get("blocked_filtering", []),
            replaced_safebrowsing_series=data.get("replaced_safebrowsing", []),
            replaced_parental_series=data.get("replaced_parental", []),
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
            filters=data.get("filters") or [],
            whitelist_filters=data.get("whitelist_filters") or [],
            user_rules=data.get("user_rules") or [],
        )


@dataclass
class DnsInfo:
    """AdGuard Home DNS configuration info.

    Note: cache_enabled field is only available in AdGuard Home v0.107.65+.
    For older versions, cache state is inferred from cache_size > 0.
    """

    cache_enabled: bool = True
    cache_size: int = 4194304  # Default 4MB
    cache_ttl_min: int = 0
    cache_ttl_max: int = 0
    upstream_dns: list[str] = field(default_factory=list)
    bootstrap_dns: list[str] = field(default_factory=list)
    rate_limit: int = 20
    blocking_mode: str = "default"
    edns_cs_enabled: bool = False
    dnssec_enabled: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DnsInfo:
        """Create instance from API response dict.

        For AdGuard Home < v0.107.65, cache_enabled is not present in the API.
        In that case, we infer cache status from cache_size > 0.
        """
        cache_size = data.get("cache_size", 4194304)
        # If cache_enabled is present, use it; otherwise infer from cache_size
        cache_enabled = data.get("cache_enabled", cache_size > 0)

        return cls(
            cache_enabled=cache_enabled,
            cache_size=cache_size,
            cache_ttl_min=data.get("cache_ttl_min", 0),
            cache_ttl_max=data.get("cache_ttl_max", 0),
            upstream_dns=data.get("upstream_dns", []),
            bootstrap_dns=data.get("bootstrap_dns", []),
            rate_limit=data.get("ratelimit", 20),
            blocking_mode=data.get("blocking_mode", "default"),
            edns_cs_enabled=data.get("edns_cs_enabled", False),
            dnssec_enabled=data.get("dnssec_enabled", False),
        )


@dataclass
class AdGuardHomeClient:
    """AdGuard Home client configuration.

    Per OpenAPI spec (v0.107.69), the Client schema includes:
    - name: Client name (required)
    - ids: List of IP addresses, CIDRs, MACs, or ClientIDs (required)
    - use_global_settings: Whether to use global filtering settings
    - filtering_enabled: Whether DNS filtering is enabled for this client
    - parental_enabled: Whether parental control is enabled
    - safebrowsing_enabled: Whether safe browsing is enabled
    - safesearch_enabled: (deprecated) Use safe_search instead
    - safe_search: SafeSearchConfig object with per-engine settings
    - use_global_blocked_services: Whether to use global blocked services
    - blocked_services: List of service IDs to block (when not using global)
    - blocked_services_schedule: Schedule for when blocking is active
    - upstreams: List of custom DNS upstream servers for this client
    - tags: List of tags for client categorization
    - ignore_querylog: Exclude this client from query log
    - ignore_statistics: Exclude this client from statistics
    - upstreams_cache_enabled: Enable DNS cache for custom upstreams
    - upstreams_cache_size: Size of the custom upstream cache

    Note: The 'uid' field exists in the configuration file
    (clients.persistent.*.uid) but is NOT returned by the HTTP API.
    """

    name: str
    ids: list[str] = field(default_factory=list)
    use_global_settings: bool = True
    filtering_enabled: bool = True
    parental_enabled: bool = False
    safebrowsing_enabled: bool = False
    safesearch_enabled: bool = False  # Deprecated, use safe_search instead
    safe_search: SafeSearchSettings | None = None  # Per-engine safe search
    use_global_blocked_services: bool = True
    blocked_services: list[str] = field(default_factory=list)
    blocked_services_schedule: dict[str, Any] | None = None
    upstreams: list[str] = field(default_factory=list)  # Custom DNS upstreams
    tags: list[str] = field(default_factory=list)
    upstreams_cache_enabled: bool = False  # Default per OpenAPI spec
    upstreams_cache_size: int = 0
    ignore_querylog: bool = False
    ignore_statistics: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdGuardHomeClient:
        """Create instance from API response dict."""
        # Parse safe_search if present
        safe_search_data = data.get("safe_search")
        safe_search = (
            SafeSearchSettings.from_dict(safe_search_data) if safe_search_data else None
        )

        return cls(
            name=data.get("name", ""),
            ids=data.get("ids", []),
            use_global_settings=data.get("use_global_settings", True),
            filtering_enabled=data.get("filtering_enabled", True),
            parental_enabled=data.get("parental_enabled", False),
            safebrowsing_enabled=data.get("safebrowsing_enabled", False),
            safesearch_enabled=data.get("safesearch_enabled", False),
            safe_search=safe_search,
            use_global_blocked_services=data.get("use_global_blocked_services", True),
            blocked_services=data.get("blocked_services") or [],
            blocked_services_schedule=data.get("blocked_services_schedule"),
            upstreams=data.get("upstreams") or [],
            tags=data.get("tags") or [],
            upstreams_cache_enabled=data.get("upstreams_cache_enabled", False),
            upstreams_cache_size=data.get("upstreams_cache_size", 0),
            ignore_querylog=data.get("ignore_querylog", False),
            ignore_statistics=data.get("ignore_statistics", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API request.

        Returns the client configuration in the format expected by
        POST /control/clients/add and POST /control/clients/update endpoints.
        """
        data: dict[str, Any] = {
            "name": self.name,
            "ids": self.ids,
            "use_global_settings": self.use_global_settings,
            "filtering_enabled": self.filtering_enabled,
            "parental_enabled": self.parental_enabled,
            "safebrowsing_enabled": self.safebrowsing_enabled,
            "use_global_blocked_services": self.use_global_blocked_services,
            "blocked_services": self.blocked_services or [],
            "upstreams": self.upstreams or [],
            "tags": self.tags or [],
            "ignore_querylog": self.ignore_querylog,
            "ignore_statistics": self.ignore_statistics,
            "upstreams_cache_enabled": self.upstreams_cache_enabled,
            "upstreams_cache_size": self.upstreams_cache_size,
        }

        # Handle safe_search - prefer the new object over deprecated boolean
        if self.safe_search is not None:
            data["safe_search"] = self.safe_search.to_dict()
        else:
            data["safesearch_enabled"] = self.safesearch_enabled

        # Include blocked_services_schedule if present
        if self.blocked_services_schedule is not None:
            data["blocked_services_schedule"] = self.blocked_services_schedule
        elif not self.use_global_blocked_services:
            # Provide default empty schedule when using per-client blocked services
            data["blocked_services_schedule"] = {"time_zone": "Local"}

        return data


@dataclass
class BlockedService:
    """AdGuard Home blocked service definition.

    Per OpenAPI schema, required fields are: icon_svg, id, name, rules.
    Optional field: group_id (added in newer versions).
    """

    id: str
    name: str
    icon_svg: str = ""
    rules: list[str] = field(default_factory=list)
    group_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlockedService:
        """Create instance from API response dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            icon_svg=data.get("icon_svg", ""),
            rules=data.get("rules", []),
            group_id=data.get("group_id", ""),
        )


@dataclass
class DnsRewrite:
    """AdGuard Home DNS rewrite rule."""

    domain: str
    answer: str
    enabled: bool = True  # Added in v0.107.68

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DnsRewrite:
        """Create instance from API response dict."""
        return cls(
            domain=data.get("domain", ""),
            answer=data.get("answer", ""),
            enabled=data.get("enabled", True),  # Default to True for backwards compat
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request dict."""
        return {
            "domain": self.domain,
            "answer": self.answer,
            "enabled": self.enabled,
        }


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
