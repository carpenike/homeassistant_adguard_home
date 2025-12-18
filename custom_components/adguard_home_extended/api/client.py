"""AdGuard Home API client."""

from __future__ import annotations

import json
import logging
from base64 import b64encode
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout

from ..const import (
    API_BLOCKED_SERVICES_ALL,
    API_BLOCKED_SERVICES_GET,
    API_BLOCKED_SERVICES_LIST,
    API_BLOCKED_SERVICES_SET,
    API_BLOCKED_SERVICES_UPDATE,
    API_CHECK_HOST,
    API_CLIENTS,
    API_CLIENTS_ADD,
    API_CLIENTS_DELETE,
    API_CLIENTS_SEARCH,
    API_CLIENTS_UPDATE,
    API_DHCP_STATUS,
    API_DNS_CONFIG,
    API_DNS_INFO,
    API_FILTERING_ADD_URL,
    API_FILTERING_CONFIG,
    API_FILTERING_REFRESH,
    API_FILTERING_REMOVE_URL,
    API_FILTERING_SET_URL,
    API_FILTERING_STATUS,
    API_PARENTAL_DISABLE,
    API_PARENTAL_ENABLE,
    API_PROTECTION,
    API_QUERYLOG,
    API_QUERYLOG_CLEAR,
    API_QUERYLOG_CONFIG,
    API_QUERYLOG_CONFIG_UPDATE,
    API_REWRITE_ADD,
    API_REWRITE_DELETE,
    API_REWRITE_LIST,
    API_REWRITE_UPDATE,
    API_SAFEBROWSING_DISABLE,
    API_SAFEBROWSING_ENABLE,
    API_SAFESEARCH_SETTINGS,
    API_SAFESEARCH_STATUS,
    API_STATS,
    API_STATS_CONFIG,
    API_STATS_CONFIG_UPDATE,
    API_STATS_RESET,
    API_STATUS,
)
from .models import (
    AdGuardHomeClient as ClientConfig,
)
from .models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
    BlockedService,
    DhcpStatus,
    DnsRewrite,
    FilteringStatus,
    SafeSearchSettings,
)

_LOGGER = logging.getLogger(__name__)

# Default timeout for API requests (30 seconds)
DEFAULT_TIMEOUT = ClientTimeout(total=30)


class AdGuardHomeError(Exception):
    """Base exception for AdGuard Home errors."""


class AdGuardHomeConnectionError(AdGuardHomeError):
    """Connection error."""


class AdGuardHomeAuthError(AdGuardHomeError):
    """Authentication error."""


