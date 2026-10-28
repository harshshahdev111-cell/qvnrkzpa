# Wind Desk

UK wind generation decision portal for the REint full stack challenge. Built with React, Django and Django REST Framework.

**Live application:** [Open Wind Desk on Vercel](https://wind-desk-snowy.vercel.app/).

The hosted January 2026 pilot includes real Elexon historical data and was verified in a signed-out browser on October 28, 2026.

## Start locally (PowerShell)

Prerequisites: Python 3.12+, Node.js 22+.

```powershell
# First-time setup: copy templates and replace SECRET_KEY with a random value.
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements.txt
.\.venv\Scripts\python backend/manage.py migrate
.\.venv\Scripts\python backend/manage.py import_elexon
.\.venv\Scripts\python backend/manage.py runserver
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. The Vite dev proxy sends API requests to Django on port 8000. The importer may take several minutes. It is safe to rerun. No API key is needed. The database is intentionally excluded from source control; import it after setup. Never substitute fabricated values for absent source data.

## Docker

Copy `.env.example` to `.env` and set a unique `SECRET_KEY` first (if not already configured). Start Docker Desktop, then:

```sh
docker compose up --build -d
docker compose exec web python manage.py import_elexon
```

Open http://localhost:8000. The multi-stage image builds React and serves its assets with WhiteNoise and APIs with Gunicorn. SQLite persists in the wind_data named volume. Do not use `docker compose down -v` unless you intend to remove imported data.

## Features

- January 1–31, 2026 purchasing decisions, adjustable London cutoff time.
- Next-day delivery forecasts chosen individually per half-hour from the latest eligible publication; no future forecast revisions enter the analysis.
- Forecast versus actual chart, complete half-hour table and CSV export.
- MAE, RMSE, signed bias, WAPE, and explicit matched coverage.
- Actual publication timestamps, source status and last successful import.
- Responsive UI, request cancellation, retry errors and empty-data states.

## Data and methodology

Source: https://bmrs.elexon.co.uk/api-documentation and https://data.elexon.co.uk/swagger/v1/swagger.json.

WINDFOR stream is fetched by daily publication windows from December 25, 2025 to February 1, 2026 (exclusive). A seven-day lookback captures earlier available vintages for the first decision. FUELHH stream is fetched by settlement date January 2–February 1, filtering fuelType=WIND. Actual duplicates select the latest publication. Forecasts have a unique (target, publication) constraint. Imports validate inputs and commit only after both datasets are fetched successfully; retries use backoff for rate limits and transient server failures.

For each delivery half-hour, choose the greatest publishTime <= decision timestamp. London is UTC throughout this interval. Decision January 31 therefore delivers February 1. The 10:00 default is an explicit user-adjustable assumption, not a claimed auction gate closure.

Error = forecast - actual. Positive bias means overforecast wind. MAE = mean absolute error; RMSE = square root of mean squared error; WAPE = 100 * sum absolute errors / sum absolute actuals. Zero actuals are valid; a zero WAPE denominator returns null. Metrics use matched periods only, and missing values remain null. Forecast energy sums available MW * 0.5 h; incomplete coverage means a partial energy total. Outturn actuals are retrospective and may have been revised.

National Elexon wind coverage does not include every UK renewable source. Demand, prices, and other generation are deliberately outside scope, so no exact procurement quantity or cost saving is claimed. A descriptive forecast error is not a prediction interval.

## API

- `GET /api/v1/dashboard/?decision_date=2026-01-15&cutoff=10:00`
- `GET /api/v1/dashboard/?decision_date=2026-01-15&cutoff=10:00&export=csv`
- `GET /api/v1/status/`

The legacy `/api/` routes remain aliases of `/api/v1/`. Invalid dates and cutoffs return HTTP 400 with field-level serializer errors. CSV is available through `export=csv`, `format=csv`, or `Accept: text/csv`. Endpoints are read-only and unauthenticated for the pilot. Import is a CLI operation, not a public write endpoint.

## Repository map

- `backend/`: Django application, REST API, integrations, schema migrations and backend tests.
- `backend/manage.py`: Django command-line entry point for migrations, imports, checks and tests.
- `backend/common/`: shared API response handling, structured logging, request middleware and circuit breaker support.
- `backend/data/pilot.sqlite3.gz`: compressed historical data snapshot used by the Vercel build; the writable local database and extracted snapshot are excluded from Git.
- `backend/requirements.txt`, `backend/requirements-dev.txt`: production and development Python dependencies.
- `backend/config/`: settings, routing and WSGI application.
- `backend/wind/models.py`: actuals, forecast vintages and import audit records.
- `backend/wind/services/analysis.py`: as-of selection, matching and metrics.
- `backend/wind/api/v1/`: DRF class-based views, request/response serializers, CSV renderer and namespaced URLs.
- `backend/wind/selectors.py`: read-only ORM queries, including database-side as-of forecast selection.
- `backend/wind/services/ingestion.py`: data validation, revision selection and atomic upserts.
- `backend/integrations/elexon/`: provider-specific integration package:
  - `__init__.py`: public exports (`ElexonClient`, `ElexonService`).
  - `client.py`: API configuration (settings defaults with optional constructor overrides), two explicit endpoint paths, request parameters, direct `requests.get()` calls, retries, circuit protection and JSON decoding. Endpoint methods return `ProviderResponse` with status, payload and headers; HTTP and invalid-response errors still raise to preserve retries and import failure handling.
  - `service.py`: application-facing fetch methods and reusable response parsers returning normalized dictionaries; creates its client by default and accepts an injected client for testing; no database operations.
  - `utils.py`: `ProviderResponse` plus shared row-shape, timestamp and generation validators.
  - Application ingestion owns date windows, revision selection and atomic database writes. It wraps a caller-owned client in `ElexonService`; the management command creates the client.

Integration flow: `ingestion -> ElexonService -> ElexonClient -> external API`; responses return through service parsers before persistence. Services can also parse existing responses directly through `parse_wind_forecasts` and `parse_wind_actuals`.
- `backend/wind/views.py`: HTML entry point only.
- `backend/wind/management/commands/import_elexon.py`: transactional upstream import.
- `backend/wind/migrations/`: committed database schema.
- `backend/wind/tests/`: cutoff leakage, metrics, missing values, date boundary and CSV checks.
- `frontend/src/`: React App, entry point, useDecision hook, API client, format utilities and responsive styles.
- `frontend/src/app/`, `frontend/src/components/`: application entry component and shared layout.
- `frontend/src/features/decisions/`: dashboard components, API functions, validation, hooks and chart utilities.
- `frontend/src/lib/`, `frontend/src/styles/`: shared HTTP/format helpers and application styles.
- `frontend/tests/`: Node validation tests and browser checks.
- `frontend/scripts/record-demo.mjs`: automated demo recording utility.
- `frontend/package.json`, `frontend/package-lock.json`: frontend scripts, dependencies and locked dependency versions.
- `frontend/index.html`, `frontend/vite.config.js`: HTML entry point, frontend build and local API proxy configuration.
- `frontend/.prettierrc.json`, `frontend/.prettierignore`: frontend formatting settings.
- `.env.example`, `frontend/.env.example`: backend and frontend environment templates; copy these for local setup.
- `scripts/prepare_vercel.py`: prepares a consistent historical SQLite snapshot from the imported local database.
- `build_vercel.py`: extracts and validates the snapshot, builds React and collects Django static assets.
- `wsgi.py`, `vercel.json`, `.python-version`: Vercel entry point, deployment configuration and Python runtime pin.
- `pyproject.toml`, `requirements.txt`: project metadata, deployment dependencies and backend formatter/linter configuration.
- `.gitignore`, `.dockerignore`, `.vercelignore`: exclude secrets, local databases, caches and generated output from source control/build uploads.
- `Dockerfile`, `compose.yaml`: complete application container and persistent database volume.
- `DEMO.md`: customer pitch and technical walkthrough outline.
- `README.md`: setup, architecture, API, validation and deployment documentation.

## Validation

```powershell
.\.venv\Scripts\python backend/manage.py test wind
.\.venv\Scripts\python backend/manage.py check
cd frontend
npm run build
```

## Hosting

The deployed application is available at [https://wind-desk-snowy.vercel.app/](https://wind-desk-snowy.vercel.app/). It serves the React dashboard and Django API from one origin, with a bundled read-only historical dataset.

For a container host, deploy the Dockerfile, set DEBUG=0, a strong SECRET_KEY and ALLOWED_HOSTS to the actual hostname, mount persistent storage and set DATABASE_PATH to it. Run migrations and import_elexon. Heroku can run this image but its ephemeral filesystem requires replacing SQLite with managed PostgreSQL for durable hosting; the provided Compose configuration is a persistent single-instance deployment. Vercel can run the full pilot using the root `vercel.json` and `wsgi.py`: Django serves the homepage and API on one domain, and React assets use `/static/`. See the deployment steps below.

Before production: configure HTTPS, managed database/backups, authentication if needed, scheduled ingestion and upstream monitoring. This January historical pilot intentionally uses explicit CLI ingestion.

## Verified Docker run

The full Docker image was built and started successfully with Docker Desktop. All fifteen backend tests passed inside the container. The homepage, compiled JavaScript asset and populated DRF dashboard returned HTTP 200. The persistent Docker database contains 1,488 actuals and 17,864 forecast vintages, and survived a container rebuild.

For the January 15 default view, there are 24 exact timestamp forecast matches against 48 actual half-hours. These source gaps are preserved, shown as isolated forecast points, and excluded from matched-error statistics. The displayed energy is explicitly an available-period partial total.


## Code structure and formatting

Backend dependency direction: versioned API views -> query serializers -> analysis services -> database selectors -> models. Output serializers define JSON contracts, and the CSV renderer consumes the same serialized output. CLI import commands delegate to ingestion services and the Elexon transport client. Services do not depend on DRF. Forecast selectors use a correlated subquery to select only the latest eligible vintage per target instead of loading every vintage into application memory.

Black is the backend formatter; Ruff checks lint and import order. Prettier formats the frontend. Install development tools and run these from the repository root:

```powershell
.\.venv\Scripts\python -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python -m black backend
.\.venv\Scripts\python -m black --check backend
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python backend/manage.py test wind
cd frontend
npm run format
npm run format:check
```

Formatter configuration is committed in `pyproject.toml` and `frontend/.prettierrc.json`. Development tools are separate from production requirements. Tests cover legacy/versioned route parity, cutoff leakage, constant analysis query count, zero-denominator metrics, validation errors, CSV negotiation, import idempotency and failed-import data retention. The refactor does not change database schema or remove imported data.


## Standard API response

DRF JSON endpoints on both `/api/v1/` and the `/api/` aliases use this contract:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Decision dashboard retrieved successfully.",
  "data": {"decision_time": "2026-01-15T10:00:00Z"},
  "errors": null
}
```

`data` contains the full dashboard or source-status payload. On failure, `success` is false, `data` is null, and `errors` contains DRF field errors or a detail object. The HTTP status is preserved (400, 404, 405, 500, etc.). Unexpected exceptions are logged server-side and return a generic message without internal details. `backend/common/api.py` provides the shared view and exception handler; endpoints do not construct envelopes individually. CSV downloads keep their tabular format; CSV errors contain an error heading and message. React's shared API client unwraps `data` and exposes status and error details on rejected requests.

## Environment configuration

Root `.env` is loaded with python-dotenv without overriding process environment variables. A missing SECRET_KEY fails startup. The local workspace has a generated unique secret; it is never committed. `.env.example` is the tracked template. Production should supply variables through the hosting platform or secret manager.

| Variable | Purpose |
| --- | --- |
| SECRET_KEY | Required Django signing key; generate a unique random value |
| DEBUG | Defaults off; accepts 1, true or yes to enable locally |
| ALLOWED_HOSTS | Comma-separated hostnames, without URL schemes |
| CORS_ALLOWED_ORIGINS | Comma-separated frontend origins |
| DATABASE_PATH | Optional local SQLite path; Compose overrides to persistent `/data/db.sqlite3` |
| ELEXON_BASE_URL | Upstream datasets API base URL |
| ELEXON_TIMEOUT | Upstream request timeout in seconds |
| ELEXON_RETRY_ATTEMPTS | Total Tenacity attempts for transient upstream errors |
| APP_PORT | Compose host port, default 8000; bound to loopback |

Frontend `.env` is separate and based on `frontend/.env.example`. VITE_API_URL is a public API origin, empty for same-origin requests; API_PROXY_TARGET configures only the Vite development proxy. Never put secrets in VITE_ variables. Frontend variables are read at build time, so rebuild after changing them. Django variables are read at startup; recreate the Compose service after changes. Compose reads the root `.env` via env_file. Neither root nor nested real `.env` files are included in Git or the Docker build context.

To generate a secret locally: `python -c "import secrets; print(secrets.token_urlsafe(48))"`, then save it as SECRET_KEY in `.env`. Do not overwrite an existing configured `.env` when updating the application.


## API logging

DRF requests emit one structured JSON completion log to stdout with timestamp, level, logger, request_id, method, route template, HTTP status and duration_ms. Successful responses log at INFO, client errors at WARNING, and server errors at ERROR. Unhandled API exceptions also log their server-side traceback using the same correlation ID. Request bodies, query strings, authorization headers and cookies are not logged by the request logger. Non-API/static requests are excluded.

Every API response includes X-Request-ID. Clients can provide a UUID in X-Request-ID; invalid values are replaced with a generated UUID. The context is cleared after each request. Cross-origin frontends may read the response header. Set LOG_LEVEL in `.env` to adjust application verbosity (default INFO); restart the service after changes.

View logs with `docker compose logs -f web`. Logs go to the container logging driver instead of local files, allowing the deployment platform to manage retention and aggregation. Keep traceback logs restricted to operators.



## Frontend structure

React code is organized by feature. `src/app/App.jsx` composes the shared shell and the decision feature. The page owns decision filter state, the hook handles request lifecycle/cancellation and retries, and presentational components receive data and callbacks as props. API endpoint paths and CSV URL construction live in the feature API module. Chart geometry is separated from JSX.

```text
frontend/src/
  app/App.jsx
  components/layout/AppLayout.jsx
  features/decisions/
    DecisionPage.jsx
    constants.js
    api/decisions.js
    hooks/useDecision.js
    utils/chart.js
    components/
      DecisionHeading.jsx
      DecisionFilters.jsx
      MetricCards.jsx
      GenerationChart.jsx
      ForecastQuality.jsx
      PeriodTable.jsx
      SourceFooter.jsx
      Methodology.jsx
  lib/
    api.js
    format.js
  styles/global.css
  main.jsx
```

Keep domain-specific additions inside their feature folder; put shared layout and cross-feature utilities in components and lib. Decision filter state survives navigation between overview and methodology. Presentational components do not fetch data. Use `npm run format` to apply Prettier and `npm run format:check` to verify it, then `npm run build` for the production bundle.

## Browser verification with Puppeteer

With the application running, use `cd frontend` then `npm run test:browser`. The script opens Chrome, checks the populated dashboard, changes the decision date and cutoff, verifies methodology navigation preserves filters, downloads and validates the CSV, checks mobile overflow, and fails on browser JavaScript exceptions. All seven checks passed against the Docker application. The run also identified and fixed mobile grid overflow and filter-label encoding.

The default Windows Chrome path is used; set CHROME_PATH to your Chrome executable on another machine. Set TEST_BASE_URL to test another local deployment. Screenshots, downloaded CSV and report.json are saved under frontend/test-results (ignored by Git and Docker). The browser is closed at the end of the run.

## External API circuit breaker

The Elexon integration shares a thread-safe circuit breaker across clients in the same process. ELEXON_CIRCUIT_FAILURE_THRESHOLD (default 3) counts consecutive failed logical requests after HTTP retries are exhausted. Network errors, timeouts, HTTP 429/5xx and malformed JSON/array payloads count; ordinary 4xx errors do not. A success resets the count.

When open, calls fail immediately with CircuitBreakerError and do not contact Elexon. After ELEXON_CIRCUIT_RECOVERY_TIMEOUT seconds (default 60), only one half-open recovery probe is admitted. A successful probe closes the circuit; a failed probe starts a fresh cooldown. State transitions are logged without request parameters. Existing HTTP timeouts and bounded retries still apply before the circuit opens.

Imports handle open-circuit errors as ImportFailure, retain existing database records, and exit cleanly. Dashboard endpoints read stored data and remain available without upstream requests. The circuit is process-local: workers do not share state, and restarting a CLI import starts a new circuit. For a distributed ingestion deployment, use shared breaker storage; the present one-shot CLI importer already stops on its first failed call rather than repeatedly hammering the upstream. This does not guarantee availability during failures of our own server or database.

The shared factory in `backend/common/circuit_breaker.py` returns `pybreaker.CircuitBreaker` directly. It configures the library and attaches a logging listener; there is no custom circuit-breaker state machine. Integrations supply their own failure predicate. Ingestion handles `pybreaker.CircuitBreakerError`.

## Recorded demo

A captioned product walkthrough can be generated with `cd frontend` then `npm run record:demo`. It records the actual running Docker app in a background Chrome browser, shows changing dates/cutoffs and methodology, validates a CSV download, and encodes H.264 MP4 using FFmpeg. Output is saved under `frontend/test-results/demo/wind-desk-demo.mp4`. It has on-screen explanations and no voice narration. Chrome must be installed (or set CHROME_PATH); TEST_BASE_URL overrides localhost:8000.


## Retry and circuit protection

Elexon requests follow pybreaker -> Tenacity -> requests. Tenacity owns all retries. ELEXON_RETRY_ATTEMPTS defaults to 3 total attempts, with exponential waits of 1 and 2 seconds capped at 10. Only network errors, 429/5xx responses and malformed payloads are retried. A final failed retry sequence counts as one breaker failure; an open breaker skips retries and HTTP entirely.

There is no Django response cache or stale fallback. Each admitted integration call fetches upstream data. Exhausted retries or CircuitBreakerError become a clean ImportFailure, preserving existing database records and the last successful import timestamp. Dashboard views continue reading stored database data without depending on upstream availability.

## Frontend validation

Decision input validation lives in `frontend/src/features/decisions/validation/input.js`. Only January 2026 dates and HH:MM times from 00:00 through 23:59 are accepted. Empty and out-of-range fields display accessible inline errors; invalid input prevents data fetching and hides CSV export. API and export URL helpers also validate their inputs.

The shared HTTP client validates the standard response envelope and rejects invalid JSON. Feature response validators check dashboard timestamps, 48-period series, duplicate targets, finite numeric metrics, coverage counts and source-status types before React stores the result. Invalid response data displays a recoverable error instead of reaching the chart or table. DRF remains responsible for server-side input validation; browser checks do not replace it.

Run `cd frontend` then `npm test` for six validation test groups. `npm run test:browser` also checks that an invalid date sends zero API requests and that a malformed dashboard response is rejected with a visible error and supports retry.


The Elexon client uses Tenacity's explicit Retrying object rather than creating a decorated bound method dynamically. The call flow is `endpoint method -> get_response -> pybreaker.call -> _fetch_with_retry -> requests.get`. This ensures one exhausted retry sequence is one circuit failure. In the current one-shot CLI workflow, ingestion exits at its first failed request, so the process-local breaker typically does not accumulate enough failures to open; it becomes useful when a long-running caller reuses the integration. The database-only dashboard is what isolates normal page requests from Elexon outages.



## Vercel pilot deployment

The root configuration deploys Django and the React build together, using Vercel's Django framework support. `build_vercel.py` builds the frontend, verifies the bundled historical database, and copies the frontend into Django's public directory. Vercel collects those assets for its CDN. `wsgi.py` selects `config.vercel_settings`, which always disables debug mode and opens `backend/data/pilot.sqlite3` in SQLite read-only mode.

1. Import the real Elexon history locally if it is not already present.
2. Run `.\.venv\Scripts\python.exe scripts/prepare_vercel.py` from the repository root to create a consistent snapshot. The current prepared snapshot contains 1,488 actuals and 17,864 forecasts.
3. Link/create the `wind-desk` Vercel project under the intended team. Set a new, random `SECRET_KEY` as an encrypted environment variable for production and preview. Do not upload the local `.env` file.
4. Deploy from the repository root with the Django preset and `python build_vercel.py` as the build command; the checked-in `vercel.json` supplies both. Use Python 3.12, as pinned in `.python-version`.
5. Verify `/`, `/api/v1/status/`, `/api/v1/dashboard/?decision_date=2026-01-15&cutoff=10:00`, static assets, and CSV export on the deployed URL.

The `.vercelignore` excludes local secrets, environments, dependencies, recordings, and the writable development database. It explicitly includes the prepared pilot snapshot. The snapshot is read-only at runtime: to refresh the historical dataset, import locally, prepare a new snapshot, and redeploy. A future continuously ingested production service should use an external managed database and ingestion job.

Local deployment checks passed: frontend production build, Django system checks, homepage/API/static asset responses, read-only snapshot configuration, 37 backend tests, and Ruff lint. Production URL: [https://wind-desk-snowy.vercel.app/](https://wind-desk-snowy.vercel.app/). The populated dashboard was verified without signing in on October 28, 2026. Deployment dependencies are declared in pyproject.toml because Vercel gives it precedence over requirements.txt. The build explicitly collects static files, and the function includes the generated frontend and read-only snapshot.
