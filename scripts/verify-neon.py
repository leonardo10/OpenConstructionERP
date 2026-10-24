"""Live Neon round trip using the application's drivers; no persistent test data."""
import argparse
import asyncio
import json
import re
import sys
import urllib.request
import uuid

from sqlalchemy import create_engine, text
from app.config import get_settings


def verify_direct():
    engine = create_engine(get_settings().database_sync_url, connect_args={"connect_timeout": 30})
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
            assert connection.connection.driver_connection.info.ssl_in_use, "Client TLS is required"
            print("PASS direct migration connection: SELECT 1; client TLS enabled", flush=True)
    finally:
        engine.dispose()


async def verify_application_driver():
    from app.database import engine

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text("CREATE TEMP TABLE oe_neon_probe (value text) ON COMMIT DROP"))
                value = str(uuid.uuid4())
                await connection.execute(text("INSERT INTO oe_neon_probe (value) VALUES (:value)"), {"value": value})
                result = await connection.execute(text("SELECT value FROM oe_neon_probe"))
                assert result.scalar_one() == value
            finally:
                await transaction.rollback()
        print("PASS application SQLAlchemy/asyncpg: write/read round trip; transaction rolled back", flush=True)
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-only", action="store_true")
    parser.add_argument("--app-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    verify_direct()
    asyncio.run(verify_application_driver())
    if not args.database_only:
        with urllib.request.urlopen(args.app_url.rstrip("/") + "/api/health", timeout=60) as response:
            result = json.load(response)
        assert result.get("database") == "ok", "Application health did not confirm database access"
        print(f"PASS HTTP /api/health: database=ok, status={result.get('status')}", flush=True)
        with urllib.request.urlopen(args.app_url.rstrip("/") + "/", timeout=60) as response:
            assert response.status == 200
            html = response.read().decode()
            assert "<html" in html.lower()
            entry = re.search(r'<script[^>]+src="([^\"]*/assets/[^\"]+\.js)"', html)
            assert entry, "Expected the Vite build's JavaScript entry point"
        with urllib.request.urlopen(args.app_url.rstrip("/") + entry.group(1), timeout=60) as response:
            assert response.status == 200
            assert "javascript" in response.headers.get("Content-Type", "")
        print("PASS HTTP /: built frontend served", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Driver exceptions can contain DSNs or query parameters. Keep the
        # public verification output free of credentials.
        print(f"FAIL {type(error).__name__}; inspect the local configuration and server logs", file=sys.stderr)
        sys.exit(1)
