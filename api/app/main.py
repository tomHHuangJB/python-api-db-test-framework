import os
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.db import get_conn

app = FastAPI(title="API + Postgres Playground")


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    expected = os.getenv("API_KEY", "local-dev-key")
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
def search_items(name: Optional[str] = None):
    if not name:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description FROM items WHERE name ILIKE %s ORDER BY id;",
                (f"%{name}%",),
            )
            rows = cur.fetchall()
    return [ItemOut(id=r[0], name=r[1], description=r[2]) for r in rows]


@app.get("/items", response_model=List[ItemOut], dependencies=[Depends(require_api_key)])
def list_items():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM items ORDER BY id;")
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
