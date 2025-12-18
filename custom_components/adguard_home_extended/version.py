"""Version utilities for AdGuard Home API compatibility.

This module provides version parsing and feature detection for the AdGuard Home API.
Different AdGuard Home versions support different API features, and this module
helps ensure we only use features available in the detected version.

Version history for key features:
- v0.100+: Base API (status, filtering, protection, clients, blocked services)
- v0.107.30+: Stats and query log configuration APIs
- v0.107.52+: Ecosia safe search engine support
- v0.107.56+: Blocked services with schedules, client search API
- v0.107.58+: Check host with client and qtype parameters
- v0.107.65+: New blocked services (ChatGPT, Claude, DeepSeek, Odysee)
- v0.107.68+: Query log response_status filter, DNS rewrite enabled field
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from typing import NamedTuple


class VersionTuple(NamedTuple):
    """Parsed version as a tuple for comparison."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        """Return version string."""
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass
class AdGuardHomeVersion:
    """Parsed AdGuard Home version with feature detection.

    Provides easy comparison and feature flag access based on the detected
    AdGuard Home server version.
    """

    raw_version: str

    # Version pattern: v0.107.43 or 0.107.43 or 0.107.43-beta.1
    _VERSION_PATTERN = re.compile(r"v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?")

    @cached_property
    def parsed(self) -> VersionTuple:
        """Parse version string into comparable tuple."""
        if not self.raw_version:
            return VersionTuple(0, 0, 0)

        match = self._VERSION_PATTERN.match(self.raw_version)
        if not match:
            return VersionTuple(0, 0, 0)

        return VersionTuple(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )

    @property
    def prerelease(self) -> str | None:
        """Extract prerelease suffix if present."""
        if not self.raw_version:
            return None
        match = self._VERSION_PATTERN.match(self.raw_version)
        return match.group(4) if match else None

    def __ge__(self, other: tuple[int, int, int] | VersionTuple) -> bool:
        """Compare version >= other."""
        return self.parsed >= other

    def __gt__(self, other: tuple[int, int, int] | VersionTuple) -> bool:
        """Compare version > other."""
        return self.parsed > other

    def __le__(self, other: tuple[int, int, int] | VersionTuple) -> bool:
        """Compare version <= other."""
        return self.parsed <= other

    def __lt__(self, other: tuple[int, int, int] | VersionTuple) -> bool:
        """Compare version < other."""
        return self.parsed < other

    def __eq__(self, other: object) -> bool:
        """Compare version == other."""
        if isinstance(other, tuple):
            return self.parsed == other
        if isinstance(other, AdGuardHomeVersion):
            return self.parsed == other.parsed
        return NotImplemented

    def __str__(self) -> str:
        """Return the raw version string."""
        return self.raw_version or "unknown"

    def __repr__(self) -> str:
        """Return repr string."""
        return f"AdGuardHomeVersion('{self.raw_version}')"

    # =========================================================================
    # Feature flags based on version detection
    # =========================================================================

    @property
    def supports_stats_config(self) -> bool:
        """Check if stats configuration API is available (v0.107.30+)."""
        return self >= (0, 107, 30)

    @property
    def supports_querylog_config(self) -> bool:
        """Check if query log configuration API is available (v0.107.30+)."""
        return self >= (0, 107, 30)

    @property
    def supports_ecosia_safesearch(self) -> bool:
        """Check if Ecosia safe search is supported (v0.107.52+)."""
        return self >= (0, 107, 52)

    @property
    def supports_blocked_services_schedule(self) -> bool:
        """Check if blocked services scheduling is available (v0.107.56+)."""
        return self >= (0, 107, 56)

    @property
    def supports_client_search(self) -> bool:
        """Check if client search API is available (v0.107.56+)."""
        return self >= (0, 107, 56)

    @property
    def supports_check_host_params(self) -> bool:
        """Check if check_host supports client/qtype params (v0.107.58+)."""
        return self >= (0, 107, 58)

    @property
    def supports_new_blocked_services(self) -> bool:
        """Check if new AI/streaming services are available (v0.107.65+)."""
        return self >= (0, 107, 65)

    @property
    def supports_querylog_response_status(self) -> bool:
        """Check if query log response_status filter is available (v0.107.68+)."""
        return self >= (0, 107, 68)

    @property
    def supports_rewrite_enabled(self) -> bool:
        """Check if DNS rewrite enabled field is available (v0.107.68+)."""
        return self >= (0, 107, 68)

    @property
    def supports_cache_enabled(self) -> bool:
        """Check if DNS cache_enabled field is available (v0.107.65+)."""
        return self >= (0, 107, 65)

    def get_feature_summary(self) -> dict[str, bool]:
        """Return a summary of all supported features."""
        return {
            "stats_config": self.supports_stats_config,
            "querylog_config": self.supports_querylog_config,
            "ecosia_safesearch": self.supports_ecosia_safesearch,
            "blocked_services_schedule": self.supports_blocked_services_schedule,
            "client_search": self.supports_client_search,
            "check_host_params": self.supports_check_host_params,
            "new_blocked_services": self.supports_new_blocked_services,
            "querylog_response_status": self.supports_querylog_response_status,
            "rewrite_enabled": self.supports_rewrite_enabled,
            "cache_enabled": self.supports_cache_enabled,
        }


def parse_version(version_string: str | None) -> AdGuardHomeVersion:
    """Parse an AdGuard Home version string.

    Args:
        version_string: Version string like "v0.107.43" or "0.107.43"

    Returns:
        AdGuardHomeVersion instance for feature detection and comparison.
    """
    return AdGuardHomeVersion(version_string or "")


# Version constants for common comparisons
VERSION_STATS_CONFIG = VersionTuple(0, 107, 30)
VERSION_BLOCKED_SERVICES_SCHEDULE = VersionTuple(0, 107, 56)
VERSION_CHECK_HOST_PARAMS = VersionTuple(0, 107, 58)
VERSION_NEW_BLOCKED_SERVICES = VersionTuple(0, 107, 65)
VERSION_QUERYLOG_RESPONSE_STATUS = VersionTuple(0, 107, 68)
VERSION_REWRITE_ENABLED = VersionTuple(0, 107, 68)
VERSION_CACHE_ENABLED = VersionTuple(0, 107, 65)
