# Python API + Postgres Test Automation Playground

This repo boots a FastAPI service backed by Postgres. It is the foundation for API + SQL validation testing with pytest.

## Quick start

1. Build and start services:
   - `docker compose up --build`
2. Check health:
   - `curl http://localhost:8000/health`
3. Create a virtualenv and install test deps (recommended Python 3.11/3.12):
   - `python3.11 -m venv .venv`
   - `. .venv/bin/activate`
   - `python -m pip install -r requirements-dev.txt`
4. Run tests:
   - `python -m pytest`
   - `python -m pytest -m smoke`

## Features

- FastAPI service with API-key auth and strict input validation
- Postgres-backed CRUD with parameterized SQL
- Connection pooling with connect/statement timeouts
- Health checks, readiness probe, structured logs, and request IDs
- Rate limiting and security headers
- CORS configuration and OpenAPI API-key security scheme
- Search and pagination (`limit`/`offset`)
- Pytest framework with API + DB validation
- BDD examples, data-driven tests, and Allure reporting
- CI with smoke/full suites, lint/type checks, perf smoke

## Structure

- `api/` FastAPI service
- `db/` Postgres init scripts
- `tests/` placeholder for pytest framework
 - `requirements-dev.txt` dev/test dependencies
 - `Makefile` helper commands
 - `docs/` TDD + Agile artifacts + traceability
 - `perf/` Locust performance smoke test

## Notes

- API auth uses the `X-API-Key` header.
- Default key is set in `docker-compose.yml` for local use.
- Allure attachments are added after each test by default. Set `ALLURE_ATTACH_ON_PASS=false` to attach only on failures.
- You can attach custom artifacts in tests via `tests/utils/allure_helpers.py` (JSON, text, or files).
- Smoke tests are marked with `@pytest.mark.smoke`. Run them with `pytest -m smoke`.
- CI publishes the Allure report as a GitHub Actions artifact and (on `master`) can deploy it to GitHub Pages.
- Makefile shortcuts: `make venv`, `make install`, `make test`, `make smoke`.
- Docker helpers: `make up`, `make down`, `make rebuild`.
- If you have multiple Python versions installed, set the one to use like: `PYTHON=python3.11 make venv`.
- If you see `ImportError: Error importing plugin "pytest_html"`, reinstall deps with `make install`.
- Lint/type checks: `make lint` and `make typecheck`.
- Performance smoke: `make perf` (requires services running, uses `LOCUST_HOST=http://localhost:8000`).
- Full local verification: `make verify` (smoke + full tests + lint + typecheck + perf).
- Allure report: `make allure` (requires Allure CLI installed).
- Install Allure CLI (macOS): `brew install allure`.
- View Allure report locally (if opening `file://` is blank):
  - `python3 -m http.server 9000 --directory allure-report`
  - Open `http://localhost:9000`
- GitHub Pages deploy is optional. Set repo variable `PAGES_ENABLED=true` and enable Pages in repo settings to deploy from CI (branch `master`).
- CI artifacts:
  - `allure-results`: raw Allure data for regenerating reports
  - `allure-report`: prebuilt HTML report (serve via `python3 -m http.server 9000 --directory allure-report`)
  - `perf-results`: Locust CSVs (stats, failures, exceptions, history)

## Jenkins

The `Jenkinsfile` supports local Jenkins (with Docker available on the agent).

Start local Jenkins:
- `java -jar tools/jenkins.war --httpPort=8282`
- Open `http://localhost:8282`
- Unlock with the password printed on first run (or `~/.jenkins/secrets/initialAdminPassword`)

Create a Jenkins Pipeline job:
- New Item → **Pipeline**
- Definition: **Pipeline script from SCM**
- SCM: **Git**
- Repository URL: your repo path or Git URL
- Script Path: `Jenkinsfile`
- Save → **Build Now**

Required Jenkins plugins:
- Email Extension Plugin (for `emailext`)
- Slack Notification Plugin (for `slackSend`)

Credentials/vars to set in Jenkins (as environment variables or in the job):
- `EMAIL_RECIPIENTS` (comma-separated list)
- `SLACK_CHANNEL` (e.g., `#localbuild`)
- `SLACK_TOKEN_CRED_ID` (Slack bot token credentials ID, e.g., `slack-bot-token`)

Slack plugin setup (recommended):
- Create a Slack App with a bot token
- Add the token to Jenkins credentials (type: Secret text)
- Set the credential ID to match `SLACK_TOKEN_CRED_ID`
- In Jenkins Slack config, set Workspace to the Slack URL subdomain (e.g., `tomlocalworkspace`)
- In Jenkins Slack config, check **Use Slack App / Custom Slack App** (required for bot tokens)
- Invite the bot to the channel: `/invite @jenkins-local`

Artifacts archived:
- `artifacts/junit*.xml` (test results)
- `artifacts/locust*.csv` (perf smoke)
- `allure-results/` and `allure-report/` (if Allure CLI is installed)

Slack troubleshooting:
- **Test connection = Failure with 404**: Workspace is wrong or Jenkins is using legacy webhook mode.
  - Use the URL subdomain from `https://<SUBDOMAIN>.slack.com`
  - Check **Use Slack App / Custom Slack App** in Jenkins Slack config
  - Reinstall the Slack app to the workspace and update the bot token in Jenkins
  - Ensure the bot is invited to `#localbuild` (or add `chat:write.public`)

## Demo skills coverage

- Python API automation: `tests/test_items_api.py`
- SQL validation: direct DB checks in tests
- API testing: CRUD + search + negative/security cases
- TDD workflow: `docs/TDD.md` + search endpoint example
- Agile artifacts + traceability: `docs/AGILE.md`, `docs/TRACEABILITY.md`
- Industry best practices: CI, Allure, smoke vs full, lint/type checks, perf smoke

## Config highlights (env vars)

- `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_WINDOW_SECONDS`
- `DB_CONNECT_TIMEOUT`, `DB_STATEMENT_TIMEOUT_MS`, `DB_POOL_MINCONN`, `DB_POOL_MAXCONN`
- `LOG_LEVEL`, `REQUEST_ID_HEADER`
- `CORS_ORIGINS` (comma-separated, e.g. `http://localhost:3000,https://example.com`)
