from contextlib import asynccontextmanager
import asyncpg
from config import DATABASE_URL

@asynccontextmanager
async def connection():
    """Короткое соединение безопаснее для serverless и лимитов Neon."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

async def search(conn, query, user_id, page, limit=5):
    term = f"%{query}%"; offset = page * limit
    total = await conn.fetchval("SELECT count(*) FROM books WHERE title ILIKE $1 OR author ILIKE $1", term)
    rows = await conn.fetch("""SELECT b.*, COALESCE(ub.is_favorite,FALSE) is_favorite, COALESCE(ub.last_page,1) last_page
        FROM books b LEFT JOIN user_books ub ON ub.book_id=b.id AND ub.user_id=$2
        WHERE b.title ILIKE $1 OR b.author ILIKE $1 ORDER BY b.title LIMIT $3 OFFSET $4""", term, user_id, limit, offset)
    return rows, total

async def all_books(conn, page, limit=5):
    offset=page*limit
    total=await conn.fetchval("SELECT count(*) FROM books")
    rows=await conn.fetch("SELECT * FROM books ORDER BY title LIMIT $1 OFFSET $2",limit,offset)
    return rows,total

async def user_list(conn, user_id, kind, page, limit=5):
    offset = page * limit
    where = {"fav": "ub.is_favorite = TRUE", "mark": "ub.last_page > 1", "recent": "ub.last_opened_at IS NOT NULL"}[kind]
    base = f"FROM user_books ub JOIN books b ON b.id=ub.book_id WHERE ub.user_id=$1 AND {where}"
    total = await conn.fetchval("SELECT count(*) " + base, user_id)
    order = "ub.last_opened_at DESC NULLS LAST" if kind == "recent" else "b.title"
    if kind == "recent":
        # Ограничиваем историю 20 записями, но выдаём пользователю по 5 за страницу.
        rows = await conn.fetch(f"SELECT * FROM (SELECT * {base} ORDER BY {order} LIMIT 20) recent_books LIMIT $2 OFFSET $3", user_id, limit, offset)
        total = min(total, 20)
    else:
        rows = await conn.fetch(f"SELECT * {base} ORDER BY {order} LIMIT $2 OFFSET $3", user_id, limit, offset)
    return rows, total

