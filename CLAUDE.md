# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration (`seerr-home-assistant`) that connects to a Seerr server. The integration allows Home Assistant to search for media, fetch media requests, and create new requests against the Seerr server.

## Architecture

The integration follows the standard Home Assistant custom component structure under `custom_components/seerr-home-assistant/`:

- **`__init__.py`** — Entry point; `async_setup_entry` wires the `SeerrClient` and `SeerrCoordinator` to the config entry lifecycle.
- **`api.py`** — `SeerrClient`: async `aiohttp`-based API client. All requests are authenticated via the `X-Api-Key` header. Raises `SeerrAuthError`, `SeerrConnectionError`, or `SeerrApiError` on failure.
- **`config_flow.py`** — UI config flow collecting host, port, API key, SSL toggle, and verify-SSL toggle. Validates connectivity before saving.
- **`coordinator.py`** — `SeerrCoordinator` (`DataUpdateCoordinator`) polls the server every 5 minutes and exposes a `SeerrData` dataclass to entities.
- **`const.py`** — Configuration keys and defaults (port: 5055, SSL: false).
- **`manifest.json`** — Integration metadata; domain `seer_home_assistant`, min HA `2025.1.0`.
- **`strings.json`** / **`translations/en.json`** — Config flow UI strings.

## API Endpoints Used

All endpoints share the base prefix **`/api/v1`**.
Authentication: `X-Api-Key: <api_key>` header on every request.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/status` | Connection test / credential validation |
| `GET` | `/api/v1/search/keyword` | Search media (`query`, `page`) |
| `GET` | `/api/v1/request` | List requests (`take`, `skip`, `filter`, `sort`, `requestedBy`) |
| `GET` | `/api/v1/request/count` | Aggregate request counts |
| `GET` | `/api/v1/request/{id}` | Single request detail |
| `POST` | `/api/v1/request` | Create a new request |
| `POST` | `/api/v1/request/{id}/approve` | Approve a request |
| `POST` | `/api/v1/request/{id}/decline` | Decline a request |
| `DELETE` | `/api/v1/request/{id}` | Delete a request |

## Development

Install the integration by copying or symlinking `custom_components/seerr-home-assistant/` to `config/custom_components/seerr-home-assistant/` in your Home Assistant installation.

No build step required. The integration uses Home Assistant's bundled dependencies (`aiohttp`, `voluptuous`).

## Workflow

- Create a new branch for each feature or fix
- Always run tests for a change
- Always write tests for a change
- Run single tests instead of all of them for performance
- Make sure the project compiles
- Make sure all tests pass
- **Never manually bump `manifest.json` version** — versions are managed automatically by release-please

## Releases

Releases are fully automated via [release-please](https://github.com/googleapis/release-please) and GitHub Actions.

On every push to `main`, release-please inspects commits since the last release. When releasable commits exist, it opens (or updates) a **Release PR** that:
- Bumps the version in `manifest.json` according to SemVer
- Generates a changelog from commit messages

Merging the Release PR triggers a second workflow that creates the GitHub Release and attaches `seerr-home-assistant.zip` for HACS users.

## Commit Message Format (Conventional Commits)

All commits **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<optional scope>): <short description>

<optional body>
```

**Types and their effect on versioning:**

| Type | Description | Version bump |
|------|-------------|--------------|
| `fix` | Bug fix | patch (0.0.x) |
| `feat` | New feature | minor (0.x.0) |
| `feat!` or `fix!` or any `!` | Breaking change | major (x.0.0) |
| `chore` | Maintenance, dependency updates | none |
| `docs` | Documentation only | none |
| `test` | Test changes only | none |
| `refactor` | Code refactoring without behaviour change | none |
| `perf` | Performance improvement | none |

**Examples:**

```
fix: handle 403 response from Seerr when API key lacks permissions

feat: add sensor for pending request count

feat!: drop support for Home Assistant versions below 2025.1

chore: update test dependencies

docs: document required Seerr server setup
```

Only `fix` and `feat` commits (and breaking changes) appear in release notes. `chore`, `docs`, `test`, and `refactor` are silently included in the release but not shown in the changelog.
