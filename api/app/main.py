import json
import logging
import time
from typing import List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from app.config import AppConfig
from app.db import close_pool, get_conn, init_pool, is_pool_ready

app = FastAPI(title="API + Postgres Playground")

cfg = AppConfig()
logging.basicConfig(level=cfg.log_level)
logger = logging.getLogger("api")

_rate_limit_state: dict[str, tuple[int, int]] = {}
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cfg.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


def require_api_key(x_api_key: str | None = Security(_api_key_header)):
    expected = cfg.api_key
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class ItemOut(BaseModel):
    id: int
    name: str
    description: str | None


@app.get("/health")
def health():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
    return {"status": "ok"}


@app.get("/health/ready")
def readiness():
    db_ok = False
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok, "pool_ready": is_pool_ready()}


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get(cfg.request_id_header, str(uuid4()))
    start = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            json.dumps(
                {
                    "event": "request_error",
                    "request_id": request_id,
                    "path": request.url.path,
                    "error": str(exc),
                }
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "request_id": request_id},
        )
    duration_ms = int((time.time() - start) * 1000)
    response.headers[cfg.request_id_header] = request_id
    logger.info(
        json.dumps(
            {
                "event": "request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            }
        )
    )
    return response


@app.on_event("startup")
def on_startup():
    init_pool(cfg)


@app.on_event("shutdown")
def on_shutdown():
    close_pool()


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    key = request.client.host if request.client else "unknown"
    now = int(time.time())
    window_start, count = _rate_limit_state.get(key, (now, 0))
    if now - window_start >= cfg.rate_limit_window_seconds:
        window_start, count = now, 0
    count += 1
    _rate_limit_state[key] = (window_start, count)
    if count > cfg.rate_limit_per_minute:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(cfg.rate_limit_window_seconds)},
        )
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(cfg.rate_limit_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(
        max(0, cfg.rate_limit_per_minute - count)
    )
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post(
    "/items",
    response_model=ItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def create_item(item: ItemIn):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id;",
                (item.name, item.description),
            )
            item_id = cur.fetchone()[0]
    return ItemOut(id=item_id, name=item.name, description=item.description)


@app.get("/items/search", response_model=List[ItemOut], dependencies=[Depends(require_api_key)])
def search_items(name: Optional[str] = None, limit: int = 100, offset: int = 0):
    if not name:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                (
                    "SELECT id, name, description FROM items WHERE name ILIKE %s "
                    "ORDER BY id LIMIT %s OFFSET %s;"
                ),
                (f"%{name}%", limit, offset),
            )
            rows = cur.fetchall()
    return [ItemOut(id=r[0], name=r[1], description=r[2]) for r in rows]


@app.get("/items", response_model=List[ItemOut], dependencies=[Depends(require_api_key)])
def list_items(limit: int = 100, offset: int = 0):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description FROM items ORDER BY id LIMIT %s OFFSET %s;",
                (limit, offset),
            )
            rows = cur.fetchall()
    return [ItemOut(id=r[0], name=r[1], description=r[2]) for r in rows]


@app.put("/items/{item_id}", response_model=ItemOut, dependencies=[Depends(require_api_key)])
def update_item(item_id: int, item: ItemIn):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE items SET name = %s, description = %s WHERE id = %s RETURNING id;",
                (item.name, item.description, item_id),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return ItemOut(id=item_id, name=item.name, description=item.description)


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
def delete_item(item_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM items WHERE id = %s RETURNING id;", (item_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return None


@app.get("/items/{item_id}", response_model=ItemOut, dependencies=[Depends(require_api_key)])
def get_item(item_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM items WHERE id = %s;", (item_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return ItemOut(id=row[0], name=row[1], description=row[2])
