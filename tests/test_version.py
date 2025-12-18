"""Tests for version parsing and feature detection."""
from __future__ import annotations

from custom_components.adguard_home_extended.version import (
    VERSION_BLOCKED_SERVICES_SCHEDULE,
    VERSION_CHECK_HOST_PARAMS,
    VERSION_NEW_BLOCKED_SERVICES,
    VERSION_QUERYLOG_RESPONSE_STATUS,
    VERSION_REWRITE_ENABLED,
    VERSION_STATS_CONFIG,
    AdGuardHomeVersion,
    VersionTuple,
    parse_version,
)


class TestVersionTuple:
    """Tests for VersionTuple."""

    def test_version_tuple_creation(self) -> None:
        """Test creating a version tuple."""
        v = VersionTuple(0, 107, 43)
        assert v.major == 0
        assert v.minor == 107
        assert v.patch == 43

    def test_version_tuple_str(self) -> None:
        """Test string representation."""
        v = VersionTuple(0, 107, 43)
        assert str(v) == "0.107.43"

    def test_version_tuple_comparison(self) -> None:
        """Test version tuple comparison."""
        v1 = VersionTuple(0, 107, 43)
        v2 = VersionTuple(0, 107, 56)
        v3 = VersionTuple(0, 108, 0)

        assert v1 < v2
        assert v2 < v3
        assert v3 > v1
        assert v1 == VersionTuple(0, 107, 43)


class TestAdGuardHomeVersion:
    """Tests for AdGuardHomeVersion."""

    def test_parse_standard_version(self) -> None:
        """Test parsing standard version string."""
        v = AdGuardHomeVersion("0.107.43")
        assert v.parsed == (0, 107, 43)

    def test_parse_version_with_v_prefix(self) -> None:
        """Test parsing version with 'v' prefix."""
        v = AdGuardHomeVersion("v0.107.43")
        assert v.parsed == (0, 107, 43)

    def test_parse_version_with_prerelease(self) -> None:
        """Test parsing version with prerelease suffix."""
        v = AdGuardHomeVersion("v0.107.43-beta.1")
        assert v.parsed == (0, 107, 43)
        assert v.prerelease == "beta.1"

    def test_prerelease_returns_none_for_empty_version(self) -> None:
        """Test prerelease property returns None for empty version string."""
        v = AdGuardHomeVersion("")
        assert v.prerelease is None

    def test_parse_empty_version(self) -> None:
        """Test parsing empty version string."""
        v = AdGuardHomeVersion("")
        assert v.parsed == (0, 0, 0)

    def test_parse_invalid_version(self) -> None:
        """Test parsing invalid version string."""
        v = AdGuardHomeVersion("not-a-version")
        assert v.parsed == (0, 0, 0)

    def test_parse_none_version(self) -> None:
        """Test parse_version with None."""
        v = parse_version(None)
        assert v.parsed == (0, 0, 0)

    def test_comparison_ge(self) -> None:
        """Test >= comparison."""
        v = AdGuardHomeVersion("0.107.56")
        assert v >= (0, 107, 30)
        assert v >= (0, 107, 56)
        assert not v >= (0, 107, 68)

    def test_comparison_gt(self) -> None:
        """Test > comparison."""
        v = AdGuardHomeVersion("0.107.56")
        assert v > (0, 107, 30)
        assert not v > (0, 107, 56)

    def test_comparison_le(self) -> None:
        """Test <= comparison."""
        v = AdGuardHomeVersion("0.107.56")
        assert v <= (0, 107, 68)
        assert v <= (0, 107, 56)
        assert not v <= (0, 107, 30)

    def test_comparison_lt(self) -> None:
        """Test < comparison."""
        v = AdGuardHomeVersion("0.107.56")
        assert v < (0, 107, 68)
        assert not v < (0, 107, 56)

    def test_comparison_eq(self) -> None:
        """Test == comparison."""
        v = AdGuardHomeVersion("0.107.56")
        assert v == (0, 107, 56)
        assert not v == (0, 107, 30)

    def test_comparison_eq_version(self) -> None:
        """Test == comparison with another AdGuardHomeVersion."""
        v1 = AdGuardHomeVersion("0.107.56")
        v2 = AdGuardHomeVersion("v0.107.56")
        assert v1 == v2

    def test_comparison_eq_unsupported_type_returns_not_implemented(self) -> None:
        """Test == comparison with unsupported type returns NotImplemented."""
        v = AdGuardHomeVersion("0.107.56")
        # Comparing with a string should return NotImplemented
        result = v.__eq__("0.107.56")
        assert result is NotImplemented

    def test_str_representation(self) -> None:
        """Test string representation."""
        v = AdGuardHomeVersion("v0.107.43")
        assert str(v) == "v0.107.43"

    def test_str_unknown(self) -> None:
        """Test string representation for unknown version."""
        v = AdGuardHomeVersion("")
        assert str(v) == "unknown"

    def test_repr(self) -> None:
        """Test repr."""
        v = AdGuardHomeVersion("0.107.43")
        assert repr(v) == "AdGuardHomeVersion('0.107.43')"


