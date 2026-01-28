import os
from contextlib import contextmanager

import psycopg2

_last_query = None
_last_params = None


def _db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "appdb"),
        "user": os.getenv("DB_USER", "appuser"),
        "password": os.getenv("DB_PASSWORD", "apppass"),
    }


@contextmanager
def get_conn():
    conn = psycopg2.connect(**_db_config())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_one(query: str, params: tuple | None = None):
    global _last_query, _last_params
    _last_query, _last_params = query, params
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetch_all(query: str, params: tuple | None = None):
    global _last_query, _last_params
    _last_query, _last_params = query, params
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def execute(query: str, params: tuple | None = None):
    global _last_query, _last_params
    _last_query, _last_params = query, params
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)


def last_query():
    return _last_query, _last_params


def fetch_value(query: str, params: tuple | None = None):
    row = fetch_one(query, params)
    if row is None:
        return None
    return row[0]