class AdGuardHomeClient:
    """AdGuard Home API client."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        use_ssl: bool = False,
        session: ClientSession | None = None,
        request_timeout: ClientTimeout | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            host: AdGuard Home server hostname or IP.
            port: AdGuard Home server port.
            username: Optional username for authentication.
            password: Optional password for authentication.
            use_ssl: Whether to use HTTPS.
            session: aiohttp ClientSession to use for requests.
            request_timeout: Optional custom timeout (default: 30 seconds).
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_ssl = use_ssl
        self._session = session
        self._base_url = f"{'https' if use_ssl else 'http'}://{host}:{port}"
        self._timeout = request_timeout or DEFAULT_TIMEOUT

    def _get_auth_header(self) -> dict[str, str]:
        """Get the authorization header."""
        if self._username and self._password:
            credentials = f"{self._username}:{self._password}"
            encoded = b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        return {}

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path.
            data: Optional JSON data to send.

        Returns:
            Parsed JSON response or None for empty responses.

        Raises:
            AdGuardHomeConnectionError: On connection or timeout errors.
            AdGuardHomeAuthError: On authentication failures.
        """
        if self._session is None:
            raise AdGuardHomeConnectionError("No session available")

        url = f"{self._base_url}{endpoint}"
        headers = {
            **self._get_auth_header(),
        }

        # Build request kwargs - only include json parameter when we have data
        # AdGuard Home v0.107.15+ requires that POST requests without a body
        # must NOT have Content-Type header set (returns 415 Unsupported Media Type)
        # This affects endpoints like /parental/enable, /safebrowsing/enable, etc.
        #
        # Important: aiohttp automatically adds Content-Type: application/octet-stream
        # for POST requests even when there's no body. We must use skip_auto_headers
        # AND avoid passing any data/json parameter to prevent this.
        request_kwargs: dict[str, Any] = {
            "headers": headers,
            "timeout": self._timeout,
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
            request_kwargs["json"] = data
        else:
            # For no-body requests, we must:
            # 1. Use skip_auto_headers to prevent aiohttp from auto-adding Content-Type
            # 2. NOT pass any data/json parameter (even None)
            # This ensures a truly empty body with no Content-Type header
            request_kwargs["skip_auto_headers"] = {"Content-Type", "Content-Length"}

        try:
            async with self._session.request(
                method,
                url,
                **request_kwargs,
            ) as response:
                if response.status == 401:
                    raise AdGuardHomeAuthError("Invalid credentials")
                if response.status == 403:
                    raise AdGuardHomeAuthError("Access forbidden")
                response.raise_for_status()

                # Some endpoints return empty body on success
                # Check content_length (may be None for chunked encoding)
                # or read the body and check if it's empty
                content = await response.read()
                if not content:
                    return None

                return json.loads(content)

        except TimeoutError as err:
            raise AdGuardHomeConnectionError(
                f"Request to {endpoint} timed out after {self._timeout.total}s"
            ) from err
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise AdGuardHomeAuthError(f"Authentication failed: {err}") from err
            raise AdGuardHomeConnectionError(f"Request failed: {err}") from err
        except ClientError as err:
            raise AdGuardHomeConnectionError(f"Connection failed: {err}") from err

    async def _get(self, endpoint: str) -> Any:
        """Make a GET request."""
        return await self._request("GET", endpoint)

    async def _post(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Make a POST request."""
        return await self._request("POST", endpoint, data)

    async def _put(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Make a PUT request."""
        return await self._request("PUT", endpoint, data)

    # Status and stats
    async def get_status(self) -> AdGuardHomeStatus:
        """Get server status."""
        data = await self._get(API_STATUS)
        return AdGuardHomeStatus.from_dict(data)

    async def get_stats(self) -> AdGuardHomeStats:
        """Get statistics."""
        data = await self._get(API_STATS)
        return AdGuardHomeStats.from_dict(data)

    # Protection toggles
    async def set_protection(
        self, enabled: bool, duration_ms: int | None = None
    ) -> None:
        """Enable or disable protection.

        Args:
            enabled: Whether protection should be enabled.
            duration_ms: If disabling, auto-resume after this many milliseconds.
                        Only used when enabled=False.
        """
        data: dict[str, Any] = {"enabled": enabled}
        if not enabled and duration_ms is not None:
            data["duration"] = duration_ms
        await self._post(API_PROTECTION, data)

    async def pause_protection(self, duration_ms: int) -> None:
        """Temporarily pause protection with auto-resume.

        Args:
            duration_ms: Resume protection after this many milliseconds.
        """
        await self.set_protection(enabled=False, duration_ms=duration_ms)

    async def set_safebrowsing(self, enabled: bool) -> None:
        """Enable or disable safe browsing."""
        endpoint = API_SAFEBROWSING_ENABLE if enabled else API_SAFEBROWSING_DISABLE
        await self._post(endpoint)

    async def set_parental(self, enabled: bool) -> None:
        """Enable or disable parental control."""
        endpoint = API_PARENTAL_ENABLE if enabled else API_PARENTAL_DISABLE
        await self._post(endpoint)

    async def set_safesearch(self, enabled: bool) -> None:
        """Enable or disable safe search.

        Uses the non-deprecated /control/safesearch/settings endpoint instead of
        the deprecated /control/safesearch/enable and /control/safesearch/disable
        endpoints. This preserves per-engine settings when toggling.
        """
        settings = await self.get_safesearch_settings()
        settings.enabled = enabled
        await self.set_safesearch_settings(settings)

    async def get_safesearch_settings(self) -> SafeSearchSettings:
        """Get SafeSearch settings with per-engine control.

        Returns detailed SafeSearch configuration including per-engine settings.
        Uses /control/safesearch/status for GET (not /settings which is PUT only).
        """
        data = await self._get(API_SAFESEARCH_STATUS)
        return SafeSearchSettings.from_dict(data or {})

    async def set_safesearch_settings(self, settings: SafeSearchSettings) -> None:
        """Set SafeSearch settings with per-engine control.

        Args:
            settings: SafeSearchSettings object with enabled flag and per-engine booleans.
        """
        await self._put(API_SAFESEARCH_SETTINGS, settings.to_dict())

    # Filtering
    async def get_filtering_status(self) -> FilteringStatus:
        """Get filtering status."""
        data = await self._get(API_FILTERING_STATUS)
        return FilteringStatus.from_dict(data)

    async def set_filtering(self, enabled: bool, interval: int = 24) -> None:
        """Enable or disable filtering.

        Args:
            enabled: Whether filtering should be enabled.
            interval: Filter update check interval in hours (default 24).
        """
        await self._post(
            API_FILTERING_CONFIG, {"enabled": enabled, "interval": interval}
        )

    async def add_filter_url(
        self, name: str, url: str, whitelist: bool = False
    ) -> None:
        """Add a filter URL."""
        await self._post(
            API_FILTERING_ADD_URL,
            {"name": name, "url": url, "whitelist": whitelist},
        )

    async def remove_filter_url(self, url: str, whitelist: bool = False) -> None:
        """Remove a filter URL."""
        await self._post(
            API_FILTERING_REMOVE_URL,
            {"url": url, "whitelist": whitelist},
        )

    async def set_filter_enabled(
        self,
        url: str,
        enabled: bool,
        whitelist: bool = False,
    ) -> None:
        """Enable or disable a filter list.

        Args:
            url: The URL of the filter list to modify.
            enabled: Whether the filter should be enabled.
            whitelist: Whether this is a whitelist filter (default False).
        """
        await self._post(
            API_FILTERING_SET_URL,
            {
                "url": url,
                "data": {
                    "enabled": enabled,
                    "url": url,
                },
                "whitelist": whitelist,
            },
        )

    async def refresh_filters(self, force: bool = False) -> None:
        """Refresh filters."""
        await self._post(API_FILTERING_REFRESH, {"whitelist": force})

    async def check_host(
        self,
        name: str,
        client: str | None = None,
        qtype: str | None = None,
    ) -> dict[str, Any]:
        """Check how a domain would be filtered.

        Queries the AdGuard Home filtering engine to determine if a domain
        would be blocked or allowed, and by which filter rules.

        Args:
            name: The domain name to check (e.g., "example.com").
            client: Optional client ID to check filtering rules for a specific
                    client (v0.107.58+). Uses global rules if not specified.
            qtype: Optional DNS query type (e.g., "A", "AAAA", "CNAME")
                   to check (v0.107.58+). Defaults to "A" if not specified.

        Returns:
            dict with filtering result including:
                - reason: Why the domain was filtered (e.g., "FilteredBlackList")
                - filter_id: ID of the filter that matched (if blocked)
                - rule: The exact rule that matched (if any)
                - rules: List of all matching rules with details
                - service_name: Blocked service name (if blocked service)
                - cname: CNAME if the domain is a CNAME record
                - ip_addrs: List of IP addresses if resolved
        """
        # Build query parameters
        params = [f"name={name}"]
        if client:
            params.append(f"client={client}")
        if qtype:
            params.append(f"qtype={qtype}")

        endpoint = f"{API_CHECK_HOST}?{'&'.join(params)}"
        result = await self._get(endpoint)
        return result if isinstance(result, dict) else {}

    # Clients
    async def get_clients(self) -> list[ClientConfig]:
        """Get all clients."""
        data = await self._get(API_CLIENTS)
        clients = data.get("clients", [])
        return [ClientConfig.from_dict(client) for client in clients]

    async def add_client(
        self,
        client: ClientConfig,
        blocked_services_schedule: dict[str, Any] | None = None,
    ) -> None:
        """Add a client.

        Args:
            client: The ClientConfig with client settings.
            blocked_services_schedule: Optional schedule for blocked services.
                Format: {"time_zone": "Local", "mon": {"start": 0, "end": 86400000}, ...}
        """
        data: dict[str, Any] = {
            "name": client.name,
            "ids": client.ids,
            "use_global_settings": client.use_global_settings,
            "filtering_enabled": client.filtering_enabled,
            "parental_enabled": client.parental_enabled,
            "safebrowsing_enabled": client.safebrowsing_enabled,
            "safesearch_enabled": client.safesearch_enabled,
            "use_global_blocked_services": client.use_global_blocked_services,
            "blocked_services": client.blocked_services or [],
            "tags": client.tags or [],
        }

        # Add blocked_services_schedule if provided (v0.107.37+)
        if blocked_services_schedule is not None:
            data["blocked_services_schedule"] = blocked_services_schedule
        elif not client.use_global_blocked_services:
            # Provide a default empty schedule when using per-client blocked services
            data["blocked_services_schedule"] = {"time_zone": "Local"}

        await self._post(API_CLIENTS_ADD, data)

    async def update_client(
        self,
        name: str,
        client: ClientConfig,
        blocked_services_schedule: dict[str, Any] | None = None,
    ) -> None:
        """Update a client.

        Args:
            name: The current name of the client to update.
            client: The ClientConfig with updated values.
            blocked_services_schedule: Optional schedule for blocked services.
                Format: {"time_zone": "Local", "mon": {"start": 0, "end": 86400000}, ...}
        """
        # Build the data dict with all required Client schema fields
        data: dict[str, Any] = {
            "name": client.name,
            "ids": client.ids,
            "use_global_settings": client.use_global_settings,
            "filtering_enabled": client.filtering_enabled,
            "parental_enabled": client.parental_enabled,
            "safebrowsing_enabled": client.safebrowsing_enabled,
            "safesearch_enabled": client.safesearch_enabled,
            "use_global_blocked_services": client.use_global_blocked_services,
            "blocked_services": client.blocked_services or [],
            "tags": client.tags or [],
        }

        # Add blocked_services_schedule if provided (v0.107.37+)
        # This is required when use_global_blocked_services is False
        if blocked_services_schedule is not None:
            data["blocked_services_schedule"] = blocked_services_schedule
        elif not client.use_global_blocked_services:
            # Provide a default empty schedule when using per-client blocked services
            data["blocked_services_schedule"] = {"time_zone": "Local"}

        await self._post(
            API_CLIENTS_UPDATE,
            {
                "name": name,
                "data": data,
            },
        )

    async def delete_client(self, name: str) -> None:
        """Delete a client."""
        await self._post(API_CLIENTS_DELETE, {"name": name})

    # Blocked services
    async def get_all_blocked_services(self) -> list[BlockedService]:
        """Get all available blocked services."""
        data = await self._get(API_BLOCKED_SERVICES_ALL)
        services = data.get("blocked_services", [])
        return [BlockedService.from_dict(svc) for svc in services]

    async def get_blocked_services(self) -> list[str]:
        """Get currently blocked services.

        Handles both old (list) and new (object with ids) API formats.
        """
        data = await self._get(API_BLOCKED_SERVICES_LIST)
        # New format returns {"ids": [...], "schedule": {...}}
        if isinstance(data, dict):
            ids = data.get("ids", [])
            return list(ids) if ids else []
        # Old format returns just a list
        return list(data) if isinstance(data, list) else []

    async def get_blocked_services_with_schedule(self) -> dict[str, Any]:
        """Get blocked services with schedule info.

        Returns the full response including schedule (v0.107.37+).
        """
        data = await self._get(API_BLOCKED_SERVICES_LIST)
        if isinstance(data, dict):
            return data
        # Old format - wrap in new format structure
        return {"ids": data if isinstance(data, list) else [], "schedule": {}}

    async def set_blocked_services(
        self,
        services: list[str],
        schedule: dict[str, Any] | None = None,
    ) -> None:
        """Set blocked services with optional schedule.

        Args:
            services: List of service IDs to block.
            schedule: Optional schedule dict with time_zone and day configs.
                     Example: {"time_zone": "America/New_York", "mon": {"start": 0, "end": 86399999}}
        """
        data: dict[str, Any] = {"ids": services}
        if schedule is not None:
            data["schedule"] = schedule
        await self._post(API_BLOCKED_SERVICES_SET, data)

    # DNS rewrites
    async def get_rewrites(self) -> list[DnsRewrite]:
        """Get DNS rewrites."""
        data = await self._get(API_REWRITE_LIST)
        return [DnsRewrite.from_dict(rewrite) for rewrite in data or []]

    async def add_rewrite(self, domain: str, answer: str) -> None:
        """Add a DNS rewrite."""
        await self._post(API_REWRITE_ADD, {"domain": domain, "answer": answer})

    async def delete_rewrite(self, domain: str, answer: str) -> None:
        """Delete a DNS rewrite."""
        await self._post(API_REWRITE_DELETE, {"domain": domain, "answer": answer})

    async def update_rewrite(
        self,
        old_domain: str,
        old_answer: str,
        new_domain: str,
        new_answer: str,
        enabled: bool | None = None,
    ) -> None:
        """Update an existing DNS rewrite.

        Args:
            old_domain: Current domain of the rewrite rule.
            old_answer: Current answer of the rewrite rule.
            new_domain: New domain for the rewrite rule.
            new_answer: New answer for the rewrite rule.
            enabled: Optional enabled state (v0.107.68+).
        """
        update_data: dict[str, Any] = {"domain": new_domain, "answer": new_answer}
        if enabled is not None:
            update_data["enabled"] = enabled
        await self._put(
            API_REWRITE_UPDATE,
            {
                "target": {"domain": old_domain, "answer": old_answer},
                "update": update_data,
            },
        )

    async def set_rewrite_enabled(
        self, domain: str, answer: str, enabled: bool
    ) -> None:
        """Enable or disable a DNS rewrite rule (v0.107.68+).

        Args:
            domain: Domain of the rewrite rule.
            answer: Answer of the rewrite rule.
            enabled: Whether the rule should be enabled.
        """
        await self.update_rewrite(
            old_domain=domain,
            old_answer=answer,
            new_domain=domain,
            new_answer=answer,
            enabled=enabled,
        )

    # Query log
    async def get_query_log(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        response_status: str | None = None,
    ) -> list[dict]:
        """Get query log entries.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.
            search: Optional search string to filter by domain.
            response_status: Optional filter by response status (v0.107.68+).
                - "all": Return all queries (default)
                - "filtered": Return only filtered/blocked queries

        Returns:
            List of query log entries.
        """
        query_parts = [f"limit={limit}", f"offset={offset}"]
        if search:
            query_parts.append(f"search={search}")
        if response_status:
            query_parts.append(f"response_status={response_status}")
        query_string = "&".join(query_parts)
        data = await self._get(f"{API_QUERYLOG}?{query_string}")
        result = data.get("data", []) if data else []
        return list(result) if result else []

    # DHCP
    async def get_dhcp_status(self) -> DhcpStatus:
        """Get DHCP status."""
        data = await self._get(API_DHCP_STATUS)
        return DhcpStatus.from_dict(data)

    # DNS configuration
    async def get_dns_info(self) -> dict[str, Any]:
        """Get DNS configuration info.

        Returns DNS server settings including cache configuration.
        Available in AdGuard Home v0.107.65+.
        """
        data = await self._get(API_DNS_INFO)
        return data or {}

    async def set_dns_config(self, config: dict[str, Any]) -> None:
        """Set DNS configuration.

        Args:
            config: Dictionary with DNS config fields to update.
                    Common fields: cache_enabled, cache_size, cache_ttl_min, etc.
        """
        await self._post(API_DNS_CONFIG, config)

    async def set_dns_cache_enabled(self, enabled: bool) -> None:
        """Enable or disable DNS caching.

        Args:
            enabled: True to enable DNS cache, False to disable.
        """
        await self.set_dns_config({"cache_enabled": enabled})

    async def set_dnssec_enabled(self, enabled: bool) -> None:
        """Enable or disable DNSSEC validation.

        DNSSEC adds cryptographic signatures to DNS responses to verify
        their authenticity. When enabled, AdGuard Home validates these
        signatures and rejects responses that fail validation.

        Args:
            enabled: True to enable DNSSEC validation, False to disable.
        """
        await self.set_dns_config({"dnssec_enabled": enabled})

    async def set_edns_cs_enabled(self, enabled: bool) -> None:
        """Enable or disable EDNS Client Subnet.

        EDNS Client Subnet (ECS) sends part of your IP address to DNS servers
        to get geographically appropriate responses. This can improve CDN
        performance but reduces privacy.

        Args:
            enabled: True to enable EDNS Client Subnet, False to disable.
        """
        await self.set_dns_config({"edns_cs_enabled": enabled})

    async def set_rate_limit(self, rate: int) -> None:
        """Set the DNS query rate limit.

        Limits the number of DNS requests per second from a single client.
        Set to 0 to disable rate limiting.

        Args:
            rate: Maximum requests per second per client (0 = unlimited).
        """
        await self.set_dns_config({"ratelimit": rate})

    async def set_blocking_mode(self, mode: str) -> None:
        """Set the DNS blocking mode.

        Determines how blocked domains are handled.

        Args:
            mode: Blocking mode, one of:
                - "default": Return 0.0.0.0 for A and :: for AAAA
                - "refused": Return REFUSED DNS response
                - "nxdomain": Return NXDOMAIN DNS response
                - "null_ip": Return 0.0.0.0 for both A and AAAA
                - "custom_ip": Return custom IP (requires blocking_ipv4/ipv6)
        """
        await self.set_dns_config({"blocking_mode": mode})

    # Connection test
    async def test_connection(self) -> bool:
        """Test the connection to AdGuard Home."""
        try:
            await self.get_status()
            return True
        except AdGuardHomeError:
            return False

    # Stats configuration (v0.107.30+)
    async def get_stats_config(self) -> dict[str, Any]:
        """Get statistics configuration.

        Returns stats settings including enabled state and retention interval.
        Available in AdGuard Home v0.107.30+.

        Returns:
            Dict with keys: enabled (bool), interval (int in ms), ignored (list of domains)
        """
        data = await self._get(API_STATS_CONFIG)
        return data or {}

    async def set_stats_config(
        self,
        enabled: bool | None = None,
        interval: int | None = None,
        ignored: list[str] | None = None,
    ) -> None:
        """Update statistics configuration.

        Args:
            enabled: Whether statistics collection is enabled.
            interval: Stats retention period in milliseconds.
            ignored: List of domains to ignore in stats.
        """
        config: dict[str, Any] = {}
        if enabled is not None:
            config["enabled"] = enabled
        if interval is not None:
            config["interval"] = interval
        if ignored is not None:
            config["ignored"] = ignored
        if config:
            await self._put(API_STATS_CONFIG_UPDATE, config)

    async def reset_stats(self) -> None:
        """Reset all statistics.

        Clears all statistics data and resets counters to zero.
        """
        await self._post(API_STATS_RESET, {})

    # Query log configuration (v0.107.30+)
    async def get_querylog_config(self) -> dict[str, Any]:
        """Get query log configuration.

        Returns query log settings including enabled state and anonymization.
        Available in AdGuard Home v0.107.30+.

        Returns:
            Dict with keys: enabled, anonymize_client_ip, interval, ignored
        """
        data = await self._get(API_QUERYLOG_CONFIG)
        return data or {}

    async def set_querylog_config(
        self,
        enabled: bool | None = None,
        anonymize_client_ip: bool | None = None,
        interval: int | None = None,
        ignored: list[str] | None = None,
    ) -> None:
        """Update query log configuration.

        Args:
            enabled: Whether query logging is enabled.
            anonymize_client_ip: Whether to anonymize client IPs.
            interval: Log retention period in milliseconds.
            ignored: List of domains to ignore in query log.
        """
        config: dict[str, Any] = {}
        if enabled is not None:
            config["enabled"] = enabled
        if anonymize_client_ip is not None:
            config["anonymize_client_ip"] = anonymize_client_ip
        if interval is not None:
            config["interval"] = interval
        if ignored is not None:
            config["ignored"] = ignored
        if config:
            await self._put(API_QUERYLOG_CONFIG_UPDATE, config)

    async def clear_query_log(self) -> None:
        """Clear all query log entries.

        Removes all entries from the query log.
        """
        await self._post(API_QUERYLOG_CLEAR, {})

    # Blocked services with schedule (v0.107.56+)
    async def get_blocked_services_v2(self) -> dict[str, Any]:
        """Get blocked services with schedule (v0.107.56+ API).

        Uses the newer /control/blocked_services/get endpoint.

        Returns:
            Dict with ids (list of service IDs) and schedule configuration.
        """
        data = await self._get(API_BLOCKED_SERVICES_GET)
        if isinstance(data, dict):
            return data
        return {"ids": data if isinstance(data, list) else [], "schedule": {}}

    async def set_blocked_services_v2(
        self,
        services: list[str],
        schedule: dict[str, Any] | None = None,
    ) -> None:
        """Set blocked services with schedule (v0.107.56+ API).

        Uses the newer /control/blocked_services/update endpoint.

        Args:
            services: List of service IDs to block.
            schedule: Optional schedule dict with time_zone and day configs.
        """
        data: dict[str, Any] = {"ids": services}
        if schedule is not None:
            data["schedule"] = schedule
        await self._put(API_BLOCKED_SERVICES_UPDATE, data)

    # Client search (v0.107.56+)
    async def search_clients(self, client_ids: list[str]) -> list[dict[str, Any]]:
        """Search for clients by ID (v0.107.56+ API).

        This replaces the deprecated GET /control/clients/find endpoint.
        Use this for looking up specific clients when you don't need all clients.
        For fetching all clients, use get_clients() instead.

        Args:
            client_ids: List of client identifiers (IPs, MACs, or names).

        Returns:
            List of client info dicts for found clients. Each dict contains
            client configuration including name, ids, filtering settings, etc.
        """
        clients_param = [{"id": cid} for cid in client_ids]
        data = await self._post(API_CLIENTS_SEARCH, {"clients": clients_param})
        return data if isinstance(data, list) else []

    async def search_client(self, client_id: str) -> dict[str, Any] | None:
        """Search for a single client by ID (v0.107.56+ API).

        Convenience method for looking up a single client.

        Args:
            client_id: Client identifier (IP, MAC, or name).

        Returns:
            Client info dict if found, None otherwise.
        """
        results = await self.search_clients([client_id])
        return results[0] if results else None
