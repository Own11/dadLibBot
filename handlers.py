import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile
from db import connection, search, user_list, all_books
from keyboards import menu, back_menu, books, card, reader
from config import ADMIN_IDS, BOOK_PAGE_SIZE
from tts import chunks
from import_books import split_pages
from book_content import pages as txt_pages

router=Router(); log=logging.getLogger(__name__)
class SearchState(StatesGroup): query=State()

def is_admin(user_id): return user_id in ADMIN_IDS

@router.message(F.text.startswith("/admin_add"))
async def admin_add(m: Message):
    if not is_admin(m.from_user.id): return await m.answer("Недостаточно прав.")
    parts=m.text.split("|", 3)
    if len(parts) < 3: return await m.answer("Формат: /admin_add | Название | Автор | Текст книги")
    _, title, author, *text = parts
    async with connection() as c:
        bid=await c.fetchval("INSERT INTO books(title,author,text_content) VALUES($1,$2,$3) RETURNING id",title.strip(),author.strip(),text[0].strip() if text else None)
        if text and text[0].strip():
            content=text[0].strip(); pages=[]; start=0
            while start < len(content):
                end=min(start+BOOK_PAGE_SIZE,len(content)); boundary=max(content.rfind("\n",start,end),content.rfind(". ",start,end))
                if boundary > start+BOOK_PAGE_SIZE//2: end=boundary+1
                pages.append(content[start:end].strip()); start=end
            await c.executemany("INSERT INTO book_pages(book_id,page_no,content) VALUES($1,$2,$3)",[(bid,i+1,p) for i,p in enumerate(pages) if p])
    await m.answer(f"Книга добавлена, id={bid}.")

@router.message(F.text.startswith("/admin_delete"))
async def admin_delete(m: Message):
    if not is_admin(m.from_user.id): return await m.answer("Недостаточно прав.")
    try: bid=int(m.text.split(maxsplit=1)[1])
    except (ValueError, IndexError): return await m.answer("Формат: /admin_delete <id>")
    async with connection() as c: result=await c.execute("DELETE FROM books WHERE id=$1",bid)
    await m.answer("Книга удалена." if result.endswith("1") else "Книга не найдена.")

@router.message(F.text == "/admin_books")
async def admin_books(m: Message):
    if not is_admin(m.from_user.id): return await m.answer("Недостаточно прав.")
    async with connection() as c: rows=await c.fetch("SELECT id,title,author FROM books ORDER BY id DESC LIMIT 50")
    await m.answer("\n".join(f"{r['id']}. {r['title']} — {r['author']}" for r in rows) or "Каталог пуст.")

async def show_list(target, user_id, kind, page=0):
    async with connection() as c:
        rows,total=await user_list(c,user_id,kind,page)
    title={"fav":"⭐ Любимые","mark":"🔖 Закладки","recent":"🕘 Недавно прочитанные"}[kind]
    text=title if rows else f"{title}\nПока здесь ничего нет."
    await target.edit_text(text, reply_markup=books(rows,page,total,f"{kind}_page") if rows else back_menu())

@router.message(CommandStart())
async def start(m: Message, state: FSMContext): await state.clear(); await m.answer("Добро пожаловать в библиотеку!", reply_markup=menu())
@router.message(F.text == "🔎 Поиск")
async def ask_search(m: Message, state: FSMContext): await state.set_state(SearchState.query); await m.answer("Введите название книги или автора:")
@router.message(F.text == "📚 Все книги")
async def all_books_message(m: Message):
    async with connection() as c: rows,total=await all_books(c,0)
    await m.answer("📚 Все книги" if rows else "Каталог пуст.", reply_markup=books(rows,0,total,"all_page") if rows else back_menu())
@router.message(SearchState.query)
async def do_search(m: Message, state: FSMContext):
    q=m.text.strip(); await state.update_data(query=q)
    async with connection() as c: rows,total=await search(c,q,m.from_user.id,0)
    await m.answer(f"Результаты поиска: {q}" if rows else "Ничего не найдено.", reply_markup=books(rows,0,total,"search") if rows else back_menu())
