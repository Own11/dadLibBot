"""Загрузить два текста из Викитеки и разложить их на страницы в Neon."""
import asyncio, json, re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import asyncpg
from import_books import split_pages
from config import DATABASE_URL

ROOT=Path(__file__).parent/"book_texts"
BOOKS={"Война и мир|Лев Толстой":"Война и мир (Толстой)","Братья Карамазовы|Фёдор Достоевский":"Братья Карамазовы (Достоевский)"}

def fetch(title):
    params={"action":"parse","page":title,"prop":"wikitext","format":"json","formatversion":2}
    with urlopen("https://ru.wikisource.org/w/api.php?"+urlencode(params),timeout=60) as r:
        raw=json.load(r)["parse"]["wikitext"]
    raw=re.sub(r"\{\{.*?\}\}|\[\[([^]|]+)(?:\|[^]]+)?\]\]|<.*?>",lambda m:m.group(1) if m.group(1) else "",raw,flags=re.S)
    raw=re.sub(r"={2,6}\s*", "\n", raw); return re.sub(r"\n{3,}","\n\n",raw).strip()

async def main():
    ROOT.mkdir(exist_ok=True); conn=await asyncpg.connect(DATABASE_URL)
    try:
        for name,title in BOOKS.items():
            text=fetch(title); book,author=name.split("|",1); (ROOT/(name+".txt")).write_text(text,encoding="utf-8")
            bid=await conn.fetchval("INSERT INTO books(title,author,text_content) VALUES($1,$2,$3) ON CONFLICT DO NOTHING RETURNING id",book,author,text)
            if not bid: bid=await conn.fetchval("SELECT id FROM books WHERE title=$1 AND author=$2",book,author)
            await conn.execute("DELETE FROM book_pages WHERE book_id=$1",bid)
            await conn.executemany("INSERT INTO book_pages(book_id,page_no,content) VALUES($1,$2,$3)",[(bid,i+1,p) for i,p in enumerate(split_pages(text))])
            print(f"{book}: импортировано страниц {len(split_pages(text))}")
    finally: await conn.close()

if __name__=="__main__": asyncio.run(main())
