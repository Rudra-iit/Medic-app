import logging
from typing import Literal, Optional

import asyncpg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Depends
from app.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_admin_user,
    get_current_staff_or_admin_user,
    get_current_user,
    get_current_user_optional,
)
from app.database import connect_db, disconnect_db, get_pool
from app.models import (
    CategoryCreate,
    CategoryOut,
    NameCreate,
    NameOut,
    ProductCreate,
    ProductOut,
    ProductStockUpdate,
    ProductUpdate,
    RoleRequestAction,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
    UserRequestOut,
    UserRoleUpdate,
)

logger = logging.getLogger(__name__)
app = FastAPI(title="Name Registry API")

# In production, replace "*" with your deployed Angular app's exact URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    try:
        await connect_db()
    except Exception as exc:
        logger.exception("Database initialization failed during startup: %s", exc)


@app.on_event("shutdown")
async def on_shutdown():
    await disconnect_db()


@app.get("/")
async def root():
    return {"status": "ok", "service": "Name Registry API"}


@app.post("/auth/register", response_model=Token, status_code=201)
async def register(payload: UserCreate):
    user = await create_user(payload)
    access_token = create_access_token({"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/login", response_model=Token)
async def login(payload: UserLogin):
    user = await authenticate_user(payload.email, payload.password)
    access_token = create_access_token({"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserOut)
async def me(current_user: UserOut = Depends(get_current_user)):
    return current_user


@app.get("/auth/role-request-status", response_model=UserRequestOut)
async def role_request_status(current_user: UserOut = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, role, admin_requested, staff_requested, created_at FROM users WHERE id = $1",
            current_user.id,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)


@app.get("/admin/user-requests", response_model=list[UserRequestOut])
async def list_user_requests(
    request_type: Optional[Literal["admin", "staff"]]=Query(default=None),
    current_user: UserOut = Depends(get_current_admin_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        if request_type == "admin":
            rows = await conn.fetch(
                "SELECT id, email, role, admin_requested, staff_requested, created_at FROM users "
                "WHERE admin_requested = TRUE ORDER BY created_at"
            )
        elif request_type == "staff":
            rows = await conn.fetch(
                "SELECT id, email, role, admin_requested, staff_requested, created_at FROM users "
                "WHERE staff_requested = TRUE ORDER BY created_at"
            )
        else:
            rows = await conn.fetch(
                "SELECT id, email, role, admin_requested, staff_requested, created_at FROM users "
                "WHERE admin_requested = TRUE OR staff_requested = TRUE ORDER BY created_at"
            )
        return [dict(r) for r in rows]


@app.patch("/admin/users/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    current_user: UserOut = Depends(get_current_admin_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE users SET role = $1, admin_requested = FALSE WHERE id = $2 "
            "RETURNING id, email, role, created_at",
            payload.role,
            user_id,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)


@app.patch("/admin/users/{user_id}/role-request", response_model=UserRequestOut)
async def respond_role_request(
    user_id: int,
    payload: RoleRequestAction,
    current_user: UserOut = Depends(get_current_admin_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        if payload.request_type == "admin":
            if payload.action == "approve":
                row = await conn.fetchrow(
                    "UPDATE users SET role = 'admin', admin_requested = FALSE, staff_requested = FALSE "
                    "WHERE id = $1 RETURNING id, email, role, admin_requested, staff_requested, created_at",
                    user_id,
                )
            else:
                row = await conn.fetchrow(
                    "UPDATE users SET admin_requested = FALSE "
                    "WHERE id = $1 RETURNING id, email, role, admin_requested, staff_requested, created_at",
                    user_id,
                )
        else:
            if payload.action == "approve":
                row = await conn.fetchrow(
                    "UPDATE users SET role = 'staff', staff_requested = FALSE "
                    "WHERE id = $1 RETURNING id, email, role, admin_requested, staff_requested, created_at",
                    user_id,
                )
            else:
                row = await conn.fetchrow(
                    "UPDATE users SET staff_requested = FALSE "
                    "WHERE id = $1 RETURNING id, email, role, admin_requested, staff_requested, created_at",
                    user_id,
                )
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)


@app.get("/names", response_model=list[NameOut])
async def list_names():
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, created_at FROM names ORDER BY id"
        )
        return [dict(r) for r in rows]


@app.post("/names", response_model=NameOut, status_code=201)
async def create_name(payload: NameCreate):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO names (name) VALUES ($1) RETURNING id, name, created_at",
            payload.name.strip(),
        )
        return dict(row)


@app.delete("/names/{name_id}", status_code=204)
async def delete_name(name_id: int):
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM names WHERE id = $1", name_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Name not found")


# ---------- Categories ----------

@app.get("/categories", response_model=list[CategoryOut])
async def list_categories(current_user: Optional[UserOut] = Depends(get_current_user_optional)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, description FROM categories ORDER BY name"
        )
        return [dict(r) for r in rows]


@app.post("/categories", response_model=CategoryOut, status_code=201)
async def create_category(
    payload: CategoryCreate,
    current_user: UserOut = Depends(get_current_admin_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO categories (name, description) VALUES ($1, $2) "
                "RETURNING id, name, description",
                payload.name.strip(),
                payload.description,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Category name already exists")
        return dict(row)


@app.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    current_user: UserOut = Depends(get_current_admin_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.execute(
                "DELETE FROM categories WHERE id = $1", category_id
            )
        except asyncpg.ForeignKeyViolationError:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete a category that still has products in it",
            )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Category not found")


# ---------- Products ----------

@app.get("/products", response_model=list[ProductOut])
async def list_products(
    current_user: Optional[UserOut] = Depends(get_current_user_optional),
    category_id: Optional[int] = Query(default=None),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        if category_id is not None:
            rows = await conn.fetch(
                """
                SELECT id, name, category_id, sku, dosage_form, strength, unit,
                       quantity_in_stock, reorder_threshold, expiry_date,
                       requires_prescription, manufacturer, notes,
                       created_at, updated_at
                FROM products
                WHERE category_id = $1
                ORDER BY name
                """,
                category_id,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, name, category_id, sku, dosage_form, strength, unit,
                       quantity_in_stock, reorder_threshold, expiry_date,
                       requires_prescription, manufacturer, notes,
                       created_at, updated_at
                FROM products
                ORDER BY name
                """
            )
        return [dict(r) for r in rows]


@app.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, current_user: Optional[UserOut] = Depends(get_current_user_optional)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name, category_id, sku, dosage_form, strength, unit,
                   quantity_in_stock, reorder_threshold, expiry_date,
                   requires_prescription, manufacturer, notes,
                   created_at, updated_at
            FROM products WHERE id = $1
            """,
            product_id,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return dict(row)


@app.post("/products", response_model=ProductOut, status_code=201)
async def create_product(
    payload: ProductCreate,
    current_user: UserOut = Depends(get_current_admin_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO products (
                    name, category_id, sku, dosage_form, strength, unit,
                    quantity_in_stock, reorder_threshold, expiry_date,
                    requires_prescription, manufacturer, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id, name, category_id, sku, dosage_form, strength, unit,
                          quantity_in_stock, reorder_threshold, expiry_date,
                          requires_prescription, manufacturer, notes,
                          created_at, updated_at
                """,
                payload.name.strip(),
                payload.category_id,
                payload.sku.strip(),
                payload.dosage_form,
                payload.strength,
                payload.unit,
                payload.quantity_in_stock,
                payload.reorder_threshold,
                payload.expiry_date,
                payload.requires_prescription,
                payload.manufacturer,
                payload.notes,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="SKU already exists")
        except asyncpg.ForeignKeyViolationError:
            raise HTTPException(status_code=400, detail="category_id does not exist")
        return dict(row)


@app.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: UserOut = Depends(get_current_admin_user),
):
    pool = get_pool()
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    set_clauses = []
    values = []
    for i, (field, value) in enumerate(updates.items(), start=1):
        set_clauses.append(f"{field} = ${i}")
        values.append(value)
    set_clauses.append("updated_at = now()")
    values.append(product_id)

    query = f"""
        UPDATE products SET {', '.join(set_clauses)}
        WHERE id = ${len(values)}
        RETURNING id, name, category_id, sku, dosage_form, strength, unit,
                  quantity_in_stock, reorder_threshold, expiry_date,
                  requires_prescription, manufacturer, notes,
                  created_at, updated_at
    """

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(query, *values)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="SKU already exists")
        except asyncpg.ForeignKeyViolationError:
            raise HTTPException(status_code=400, detail="category_id does not exist")
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return dict(row)


@app.patch("/products/{product_id}/stock", response_model=ProductOut)
async def update_product_stock(
    product_id: int,
    payload: ProductStockUpdate,
    current_user: UserOut = Depends(get_current_staff_or_admin_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE products SET quantity_in_stock = $1, updated_at = now() "
            "WHERE id = $2 RETURNING id, name, category_id, sku, dosage_form, strength, unit, "
            "quantity_in_stock, reorder_threshold, expiry_date, requires_prescription, "
            "manufacturer, notes, created_at, updated_at",
            payload.quantity_in_stock,
            product_id,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return dict(row)


@app.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    current_user: UserOut = Depends(get_current_admin_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM products WHERE id = $1", product_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Product not found")

