"""Shared entity helpers for AdGuard Home Extended."""

from __future__ import annotations

from homeassistant.core import callback


class OptimisticSwitchMixin:
    """Mixin adding optimistic state to coordinator-backed switches.

    After a turn_on/turn_off command, the switch immediately reflects the
    requested state in the UI via :meth:`_set_optimistic_state` instead of
    waiting for the next coordinator refresh (which is debounced and only
    runs on the polling interval). The optimistic value is cleared as soon
    as fresh coordinator data arrives, at which point the real server state
    takes over again.

    Subclasses must:
      * Be declared with this mixin *before* ``CoordinatorEntity`` so the
        overridden ``_handle_coordinator_update`` participates in the MRO.
      * Return ``self._optimistic_is_on`` from ``is_on`` when it is not
        ``None`` before falling back to coordinator-derived state.
      * Call ``self._set_optimistic_state(...)`` from their turn on/off
        handlers after issuing the API command.
    """

    _optimistic_is_on: bool | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state when fresh data arrives, then update."""
        self._optimistic_is_on = None
        super()._handle_coordinator_update()  # type: ignore[misc]

    def _set_optimistic_state(self, value: bool) -> None:
        """Optimistically set state and write it to HA immediately."""
        self._optimistic_is_on = value
        # ``hass`` is None until the entity is added to a platform; guard so
        # this is safe to call from unit tests on un-added entities.
        if self.hass is not None:  # type: ignore[attr-defined]
            self.async_write_ha_state()  # type: ignore[attr-defined]
