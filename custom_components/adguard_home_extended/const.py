"""Constants for the AdGuard Home Extended integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "adguard_home_extended"

# Default values
DEFAULT_PORT: Final = 3000
DEFAULT_SSL: Final = False
DEFAULT_VERIFY_SSL: Final = True
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_QUERY_LOG_LIMIT: Final = 100
DEFAULT_ATTR_TOP_ITEMS_LIMIT: Final = 10
DEFAULT_ATTR_LIST_LIMIT: Final = 20

# Configuration keys
CONF_QUERY_LOG_LIMIT: Final = "query_log_limit"
CONF_ATTR_TOP_ITEMS_LIMIT: Final = "attr_top_items_limit"
CONF_ATTR_LIST_LIMIT: Final = "attr_list_limit"

# =============================================================================
# API Endpoints
# =============================================================================
# AdGuard Home REST API reference: https://github.com/AdguardTeam/AdGuardHome
# All endpoints are under /control/ prefix and require Basic Auth.
#
# Version compatibility notes:
# - Base API (v0.100+): Core protection, filtering, and status endpoints
# - v0.107.30+: Stats and query log configuration APIs
# - v0.107.56+: Blocked services with schedules, client search API
# - v0.107.68+: Query log response_status filter, check_host improvements
# =============================================================================

# -----------------------------------------------------------------------------
# Core Status & Protection APIs (v0.100+)
# Available in all supported AdGuard Home versions
# -----------------------------------------------------------------------------
API_STATUS: Final = "/control/status"
API_PROTECTION: Final = "/control/protection"

# -----------------------------------------------------------------------------
# Statistics APIs (v0.100+)
# GET /control/stats returns query statistics
# -----------------------------------------------------------------------------
API_STATS: Final = "/control/stats"

# v0.107.30+: Stats configuration endpoints
API_STATS_CONFIG: Final = "/control/stats/config"
API_STATS_CONFIG_UPDATE: Final = "/control/stats/config/update"
API_STATS_RESET: Final = "/control/stats_reset"

# -----------------------------------------------------------------------------
# Query Log APIs (v0.100+)
# GET /control/querylog returns recent DNS queries
# Supports filtering by: older_than, search, response_status (v0.107.68+)
# -----------------------------------------------------------------------------
API_QUERYLOG: Final = "/control/querylog"

# v0.107.30+: Query log configuration endpoints
API_QUERYLOG_CONFIG: Final = "/control/querylog/config"
API_QUERYLOG_CONFIG_UPDATE: Final = "/control/querylog/config/update"
API_QUERYLOG_CLEAR: Final = "/control/querylog_clear"

# -----------------------------------------------------------------------------
# Safe Browsing APIs (v0.100+)
# Protects against malicious and phishing websites
# -----------------------------------------------------------------------------
API_SAFEBROWSING_STATUS: Final = "/control/safebrowsing/status"
API_SAFEBROWSING_ENABLE: Final = "/control/safebrowsing/enable"
API_SAFEBROWSING_DISABLE: Final = "/control/safebrowsing/disable"

# -----------------------------------------------------------------------------
# Parental Control APIs (v0.100+)
# Blocks adult content across the network
# -----------------------------------------------------------------------------
API_PARENTAL_STATUS: Final = "/control/parental/status"
API_PARENTAL_ENABLE: Final = "/control/parental/enable"
API_PARENTAL_DISABLE: Final = "/control/parental/disable"

# -----------------------------------------------------------------------------
# Safe Search APIs (v0.100+)
# Enforces safe search on major search engines
# -----------------------------------------------------------------------------
API_SAFESEARCH_ENABLE: Final = "/control/safesearch/enable"
API_SAFESEARCH_DISABLE: Final = "/control/safesearch/disable"
API_SAFESEARCH_STATUS: Final = "/control/safesearch/status"
API_SAFESEARCH_SETTINGS: Final = "/control/safesearch/settings"

# -----------------------------------------------------------------------------
# Filtering APIs (v0.100+)
# Manage DNS blocklists and filtering rules
# -----------------------------------------------------------------------------
API_FILTERING_ADD_URL: Final = "/control/filtering/add_url"
API_FILTERING_REMOVE_URL: Final = "/control/filtering/remove_url"
API_FILTERING_SET_URL: Final = "/control/filtering/set_url"
API_FILTERING_REFRESH: Final = "/control/filtering/refresh"
API_FILTERING_STATUS: Final = "/control/filtering/status"
API_FILTERING_CONFIG: Final = "/control/filtering/config"

# -----------------------------------------------------------------------------
# Client Management APIs (v0.100+)
# Manage per-client settings and configurations
# -----------------------------------------------------------------------------
API_CLIENTS: Final = "/control/clients"
API_CLIENTS_ADD: Final = "/control/clients/add"
API_CLIENTS_UPDATE: Final = "/control/clients/update"
API_CLIENTS_DELETE: Final = "/control/clients/delete"

# v0.107.56+: Search API for finding clients (replaces deprecated clients/find)
API_CLIENTS_SEARCH: Final = "/control/clients/search"

# -----------------------------------------------------------------------------
# Blocked Services APIs (v0.100+)
# Block access to specific services (social media, gaming, etc.)
# -----------------------------------------------------------------------------
API_BLOCKED_SERVICES_ALL: Final = "/control/blocked_services/all"
API_BLOCKED_SERVICES_LIST: Final = "/control/blocked_services/list"
API_BLOCKED_SERVICES_SET: Final = "/control/blocked_services/set"

# v0.107.56+: Schedule-aware blocked services management
API_BLOCKED_SERVICES_GET: Final = "/control/blocked_services/get"
API_BLOCKED_SERVICES_UPDATE: Final = "/control/blocked_services/update"

# -----------------------------------------------------------------------------
# DNS Rewrite APIs (v0.100+)
# Custom DNS responses for specific domains
# v0.107.68+: Added enabled field for toggling individual rewrites
# -----------------------------------------------------------------------------
API_REWRITE_LIST: Final = "/control/rewrite/list"
API_REWRITE_ADD: Final = "/control/rewrite/add"
API_REWRITE_DELETE: Final = "/control/rewrite/delete"
API_REWRITE_UPDATE: Final = "/control/rewrite/update"

# -----------------------------------------------------------------------------
# DHCP APIs (v0.100+)
# DHCP server status and lease management
# -----------------------------------------------------------------------------
API_DHCP_STATUS: Final = "/control/dhcp/status"

# -----------------------------------------------------------------------------
# DNS Configuration APIs (v0.100+)
# DNS server settings and upstream configuration
# -----------------------------------------------------------------------------
API_DNS_INFO: Final = "/control/dns_info"
API_DNS_CONFIG: Final = "/control/dns_config"

# -----------------------------------------------------------------------------
# DNS Filtering Check API (v0.100+)
# Check how a domain would be filtered
# v0.107.58+: Added optional client and qtype parameters
# -----------------------------------------------------------------------------
API_CHECK_HOST: Final = "/control/filtering/check_host"

# Attributes
ATTR_PROCESSING_TIME: Final = "avg_processing_time"
ATTR_DNS_QUERIES: Final = "dns_queries"
ATTR_BLOCKED_QUERIES: Final = "blocked_filtering"
ATTR_BLOCKED_SAFEBROWSING: Final = "replaced_safebrowsing"
ATTR_BLOCKED_PARENTAL: Final = "replaced_parental"
ATTR_TOP_CLIENTS: Final = "top_clients"
ATTR_TOP_BLOCKED_DOMAINS: Final = "top_blocked_domains"
ATTR_TOP_QUERIED_DOMAINS: Final = "top_queried_domains"
