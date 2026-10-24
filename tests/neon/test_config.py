"""Connection compatibility tests without the full suite's embedded database."""
from pathlib import Path
import tempfile
import ssl
import unittest
from unittest.mock import patch

from sqlalchemy.engine import make_url
from app import config


class NeonConfigTests(unittest.TestCase):
    def test_verified_tls_uses_system_roots(self):
        options = config.asyncpg_tls_connect_args(
            "postgresql+asyncpg://role:fake@ep-example.neon.tech/neondb?ssl=verify-full"
        )
        self.assertIsInstance(options["ssl"], ssl.SSLContext)
        self.assertTrue(options["ssl"].check_hostname)
        self.assertEqual(options["ssl"].verify_mode, ssl.CERT_REQUIRED)

    def test_asyncpg_accepts_neon_libpq_connection_string(self):
        result = make_url(config._canonicalize_db_url(
            "postgresql://role:fake-password@ep-example.neon.tech/neondb"
            "?sslmode=require&channel_binding=require",
            driver="asyncpg",
        ))
        self.assertEqual(result.drivername, "postgresql+asyncpg")
        self.assertEqual(result.query, {"ssl": "verify-full"})
        self.assertEqual(result.host, "ep-example.neon.tech")

    def test_sync_migrations_keep_libpq_tls_options(self):
        result = make_url(config._canonicalize_db_url(
            "postgresql://role:fake-password@ep-example.neon.tech/neondb"
            "?sslmode=require&channel_binding=require",
            driver="psycopg2",
        ))
        self.assertEqual(result.query["sslmode"], "require")
        self.assertEqual(result.query["channel_binding"], "require")

    def test_derived_sync_url_uses_sslmode(self):
        result = make_url(config._canonicalize_db_url(
            "postgresql+asyncpg://role:fake-password@ep-example.neon.tech/neondb?ssl=verify-full",
            driver="psycopg2",
        ))
        self.assertEqual(result.query, {"sslmode": "verify-full"})

    def test_env_local_is_discovered_outside_project_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            app_dir = root / "backend" / "app"
            app_dir.mkdir(parents=True)
            files = [root / "backend" / ".env", root / ".env", root / ".env.local"]
            for file in files:
                file.touch()
            with patch.object(config, "__file__", str(app_dir / "config.py")):
                self.assertEqual(config._find_env_file(), [str(file) for file in files])

    def test_neon_direct_url_is_used_for_migrations(self):
        settings = config.Settings(
            _env_file=None,
            jwt_secret="x" * 64,
            database_url="postgresql://role:fake@ep-example-pooler.neon.tech/neondb?sslmode=require",
            database_url_unpooled="postgresql://role:fake@ep-example.neon.tech/neondb?sslmode=require",
        )
        self.assertEqual(make_url(settings.database_url).host, "ep-example-pooler.neon.tech")
        self.assertEqual(make_url(settings.database_sync_url).host, "ep-example.neon.tech")


if __name__ == "__main__":
    unittest.main()
