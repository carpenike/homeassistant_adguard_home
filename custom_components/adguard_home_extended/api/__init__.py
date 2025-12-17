"""AdGuard Home API client package."""
from .client import (
    AdGuardHomeAuthError,
    AdGuardHomeClient,
    AdGuardHomeConnectionError,
    AdGuardHomeError,
)
from .models import (
    AdGuardHomeClient as ClientConfig,
)
from .models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
    BlockedService,
    DhcpLease,
    DhcpStatus,
    DnsRewrite,
    FilteringStatus,
)

__all__ = [
    # Client
    "AdGuardHomeClient",
    # Exceptions
    "AdGuardHomeError",
    "AdGuardHomeConnectionError",
    "AdGuardHomeAuthError",
    # Models
    "AdGuardHomeStatus",
    "AdGuardHomeStats",
    "ClientConfig",
    "BlockedService",
    "DhcpLease",
    "DhcpStatus",
    "DnsRewrite",
    "FilteringStatus",
]
