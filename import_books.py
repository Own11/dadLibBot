"""Импорт легально полученных UTF-8 текстов книг в Neon."""
import asyncio
from pathlib import Path
import asyncpg
from config import DATABASE_URL, BOOK_PAGE_SIZE

ROOT = Path(__file__).parent / "book_texts"

def split_pages(text):
    pages=[]; pos=0
    while pos < len(text):
        end=min(pos+BOOK_PAGE_SIZE,len(text)); cut=max(text.rfind("\n",pos,end),text.rfind(". ",pos,end))
        if cut > pos + BOOK_PAGE_SIZE//2: end=cut+1
        pages.append(text[pos:end].strip()); pos=end
    return [p for p in pages if p]

async def main():
    conn=await asyncpg.connect(DATABASE_URL)
    try:
        for path in ROOT.glob("*.txt"):
            if "|" not in path.stem: print(f"Пропуск {path.name}: нужно Название|Автор.txt"); continue
            title,author=path.stem.split("|",1); text=path.read_text(encoding="utf-8")
            async with conn.transaction():
                bid=await conn.fetchval("INSERT INTO books(title,author,text_content) VALUES($1,$2,$3) ON CONFLICT DO NOTHING RETURNING id",title,author,text)
                if not bid: bid=await conn.fetchval("SELECT id FROM books WHERE title=$1 AND author=$2",title,author)
                await conn.execute("DELETE FROM book_pages WHERE book_id=$1",bid)
                await conn.executemany("INSERT INTO book_pages(book_id,page_no,content) VALUES($1,$2,$3)",[(bid,i+1,p) for i,p in enumerate(split_pages(text))])
            print(f"Импортировано: {title} ({bid})")
    finally: await conn.close()

if __name__ == "__main__": asyncio.run(main())
