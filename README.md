# Seerr for Home Assistant

[![CI](https://github.com/sgeorgakis/seerr-home-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/sgeorgakis/seerr-home-assistant/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/sgeorgakis/seerr-home-assistant/branch/main/graph/badge.svg)](https://codecov.io/gh/sgeorgakis/seerr-home-assistant)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

A Home Assistant custom integration that connects to a Seerr server, enabling media request management directly from Home Assistant.

## Features

- Search for movies and TV shows from Home Assistant
- View and monitor media requests (pending, approved, declined, available)
- Create new media requests
- Secure API key authentication
- Support for HTTP and HTTPS with optional SSL certificate verification

## Requirements

- Home Assistant 2025.1 or newer
- A running Seerr server with an API key

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sgeorgakis&repository=seerr-home-assistant&category=integration)

Or manually add via HACS:

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add `https://github.com/sgeorgakis/seerr-home-assistant` with category "Integration"
5. Click "Download" on the Seerr card
6. Restart Home Assistant

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/seerr_home_assistant` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Seerr"
4. Enter your server details:

| Option | Default | Description |
|--------|---------|-------------|
| Host | — | Hostname or IP address of your Seerr server |
| Port | `5055` | Port your Seerr server listens on |
| API Key | — | API key from Seerr → Settings → General |
| Use HTTPS | `false` | Enable if your server uses HTTPS |
| Verify SSL Certificate | `true` | Disable only for self-signed certificates |

## Obtaining an API Key

1. Open your Seerr web UI
2. Go to **Settings** → **General**
3. Copy the value from the **API Key** field

## Troubleshooting

### Cannot connect to Seerr

- Verify the server is running: `curl http://HOST:PORT/api/v1/status`
- Check firewall settings if running on a different machine
- Ensure the host and port are correct (default port: 5055)
- If using HTTPS, check that the SSL toggle is enabled

### Invalid API Key

- Regenerate the API key in Seerr → Settings → General and re-enter it in the integration options

## License

This project is licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0).

You are free to use, modify, fork, and share this software. Any derivative works must also be open source under the same license.
