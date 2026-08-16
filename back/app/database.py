import asyncio
import logging

import asyncpg
from app.config import DATABASE_URL

logger = logging.getLogger(__name__)
pool: asyncpg.Pool | None = None


async def connect_db():
    """Create the connection pool and ensure the table exists."""
    global pool

    if pool is not None:
        return

    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS names (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            )
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'client',
                admin_requested BOOLEAN NOT NULL DEFAULT FALSE,
                staff_requested BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT now()
            )
            """
        )

        await conn.execute(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS hashed_password TEXT,
            ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'client',
            ADD COLUMN IF NOT EXISTS admin_requested BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS staff_requested BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
            """
        )

        await conn.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                      AND column_name = 'password_hash'
                ) THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'users'
                          AND column_name = 'hashed_password'
                    ) THEN
                        ALTER TABLE users RENAME COLUMN password_hash TO hashed_password;
                    ELSE
                        UPDATE users
                        SET hashed_password = password_hash
                        WHERE hashed_password IS NULL;
                        ALTER TABLE users DROP COLUMN password_hash;
                    END IF;
                END IF;
            END
            $$;
            """
        )

        await conn.execute(
            """
            UPDATE users
            SET hashed_password = ''
            WHERE hashed_password IS NULL;
            """
        )

        await conn.execute(
            """
            ALTER TABLE users
            ALTER COLUMN hashed_password SET NOT NULL,
            ALTER COLUMN hashed_password DROP DEFAULT;
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                sku TEXT NOT NULL UNIQUE,
                dosage_form TEXT,
                strength TEXT,
                unit TEXT,
                quantity_in_stock INTEGER NOT NULL DEFAULT 0,
                reorder_threshold INTEGER,
                expiry_date DATE,
                requires_prescription BOOLEAN NOT NULL DEFAULT FALSE,
                manufacturer TEXT,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
            """
        )


async def disconnect_db():
    """Close the connection pool on shutdown."""
    global pool
    if pool:
        await pool.close()
        pool = None


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool not initialized. Did startup run?")
    return pool
