"""AdGuard Home API client package."""
from .client import AdGuardHomeClient
from .models import (
    AdGuardHomeStatus,
    AdGuardHomeStats,
    AdGuardHomeClient as ClientConfig,
)

__all__ = [
    "AdGuardHomeClient",
    "AdGuardHomeStatus",
    "AdGuardHomeStats",
    "ClientConfig",
]
