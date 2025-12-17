"""Tests for the AdGuard Home Extended API client."""
from __future__ import annotations

import pytest
from aiohttp import ClientError, ClientResponseError
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.adguard_home_extended.api.client import (
    AdGuardHomeClient,
    AdGuardHomeError,
    AdGuardHomeConnectionError,
    AdGuardHomeAuthError,
)
from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStatus,
    AdGuardHomeStats,
    FilteringStatus,
    BlockedService,
)


class TestAdGuardHomeClient:
    """Tests for AdGuardHomeClient."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Return a mock aiohttp session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def client(self, mock_session: AsyncMock) -> AdGuardHomeClient:
        """Return an AdGuard Home client with mock session."""
        return AdGuardHomeClient(
            host="192.168.1.1",
            port=3000,
            username="admin",
            password="password",
            use_ssl=False,
            session=mock_session,
        )

    def test_init(self) -> None:
        """Test client initialization."""
        client = AdGuardHomeClient(
            host="192.168.1.1",
            port=3000,
            username="admin",
            password="secret",
            use_ssl=True,
        )
        assert client._host == "192.168.1.1"
        assert client._port == 3000
        assert client._username == "admin"
        assert client._password == "secret"
        assert client._use_ssl is True
        assert client._base_url == "https://192.168.1.1:3000"

    def test_init_without_ssl(self) -> None:
        """Test client initialization without SSL."""
        client = AdGuardHomeClient(
            host="192.168.1.1",
            port=3000,
        )
        assert client._base_url == "http://192.168.1.1:3000"

    def test_get_auth_header_with_credentials(self) -> None:
        """Test auth header generation with credentials."""
        client = AdGuardHomeClient(
            host="192.168.1.1",
            port=3000,
            username="admin",
            password="password",
        )
        headers = client._get_auth_header()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    def test_get_auth_header_without_credentials(self) -> None:
        """Test auth header generation without credentials."""
        client = AdGuardHomeClient(
            host="192.168.1.1",
            port=3000,
        )
        headers = client._get_auth_header()
        assert headers == {}

    @pytest.mark.asyncio
    async def test_request_no_session(self) -> None:
        """Test request fails without session."""
        client = AdGuardHomeClient(
            host="192.168.1.1",
            port=3000,
        )
        with pytest.raises(AdGuardHomeConnectionError, match="No session available"):
            await client._request("GET", "/control/status")

    @pytest.mark.asyncio
    async def test_get_status(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test getting status."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_length = 100
        mock_response.json = AsyncMock(return_value={
            "protection_enabled": True,
            "running": True,
            "dns_addresses": ["192.168.1.1"],
            "dns_port": 53,
            "http_port": 3000,
            "version": "0.107.43",
        })
        mock_response.raise_for_status = MagicMock()

        mock_session.request.return_value.__aenter__.return_value = mock_response

        status = await client.get_status()

        assert isinstance(status, AdGuardHomeStatus)
        assert status.protection_enabled is True
        assert status.running is True
        assert status.version == "0.107.43"

    @pytest.mark.asyncio
    async def test_get_stats(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test getting statistics."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_length = 100
        mock_response.json = AsyncMock(return_value={
            "num_dns_queries": 12345,
            "num_blocked_filtering": 1234,
            "num_replaced_safebrowsing": 10,
            "num_replaced_parental": 5,
            "num_replaced_safesearch": 2,
            "avg_processing_time": 15.5,
            "top_queried_domains": [],
            "top_blocked_domains": [],
            "top_clients": [],
        })
        mock_response.raise_for_status = MagicMock()

        mock_session.request.return_value.__aenter__.return_value = mock_response

        stats = await client.get_stats()

        assert isinstance(stats, AdGuardHomeStats)
        assert stats.dns_queries == 12345
        assert stats.blocked_filtering == 1234
        assert stats.avg_processing_time == 15.5

    @pytest.mark.asyncio
    async def test_set_protection(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test setting protection."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_length = 0
        mock_response.raise_for_status = MagicMock()

        mock_session.request.return_value.__aenter__.return_value = mock_response

        await client.set_protection(True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/protection" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_blocked_services(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test getting blocked services."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_length = 100
        mock_response.json = AsyncMock(return_value=["facebook", "tiktok"])
        mock_response.raise_for_status = MagicMock()

        mock_session.request.return_value.__aenter__.return_value = mock_response

        services = await client.get_blocked_services()

        assert services == ["facebook", "tiktok"]

    @pytest.mark.asyncio
    async def test_set_blocked_services(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test setting blocked services."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_length = 0
        mock_response.raise_for_status = MagicMock()

        mock_session.request.return_value.__aenter__.return_value = mock_response

        await client.set_blocked_services(["facebook", "youtube"])

        mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_auth_error_401(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test authentication error on 401."""
        mock_response = AsyncMock()
        mock_response.status = 401

        mock_session.request.return_value.__aenter__.return_value = mock_response

        with pytest.raises(AdGuardHomeAuthError, match="Invalid credentials"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_auth_error_403(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test authentication error on 403."""
        mock_response = AsyncMock()
        mock_response.status = 403

        mock_session.request.return_value.__aenter__.return_value = mock_response

        with pytest.raises(AdGuardHomeAuthError, match="Access forbidden"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_connection_error(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test connection error handling."""
        mock_session.request.side_effect = ClientError("Connection failed")

        with pytest.raises(AdGuardHomeConnectionError, match="Connection failed"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_test_connection_success(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test successful connection test."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_length = 100
        mock_response.json = AsyncMock(return_value={
            "protection_enabled": True,
            "running": True,
        })
        mock_response.raise_for_status = MagicMock()

        mock_session.request.return_value.__aenter__.return_value = mock_response

        result = await client.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(
        self, client: AdGuardHomeClient, mock_session: AsyncMock
    ) -> None:
        """Test failed connection test."""
        mock_session.request.side_effect = ClientError("Connection refused")

        result = await client.test_connection()
        assert result is False
