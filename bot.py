

import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ========== НАСТРОЙКИ ==========
# Берем токен из переменных окружения (так безопасно!)
BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_СЮДА_НА_ВСЯКИЙ_СЛУЧАЙ")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8558634705"))  # Твой ID

# https://render.com/
RAILWAY_URL = os.getenv('RAILWAY_PUBLIC_DOMAIN')
# webhook
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{RAILWAY_URL}{WEBHOOK_PATH}"import asyncio

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ========== СОСТОЯНИЯ (FSM) ==========
class LessonForm(StatesGroup):
    name = State()
    subject = State()
    contact = State()

class OrderForm(StatesGroup):
    site_type = State()
    budget = State()

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="📝 Записаться на урок")],
        [KeyboardButton(text="💻 Заказать сайт")],
        [KeyboardButton(text="🎓 Купить курс"), KeyboardButton(text="ℹ️ Обо мне")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cancel_keyboard():
    buttons = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ========== ВСЕ ТВОИ ОБРАБОТЧИКИ ==========
# Они остаются точно такими же! Я их скопирую кратко для целостности файла

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я помощник [Твое Имя]. Я помогу тебе записаться на урок, заказать сайт или приобрести готовый курс.\n"
        f"Выбери нужный пункт в меню снизу.",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "ℹ️ Обо мне")
async def about_me(message: types.Message):
    text = (
        "👩‍🏫 Привет! Я [Твое Имя]. \n\n"
        "🔥 Преподаю программирование с 201Х года.\n"
        "🚀 Разрабатываю сайты на [React/HTML/и т.д.].\n"
        "🎓 Мои ученики поступают в топовые вузы и находят работу.\n\n"
        "Ссылки:\n"
        "GitHub: [ссылка]\n"
        "YouTube: [ссылка]"
    )
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(F.text == "🎓 Купить курс")
async def buy_course(message: types.Message):
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти к курсам", url="https://ссылка_на_твой_курс/")]
    ])
    await message.answer(
        "Мои готовые курсы:\n"
        "— Курс по Python для новичков (2500 руб.)\n"
        "— Курс по созданию сайтов (4000 руб.)\n\n"
        "Нажми кнопку ниже, чтобы посмотреть подробности и купить:",
        reply_markup=inline_kb
    )

@dp.message(F.text == "📝 Записаться на урок")
async def start_lesson_signup(message: types.Message, state: FSMContext):
    await state.set_state(LessonForm.name)
    await message.answer(
        "Давай запишем тебя на пробный урок!\n"
        "Как мне к тебе обращаться? (Напиши имя)",
        reply_markup=get_cancel_keyboard()
    )

@dp.message(LessonForm.name)
async def process_lesson_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_main_keyboard())
        return
    await state.update_data(name=message.text)
    await state.set_state(LessonForm.subject)
    await message.answer("Какой предмет тебя интересует? (Верстка, Python, JavaScript и т.д.)")

@dp.message(LessonForm.subject)
async def process_lesson_subject(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_main_keyboard())
        return
    await state.update_data(subject=message.text)
    await state.set_state(LessonForm.contact)
    await message.answer("Оставь свой контакт (телефон или Telegram @username), чтобы я с тобой связалась.")

@dp.message(LessonForm.contact)
async def process_lesson_contact(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_main_keyboard())
        return
    await state.update_data(contact=message.text)
    user_data = await state.get_data()
    
    admin_message = (
        f"📌 Новая заявка на урок!\n\n"
        f"👤 Имя: {user_data.get('name')}\n"
        f"📚 Предмет: {user_data.get('subject')}\n"
        f"📞 Контакт: {user_data.get('contact')}"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    await message.answer(
        f"✅ Спасибо, {user_data.get('name')}! Я получила твою заявку на урок по '{user_data.get('subject')}'.\n"
        f"Скоро свяжусь с тобой через {user_data.get('contact')}.",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

@dp.message(F.text == "💻 Заказать сайт")
async def start_order(message: types.Message, state: FSMContext):
    await state.set_state(OrderForm.site_type)
    await message.answer(
        "Расскажи, какой сайт тебе нужен?\n"
        "(Например: Landing Page, Интернет-магазин, Блог, Визитка)",
        reply_markup=get_cancel_keyboard()
    )

@dp.message(OrderForm.site_type)
async def process_order_type(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_main_keyboard())
        return
    await state.update_data(site_type=message.text)
    await state.set_state(OrderForm.budget)
    await message.answer("Какой бюджет планируешь на разработку?")

@dp.message(OrderForm.budget)
async def process_order_budget(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_main_keyboard())
        return
    await state.update_data(budget=message.text)
    user_data = await state.get_data()
    
    admin_message = (
        f"💰 Новый заказ на разработку!\n\n"
        f"🖥 Тип сайта: {user_data.get('site_type')}\n"
        f"💵 Бюджет: {user_data.get('budget')}\n"
        f"👤 Клиент: @{message.from_user.username or 'нет username'} (ID: {message.from_user.id})"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    await message.answer(
        f"✅ Спасибо за заказ! Я рассмотрю твои пожелания (Тип: {user_data.get('site_type')}, Бюджет: {user_data.get('budget')}) и напишу тебе в ближайшее время.",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# ========== НОВАЯ ЧАСТЬ: НАСТРОЙКА ВЕБ-СЕРВЕРА ==========

async def on_startup():
    """Действия при запуске приложения"""
    # Устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен на {WEBHOOK_URL}")
    
    # Отправляем сообщение админу о запуске
    try:
        await bot.send_message(chat_id=ADMIN_ID, text="✅ Бот успешно запущен на Render!")
    except:
        pass

async def on_shutdown():
    """Действия при остановке приложения"""
    # Удаляем вебхук
    await bot.delete_webhook()
    logging.info("Webhook удален")

def main():
    """Главная функция для запуска веб-приложения"""
    # Создаем aiohttp приложение
    app = web.Application()
    
    # Настраиваем обработчик вебхуков
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    
    # Регистрируем путь для вебхуков
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Регистрируем функции запуска и остановки
    app.on_startup.append(on_startup())
    app.on_shutdown.append(on_shutdown())
    
    # Настраиваем приложение с диспетчером
    setup_application(app, dp, bot=bot)
    
    # Получаем порт из переменных окружения Render
    port = int(os.getenv("PORT", "8080"))
    
    # Запускаем веб-сервер
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":

    main()

