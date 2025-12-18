"""Tests for the AdGuard Home Extended config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.adguard_home_extended.api.models import AdGuardHomeStatus
from custom_components.adguard_home_extended.config_flow import (
    AdGuardHomeConfigFlow,
    AdGuardHomeOptionsFlow,
)
from custom_components.adguard_home_extended.const import (
    CONF_ATTR_LIST_LIMIT,
    CONF_ATTR_TOP_ITEMS_LIMIT,
    CONF_QUERY_LOG_LIMIT,
    DEFAULT_ATTR_LIST_LIMIT,
    DEFAULT_ATTR_TOP_ITEMS_LIMIT,
    DEFAULT_QUERY_LOG_LIMIT,
    DEFAULT_SCAN_INTERVAL,
)


class TestConfigFlow:
    """Tests for the config flow."""

    @pytest.mark.asyncio
    async def test_form_user_success(self, hass: HomeAssistant) -> None:
        """Test successful user form submission."""
        # Use proper flow initialization through hass for correct context handling
        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_status = AdGuardHomeStatus(
                protection_enabled=True,
                running=True,
                version="0.107.43",
            )
            mock_client.get_status = AsyncMock(return_value=mock_status)
            mock_client_class.return_value = mock_client

            # Initialize flow properly
            flow = AdGuardHomeConfigFlow()
            flow.hass = hass
            flow.context = {"source": "user"}

            # Get the form first
            result = await flow.async_step_user()
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "user"

            result = await flow.async_step_user(
                user_input={
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "password",
                    "ssl": False,
                    "verify_ssl": True,
                }
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert "192.168.1.1" in result["title"]
            assert result["data"]["host"] == "192.168.1.1"
            assert result["data"]["port"] == 3000

    @pytest.mark.asyncio
    async def test_form_user_sets_unique_id(self, hass: HomeAssistant) -> None:
        """Test that successful submission sets a unique ID."""
        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_status = AdGuardHomeStatus(
                protection_enabled=True,
                running=True,
                version="0.107.43",
            )
            mock_client.get_status = AsyncMock(return_value=mock_status)
            mock_client_class.return_value = mock_client

            flow = AdGuardHomeConfigFlow()
            flow.hass = hass
            flow.context = {"source": "user"}

            result = await flow.async_step_user(
                user_input={
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "password",
                    "ssl": False,
                    "verify_ssl": True,
                }
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            # Verify unique_id was set (host:port format)
            assert flow.unique_id == "192.168.1.1:3000"

    @pytest.mark.asyncio
    async def test_form_user_already_configured(self, hass: HomeAssistant) -> None:
        """Test that duplicate entries are aborted."""
        from homeassistant.data_entry_flow import AbortFlow

        # Create a mock existing entry with same unique_id
        mock_entry = MagicMock()
        mock_entry.unique_id = "192.168.1.1:3000"

        # Register the existing entry
        hass.config_entries = MagicMock()
        hass.config_entries._entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_status = AdGuardHomeStatus(
                protection_enabled=True,
                running=True,
                version="0.107.43",
            )
            mock_client.get_status = AsyncMock(return_value=mock_status)
            mock_client_class.return_value = mock_client

            flow = AdGuardHomeConfigFlow()
            flow.hass = hass
            flow.context = {"source": "user"}

            # Mock the _abort_if_unique_id_configured to actually abort
            def abort_if_configured(*args, **kwargs):
                if flow.unique_id == mock_entry.unique_id:
                    raise AbortFlow("already_configured")

            flow._abort_if_unique_id_configured = abort_if_configured

            # The AbortFlow exception should be raised
            with pytest.raises(AbortFlow) as exc_info:
                await flow.async_step_user(
                    user_input={
                        "host": "192.168.1.1",
                        "port": 3000,
                        "username": "admin",
                        "password": "password",
                        "ssl": False,
                        "verify_ssl": True,
                    }
                )

            assert exc_info.value.reason == "already_configured"

    @pytest.mark.asyncio
    async def test_form_user_cannot_connect(self, hass: HomeAssistant) -> None:
        """Test connection failure."""
        from custom_components.adguard_home_extended.api.client import (
            AdGuardHomeConnectionError,
        )

        flow = AdGuardHomeConfigFlow()
        flow.hass = hass

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_status = AsyncMock(
                side_effect=AdGuardHomeConnectionError("Connection failed")
            )
            mock_client_class.return_value = mock_client

            result = await flow.async_step_user(
                user_input={
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "wrong",
                    "ssl": False,
                    "verify_ssl": True,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_form_user_invalid_auth(self, hass: HomeAssistant) -> None:
        """Test invalid authentication."""
        from custom_components.adguard_home_extended.api.client import (
            AdGuardHomeAuthError,
        )

        flow = AdGuardHomeConfigFlow()
        flow.hass = hass

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_status = AsyncMock(
                side_effect=AdGuardHomeAuthError("Invalid credentials")
            )
            mock_client_class.return_value = mock_client

            result = await flow.async_step_user(
                user_input={
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "wrong",
                    "ssl": False,
                    "verify_ssl": True,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}


class TestOptionsFlow:
    """Tests for the options flow."""

    @pytest.mark.asyncio
    async def test_options_flow_init_shows_form(self, hass: HomeAssistant) -> None:
        """Test options flow shows form with current values."""
        # Create a mock config entry
        mock_entry = MagicMock()
        mock_entry.options = {CONF_SCAN_INTERVAL: 60}

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"
        # Check that the schema has the scan_interval field
        assert CONF_SCAN_INTERVAL in str(result["data_schema"].schema)

    @pytest.mark.asyncio
    async def test_options_flow_init_default_value(self, hass: HomeAssistant) -> None:
        """Test options flow uses default when no options set."""
        # Create a mock config entry with no options
        mock_entry = MagicMock()
        mock_entry.options = {}

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        # The default value should be DEFAULT_SCAN_INTERVAL
        schema = result["data_schema"].schema
        scan_interval_key = next(k for k in schema if k.schema == CONF_SCAN_INTERVAL)
        assert scan_interval_key.default() == DEFAULT_SCAN_INTERVAL

    @pytest.mark.asyncio
    async def test_options_flow_submit(self, hass: HomeAssistant) -> None:
        """Test options flow saves new values."""
        mock_entry = MagicMock()
        mock_entry.options = {CONF_SCAN_INTERVAL: 30}

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init(
            user_input={
                CONF_SCAN_INTERVAL: 120,
                CONF_QUERY_LOG_LIMIT: 200,
                CONF_ATTR_TOP_ITEMS_LIMIT: 15,
                CONF_ATTR_LIST_LIMIT: 25,
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"] == {
            CONF_SCAN_INTERVAL: 120,
            CONF_QUERY_LOG_LIMIT: 200,
            CONF_ATTR_TOP_ITEMS_LIMIT: 15,
            CONF_ATTR_LIST_LIMIT: 25,
        }

    @pytest.mark.asyncio
    async def test_options_flow_query_log_limit_default(
        self, hass: HomeAssistant
    ) -> None:
        """Test options flow shows default query log limit."""
        mock_entry = MagicMock()
        mock_entry.options = {}  # No options set, should use defaults

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        # Check that the schema has the query_log_limit field with correct default
        schema = result["data_schema"].schema
        query_log_key = next(k for k in schema if k.schema == CONF_QUERY_LOG_LIMIT)
        assert query_log_key.default() == DEFAULT_QUERY_LOG_LIMIT

    @pytest.mark.asyncio
    async def test_options_flow_attr_limits_default(self, hass: HomeAssistant) -> None:
        """Test options flow shows default attribute limits."""
        mock_entry = MagicMock()
        mock_entry.options = {}  # No options set, should use defaults

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        schema = result["data_schema"].schema

        # Check top items limit default
        top_items_key = next(k for k in schema if k.schema == CONF_ATTR_TOP_ITEMS_LIMIT)
        assert top_items_key.default() == DEFAULT_ATTR_TOP_ITEMS_LIMIT

        # Check list limit default
        list_limit_key = next(k for k in schema if k.schema == CONF_ATTR_LIST_LIMIT)
        assert list_limit_key.default() == DEFAULT_ATTR_LIST_LIMIT

    @pytest.mark.asyncio
    async def test_options_flow_preserves_existing_query_log_limit(
        self, hass: HomeAssistant
    ) -> None:
        """Test options flow preserves existing query log limit value."""
        mock_entry = MagicMock()
        mock_entry.options = {CONF_SCAN_INTERVAL: 60, CONF_QUERY_LOG_LIMIT: 500}

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        schema = result["data_schema"].schema
        query_log_key = next(k for k in schema if k.schema == CONF_QUERY_LOG_LIMIT)
        assert query_log_key.default() == 500

    def test_config_flow_has_options_flow_handler(self) -> None:
        """Test that config flow has options flow handler."""
        mock_entry = MagicMock()

        # The @staticmethod decorator means we call it on the class, not instance
        options_flow = AdGuardHomeConfigFlow.async_get_options_flow(mock_entry)

        assert isinstance(options_flow, AdGuardHomeOptionsFlow)


class TestReauthFlow:
    """Tests for the reauth flow."""

    @pytest.fixture
    def mock_reauth_entry(self) -> MagicMock:
        """Create a mock config entry for reauth."""
        entry = MagicMock()
        entry.data = {
            "host": "192.168.1.1",
            "port": 3000,
            "ssl": False,
            "verify_ssl": True,
            "username": "old_user",
            "password": "old_pass",
        }
        entry.unique_id = "192.168.1.1:3000"
        return entry

    @pytest.mark.asyncio
    async def test_reauth_step_triggers_confirm(self, hass: HomeAssistant) -> None:
        """Test reauth step calls reauth_confirm."""
        flow = AdGuardHomeConfigFlow()
        flow.hass = hass
        flow.context = {"source": "reauth"}

        # async_step_reauth should call async_step_reauth_confirm
        with patch.object(
            flow, "async_step_reauth_confirm", return_value={"type": "form"}
        ) as mock_confirm:
            await flow.async_step_reauth({"host": "192.168.1.1"})
            mock_confirm.assert_called_once()

    @pytest.mark.asyncio
    async def test_reauth_confirm_shows_form(
        self, hass: HomeAssistant, mock_reauth_entry: MagicMock
    ) -> None:
        """Test reauth confirm shows form with no input."""
        flow = AdGuardHomeConfigFlow()
        flow.hass = hass
        flow.context = {"source": "reauth"}
        flow._get_reauth_entry = MagicMock(return_value=mock_reauth_entry)

        result = await flow.async_step_reauth_confirm()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_reauth_confirm_success(
        self, hass: HomeAssistant, mock_reauth_entry: MagicMock
    ) -> None:
        """Test successful reauth updates credentials."""
        from custom_components.adguard_home_extended.api.models import AdGuardHomeStatus

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_status = AdGuardHomeStatus(
                protection_enabled=True, running=True, version="0.107.43"
            )
            mock_client.get_status = AsyncMock(return_value=mock_status)
            mock_client_class.return_value = mock_client

            flow = AdGuardHomeConfigFlow()
            flow.hass = hass
            flow.context = {"source": "reauth"}
            flow._get_reauth_entry = MagicMock(return_value=mock_reauth_entry)

            # Mock async_update_reload_and_abort
            flow.async_update_reload_and_abort = MagicMock(
                return_value={"type": "abort", "reason": "reauth_successful"}
            )

            result = await flow.async_step_reauth_confirm(
                user_input={
                    "username": "new_user",
                    "password": "new_pass",
                }
            )

            assert result["type"] == "abort"
            assert result["reason"] == "reauth_successful"
            flow.async_update_reload_and_abort.assert_called_once_with(
                mock_reauth_entry,
                data_updates={
                    "username": "new_user",
                    "password": "new_pass",
                },
            )

    @pytest.mark.asyncio
    async def test_reauth_confirm_invalid_auth(
        self, hass: HomeAssistant, mock_reauth_entry: MagicMock
    ) -> None:
        """Test reauth with invalid credentials."""
        from custom_components.adguard_home_extended.api.client import (
            AdGuardHomeAuthError,
        )

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_status = AsyncMock(
                side_effect=AdGuardHomeAuthError("Invalid credentials")
            )
            mock_client_class.return_value = mock_client

            flow = AdGuardHomeConfigFlow()
            flow.hass = hass
            flow.context = {"source": "reauth"}
            flow._get_reauth_entry = MagicMock(return_value=mock_reauth_entry)

            result = await flow.async_step_reauth_confirm(
                user_input={
                    "username": "wrong_user",
                    "password": "wrong_pass",
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}

    @pytest.mark.asyncio
    async def test_reauth_confirm_connection_error(
        self, hass: HomeAssistant, mock_reauth_entry: MagicMock
    ) -> None:
        """Test reauth with connection error."""
        from custom_components.adguard_home_extended.api.client import (
            AdGuardHomeConnectionError,
        )

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_status = AsyncMock(
                side_effect=AdGuardHomeConnectionError("Connection failed")
            )
            mock_client_class.return_value = mock_client

            flow = AdGuardHomeConfigFlow()
            flow.hass = hass
            flow.context = {"source": "reauth"}
            flow._get_reauth_entry = MagicMock(return_value=mock_reauth_entry)

            result = await flow.async_step_reauth_confirm(
                user_input={
                    "username": "user",
                    "password": "pass",
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_reauth_confirm_unknown_error(
        self, hass: HomeAssistant, mock_reauth_entry: MagicMock
    ) -> None:
        """Test reauth with unexpected error."""
        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_status = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_client_class.return_value = mock_client

            flow = AdGuardHomeConfigFlow()
            flow.hass = hass
            flow.context = {"source": "reauth"}
            flow._get_reauth_entry = MagicMock(return_value=mock_reauth_entry)

            result = await flow.async_step_reauth_confirm(
                user_input={
                    "username": "user",
                    "password": "pass",
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "unknown"}


# Note: already_configured and reauth tests require full integration setup
# These should be tested via integration tests with a real Home Assistant instance
