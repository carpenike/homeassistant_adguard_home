"""Config flow for AdGuard Home Extended integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import (
    AdGuardHomeAuthError,
    AdGuardHomeClient,
    AdGuardHomeConnectionError,
)
from .const import (
    CONF_ATTR_LIST_LIMIT,
    CONF_ATTR_TOP_ITEMS_LIMIT,
    CONF_QUERY_LOG_LIMIT,
    DEFAULT_ATTR_LIST_LIMIT,
    DEFAULT_ATTR_TOP_ITEMS_LIMIT,
    DEFAULT_PORT,
    DEFAULT_QUERY_LOG_LIMIT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
        vol.Required(CONF_SSL, default=DEFAULT_SSL): bool,
        vol.Required(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


class AdGuardHomeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AdGuard Home Extended."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry,
    ) -> AdGuardHomeOptionsFlow:
        """Get the options flow for this handler."""
        return AdGuardHomeOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

            # Test connection
            session = async_get_clientsession(
                self.hass, verify_ssl=user_input.get(CONF_VERIFY_SSL, True)
            )

            client = AdGuardHomeClient(
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
                username=user_input.get(CONF_USERNAME),
                password=user_input.get(CONF_PASSWORD),
                use_ssl=user_input.get(CONF_SSL, False),
                session=session,
            )

            try:
                status = await client.get_status()
            except AdGuardHomeAuthError:
                errors["base"] = "invalid_auth"
            except AdGuardHomeConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID based on host and port to prevent duplicates
                unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # Create a title from the host
                title = f"AdGuard Home ({user_input[CONF_HOST]})"
                if status.version:
                    title = f"AdGuard Home {status.version} ({user_input[CONF_HOST]})"

                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthorization flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauthorization confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            reauth_entry = self._get_reauth_entry()

            session = async_get_clientsession(
                self.hass,
                verify_ssl=reauth_entry.data.get(CONF_VERIFY_SSL, True),
            )

            client = AdGuardHomeClient(
                host=reauth_entry.data[CONF_HOST],
                port=reauth_entry.data[CONF_PORT],
                username=user_input.get(CONF_USERNAME),
                password=user_input.get(CONF_PASSWORD),
                use_ssl=reauth_entry.data.get(CONF_SSL, False),
                session=session,
            )

            try:
                await client.get_status()
            except AdGuardHomeAuthError:
                errors["base"] = "invalid_auth"
            except AdGuardHomeConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_USERNAME: user_input.get(CONF_USERNAME),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_USERNAME): str,
                    vol.Optional(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )


class AdGuardHomeOptionsFlow(OptionsFlow):
    """Handle options flow for AdGuard Home Extended."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values from options, falling back to defaults
        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_query_log_limit = self.config_entry.options.get(
            CONF_QUERY_LOG_LIMIT, DEFAULT_QUERY_LOG_LIMIT
        )
        current_attr_top_items_limit = self.config_entry.options.get(
            CONF_ATTR_TOP_ITEMS_LIMIT, DEFAULT_ATTR_TOP_ITEMS_LIMIT
        )
        current_attr_list_limit = self.config_entry.options.get(
            CONF_ATTR_LIST_LIMIT, DEFAULT_ATTR_LIST_LIMIT
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current_scan_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                    vol.Required(
                        CONF_QUERY_LOG_LIMIT,
                        default=current_query_log_limit,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10000)),
                    vol.Required(
                        CONF_ATTR_TOP_ITEMS_LIMIT,
                        default=current_attr_top_items_limit,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                    vol.Required(
                        CONF_ATTR_LIST_LIMIT,
                        default=current_attr_list_limit,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                }
            ),
        )
