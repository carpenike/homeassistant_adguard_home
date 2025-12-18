"""Tests for the AdGuard Home Extended API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError, ClientTimeout

from custom_components.adguard_home_extended.api.client import (
    DEFAULT_TIMEOUT,
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
    import json as json_module

    mock_response = MagicMock()
    mock_response.status = status
    mock_response.content_length = content_length if json_data is not None else 0
    mock_response.json = AsyncMock(return_value=json_data)
    mock_response.raise_for_status = MagicMock()
    # Add read() mock for the new implementation that reads body first
    if json_data is not None:
        mock_response.read = AsyncMock(
            return_value=json_module.dumps(json_data).encode()
        )
    else:
        mock_response.read = AsyncMock(return_value=b"")
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
    async def test_request_timeout(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test request handles timeout properly."""
        # Simulate a timeout by raising asyncio.TimeoutError
        mock_session.request.side_effect = TimeoutError()

        with pytest.raises(AdGuardHomeConnectionError, match="timed out"):
            await client._request("GET", "/control/status")

    @pytest.mark.asyncio
    async def test_request_uses_timeout(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test that requests include timeout parameter."""
        mock_response = create_mock_response(
            status=200,
            json_data={"protection_enabled": True, "running": True},
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        await client._request("GET", "/control/status")

        # Verify timeout was passed to the request
        call_kwargs = mock_session.request.call_args
        assert "timeout" in call_kwargs.kwargs
        assert call_kwargs.kwargs["timeout"] == DEFAULT_TIMEOUT

    @pytest.mark.asyncio
    async def test_request_with_json_data_includes_content_type(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test that requests WITH JSON data include Content-Type header."""
        mock_response = create_mock_response(status=200, json_data={})
        mock_session.request.return_value = MockContextManager(mock_response)

        await client._request("POST", "/control/protection", data={"enabled": True})

        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs["headers"]
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_request_without_json_data_omits_content_type(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test that requests WITHOUT JSON data omit Content-Type header.

        This is critical for AdGuard Home endpoints like /control/parental/enable
        that return 415 Unsupported Media Type if Content-Type: application/json
        is sent without a body.
        """
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client._request("POST", "/control/parental/enable")

        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs["headers"]
        assert "Content-Type" not in headers

    @pytest.mark.asyncio
    async def test_set_parental_enable_no_content_type(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test set_parental(True) does not send Content-Type header.

        Regression test for 415 Unsupported Media Type error.
        """
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_parental(True)

        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs["headers"]
        assert "Content-Type" not in headers

    @pytest.mark.asyncio
    async def test_set_safebrowsing_enable_no_content_type(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test set_safebrowsing(True) does not send Content-Type header.

        Regression test for 415 Unsupported Media Type error.
        """
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_safebrowsing(True)

        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs["headers"]
        assert "Content-Type" not in headers

    def test_default_timeout_value(self) -> None:
        """Test default timeout is 30 seconds."""
        assert DEFAULT_TIMEOUT.total == 30

    def test_custom_timeout(self) -> None:
        """Test client accepts custom timeout."""
        custom_timeout = ClientTimeout(total=60)
        client = AdGuardHomeClient(
            host="192.168.1.1",
            port=3000,
            request_timeout=custom_timeout,
        )
        assert client._timeout == custom_timeout
        assert client._timeout.total == 60

    @pytest.mark.asyncio
    async def test_get_status(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting status.

        Per OpenAPI ServerStatus schema, required fields are:
        dns_addresses, dns_port, http_port, protection_enabled,
        protection_disabled_until (nullable), running, version, language.
        """
        mock_response = create_mock_response(
            status=200,
            json_data={
                "protection_enabled": True,
                "protection_disabled_until": None,
                "running": True,
                "dns_addresses": ["192.168.1.1"],
                "dns_port": 53,
                "http_port": 3000,
                "version": "0.107.43",
                "language": "en",
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
        """Test getting statistics.

        Per OpenAPI Stats schema, includes time_units (hours/days enum),
        num_* counters, avg_processing_time, top_* arrays, and time-series
        arrays (dns_queries, blocked_filtering, etc.).
        """
        mock_response = create_mock_response(
            status=200,
            json_data={
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
                "top_upstreams_responses": [{"1.1.1.1": 1000}],
                "top_upstreams_avg_time": [{"1.1.1.1": 0.025}],
                "dns_queries": [100, 150, 200],
                "blocked_filtering": [10, 15, 20],
                "replaced_safebrowsing": [1, 2, 1],
                "replaced_parental": [0, 1, 0],
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
    async def test_set_protection_with_duration(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test disabling protection with auto-resume duration."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        # Disable protection for 1 hour (3600000 ms)
        await client.set_protection(False, duration_ms=3600000)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/protection" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_pause_protection(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test pausing protection for a duration."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        # Pause for 30 minutes
        await client.pause_protection(duration_ms=1800000)

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
    async def test_set_blocked_services_with_schedule(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting blocked services with schedule."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        schedule = {
            "time_zone": "America/New_York",
            "mon": {"start": 32400000, "end": 61200000},  # 9am-5pm
        }
        await client.set_blocked_services(["facebook"], schedule=schedule)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[1]["json"]["ids"] == ["facebook"]
        assert call_args[1]["json"]["schedule"] == schedule

    @pytest.mark.asyncio
    async def test_get_blocked_services_with_schedule(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting blocked services with schedule info."""
        response_data = {
            "ids": ["facebook", "tiktok"],
            "schedule": {
                "time_zone": "America/New_York",
                "mon": {"start": 0, "end": 86399999},
            },
        }
        mock_response = create_mock_response(status=200, json_data=response_data)
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_blocked_services_with_schedule()

        assert result["ids"] == ["facebook", "tiktok"]
        assert "schedule" in result
        assert result["schedule"]["time_zone"] == "America/New_York"

    @pytest.mark.asyncio
    async def test_get_blocked_services_with_schedule_old_format_list(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting blocked services when API returns old list format."""
        # Old format returned a list of service IDs directly
        response_data = ["facebook", "tiktok"]
        mock_response = create_mock_response(status=200, json_data=response_data)
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_blocked_services_with_schedule()

        # Should wrap in new format structure
        assert result["ids"] == ["facebook", "tiktok"]
        assert result["schedule"] == {}

    @pytest.mark.asyncio
    async def test_get_filtering_status(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting filtering status.

        Per OpenAPI FilterStatus schema, Filter objects require:
        enabled, id, name, rules_count, url. Optional: last_updated.
        """
        mock_response = create_mock_response(
            status=200,
            json_data={
                "enabled": True,
                "interval": 12,
                "filters": [
                    {
                        "id": 1,
                        "enabled": True,
                        "name": "AdGuard DNS filter",
                        "url": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
                        "rules_count": 5912,
                        "last_updated": "2024-01-15T10:30:00Z",
                    }
                ],
                "whitelist_filters": [],
                "user_rules": ["||example.com^"],
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        status = await client.get_filtering_status()

        assert isinstance(status, FilteringStatus)
        assert status.enabled is True
        assert status.interval == 12
        assert len(status.filters) == 1
        assert status.filters[0]["rules_count"] == 5912

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

    @pytest.mark.asyncio
    async def test_chunked_response_no_content_length(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test handling chunked transfer encoding (content_length is None)."""
        # Simulate chunked transfer encoding where content_length is None
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.content_length = None  # Chunked transfer encoding
        mock_response.raise_for_status = MagicMock()
        # read() returns the body
        import json as json_module

        mock_response.read = AsyncMock(
            return_value=json_module.dumps(
                {"protection_enabled": True, "running": True}
            ).encode()
        )

        mock_session.request.return_value = MockContextManager(mock_response)

        status = await client.get_status()

        # Verify read() was called (our fix)
        mock_response.read.assert_called_once()
        assert status.protection_enabled is True

    @pytest.mark.asyncio
    async def test_empty_response_body(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test handling empty response body (e.g., POST with no return)."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.content_length = 0
        mock_response.raise_for_status = MagicMock()
        mock_response.read = AsyncMock(return_value=b"")

        mock_session.request.return_value = MockContextManager(mock_response)

        # For POST endpoints that return empty body, this should work
        await client.set_protection(True)

        # No exception should be raised

    @pytest.mark.asyncio
    async def test_get_query_log_basic(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting query log with default parameters."""

        mock_response = create_mock_response(
            json_data={"data": [{"question": "example.com"}]}
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_query_log()

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        # Verify the URL contains limit and offset but not search
        url = call_args[0][1]
        assert "limit=100" in url
        assert "offset=0" in url
        assert "search=" not in url
        assert result == [{"question": "example.com"}]

    @pytest.mark.asyncio
    async def test_get_query_log_with_search(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting query log with search parameter."""

        mock_response = create_mock_response(
            json_data={"data": [{"question": "ads.example.com"}]}
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_query_log(limit=50, offset=10, search="ads")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        # Verify the URL contains all parameters including search
        url = call_args[0][1]
        assert "limit=50" in url
        assert "offset=10" in url
        assert "search=ads" in url
        assert result == [{"question": "ads.example.com"}]

    @pytest.mark.asyncio
    async def test_get_query_log_custom_limit_offset(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting query log with custom limit and offset."""
        mock_response = create_mock_response(json_data={"data": []})
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_query_log(limit=500, offset=100)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        url = call_args[0][1]
        assert "limit=500" in url
        assert "offset=100" in url
        assert result == []

    @pytest.mark.asyncio
    async def test_get_query_log_with_response_status(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting query log with response_status filter (v0.107.68+)."""
        mock_response = create_mock_response(
            json_data={
                "data": [
                    {"question": "blocked.example.com", "reason": "FilteredBlackList"}
                ]
            }
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_query_log(limit=100, response_status="filtered")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        url = call_args[0][1]
        assert "limit=100" in url
        assert "response_status=filtered" in url
        assert result == [
            {"question": "blocked.example.com", "reason": "FilteredBlackList"}
        ]

    @pytest.mark.asyncio
    async def test_get_query_log_all_params(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting query log with all parameters."""
        mock_response = create_mock_response(
            json_data={"data": [{"question": "ads.example.com"}]}
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.get_query_log(
            limit=50,
            offset=10,
            search="ads",
            response_status="filtered",
        )

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        url = call_args[0][1]
        assert "limit=50" in url
        assert "offset=10" in url
        assert "search=ads" in url
        assert "response_status=filtered" in url

    @pytest.mark.asyncio
    async def test_get_dns_info(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting DNS configuration info."""
        dns_info = {
            "cache_enabled": True,
            "cache_size": 4194304,
            "cache_ttl_min": 0,
            "cache_ttl_max": 0,
            "upstream_dns": ["https://dns.cloudflare.com/dns-query"],
        }
        mock_response = create_mock_response(json_data=dns_info)
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_dns_info()

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/control/dns_info" in call_args[0][1]
        assert result["cache_enabled"] is True
        assert result["cache_size"] == 4194304

    @pytest.mark.asyncio
    async def test_set_dns_config(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting DNS configuration."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_dns_config({"cache_enabled": False, "cache_size": 8388608})

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/dns_config" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_dns_cache_enabled(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test enabling/disabling DNS cache."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_dns_cache_enabled(True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/dns_config" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_dnssec_enabled(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test enabling/disabling DNSSEC."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_dnssec_enabled(True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/dns_config" in call_args[0][1]
        assert call_args[1]["json"] == {"dnssec_enabled": True}

    @pytest.mark.asyncio
    async def test_set_dnssec_disabled(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test disabling DNSSEC."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_dnssec_enabled(False)

        call_args = mock_session.request.call_args
        assert call_args[1]["json"] == {"dnssec_enabled": False}

    @pytest.mark.asyncio
    async def test_set_edns_cs_enabled(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test enabling EDNS Client Subnet."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_edns_cs_enabled(True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/dns_config" in call_args[0][1]
        assert call_args[1]["json"] == {"edns_cs_enabled": True}

    @pytest.mark.asyncio
    async def test_set_edns_cs_disabled(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test disabling EDNS Client Subnet."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_edns_cs_enabled(False)

        call_args = mock_session.request.call_args
        assert call_args[1]["json"] == {"edns_cs_enabled": False}

    @pytest.mark.asyncio
    async def test_set_rate_limit(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting DNS rate limit."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_rate_limit(50)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/dns_config" in call_args[0][1]
        assert call_args[1]["json"] == {"ratelimit": 50}

    @pytest.mark.asyncio
    async def test_set_rate_limit_zero(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test disabling DNS rate limit by setting to 0."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_rate_limit(0)

        call_args = mock_session.request.call_args
        assert call_args[1]["json"] == {"ratelimit": 0}

    @pytest.mark.asyncio
    async def test_set_blocking_mode_refused(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting blocking mode to refused."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_blocking_mode("refused")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/dns_config" in call_args[0][1]
        assert call_args[1]["json"] == {"blocking_mode": "refused"}

    @pytest.mark.asyncio
    async def test_set_blocking_mode_nxdomain(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting blocking mode to nxdomain."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_blocking_mode("nxdomain")

        call_args = mock_session.request.call_args
        assert call_args[1]["json"] == {"blocking_mode": "nxdomain"}

    @pytest.mark.asyncio
    async def test_update_rewrite(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test updating a DNS rewrite rule."""
        mock_response = create_mock_response(json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.update_rewrite(
            old_domain="old.example.com",
            old_answer="1.2.3.4",
            new_domain="new.example.com",
            new_answer="5.6.7.8",
        )

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/control/rewrite/update" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_safesearch_settings(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting SafeSearch settings with per-engine control."""
        response_data = {
            "enabled": True,
            "bing": True,
            "duckduckgo": False,
            "google": True,
            "pixabay": True,
            "yandex": False,
            "youtube": True,
        }
        mock_response = create_mock_response(status=200, json_data=response_data)
        mock_session.request.return_value = MockContextManager(mock_response)

        from custom_components.adguard_home_extended.api.models import (
            SafeSearchSettings,
        )

        settings = await client.get_safesearch_settings()

        assert isinstance(settings, SafeSearchSettings)
        assert settings.enabled is True
        assert settings.google is True
        assert settings.duckduckgo is False
        assert settings.yandex is False

    @pytest.mark.asyncio
    async def test_set_safesearch_settings(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting SafeSearch settings with per-engine control."""
        from custom_components.adguard_home_extended.api.models import (
            SafeSearchSettings,
        )

        mock_response = create_mock_response(status=200, json_data=None)
        mock_response.content_length = 0
        mock_session.request.return_value = MockContextManager(mock_response)

        settings = SafeSearchSettings(
            enabled=True,
            google=True,
            youtube=True,
            bing=False,
            duckduckgo=False,
            pixabay=True,
            yandex=False,
        )
        await client.set_safesearch_settings(settings)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/control/safesearch/settings" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_safesearch_toggle(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test toggling SafeSearch on/off preserves per-engine settings.

        The set_safesearch method should use the non-deprecated settings
        endpoint instead of the deprecated enable/disable endpoints.
        """

        # First call: GET to retrieve current settings
        get_response_data = {
            "enabled": False,
            "bing": True,
            "duckduckgo": False,
            "google": True,
            "pixabay": True,
            "yandex": False,
            "youtube": True,
        }
        mock_get_response = create_mock_response(
            status=200, json_data=get_response_data
        )

        # Second call: PUT to update settings
        mock_put_response = create_mock_response(status=200, json_data=None)
        mock_put_response.content_length = 0

        mock_session.request.side_effect = [
            MockContextManager(mock_get_response),
            MockContextManager(mock_put_response),
        ]

        # Enable safesearch (was disabled)
        await client.set_safesearch(True)

        # Should have made 2 calls: GET then PUT
        assert mock_session.request.call_count == 2

        # First call should be GET for current settings
        first_call = mock_session.request.call_args_list[0]
        assert first_call[0][0] == "GET"
        assert "/control/safesearch/settings" in first_call[0][1]

        # Second call should be PUT with enabled=True and preserved engine settings
        second_call = mock_session.request.call_args_list[1]
        assert second_call[0][0] == "PUT"
        assert "/control/safesearch/settings" in second_call[0][1]

        # Verify the payload has enabled=True and preserves engine settings
        request_json = second_call[1].get("json", {})
        assert request_json["enabled"] is True
        assert request_json["google"] is True  # Preserved
        assert request_json["duckduckgo"] is False  # Preserved

    @pytest.mark.asyncio
    async def test_get_stats_config(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting stats configuration (v0.107.30+)."""
        response_data = {
            "enabled": True,
            "interval": 86400000,
            "ignored": ["example.com"],
        }
        mock_response = create_mock_response(status=200, json_data=response_data)
        mock_session.request.return_value = MockContextManager(mock_response)

        config = await client.get_stats_config()

        assert config["enabled"] is True
        assert config["interval"] == 86400000
        assert "example.com" in config["ignored"]
        call_args = mock_session.request.call_args
        assert "/control/stats/config" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_stats_config(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting stats configuration."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_stats_config(enabled=True, interval=3600000)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/control/stats/config/update" in call_args[0][1]
        assert call_args[1]["json"]["enabled"] is True
        assert call_args[1]["json"]["interval"] == 3600000

    @pytest.mark.asyncio
    async def test_get_querylog_config(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting query log configuration (v0.107.30+)."""
        response_data = {
            "enabled": True,
            "anonymize_client_ip": False,
            "interval": 2592000000,
            "ignored": [],
        }
        mock_response = create_mock_response(status=200, json_data=response_data)
        mock_session.request.return_value = MockContextManager(mock_response)

        config = await client.get_querylog_config()

        assert config["enabled"] is True
        assert config["anonymize_client_ip"] is False
        call_args = mock_session.request.call_args
        assert "/control/querylog/config" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_querylog_config(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting query log configuration."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_querylog_config(enabled=True, anonymize_client_ip=True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/control/querylog/config/update" in call_args[0][1]
        assert call_args[1]["json"]["enabled"] is True
        assert call_args[1]["json"]["anonymize_client_ip"] is True

    @pytest.mark.asyncio
    async def test_get_blocked_services_v2(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting blocked services with schedule (v0.107.56+)."""
        response_data = {
            "ids": ["facebook", "tiktok"],
            "schedule": {
                "time_zone": "America/New_York",
                "mon": {"start": 0, "end": 86399999},
            },
        }
        mock_response = create_mock_response(status=200, json_data=response_data)
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_blocked_services_v2()

        assert result["ids"] == ["facebook", "tiktok"]
        assert "schedule" in result
        call_args = mock_session.request.call_args
        assert "/control/blocked_services/get" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_blocked_services_v2(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting blocked services with schedule (v0.107.56+)."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        schedule = {"time_zone": "UTC", "mon": {"start": 0, "end": 43200000}}
        await client.set_blocked_services_v2(["facebook"], schedule=schedule)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/control/blocked_services/update" in call_args[0][1]
        assert call_args[1]["json"]["ids"] == ["facebook"]
        assert "schedule" in call_args[1]["json"]

    @pytest.mark.asyncio
    async def test_search_clients(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test searching for clients (v0.107.56+)."""
        response_data = [
            {
                "name": "Test Client",
                "ids": ["192.168.1.100"],
                "use_global_settings": True,
            }
        ]
        mock_response = create_mock_response(status=200, json_data=response_data)
        mock_session.request.return_value = MockContextManager(mock_response)

        results = await client.search_clients(["192.168.1.100"])

        assert len(results) == 1
        assert results[0]["name"] == "Test Client"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/clients/search" in call_args[0][1]
        assert call_args[1]["json"]["clients"] == [{"id": "192.168.1.100"}]

    @pytest.mark.asyncio
    async def test_set_rewrite_enabled(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test enabling/disabling a DNS rewrite rule (v0.107.68+)."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_rewrite_enabled("ads.example.com", "0.0.0.0", False)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/control/rewrite/update" in call_args[0][1]
        json_data = call_args[1]["json"]
        assert json_data["target"]["domain"] == "ads.example.com"
        assert json_data["target"]["answer"] == "0.0.0.0"
        assert json_data["update"]["domain"] == "ads.example.com"
        assert json_data["update"]["answer"] == "0.0.0.0"
        assert json_data["update"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_update_rewrite_with_enabled(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test updating a rewrite with enabled field."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.update_rewrite(
            old_domain="old.example.com",
            old_answer="1.2.3.4",
            new_domain="new.example.com",
            new_answer="5.6.7.8",
            enabled=True,
        )

        call_args = mock_session.request.call_args
        json_data = call_args[1]["json"]
        assert json_data["update"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_check_host_basic(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test checking if a domain would be filtered."""
        mock_response = create_mock_response(
            json_data={
                "reason": "FilteredBlackList",
                "filter_id": 1,
                "rule": "||doubleclick.net^",
                "rules": [{"filter_list_id": 1, "text": "||doubleclick.net^"}],
            }
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.check_host(name="doubleclick.net")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/control/filtering/check_host" in call_args[0][1]
        assert "name=doubleclick.net" in call_args[0][1]
        assert result["reason"] == "FilteredBlackList"
        assert result["rule"] == "||doubleclick.net^"

    @pytest.mark.asyncio
    async def test_check_host_with_client(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test checking domain filtering for a specific client (v0.107.58+)."""
        mock_response = create_mock_response(
            json_data={
                "reason": "NotFilteredAllowList",
                "rules": [],
            }
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.check_host(
            name="example.com",
            client="192.168.1.100",
        )

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        url = call_args[0][1]
        assert "name=example.com" in url
        assert "client=192.168.1.100" in url
        assert result["reason"] == "NotFilteredAllowList"

    @pytest.mark.asyncio
    async def test_check_host_with_qtype(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test checking domain filtering with query type (v0.107.58+)."""
        mock_response = create_mock_response(
            json_data={
                "reason": "NotFilteredNotFound",
                "rules": [],
            }
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.check_host(
            name="example.com",
            qtype="AAAA",
        )

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        url = call_args[0][1]
        assert "name=example.com" in url
        assert "qtype=AAAA" in url
        assert result["reason"] == "NotFilteredNotFound"

    @pytest.mark.asyncio
    async def test_check_host_with_all_params(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test check_host with domain, client, and qtype parameters."""
        mock_response = create_mock_response(
            json_data={
                "reason": "FilteredBlockedService",
                "service_name": "youtube",
            }
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.check_host(
            name="youtube.com",
            client="kids-tablet",
            qtype="A",
        )

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        url = call_args[0][1]
        assert "name=youtube.com" in url
        assert "client=kids-tablet" in url
        assert "qtype=A" in url
        assert result["reason"] == "FilteredBlockedService"
        assert result["service_name"] == "youtube"

    @pytest.mark.asyncio
    async def test_check_host_returns_empty_dict_on_non_dict(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test that check_host returns empty dict if API returns non-dict."""
        mock_response = create_mock_response(json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.check_host(name="example.com")

        assert result == {}

    @pytest.mark.asyncio
    async def test_search_client_found(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test searching for a single client that exists."""
        mock_response = create_mock_response(
            json_data=[{"name": "Test Client", "ids": ["192.168.1.100"]}]
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.search_client("192.168.1.100")

        assert result is not None
        assert result["name"] == "Test Client"
        call_args = mock_session.request.call_args
        assert call_args[1]["json"]["clients"] == [{"id": "192.168.1.100"}]

    @pytest.mark.asyncio
    async def test_search_client_not_found(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test searching for a single client that doesn't exist."""
        mock_response = create_mock_response(json_data=[])
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.search_client("192.168.1.200")

        assert result is None

    @pytest.mark.asyncio
    async def test_clear_query_log(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test clearing query log."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.clear_query_log()

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/querylog_clear" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_reset_stats(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test resetting statistics."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.reset_stats()

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/control/stats_reset" in call_args[0][1]


class TestApiClientAdditionalMethods:
    """Additional tests for API client methods not yet covered."""

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

    @pytest.mark.asyncio
    async def test_client_response_error_401(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test handling of 401 ClientResponseError."""
        from aiohttp import ClientResponseError

        # Simulate ClientResponseError from raise_for_status
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status.side_effect = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=401,
            message="Unauthorized",
        )

        mock_session.request.return_value = MockContextManager(mock_response)

        with pytest.raises(AdGuardHomeAuthError, match="Authentication failed"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_client_response_error_403(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test handling of 403 ClientResponseError."""
        from aiohttp import ClientResponseError

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status.side_effect = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=403,
            message="Forbidden",
        )

        mock_session.request.return_value = MockContextManager(mock_response)

        with pytest.raises(AdGuardHomeAuthError, match="Authentication failed"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_client_response_error_other(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test handling of non-auth ClientResponseError."""
        from aiohttp import ClientResponseError

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status.side_effect = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=500,
            message="Internal Server Error",
        )

        mock_session.request.return_value = MockContextManager(mock_response)

        with pytest.raises(AdGuardHomeConnectionError, match="Request failed"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_set_safebrowsing_enable(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test enabling safe browsing."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_safebrowsing(True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/safebrowsing/enable" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_safebrowsing_disable(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test disabling safe browsing."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_safebrowsing(False)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/safebrowsing/disable" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_parental_enable(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test enabling parental control."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_parental(True)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/parental/enable" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_parental_disable(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test disabling parental control."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_parental(False)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/parental/disable" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_add_filter_url(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test adding a filter URL."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.add_filter_url("AdBlock", "https://example.com/filter.txt")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/filtering/add_url" in call_args[0][1]
        assert call_args[1]["json"]["name"] == "AdBlock"
        assert call_args[1]["json"]["url"] == "https://example.com/filter.txt"

    @pytest.mark.asyncio
    async def test_remove_filter_url(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test removing a filter URL."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.remove_filter_url("https://example.com/filter.txt")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/filtering/remove_url" in call_args[0][1]
        assert call_args[1]["json"]["url"] == "https://example.com/filter.txt"

    @pytest.mark.asyncio
    async def test_refresh_filters(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test refreshing filters."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.refresh_filters()

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/filtering/refresh" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_check_host_basic(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test checking a host."""
        mock_response = create_mock_response(
            status=200, json_data={"reason": "FilteredBlackList", "filtered": True}
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.check_host("ads.example.com")

        assert result["filtered"] is True
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/filtering/check_host" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_clients(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting all clients."""
        mock_response = create_mock_response(
            status=200,
            json_data={
                "clients": [
                    {"name": "Client1", "ids": ["192.168.1.100"]},
                    {"name": "Client2", "ids": ["192.168.1.101"]},
                ]
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_clients()

        assert len(result) == 2
        assert result[0].name == "Client1"

    @pytest.mark.asyncio
    async def test_add_client(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test adding a client."""
        from custom_components.adguard_home_extended.api.models import (
            AdGuardHomeClient as ClientConfig,
        )

        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        new_client = ClientConfig(
            name="New Client",
            ids=["192.168.1.200"],
            use_global_settings=True,
            filtering_enabled=True,
            parental_enabled=False,
            safebrowsing_enabled=False,
            safesearch_enabled=False,
            use_global_blocked_services=True,
            blocked_services=[],
            tags=[],
        )
        await client.add_client(new_client)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/clients/add" in call_args[0][1]
        assert call_args[1]["json"]["name"] == "New Client"

    @pytest.mark.asyncio
    async def test_update_client(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test updating a client."""
        from custom_components.adguard_home_extended.api.models import (
            AdGuardHomeClient as ClientConfig,
        )

        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        updated_client = ClientConfig(
            name="Updated Client",
            ids=["192.168.1.200"],
            use_global_settings=True,
            filtering_enabled=True,
            parental_enabled=False,
            safebrowsing_enabled=False,
            safesearch_enabled=False,
            use_global_blocked_services=True,
            blocked_services=[],
            tags=[],
        )
        await client.update_client("Old Client", updated_client)

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/clients/update" in call_args[0][1]
        assert call_args[1]["json"]["name"] == "Old Client"

    @pytest.mark.asyncio
    async def test_delete_client(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test deleting a client."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.delete_client("Client to Delete")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/clients/delete" in call_args[0][1]
        assert call_args[1]["json"]["name"] == "Client to Delete"

    @pytest.mark.asyncio
    async def test_get_all_blocked_services(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting all available blocked services.

        Per OpenAPI schema, BlockedService requires: icon_svg, id, name, rules.
        Optional: group_id.
        """
        mock_response = create_mock_response(
            status=200,
            json_data={
                "blocked_services": [
                    {
                        "id": "facebook",
                        "name": "Facebook",
                        "icon_svg": "<svg></svg>",
                        "rules": ["||facebook.com^", "||fbcdn.net^"],
                        "group_id": "social",
                    },
                    {
                        "id": "twitter",
                        "name": "Twitter",
                        "icon_svg": "<svg></svg>",
                        "rules": ["||twitter.com^", "||x.com^"],
                        "group_id": "social",
                    },
                ],
                "groups": [{"id": "social"}],
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_all_blocked_services()

        assert len(result) == 2
        assert result[0].id == "facebook"
        assert result[0].rules == ["||facebook.com^", "||fbcdn.net^"]
        assert result[0].group_id == "social"

    @pytest.mark.asyncio
    async def test_get_blocked_services_old_format(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting blocked services with old list format."""
        # Old format returns just a list of IDs
        mock_response = create_mock_response(
            status=200, json_data=["facebook", "twitter"]
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_blocked_services()

        # Should return the list directly
        assert result == ["facebook", "twitter"]

    @pytest.mark.asyncio
    async def test_get_blocked_services_new_format(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting blocked services with new dict format."""
        mock_response = create_mock_response(
            status=200,
            json_data={"ids": ["facebook"], "schedule": {"mon": {"start": 0}}},
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_blocked_services()

        # Should return just the ids list
        assert result == ["facebook"]

    @pytest.mark.asyncio
    async def test_get_blocked_services_v2_old_format(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test get_blocked_services_v2 with old list format."""
        mock_response = create_mock_response(
            status=200, json_data=["facebook", "twitter"]
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_blocked_services_v2()

        assert result["ids"] == ["facebook", "twitter"]
        assert result["schedule"] == {}

    @pytest.mark.asyncio
    async def test_get_dhcp_status(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting DHCP status."""
        mock_response = create_mock_response(
            status=200,
            json_data={
                "enabled": True,
                "interface_name": "eth0",
                "leases": [],
                "static_leases": [],
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_dhcp_status()

        assert result.enabled is True
        assert result.interface_name == "eth0"

    @pytest.mark.asyncio
    async def test_get_dns_info(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting DNS info."""
        mock_response = create_mock_response(
            status=200,
            json_data={
                "protection_enabled": True,
                "upstream_dns": ["8.8.8.8"],
                "cache_size": 4194304,
            },
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_dns_info()

        assert result["protection_enabled"] is True
        assert result["cache_size"] == 4194304

    @pytest.mark.asyncio
    async def test_set_stats_config_with_values(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting stats config with all parameters."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_stats_config(enabled=True, interval=7, ignored=["192.168.1.1"])

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[1]["json"]["enabled"] is True
        assert call_args[1]["json"]["interval"] == 7
        assert call_args[1]["json"]["ignored"] == ["192.168.1.1"]

    @pytest.mark.asyncio
    async def test_set_stats_config_empty(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test set_stats_config does nothing when no params provided."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_stats_config()

        # Should not make any request when no config changes
        mock_session.request.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_querylog_config_with_values(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting querylog config with all parameters."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_querylog_config(
            enabled=True,
            anonymize_client_ip=True,
            interval=720,
            ignored=["192.168.1.1"],
        )

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[1]["json"]["enabled"] is True
        assert call_args[1]["json"]["anonymize_client_ip"] is True
        assert call_args[1]["json"]["interval"] == 720

    @pytest.mark.asyncio
    async def test_set_querylog_config_empty(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test set_querylog_config does nothing when no params provided."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_querylog_config()

        # Should not make any request when no config changes
        mock_session.request.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_rewrites(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting DNS rewrites."""
        mock_response = create_mock_response(
            status=200,
            json_data=[
                {"domain": "ads.example.com", "answer": "0.0.0.0"},
                {"domain": "local.test", "answer": "192.168.1.50"},
            ],
        )
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_rewrites()

        assert len(result) == 2
        assert result[0].domain == "ads.example.com"

    @pytest.mark.asyncio
    async def test_get_rewrites_empty(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test getting DNS rewrites when list is empty/None."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        result = await client.get_rewrites()

        assert result == []

    @pytest.mark.asyncio
    async def test_add_rewrite(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test adding a DNS rewrite."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.add_rewrite("ads.example.com", "0.0.0.0")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/rewrite/add" in call_args[0][1]
        assert call_args[1]["json"]["domain"] == "ads.example.com"
        assert call_args[1]["json"]["answer"] == "0.0.0.0"

    @pytest.mark.asyncio
    async def test_delete_rewrite(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test deleting a DNS rewrite."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.delete_rewrite("ads.example.com", "0.0.0.0")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/rewrite/delete" in call_args[0][1]
        assert call_args[1]["json"]["domain"] == "ads.example.com"

    @pytest.mark.asyncio
    async def test_set_blocked_services(
        self, client: AdGuardHomeClient, mock_session: MagicMock
    ) -> None:
        """Test setting blocked services."""
        mock_response = create_mock_response(status=200, json_data=None)
        mock_session.request.return_value = MockContextManager(mock_response)

        await client.set_blocked_services(["facebook", "twitter"])

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert "/control/blocked_services/set" in call_args[0][1]
