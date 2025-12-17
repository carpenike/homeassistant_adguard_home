"""AdGuard Home API client."""
from __future__ import annotations

import json
import logging
from base64 import b64encode
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from ..const import (
    API_BLOCKED_SERVICES_ALL,
    API_BLOCKED_SERVICES_LIST,
    API_BLOCKED_SERVICES_SET,
    API_CLIENTS,
    API_CLIENTS_ADD,
    API_CLIENTS_DELETE,
    API_CLIENTS_UPDATE,
    API_DHCP_STATUS,
    API_FILTERING_ADD_URL,
    API_FILTERING_CONFIG,
    API_FILTERING_REFRESH,
    API_FILTERING_REMOVE_URL,
    API_FILTERING_STATUS,
    API_PARENTAL_DISABLE,
    API_PARENTAL_ENABLE,
    API_PROTECTION,
    API_QUERYLOG,
    API_REWRITE_ADD,
    API_REWRITE_DELETE,
    API_REWRITE_LIST,
    API_SAFEBROWSING_DISABLE,
    API_SAFEBROWSING_ENABLE,
    API_SAFESEARCH_DISABLE,
    API_SAFESEARCH_ENABLE,
    API_STATS,
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
)

_LOGGER = logging.getLogger(__name__)


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
    ) -> None:
        """Initialize the client."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_ssl = use_ssl
        self._session = session
        self._base_url = f"{'https' if use_ssl else 'http'}://{host}:{port}"

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
        """Make an API request."""
        if self._session is None:
            raise AdGuardHomeConnectionError("No session available")

        url = f"{self._base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            **self._get_auth_header(),
        }

        try:
            async with self._session.request(
                method,
                url,
                json=data,
                headers=headers,
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
    async def set_protection(self, enabled: bool) -> None:
        """Enable or disable protection."""
        await self._post(API_PROTECTION, {"enabled": enabled})

    async def set_safebrowsing(self, enabled: bool) -> None:
        """Enable or disable safe browsing."""
        endpoint = API_SAFEBROWSING_ENABLE if enabled else API_SAFEBROWSING_DISABLE
        await self._post(endpoint)

    async def set_parental(self, enabled: bool) -> None:
        """Enable or disable parental control."""
        endpoint = API_PARENTAL_ENABLE if enabled else API_PARENTAL_DISABLE
        await self._post(endpoint)

    async def set_safesearch(self, enabled: bool) -> None:
        """Enable or disable safe search."""
        endpoint = API_SAFESEARCH_ENABLE if enabled else API_SAFESEARCH_DISABLE
        await self._post(endpoint)

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

    async def refresh_filters(self, force: bool = False) -> None:
        """Refresh filters."""
        await self._post(API_FILTERING_REFRESH, {"whitelist": force})

    # Clients
    async def get_clients(self) -> list[ClientConfig]:
        """Get all clients."""
        data = await self._get(API_CLIENTS)
        clients = data.get("clients", [])
        return [ClientConfig.from_dict(client) for client in clients]

    async def add_client(self, client: ClientConfig) -> None:
        """Add a client."""
        await self._post(
            API_CLIENTS_ADD,
            {
                "name": client.name,
                "ids": client.ids,
                "use_global_settings": client.use_global_settings,
                "filtering_enabled": client.filtering_enabled,
                "parental_enabled": client.parental_enabled,
                "safebrowsing_enabled": client.safebrowsing_enabled,
                "safesearch_enabled": client.safesearch_enabled,
                "use_global_blocked_services": client.use_global_blocked_services,
                "blocked_services": client.blocked_services,
                "tags": client.tags,
            },
        )

    async def update_client(self, name: str, client: ClientConfig) -> None:
        """Update a client."""
        await self._post(
            API_CLIENTS_UPDATE,
            {
                "name": name,
                "data": {
                    "name": client.name,
                    "ids": client.ids,
                    "use_global_settings": client.use_global_settings,
                    "filtering_enabled": client.filtering_enabled,
                    "parental_enabled": client.parental_enabled,
                    "safebrowsing_enabled": client.safebrowsing_enabled,
                    "safesearch_enabled": client.safesearch_enabled,
                    "use_global_blocked_services": client.use_global_blocked_services,
                    "blocked_services": client.blocked_services,
                    "tags": client.tags,
                },
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
            return data.get("ids", [])
        # Old format returns just a list
        return data if isinstance(data, list) else []

    async def set_blocked_services(self, services: list[str]) -> None:
        """Set blocked services.

        Uses the new API format (v0.107.37+) with {"ids": [...]}.
        """
        await self._post(API_BLOCKED_SERVICES_SET, {"ids": services})

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

    # Query log
    async def get_query_log(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict]:
        """Get query log entries."""
        params = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        data = await self._get(f"{API_QUERYLOG}?limit={limit}&offset={offset}")
        return data.get("data", []) if data else []

    # DHCP
    async def get_dhcp_status(self) -> DhcpStatus:
        """Get DHCP status."""
        data = await self._get(API_DHCP_STATUS)
        return DhcpStatus.from_dict(data)

    # Connection test
    async def test_connection(self) -> bool:
        """Test the connection to AdGuard Home."""
        try:
            await self.get_status()
            return True
        except AdGuardHomeError:
            return False