@router.message(F.text == "⭐ Любимые")
async def fav(m: Message):
    async with connection() as c: rows,total=await user_list(c,m.from_user.id,"fav",0)
    await m.answer("⭐ Любимые" if rows else "⭐ Любимые\nПока здесь ничего нет.", reply_markup=books(rows,0,total,"fav_page") if rows else back_menu())
@router.message(F.text == "🔖 Закладки")
async def mark(m: Message):
    async with connection() as c: rows,total=await user_list(c,m.from_user.id,"mark",0)
    await m.answer("🔖 Закладки" if rows else "🔖 Закладки\nПока здесь ничего нет.", reply_markup=books(rows,0,total,"mark_page") if rows else back_menu())
@router.message(F.text == "🕘 Недавно прочитанные")
async def recent(m: Message):
    async with connection() as c: rows,total=await user_list(c,m.from_user.id,"recent",0)
    await m.answer("🕘 Недавно прочитанные" if rows else "🕘 Недавно прочитанные\nПока здесь ничего нет.", reply_markup=books(rows,0,total,"recent_page") if rows else back_menu())

@router.callback_query()
async def callbacks(q: CallbackQuery, state: FSMContext, bot: Bot):
    d=q.data; uid=q.from_user.id; await q.answer()
    if d=="menu:main": await q.message.answer("Главное меню",reply_markup=menu()); return
    if d.startswith("menu:"):
        kind={"menu:fav":"fav","menu:mark":"mark","menu:recent":"recent"}[d]; await show_list(q.message,uid,kind); return
    if d.startswith("all_page:"):
        page=int(d.split(":")[1])
        async with connection() as c: rows,total=await all_books(c,page)
        await q.message.edit_text("📚 Все книги",reply_markup=books(rows,page,total,"all_page")); return
    if d.startswith(("fav_page:","mark_page:","recent_page:")):
        p=d.split(":"); await show_list(q.message,uid,{"fav_page":"fav","mark_page":"mark","recent_page":"recent"}[p[0]],int(p[1])); return
    if d.startswith("search:"):
        data=await state.get_data(); qtext=data.get("query",""); page=int(d.split(":")[1])
        async with connection() as c: rows,total=await search(c,qtext,uid,page)
        await q.message.edit_text(f"Результаты поиска: {qtext}",reply_markup=books(rows,page,total,"search")); return
    bid=int(d.split(":")[1])
    async with connection() as c:
        if d.startswith("page:"):
            _, book_id, page = d.split(":"); book_id=int(book_id); page=int(page)
            book=await c.fetchrow("SELECT title,author FROM books WHERE id=$1",book_id)
            txt=txt_pages(book['title'],book['author']) if book else []
            if txt:
                page=int(page)
                if page < 1 or page > len(txt): await q.answer("Страница не найдена",show_alert=True); return
                await c.execute("INSERT INTO user_books(user_id,book_id,last_page,last_opened_at) VALUES($1,$2,$3,NOW()) ON CONFLICT(user_id,book_id) DO UPDATE SET last_page=$3,last_opened_at=NOW()",uid,book_id,page)
                await q.message.edit_text(f"📖 {book['title']}\n\n{txt[page-1]}\n\nСтраница {page}/{len(txt)}",reply_markup=reader(book_id,page,len(txt))); return
            row=await c.fetchrow("SELECT b.title,p.content,(SELECT count(*) FROM book_pages WHERE book_id=$1) total FROM book_pages p JOIN books b ON b.id=p.book_id WHERE p.book_id=$1 AND p.page_no=$2",book_id,page)
            if not row: await q.answer("Страница не найдена",show_alert=True); return
            await c.execute("INSERT INTO user_books(user_id,book_id,last_page,last_opened_at) VALUES($1,$2,$3,NOW()) ON CONFLICT(user_id,book_id) DO UPDATE SET last_page=$3,last_opened_at=NOW()",uid,book_id,page)
            await q.message.edit_text(f"📖 {row['title']}\n\n{row['content']}\n\nСтраница {page}/{row['total']}",reply_markup=reader(book_id,page,row['total'])); return
        if d.startswith("savepage:"):
            _, book_id, page=d.split(":")
            await c.execute("INSERT INTO user_books(user_id,book_id,last_page,last_opened_at) VALUES($1,$2,$3,NOW()) ON CONFLICT(user_id,book_id) DO UPDATE SET last_page=$3,last_opened_at=NOW()",uid,int(book_id),int(page)); await q.answer("Прогресс сохранён"); return
        if d.startswith("book:"):
            b=await c.fetchrow("SELECT b.*,COALESCE(ub.is_favorite,FALSE) is_favorite FROM books b LEFT JOIN user_books ub ON ub.book_id=b.id AND ub.user_id=$1 WHERE b.id=$2",uid,bid)
            await q.message.edit_text(f"📚 {b['title']}\nАвтор: {b['author']}\nЖанр: {b['genre'] or '—'}",reply_markup=card(b,b['is_favorite'])); return
        if d.startswith("fav:"):
            favv=await c.fetchval("INSERT INTO user_books(user_id,book_id,is_favorite) VALUES($1,$2,TRUE) ON CONFLICT(user_id,book_id) DO UPDATE SET is_favorite=NOT user_books.is_favorite RETURNING is_favorite",uid,bid)
            await q.message.edit_reply_markup(reply_markup=card(await c.fetchrow("SELECT * FROM books WHERE id=$1",bid),favv)); return
        if d.startswith("mark:"):
            await c.execute("INSERT INTO user_books(user_id,book_id,last_page,last_opened_at) VALUES($1,$2,1,NOW()) ON CONFLICT(user_id,book_id) DO UPDATE SET last_page=$3,last_opened_at=NOW()",uid,bid,1); await q.answer("Закладка сохранена"); return
        if d.startswith("read:"):
            b=await c.fetchrow("SELECT b.*,COALESCE(ub.last_page,1) last_page FROM books b LEFT JOIN user_books ub ON ub.book_id=b.id AND ub.user_id=$1 WHERE b.id=$2",uid,bid); await c.execute("INSERT INTO user_books(user_id,book_id,last_opened_at) VALUES($1,$2,NOW()) ON CONFLICT(user_id,book_id) DO UPDATE SET last_opened_at=NOW()",uid,bid)
            # Основной источник текста — TXT в репозитории, а не Neon.
            page_rows=txt_pages(b['title'], b['author'])
            total=len(page_rows)
            if total:
                page=min(int(b['last_page']),total); await q.message.answer(f"📖 {b['title']}\n\n{page_rows[page-1]}\n\nСтраница {page}/{total}",reply_markup=reader(bid,page,total)); return
            total=await c.fetchval("SELECT count(*) FROM book_pages WHERE book_id=$1",bid)
            # Для старых записей создаём страницы лениво из text_content.
            if not total and b['text_content']:
                page_rows=split_pages(b['text_content'])
                await c.executemany("INSERT INTO book_pages(book_id,page_no,content) VALUES($1,$2,$3) ON CONFLICT(book_id,page_no) DO NOTHING",[(bid,i+1,p) for i,p in enumerate(page_rows)])
                total=len(page_rows)
            if total:
                page=min(int(b['last_page']),total); row=await c.fetchrow("SELECT content FROM book_pages WHERE book_id=$1 AND page_no=$2",bid,page)
                await q.message.answer(f"📖 {b['title']}\n\n{row['content']}\n\nСтраница {page}/{total}",reply_markup=reader(bid,page,total)); return
            if b['file_id']: await bot.send_document(uid,b['file_id'])
            elif b['file_path']: await bot.send_document(uid,FSInputFile(b['file_path']))
            else: await q.answer("Файл книги не загружен",show_alert=True)
        if d.startswith("tts:"):
            b=await c.fetchrow("SELECT text_content FROM books WHERE id=$1",bid)
            if not b or not b['text_content']: await q.answer("Для книги нет текста",show_alert=True); return
            cs=chunks(b['text_content']); job=await c.fetchval("INSERT INTO audio_jobs(user_id,book_id,total_chunks) VALUES($1,$2,$3) RETURNING id",uid,bid,len(cs))
            await c.executemany("INSERT INTO audio_chunks(job_id,chunk_index,text_content) VALUES($1,$2,$3)",[(job,i,x) for i,x in enumerate(cs)])
            await q.message.answer("Озвучка запущена, это может занять время. Я пришлю аудио, когда будет готово.")

