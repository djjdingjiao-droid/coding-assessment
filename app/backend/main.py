from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Variant PDP API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)


@dataclass
class Sku:
    id: str
    colour: str
    size: str
    price_cents: int
    stock: int
    image: str


PRODUCT = {
    "id": "trail-jacket",
    "name": "Trail Jacket",
    "description": "A light waterproof jacket for changing weather.",
    "options": {"colour": ["Ocean", "Moss", "Clay"], "size": ["S", "M", "L"]},
}
SKUS = {
    sku.id: sku for sku in [
        Sku("ocean-s", "Ocean", "S", 12900, 4, "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800"),
        Sku("ocean-m", "Ocean", "M", 12900, 1, "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800"),
        Sku("ocean-l", "Ocean", "L", 12900, 0, "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800"),
        Sku("moss-s", "Moss", "S", 12500, 3, "https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=800"),
        Sku("moss-m", "Moss", "M", 12500, 2, "https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=800"),
        Sku("moss-l", "Moss", "L", 12500, 1, "https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=800"),
        # 不提供 Clay/L：用于无效的规格组合。
        Sku("clay-s", "Clay", "S", 13500, 2, "https://images.unsplash.com/photo-1523779917675-b6ed3a42a561?w=800"),
        Sku("clay-m", "Clay", "M", 13500, 2, "https://images.unsplash.com/photo-1523779917675-b6ed3a42a561?w=800"),
    ]
}
cart: dict[str, int] = {}
idempotency: dict[str, tuple[str, dict]] = {}
lock = asyncio.Lock()


class CartItemInput(BaseModel):
    sku_id: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=99)


def serialise_sku(sku: Sku) -> dict:
    return {"id": sku.id, "options": {"colour": sku.colour, "size": sku.size},
            "price_cents": sku.price_cents, "available_quantity": sku.stock, "image": sku.image}


def cart_response() -> dict:
    items = [{"sku_id": sku_id, "quantity": quantity} for sku_id, quantity in cart.items()]
    return {"items": items, "item_count": sum(cart.values())}


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    if product_id != PRODUCT["id"]:
        raise HTTPException(404, detail={"code": "PRODUCT_NOT_FOUND", "message": "Product not found"})
    return {**PRODUCT, "skus": [serialise_sku(sku) for sku in SKUS.values()]}


@app.get("/api/cart")
def get_cart() -> dict:
    return cart_response()


@app.post("/api/cart/items", status_code=201)
async def add_cart_item(item: CartItemInput, idempotency_key: Annotated[str | None, Header()] = None) -> dict:
    if not idempotency_key:
        raise HTTPException(400, detail={"code": "IDEMPOTENCY_KEY_REQUIRED", "message": "Idempotency-Key is required"})
    body_fingerprint = hashlib.sha256(item.model_dump_json().encode()).hexdigest()
    async with lock:
        replay = idempotency.get(idempotency_key)
        if replay:
            if replay[0] != body_fingerprint:
                raise HTTPException(409, detail={"code": "IDEMPOTENCY_KEY_REUSED", "message": "Key belongs to a different request"})
            return {**replay[1], "idempotent_replay": True}
        sku = SKUS.get(item.sku_id)
        if not sku:
            raise HTTPException(404, detail={"code": "SKU_NOT_FOUND", "message": "SKU not found"})
        if item.quantity > sku.stock:
            raise HTTPException(409, detail={"code": "INSUFFICIENT_STOCK", "message": "Requested quantity is no longer available"})
        sku.stock -= item.quantity
        cart[sku.id] = cart.get(sku.id, 0) + item.quantity
        response = {"cart": cart_response(), "sku": serialise_sku(sku), "idempotent_replay": False}
        idempotency[idempotency_key] = (body_fingerprint, response)
        return response

