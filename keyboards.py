from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def menu():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔎 Поиск")], [KeyboardButton(text="📚 Все книги")], [KeyboardButton(text="⭐ Любимые"), KeyboardButton(text="🔖 Закладки")], [KeyboardButton(text="🕘 Недавно прочитанные")]], resize_keyboard=True)

def back_menu(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩️ В меню", callback_data="menu:main")]])

def books(rows, page, total, prefix, extra=None):
    b=InlineKeyboardBuilder()
    for r in rows: b.button(text=f"{r['title']} — {r['author']}", callback_data=f"book:{r['id']}")
    nav=[]
    if page>0: nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}:{page-1}"))
    if (page+1)*5 < total: nav.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"{prefix}:{page+1}"))
    if nav: b.row(*nav)
    b.row(InlineKeyboardButton(text="↩️ В меню", callback_data="menu:main")); return b.as_markup()

def card(book, favorite):
    f="⭐ Убрать" if favorite else "☆ В любимые"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📖 Читать",callback_data=f"read:{book['id']}"), InlineKeyboardButton(text=f,callback_data=f"fav:{book['id']}")],[InlineKeyboardButton(text="🔖 Закладка",callback_data=f"mark:{book['id']}"),InlineKeyboardButton(text="🎧 Озвучить",callback_data=f"tts:{book['id']}")],[InlineKeyboardButton(text="↩️ В меню",callback_data="menu:main")]])

def reader(book_id, page, total):
    buttons=[]
    if page > 1: buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page:{book_id}:{page-1}"))
    if page < total: buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page:{book_id}:{page+1}"))
    buttons.append(InlineKeyboardButton(text="🔖 Сохранить прогресс", callback_data=f"savepage:{book_id}:{page}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text="↩️ К книге", callback_data=f"book:{book_id}")]])

