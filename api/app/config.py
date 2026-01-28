import os
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    api_key: str = os.getenv("API_KEY", "local-dev-key")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    request_id_header: str = os.getenv("REQUEST_ID_HEADER", "X-Request-Id")
    rate_limit_per_minute: int = _get_int("RATE_LIMIT_PER_MINUTE", 1000)
    rate_limit_window_seconds: int = _get_int("RATE_LIMIT_WINDOW_SECONDS", 60)
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = _get_int("DB_PORT", 5432)
    db_name: str = os.getenv("DB_NAME", "appdb")
    db_user: str = os.getenv("DB_USER", "appuser")
    db_password: str = os.getenv("DB_PASSWORD", "apppass")
    db_connect_timeout: int = _get_int("DB_CONNECT_TIMEOUT", 5)
    db_statement_timeout_ms: int = _get_int("DB_STATEMENT_TIMEOUT_MS", 5000)
    db_pool_minconn: int = _get_int("DB_POOL_MINCONN", 1)
    db_pool_maxconn: int = _get_int("DB_POOL_MAXCONN", 5)
