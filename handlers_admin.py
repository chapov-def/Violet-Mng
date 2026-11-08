import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from database import async_session, User, ensure_user

router = Router()

# СЮДА ВПИШИ СВОЙ ID (и ID других Главных Админов через запятую)
SUPER_ADMINS = [123456789] 

# Список всех рангов проекта
RANKS = [
    "Игрок",
    "Ютубер",
    "Модератор",
    "Младший Администратор",
    "Средний Администратор",
    "Старший Администратор",
    "ЗГА"
]

async def check_access(user_id: int, required_rank="Модератор"):
    if user_id in SUPER_ADMINS: return True
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user or user.role == "Игрок" or user.role == "Ютубер": 
            return False
        
        # Проверка уровня доступа
        user_index = RANKS.index(user.role) if user.role in RANKS else 0
        required_index = RANKS.index(required_rank) if required_rank in RANKS else 0
        
        return user_index >= required_index

# --- ВЫДАЧА РАНГА (Только для ЗГА и Главных админов) ---
@router.message(Command("ранг"))
async def cmd_set_rank(message: Message):
    if not await check_access(message.from_user.id, "ЗГА"): 
        return await message.answer("❌ У вас нет прав на выдачу рангов (нужен ЗГА).")
    
    if not message.reply_to_message:
        return await message.answer("⚠️ Ответь на сообщение игрока, чтобы выдать ему ранг.")
    
    target = message.reply_to_message.from_user
    
    # Создаем кнопки с рангами
    kb_list = []
    for rank in RANKS:
        kb_list.append([InlineKeyboardButton(text=rank, callback_data=f"setr_{target.id}_{rank}")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
    await message.answer(f"👑 Выберите ранг для игрока <b>{target.full_name}</b>:", reply_markup=kb)

@router.callback_query(F.data.startswith("setr_"))
async def process_set_rank(callback: CallbackQuery):
    if not await check_access(callback.from_user.id, "ЗГА"):
        return await callback.answer("❌ Нет прав!", show_alert=True)
    
    parts = callback.data.split("_")
    target_id = int(parts[1])
    new_rank = parts[2]
    
    async with async_session() as session:
        user = await session.get(User, target_id)
        if not user:
            return await callback.answer("❌ Игрок не найден в базе (пусть напишет боту /start).", show_alert=True)
        
        user.role = new_rank
        await session.commit()
    
    await callback.message.edit_text(f"✅ Игроку <b>{user.first_name}</b> успешно выдан ранг: <b>{new_rank}</b>")
    await callback.answer("Ранг выдан!")

# --- МУТ (От Модератора и выше) ---
@router.message(Command("мут"))
async def cmd_mute(message: Message):
    if not await check_access(message.from_user.id, "Модератор"): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Ответь на сообщение игрока, чтобы замутить его.")
    
    target = message.reply_to_message.from_user
    async with async_session() as session:
        user = await ensure_user(session, target)
        user.is_muted = True
        await session.commit()
    
    try:
        await message.chat.restrict_member(target.id, can_send_messages=False)
        await message.answer(f"🔇 Игрок {target.full_name} замучен.")
    except:
        await message.answer(f"🔇 В базе {target.full_name} замучен. (Выдайте боту права админа).")

# --- РАЗМУТ ---
@router.message(Command("размут"))
async def cmd_unmute(message: Message):
    if not await check_access(message.from_user.id, "Модератор"): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Ответь на сообщение игрока.")
    
    target = message.reply_to_message.from_user
    async with async_session() as session:
        user = await ensure_user(session, target)
        user.is_muted = False
        await session.commit()
    
    try:
        await message.chat.restrict_member(target.id, can_send_messages=True)
        await message.answer(f"🔊 Игрок {target.full_name} размучен.")
    except:
        await message.answer(f"🔊 В базе {target.full_name} размучен.")

# --- БАН (От Младшего Администратора и выше) ---
@router.message(Command("бан"))
async def cmd_ban(message: Message):
    if not await check_access(message.from_user.id, "Младший Администратор"): 
        return await message.answer("❌ Банить могут только от Мл. Администратора и выше.")
    if not message.reply_to_message:
        return await message.answer("⚠️ Ответь на сообщение игрока.")
    
    target = message.reply_to_message.from_user
    async with async_session() as session:
        user = await ensure_user(session, target)
        user.is_banned = True
        await session.commit()
    
    try:
        await message.chat.ban_member(target.id)
        await message.answer(f"⛔ Игрок {target.full_name} забанен.")
    except:
        await message.answer(f"⛔ В базе {target.full_name} забанен.")

# --- РАЗБАН ---
@router.message(Command("разбан"))
async def cmd_unban(message: Message):
    if not await check_access(message.from_user.id, "Младший Администратор"): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Ответь на сообщение игрока.")
    
    target = message.reply_to_message.from_user
    async with async_session() as session:
        user = await ensure_user(session, target)
        user.is_banned = False
        await session.commit()
    
    try:
        await message.chat.unban_member(target.id)
        await message.answer(f"✅ Игрок {target.full_name} разбанен.")
    except:
        await message.answer(f"✅ В базе {target.full_name} разбанен.")

# --- ВЫГОВОР (От Модератора и выше) ---
@router.message(Command("выговор"))
async def cmd_warn(message: Message):
    if not await check_access(message.from_user.id, "Модератор"): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Ответь на сообщение игрока.")
    
    target = message.reply_to_message.from_user
    async with async_session() as session:
        user = await ensure_user(session, target)
        user.warns += 1
        await session.commit()
        warns = user.warns
    
    await message.answer(f"⚠️ Игроку {target.full_name} выдан выговор. (Всего: {warns}/3)")
    
    if warns >= 3:
        async with async_session() as session:
            user = await ensure_user(session, target)
            user.is_banned = True
            await session.commit()
        try: await message.chat.ban_member(target.id)
        except: pass
        await message.answer(f"⛔ Игрок {target.full_name} получил 3/3 и был автоматически забанен!")

# --- ПРОФИЛЬ ИГРОКА ---
@router.message(Command("профиль"))
async def cmd_profile(message: Message):
    if not message.reply_to_message:
        return await message.answer("⚠️ Ответь на сообщение игрока, чтобы посмотреть его профиль.")
    
    target = message.reply_to_message.from_user
    async with async_session() as session:
        user = await ensure_user(session, target)
        warns = user.warns
        role = user.role
        muted = "Да" if user.is_muted else "Нет"
        banned = "Да" if user.is_banned else "Нет"
    
    # Красивые эмодзи для каждого ранга
    role_emoji = "👤"
    if role == "Ютубер": role_emoji = "🎥"
    elif role == "Модератор": role_emoji = "🛡"
    elif role == "Младший Администратор": role_emoji = "⚔️"
    elif role == "Средний Администратор": role_emoji = "🔥"
    elif role == "Старший Администратор": role_emoji = "💎"
    elif role == "ЗГА": role_emoji = "👑"

    await message.answer(
        f"👤 <b>Профиль игрока</b>\n\n"
        f"📝 Ник: {target.full_name}\n"
        f"🆔 ID: <code>{target.id}</code>\n"
        f"{role_emoji} Должность: <b>{role}</b>\n"
        f"⚠️ Выговоры: <b>{warns}/3</b>\n"
        f"🔇 Мут: {muted}\n"
        f"⛔ Бан: {banned}"
  )
