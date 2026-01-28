from contextlib import contextmanager

from psycopg2 import pool

from app.config import AppConfig

_pool: pool.SimpleConnectionPool | None = None


def _db_config(cfg: AppConfig):
    return {
        "host": cfg.db_host,
        "port": cfg.db_port,
        "dbname": cfg.db_name,
        "user": cfg.db_user,
        "password": cfg.db_password,
        "connect_timeout": cfg.db_connect_timeout,
    }


def init_pool(cfg: AppConfig):
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            cfg.db_pool_minconn,
            cfg.db_pool_maxconn,
            **_db_config(cfg),
        )


def close_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


def is_pool_ready() -> bool:
    return _pool is not None


@contextmanager
def get_conn():
    cfg = AppConfig()
    if _pool is None:
        init_pool(cfg)
    assert _pool is not None
    conn = _pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout TO %s;", (cfg.db_statement_timeout_ms,))
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)
