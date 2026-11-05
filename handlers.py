import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile
from db import connection, search, user_list
from keyboards import menu, back_menu, books, card
from tts import chunks

router=Router(); log=logging.getLogger(__name__)
class SearchState(StatesGroup): query=State()

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
@router.message(SearchState.query)
async def do_search(m: Message, state: FSMContext):
    q=m.text.strip(); await state.update_data(query=q); await state.clear()
    async with connection() as c: rows,total=await search(c,q,m.from_user.id,0)
    await m.answer(f"Результаты поиска: {q}" if rows else "Ничего не найдено.", reply_markup=books(rows,0,total,"search") if rows else back_menu())
@router.message(F.text == "⭐ Любимые")
async def fav(m: Message): await m.answer("⭐ Любимые");
@router.message(F.text == "🔖 Закладки")
async def mark(m: Message): await m.answer("🔖 Закладки");
@router.message(F.text == "🕘 Недавно прочитанные")
async def recent(m: Message): await m.answer("🕘 Недавно прочитанные");

@router.callback_query()
async def callbacks(q: CallbackQuery, state: FSMContext, bot: Bot):
    d=q.data; uid=q.from_user.id; await q.answer()
    if d=="menu:main": await q.message.answer("Главное меню",reply_markup=menu()); return
    if d.startswith("menu:"):
        kind={"menu:fav":"fav","menu:mark":"mark","menu:recent":"recent"}[d]; await show_list(q.message,uid,kind); return
    if d.startswith(("fav_page:","mark_page:","recent_page:")):
        p=d.split(":"); await show_list(q.message,uid,{"fav_page":"fav","mark_page":"mark","recent_page":"recent"}[p[0]],int(p[1])); return
    if d.startswith("search:"):
        data=await state.get_data(); qtext=data.get("query",""); page=int(d.split(":")[1])
        async with connection() as c: rows,total=await search(c,qtext,uid,page)
        await q.message.edit_text(f"Результаты поиска: {qtext}",reply_markup=books(rows,page,total,"search")); return
    bid=int(d.split(":")[1])
    async with connection() as c:
        if d.startswith("book:"):
            b=await c.fetchrow("SELECT b.*,COALESCE(ub.is_favorite,FALSE) is_favorite FROM books b LEFT JOIN user_books ub ON ub.book_id=b.id AND ub.user_id=$1 WHERE b.id=$2",uid,bid)
            await q.message.edit_text(f"📚 {b['title']}\nАвтор: {b['author']}\nЖанр: {b['genre'] or '—'}",reply_markup=card(b,b['is_favorite'])); return
        if d.startswith("fav:"):
            favv=await c.fetchval("INSERT INTO user_books(user_id,book_id,is_favorite) VALUES($1,$2,TRUE) ON CONFLICT(user_id,book_id) DO UPDATE SET is_favorite=NOT user_books.is_favorite RETURNING is_favorite",uid,bid)
            await q.message.edit_reply_markup(reply_markup=card(await c.fetchrow("SELECT * FROM books WHERE id=$1",bid),favv)); return
        if d.startswith("mark:"):
            await c.execute("INSERT INTO user_books(user_id,book_id,last_page,last_opened_at) VALUES($1,$2,1,NOW()) ON CONFLICT(user_id,book_id) DO UPDATE SET last_page=$3,last_opened_at=NOW()",uid,bid,1); await q.answer("Закладка сохранена"); return
        if d.startswith("read:"):
            b=await c.fetchrow("SELECT * FROM books WHERE id=$1",bid); await c.execute("INSERT INTO user_books(user_id,book_id,last_opened_at) VALUES($1,$2,NOW()) ON CONFLICT(user_id,book_id) DO UPDATE SET last_opened_at=NOW()",uid,bid)
            if b['file_id']: await bot.send_document(uid,b['file_id'])
            elif b['file_path']: await bot.send_document(uid,FSInputFile(b['file_path']))
            else: await q.answer("Файл книги не загружен",show_alert=True)
        if d.startswith("tts:"):
            b=await c.fetchrow("SELECT text_content FROM books WHERE id=$1",bid)
            if not b or not b['text_content']: await q.answer("Для книги нет текста",show_alert=True); return
            cs=chunks(b['text_content']); job=await c.fetchval("INSERT INTO audio_jobs(user_id,book_id,total_chunks) VALUES($1,$2,$3) RETURNING id",uid,bid,len(cs))
            await c.executemany("INSERT INTO audio_chunks(job_id,chunk_index,text_content) VALUES($1,$2,$3)",[(job,i,x) for i,x in enumerate(cs)])
            await q.message.answer("Озвучка запущена, это может занять время. Я пришлю аудио, когда будет готово.")

