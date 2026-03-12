"""Constants for the Seerr Home Assistant integration."""
import logging

DOMAIN = "seerr_home_assistant"
LOGGER = logging.getLogger(__package__)

# Config entry keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_API_KEY = "api_key"
CONF_SSL = "ssl"
CONF_VERIFY_SSL = "verify_ssl"

# Defaults
DEFAULT_PORT = 5055  # Overseerr / Jellyseerr default
DEFAULT_SSL = False
DEFAULT_VERIFY_SSL = True

# API
API_BASE_PATH = "/api/v1"
REQUEST_TIMEOUT = 10  # seconds

# Polling
SCAN_INTERVAL_MINUTES = 5
