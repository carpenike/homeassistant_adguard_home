"""Config flow for AdGuard Home Extended integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
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

if TYPE_CHECKING:  # pragma: no cover
    from homeassistant.components.dhcp import DhcpServiceInfo

_LOGGER = logging.getLogger(__name__)


def _normalize_host_input(host: str) -> tuple[str, bool | None, int | None]:
    """Normalize host input by stripping scheme and extracting SSL/port.

    Args:
        host: The host input which may include http:// or https:// scheme,
              and optionally a port number (e.g., "https://adguard:8443")

    Returns:
        Tuple of (normalized_host, ssl_from_scheme, port_from_url) where:
        - ssl_from_scheme is True for https, False for http, or None if no scheme
        - port_from_url is the port if specified in URL, or suggested default
          (443 for https, 80 for http), or None if no scheme was provided
    """
    host = host.strip()
    ssl_from_scheme: bool | None = None
    port_from_url: int | None = None

    if host.startswith("https://"):
        host = host[8:]  # Remove "https://"
        ssl_from_scheme = True
        port_from_url = 443  # Default HTTPS port
    elif host.startswith("http://"):
        host = host[7:]  # Remove "http://"
        ssl_from_scheme = False
        port_from_url = 80  # Default HTTP port

    # Strip trailing slashes and paths
    host = host.rstrip("/")
    if "/" in host:
        host = host.split("/")[0]

    # Extract port if specified in host (e.g., "adguard:8443")
    if ":" in host:
        host_part, port_str = host.rsplit(":", 1)
        try:
            port_from_url = int(port_str)
            host = host_part
        except ValueError:
            # Not a valid port, keep as-is (might be IPv6 without brackets)
            pass

    return host, ssl_from_scheme, port_from_url


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

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_port: int = DEFAULT_PORT

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> AdGuardHomeOptionsFlow:
        """Get the options flow for this handler."""
        return AdGuardHomeOptionsFlow()

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle DHCP discovery.

        This is called when registered_devices is true and an already-configured
        device's IP address changes on the network.
        """
        _LOGGER.debug("DHCP discovery received: %s", discovery_info)

        # Store discovered host for later use
        self._discovered_host = discovery_info.ip

        # Check if we have any entries that match this IP or need updating
        # For registered_devices, we update existing entries with new IP
        for entry in self._async_current_entries():
            if entry.data.get(CONF_HOST) == discovery_info.ip:
                # Already configured with this IP
                return self.async_abort(reason="already_configured")

        # Set context to indicate this came from discovery
        self.context["title_placeholders"] = {"host": discovery_info.ip}

        # Show confirmation form to the user
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user confirmation of discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # User has confirmed, try to connect
            # Use user-provided host (user can edit), fallback to discovered host
            raw_host = user_input.get(CONF_HOST, self._discovered_host or "")
            host, ssl_from_scheme, port_from_url = _normalize_host_input(raw_host)
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # If user provided a scheme, use it to set SSL
            use_ssl = user_input.get(CONF_SSL, False)
            if ssl_from_scheme is not None:
                use_ssl = ssl_from_scheme

            # If port was extracted from URL or scheme implies a port, use it
            if port_from_url is not None and port == DEFAULT_PORT:
                port = port_from_url

            # Check if already configured
            self._async_abort_entries_match({CONF_HOST: host})

            session = async_get_clientsession(
                self.hass, verify_ssl=user_input.get(CONF_VERIFY_SSL, True)
            )

            client = AdGuardHomeClient(
                host=host,
                port=port,
                username=user_input.get(CONF_USERNAME),
                password=user_input.get(CONF_PASSWORD),
                use_ssl=use_ssl,
                session=session,
            )

            try:
                status = await client.get_status()
            except AdGuardHomeAuthError:
                errors["base"] = "invalid_auth"
            except AdGuardHomeConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during discovery confirmation")
                errors["base"] = "unknown"
            else:
                # Set unique ID based on host and port
                unique_id = f"{host}:{port}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})

                # Create the entry
                title = f"AdGuard Home ({host})"
                if status.version:
                    title = f"AdGuard Home {status.version} ({host})"

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_USERNAME: user_input.get(CONF_USERNAME),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                        CONF_SSL: use_ssl,
                        CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, True),
                    },
                )

        # Show form for user to provide connection details
        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self._discovered_host): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(CONF_USERNAME): str,
                    vol.Optional(CONF_PASSWORD): str,
                    vol.Required(CONF_SSL, default=DEFAULT_SSL): bool,
                    vol.Required(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
                }
            ),
            errors=errors,
            description_placeholders={"host": self._discovered_host or ""},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Normalize host input (strip http:// or https:// if present)
            host, ssl_from_scheme, port_from_url = _normalize_host_input(
                user_input[CONF_HOST]
            )
            user_input[CONF_HOST] = host

            # If user provided a scheme, use it to set SSL
            if ssl_from_scheme is not None:
                user_input[CONF_SSL] = ssl_from_scheme

            # If port was extracted from URL or scheme implies a port, use it
            # (only if user hasn't changed port from default)
            if port_from_url is not None and user_input[CONF_PORT] == DEFAULT_PORT:
                user_input[CONF_PORT] = port_from_url

            # Check if already configured
            self._async_abort_entries_match({CONF_HOST: host})

            # Test connection
            session = async_get_clientsession(
                self.hass, verify_ssl=user_input.get(CONF_VERIFY_SSL, True)
            )

            client = AdGuardHomeClient(
                host=host,
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
                unique_id = f"{host}:{user_input[CONF_PORT]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # Create a title from the host
                title = f"AdGuard Home ({host})"
                if status.version:
                    title = f"AdGuard Home {status.version} ({host})"

                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauthorization flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