class TestFeatureFlags:
    """Tests for feature detection flags."""

    def test_supports_stats_config_old_version(self) -> None:
        """Test stats config not supported on old version."""
        v = AdGuardHomeVersion("0.107.29")
        assert not v.supports_stats_config

    def test_supports_stats_config_exact_version(self) -> None:
        """Test stats config supported on exact version."""
        v = AdGuardHomeVersion("0.107.30")
        assert v.supports_stats_config

    def test_supports_stats_config_new_version(self) -> None:
        """Test stats config supported on newer version."""
        v = AdGuardHomeVersion("0.107.65")
        assert v.supports_stats_config

    def test_supports_querylog_config(self) -> None:
        """Test querylog config feature flag."""
        old = AdGuardHomeVersion("0.107.29")
        new = AdGuardHomeVersion("0.107.30")
        assert not old.supports_querylog_config
        assert new.supports_querylog_config

    def test_supports_ecosia_safesearch(self) -> None:
        """Test ecosia safe search feature flag."""
        old = AdGuardHomeVersion("0.107.51")
        new = AdGuardHomeVersion("0.107.52")
        assert not old.supports_ecosia_safesearch
        assert new.supports_ecosia_safesearch

    def test_supports_blocked_services_schedule(self) -> None:
        """Test blocked services schedule feature flag."""
        old = AdGuardHomeVersion("0.107.55")
        new = AdGuardHomeVersion("0.107.56")
        assert not old.supports_blocked_services_schedule
        assert new.supports_blocked_services_schedule

    def test_supports_client_search(self) -> None:
        """Test client search feature flag."""
        old = AdGuardHomeVersion("0.107.55")
        new = AdGuardHomeVersion("0.107.56")
        assert not old.supports_client_search
        assert new.supports_client_search

    def test_supports_check_host_params(self) -> None:
        """Test check host params feature flag."""
        old = AdGuardHomeVersion("0.107.57")
        new = AdGuardHomeVersion("0.107.58")
        assert not old.supports_check_host_params
        assert new.supports_check_host_params

    def test_supports_new_blocked_services(self) -> None:
        """Test new blocked services feature flag."""
        old = AdGuardHomeVersion("0.107.64")
        new = AdGuardHomeVersion("0.107.65")
        assert not old.supports_new_blocked_services
        assert new.supports_new_blocked_services

    def test_supports_querylog_response_status(self) -> None:
        """Test querylog response status feature flag."""
        old = AdGuardHomeVersion("0.107.67")
        new = AdGuardHomeVersion("0.107.68")
        assert not old.supports_querylog_response_status
        assert new.supports_querylog_response_status

    def test_supports_rewrite_enabled(self) -> None:
        """Test rewrite enabled feature flag."""
        old = AdGuardHomeVersion("0.107.67")
        new = AdGuardHomeVersion("0.107.68")
        assert not old.supports_rewrite_enabled
        assert new.supports_rewrite_enabled

    def test_get_feature_summary(self) -> None:
        """Test feature summary generation."""
        v = AdGuardHomeVersion("0.107.56")
        summary = v.get_feature_summary()

        assert summary["stats_config"] is True
        assert summary["querylog_config"] is True
        assert summary["ecosia_safesearch"] is True
        assert summary["blocked_services_schedule"] is True
        assert summary["client_search"] is True
        assert summary["check_host_params"] is False
        assert summary["new_blocked_services"] is False
        assert summary["querylog_response_status"] is False
        assert summary["rewrite_enabled"] is False


class TestVersionConstants:
    """Tests for version constants."""

    def test_version_stats_config(self) -> None:
        """Test VERSION_STATS_CONFIG constant."""
        assert VERSION_STATS_CONFIG == (0, 107, 30)

    def test_version_blocked_services_schedule(self) -> None:
        """Test VERSION_BLOCKED_SERVICES_SCHEDULE constant."""
        assert VERSION_BLOCKED_SERVICES_SCHEDULE == (0, 107, 56)

    def test_version_check_host_params(self) -> None:
        """Test VERSION_CHECK_HOST_PARAMS constant."""
        assert VERSION_CHECK_HOST_PARAMS == (0, 107, 58)

    def test_version_new_blocked_services(self) -> None:
        """Test VERSION_NEW_BLOCKED_SERVICES constant."""
        assert VERSION_NEW_BLOCKED_SERVICES == (0, 107, 65)

    def test_version_querylog_response_status(self) -> None:
        """Test VERSION_QUERYLOG_RESPONSE_STATUS constant."""
        assert VERSION_QUERYLOG_RESPONSE_STATUS == (0, 107, 68)

    def test_version_rewrite_enabled(self) -> None:
        """Test VERSION_REWRITE_ENABLED constant."""
        assert VERSION_REWRITE_ENABLED == (0, 107, 68)


class TestParseVersionFunction:
    """Tests for the parse_version convenience function."""

    def test_parse_version_string(self) -> None:
        """Test parsing a version string."""
        v = parse_version("0.107.43")
        assert isinstance(v, AdGuardHomeVersion)
        assert v.parsed == (0, 107, 43)

    def test_parse_version_none(self) -> None:
        """Test parsing None."""
        v = parse_version(None)
        assert v.parsed == (0, 0, 0)

    def test_parse_version_empty(self) -> None:
        """Test parsing empty string."""
        v = parse_version("")
        assert v.parsed == (0, 0, 0)
