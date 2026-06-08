import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database as db
import downloader as dl

BOT_TOKEN = ""
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

INFOSEC_FACTS = [
    "🛡️ А ты знал, что UDP доставляет пакеты на отшибись? Ему без разницы, дошел он или потерялся в бездне. В отличие от него, TCP — надежный как швейцарские часы: пока не получит подтверждение (ACK), фиг успокоится!",
    "🛡️ Хэш — это не шифрование! Шифрование можно расшифровать обратно, имея ключ. А хэширование (например, SHA-256) — это дорога в один конец. Из хэша «пароль123» технически невозможно восстановить сам пароль, можно только подобрать его перебором.",
    "🛡️ Бесплатный Wi-Fi в кофейне — это рай для хакера. С помощью атаки MITM (Человек посередине) злоумышленник может создать фейковую точку с таким же именем и перехватывать весь твой незашифрованный трафик. Включай VPN!",
    "🛡️ Самая частая уязвимость — это не кривой код, а 'социальная инженерия' (то есть человеческая глупость). Фишинговые сайты маскируются под Telegram или банки так искусно, что люди сами отдают пароли и коды из SMS.",
    "🛡️ HTTPS не защищает тебя на 100%. Буковка 'S' (Secure) означает лишь то, что твой трафик до сайта зашифрован и провайдер его не прочитает. Но если сам сайт принадлежит мошенникам, шифрование защитит твою передачу данных... прямо в руки мошенникам!"
]

current_fact = random.choice(INFOSEC_FACTS)

class Form(StatesGroup):
    add_bday = State()

def get_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать", callback_data="dl_menu")],
        [InlineKeyboardButton(text="🎂 Дни рождения", callback_data="bd_list")],
        [InlineKeyboardButton(text="🛡️ ИнфоБез", callback_data="infosec_menu")]
    ])

def get_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Меню", callback_data="back")]
    ])

async def daily_job():
    global current_fact

    current_fact = random.choice(INFOSEC_FACTS)
    
    users = db.get_all_users()
    
    for days_left in [7, 3, 1]:
        birthdays = db.get_birthdays_by_days_left(days_left)
        for user_id, name in birthdays:
            try:
                days_text = {7: "через неделю", 3: "через 3 дня", 1: "завтра"}[days_left]
                await bot.send_message(user_id, f"🎂 Напоминание: {days_text} день рождения у {name}!")
            except Exception:
                pass
            
    for user_id in users:
        try:
            await bot.send_message(user_id, current_fact)
        except Exception:
            pass

@dp.callback_query(F.data == "back")
async def back_to_menu(call: CallbackQuery, state: FSMContext = None):
    if state: 
        await state.clear()
    await call.message.edit_text("Главное меню:", reply_markup=get_menu())

@dp.message(CommandStart())
async def start(message: Message):
    db.add_user(message.from_user.id)
    await message.answer("Главное меню:", reply_markup=get_menu())

@dp.callback_query(F.data == "dl_menu")
async def dl_menu(call: CallbackQuery):
    await call.message.edit_text("Пришли ссылку на видео:", reply_markup=get_back_kb())

@dp.message(F.text.startswith("http"))
async def handle_video(message: Message):
    msg = await message.answer("⏳ Скачиваю...")
    try:
        path = await asyncio.to_thread(dl.download_media, message.text, message.from_user.id)
        await message.answer_video(video=FSInputFile(path))
        await msg.delete()
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    await message.answer("Вернуться в меню:", reply_markup=get_menu())

@dp.callback_query(F.data == "bd_list")
async def show_bdays(call: CallbackQuery):
    bdays = db.get_all_birthdays(call.from_user.id)
    text = "🎂 Твои дни рождения:\n\n"
    if not bdays:
        text += "Список пуст."
    else:
        for name, date in bdays:
            text += f"• {name}: {date}\n"
    
    text += "\n\nДобавить нового: Имя, ДД.ММ.ГГГГ"
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_bd_menu")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="back")]
    ]))

@dp.callback_query(F.data == "add_bd_menu")
async def add_bd(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Пришли данные: Имя, ДД.ММ.ГГГГ", reply_markup=get_back_kb())
    await state.set_state(Form.add_bday)

@dp.message(Form.add_bday)
async def proc_bday(message: Message, state: FSMContext):
    try:
        name, date = message.text.split(',')
        db.add_birthday(message.from_user.id, name.strip(), date.strip())
        await message.answer("✅ Сохранено!", reply_markup=get_menu())
        await state.clear()
    except Exception:
        await message.answer("Ошибка! Формат: Имя, ДД.ММ.ГГГГ", reply_markup=get_back_kb())

@dp.callback_query(F.data == "infosec_menu")
async def show_fact(call: CallbackQuery):
    await call.message.edit_text(f"{current_fact}\n\n(Завтра в 8:00 тебя ждет новый факт!)", reply_markup=get_back_kb())

async def main():
    db.init_db()
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(daily_job, trigger='cron', hour=8, minute=0)
    scheduler.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
