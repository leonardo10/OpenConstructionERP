# OpenConstructionERP with Neon

The project is linked locally to Neon project `plain-thunder-95010439`
(OpenERP), organization `org-ancient-bird-21267630`, branch `production`.
Only Postgres is declared. The existing application authentication remains
in place; Neon Auth, Functions, and Object Storage have not been provisioned.

`neon.ts` is the versioned service policy. The CLI writes the local project
binding to `.neon` and credentials to `.env.local`; both are ignored by Git.
Never copy database credentials to frontend variables prefixed with `VITE_`.

## Connections

- `DATABASE_URL`: application connection, using SQLAlchemy and asyncpg.
- `DATABASE_URL_UNPOOLED`: direct connection used to derive the synchronous
  migration connection. An explicit `DATABASE_SYNC_URL` takes precedence.
- The backend reads `.env.local` from the repository root even when started
  from another directory. OS environment variables have higher priority.
- Neon libpq connection parameters are adapted for asyncpg. Hostname and
  certificate verification use a Python SSL context with system CA roots.
  Background job connections use the same TLS configuration.

## Local development (Python 3.12+ and Node.js 22+)

From the repository root:

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -e "./backend[server]"
npm ci
npm --prefix frontend ci
neon deploy
npm run build
npm start
```

On Linux/macOS, use `.venv/bin/python` instead of `.venv\Scripts\python.exe`
in Python commands. `npm start` selects the virtualenv interpreter for the
current OS automatically. The built app is served at http://127.0.0.1:8000.
For frontend hot reload, also run `npm run dev` and open the Vite URL.

The local `.env.local` also contains a generated JWT signing secret and
small connection-pool settings. Demo seeding is disabled to avoid filling
the free database with showcase data. Registration is closed, with the
application's existing first-admin bootstrap exception. The first user
should complete that bootstrap locally before exposing the application.
Generated files are kept under the ignored `.local-data` directory.

## Verification

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests\neon -v
.venv\Scripts\python.exe scripts\verify-neon.py --database-only
# With npm start running:
.venv\Scripts\python.exe scripts\verify-neon.py
```

The live check exercises the actual configured direct connection and the
application's asynchronous database engine. It writes and reads a temporary
table in a transaction, then rolls that transaction back. No permanent test
table or test row is left behind. The full check also verifies the API's
database health and that the built frontend is served over HTTP.

Do not run the full backend pytest suite against the production branch.
Use an isolated Neon development/test branch for future migration testing.
The configuration-only tests above do not connect to a database.

## Hosting

This integration connects the existing Python application to Neon; it does
not deploy the website to Vercel or Cloud Run. Hosting the complete ERP also
requires durable file storage for BIM/uploads and a compatible Python runtime.
The current `neon.ts` does not deploy the Python backend to Neon Functions.

## Optional remote frontend build

`.github/workflows/build-web-preview.yml` is a manual GitHub Actions workflow.
It installs the locked dependencies, runs the root `npm run build`, and saves
`frontend/dist` as a one-day artifact. It does not deploy the website or receive
database credentials. Remote execution is tracked in the fork’s Actions page.

The standard Ubuntu runner for a public repository has 16 GB RAM. Standard
runner execution is free for public repositories; artifact retention remains
subject to GitHub storage allowances. Private repositories have different
runner resources and billing allowances. Review those before using them.

## Verified state — 24 October 2026

- Neon CLI 8.11.1 installed and authenticated.
- `neon deploy` succeeded; production matches the Postgres-only policy.
- Six connection/configuration tests passed.
- Direct PostgreSQL connection: SELECT 1 passed, client TLS enabled.
- Application SQLAlchemy/asyncpg connection: temporary write/read round trip
  passed and was rolled back.
- Running backend: HTTP `/api/health` returned 200, `database=ok`,
  `schema_matches_models=true`, and 213/213 modules loaded.
- Overall backend health is currently `degraded` solely because the frontend
  build is absent (`frontend_dist_present=false`).
- Local `npm run build` was still running at this checkpoint; it has not been
  recorded as passed. The built frontend HTTP checks remain pending.
- Initial `neon init` hit a timeout installing plugins for Codex/Claude.
  Retrying with `--no-agent-setup` completed project setup. The downloaded
  Neon skills were consulted directly.
- The remote GitHub workflow has been prepared and YAML-checked but has not
  been published or executed. Publishing a public fork awaits user approval.
- No GCP VM, Cloud Run service, or Vercel website deployment was created.
