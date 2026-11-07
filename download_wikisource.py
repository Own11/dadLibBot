"""Загрузить два текста из Викитеки и разложить их на страницы в Neon."""
import asyncio, json, re, html
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import asyncpg
from import_books import split_pages
from config import DATABASE_URL

ROOT=Path(__file__).parent/"book_texts"
BOOKS={"Война и мир|Лев Толстой":"Война и мир (Толстой)","Братья Карамазовы|Фёдор Достоевский":"Братья Карамазовы (Достоевский)"}

def request_api(params):
    with urlopen(Request("https://ru.wikisource.org/w/api.php?"+urlencode(params),headers={"User-Agent":"dadlib-book-import/1.0 (personal project)"}),timeout=60) as r:
        return json.load(r)

def linked_pages(title, prefix):
    data=request_api({"action":"query","prop":"links","titles":title,"plnamespace":0,"pllimit":"max","format":"json"})
    pages=next(iter(data["query"]["pages"].values()))
    return [x["title"] for x in pages.get("links",[]) if x["title"].startswith(prefix+"/")]

def fetch(title):
    params={"action":"parse","page":title,"prop":"text","format":"json","formatversion":2}
    raw=request_api(params)["parse"]["text"]
    raw=re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    raw=re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n\n\1\n\n", raw, flags=re.S|re.I)
    raw=re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\n{3,}","\n\n",html.unescape(raw)).strip()

def full_book(title):
    pages=[]; queue=[title]; seen=set()
    for _ in range(4):
        next_queue=[]
        for page in queue:
            if page in seen: continue
            seen.add(page); children=linked_pages(page,title)
            next_queue.extend(children)
            if page != title and children == []: pages.append(page)
        queue=next_queue
        if not queue: break
    if not pages: pages=[title]
    return "\n\n".join(fetch(page) for page in sorted(set(pages)))

async def main():
    ROOT.mkdir(exist_ok=True); conn=await asyncpg.connect(DATABASE_URL)
    try:
        for name,title in BOOKS.items():
            text=full_book(title); book,author=name.split("|",1); (ROOT/(name+".txt")).write_text(text,encoding="utf-8")
            bid=await conn.fetchval("INSERT INTO books(title,author,text_content) VALUES($1,$2,$3) ON CONFLICT DO NOTHING RETURNING id",book,author,text)
            if not bid: bid=await conn.fetchval("SELECT id FROM books WHERE title=$1 AND author=$2",book,author)
            await conn.execute("DELETE FROM book_pages WHERE book_id=$1",bid)
            await conn.executemany("INSERT INTO book_pages(book_id,page_no,content) VALUES($1,$2,$3)",[(bid,i+1,p) for i,p in enumerate(split_pages(text))])
            print(f"{book}: импортировано страниц {len(split_pages(text))}")
    finally: await conn.close()

if __name__=="__main__": asyncio.run(main())
