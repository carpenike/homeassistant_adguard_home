"""Tests for the AdGuard Home Extended API client."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError

from custom_components.adguard_home_extended.api.client import (
    AdGuardHomeAuthError,
    AdGuardHomeClient,
    AdGuardHomeConnectionError,
)
from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
    FilteringStatus,
)


def create_mock_response(
    status: int = 200, json_data: dict | list | None = None, content_length: int = 100
):
    """Create a mock response that works as an async context manager."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.content_length = content_length if json_data is not None else 0
    mock_response.json = AsyncMock(return_value=json_data)
    mock_response.raise_for_status = MagicMock()
    return mock_response


class MockContextManager:
    """Async context manager for mock responses."""

    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestAdGuardHomeClient:
    """Tests for AdGuardHomeClient."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Return a mock aiohttp session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def client(self, mock_session: MagicMock) -> AdGuardHomeClient:
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
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting status."""
        mock_response = create_mock_response(
            status=200,
            json_data={
                "protection_enabled": True,
                "running": True,
                "dns_addresses": ["192.168.1.1"],
                "dns_port": 53,
                "http_port": 3000,
                "version": "0.107.43",
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        status = await client.get_status()

        assert isinstance(status, AdGuardHomeStatus)
        assert status.protection_enabled is True
        assert status.running is True
        assert status.version == "0.107.43"

    @pytest.mark.asyncio
    async def test_get_stats(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting statistics."""
        mock_response = create_mock_response(
            status=200,
            json_data={
                "num_dns_queries": 12345,
                "num_blocked_filtering": 1234,
                "num_replaced_safebrowsing": 10,
                "num_replaced_parental": 5,
                "num_replaced_safesearch": 2,
                "avg_processing_time": 15.5,
                "top_queried_domains": [],
                "top_blocked_domains": [],
                "top_clients": [],
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        stats = await client.get_stats()

        assert isinstance(stats, AdGuardHomeStats)
        assert stats.dns_queries == 12345
        assert stats.blocked_filtering == 1234
        assert stats.avg_processing_time == 15.5

    @pytest.mark.asyncio
    async def test_set_protection(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting protection."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_protection(True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/protection" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_blocked_services_new_format(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting blocked services with new API format."""
        mock_response = create_mock_response(
            status=200, json_data={"ids": ["facebook", "tiktok"], "schedule": {}}
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        services = await client.get_blocked_services()

        assert services == ["facebook", "tiktok"]

    @pytest.mark.asyncio
    async def test_get_blocked_services_legacy_format(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting blocked services with legacy API format (list)."""
        mock_response = create_mock_response(
            status=200, json_data=["facebook", "tiktok"]
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        services = await client.get_blocked_services()

        assert services == ["facebook", "tiktok"]

    @pytest.mark.asyncio
    async def test_set_blocked_services(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting blocked services uses new API format."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_blocked_services(["facebook", "youtube"])

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        # Verify it sends the new format {"ids": [...]}
        assert call_args[1]["json"] == {"ids": ["facebook", "youtube"]}

    @pytest.mark.asyncio
    async def test_get_filtering_status(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting filtering status."""
        mock_response = create_mock_response(
            status=200,
            json_data={
                "enabled": True,
                "interval": 12,
                "filters": [],
                "whitelist_filters": [],
                "user_rules": [],
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        status = await client.get_filtering_status()

        assert isinstance(status, FilteringStatus)
        assert status.enabled is True
        assert status.interval == 12

    @pytest.mark.asyncio
    async def test_set_filtering_enabled(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test enabling filtering."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_filtering(True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/filtering/config" in call_args[0][1]
        assert call_args[1]["json"] == {"enabled": True, "interval": 24}

    @pytest.mark.asyncio
    async def test_set_filtering_disabled_custom_interval(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test disabling filtering with custom interval."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_filtering(False, interval=12)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[1]["json"] == {"enabled": False, "interval": 12}

    @pytest.mark.asyncio
    async def test_auth_error_401(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test authentication error on 401."""
        mock_response = create_mock_response(status=401, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        with pytest.raises(AdGuardHomeAuthError, match="Invalid credentials"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_auth_error_403(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test authentication error on 403."""
        mock_response = create_mock_response(status=403, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        with pytest.raises(AdGuardHomeAuthError, match="Access forbidden"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_connection_error(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test connection error handling."""
        mock_session.request.side_effect = ClientError("Connection failed")

        with pytest.raises(AdGuardHomeConnectionError, match="Connection failed"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_test_connection_success(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test successful connection test."""
        mock_response = create_mock_response(
            status=200,
            json_data={
                "protection_enabled": True,
                "running": True,
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test failed connection test."""
        mock_session.request.side_effect = ClientError("Connection refused")

        result = await client.test_connection()
        assert result is False
