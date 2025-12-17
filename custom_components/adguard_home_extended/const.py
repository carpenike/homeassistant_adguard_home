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

# API endpoints
API_STATUS: Final = "/control/status"
API_STATS: Final = "/control/stats"
API_QUERYLOG: Final = "/control/querylog"
API_PROTECTION: Final = "/control/protection"
API_SAFEBROWSING_ENABLE: Final = "/control/safebrowsing/enable"
API_SAFEBROWSING_DISABLE: Final = "/control/safebrowsing/disable"
API_PARENTAL_ENABLE: Final = "/control/parental/enable"
API_PARENTAL_DISABLE: Final = "/control/parental/disable"
API_SAFESEARCH_ENABLE: Final = "/control/safesearch/enable"
API_SAFESEARCH_DISABLE: Final = "/control/safesearch/disable"
API_FILTERING_ADD_URL: Final = "/control/filtering/add_url"
API_FILTERING_REMOVE_URL: Final = "/control/filtering/remove_url"
API_FILTERING_REFRESH: Final = "/control/filtering/refresh"
API_FILTERING_STATUS: Final = "/control/filtering/status"
API_FILTERING_CONFIG: Final = "/control/filtering/config"
API_CLIENTS: Final = "/control/clients"
API_CLIENTS_ADD: Final = "/control/clients/add"
API_CLIENTS_UPDATE: Final = "/control/clients/update"
API_CLIENTS_DELETE: Final = "/control/clients/delete"
API_BLOCKED_SERVICES_ALL: Final = "/control/blocked_services/all"
API_BLOCKED_SERVICES_LIST: Final = "/control/blocked_services/list"
API_BLOCKED_SERVICES_SET: Final = "/control/blocked_services/set"
API_REWRITE_LIST: Final = "/control/rewrite/list"
API_REWRITE_ADD: Final = "/control/rewrite/add"
API_REWRITE_DELETE: Final = "/control/rewrite/delete"
API_REWRITE_UPDATE: Final = "/control/rewrite/update"
API_DHCP_STATUS: Final = "/control/dhcp/status"
API_DNS_INFO: Final = "/control/dns_info"
API_DNS_CONFIG: Final = "/control/dns_config"

# Attributes
ATTR_PROCESSING_TIME: Final = "avg_processing_time"
ATTR_DNS_QUERIES: Final = "dns_queries"
ATTR_BLOCKED_QUERIES: Final = "blocked_filtering"
ATTR_BLOCKED_SAFEBROWSING: Final = "replaced_safebrowsing"
ATTR_BLOCKED_PARENTAL: Final = "replaced_parental"
ATTR_TOP_CLIENTS: Final = "top_clients"
ATTR_TOP_BLOCKED_DOMAINS: Final = "top_blocked_domains"
ATTR_TOP_QUERIED_DOMAINS: Final = "top_queried_domains"
