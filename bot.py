 # pip install aiogram
import os
# botfather
# /newbot
# 1 шаг Имя любое
# 2 шаг логин
# name_bot
# 3 шаг - получите токен
# 4 шаг - по ссылке запустите свой бот
BOT_TOKEN = os.getenv('BOT_TOKEN', 'ТОКЕН')
# 5 шаг - userinfobot
ADMIN_ID = os.getenv('ADMIN_ID', 'ID')
# https://render.com/
RAILWAY_URL = os.getenv('RAILWAY_PUBLIC_DOMAIN')
# webhook
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{RAILWAY_URL}{WEBHOOK_PATH}"
# модуль чтобы видеть ошибки
import logging
# показывать сообщения уровня INFO - информация, предупреждения, ошибки
logging.basicConfig(level=logging.INFO)
# /mybots
# /newbot
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
# если нужна форма - задать несколько вопросов
from aiogram.fsm.state import State, StatesGroup
class OrderForm(StatesGroup):
    name = State()
    site = State()
    budget = State()
    contact = State()
# добавление кнопок в телеграм бот
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="Заказать сайт"), KeyboardButton("Узнать")],
        [KeyboardButton(text="Подробнее")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# функция для кнопки отмены
def get_cancel_keyboard():
    # список всех доступных кнопок
    buttons = [
        # если нужна еще кнопка рядом, то вы ее внутри вложенного списка создаете
        [KeyboardButton(text="Отменить")]
        # если нужна ПОД ней кнопка, то сделайте еще один список
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)   
 
from aiogram.filters import Command
from aiogram import types
# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выбери нужный пункт из меню снизу",
                         reply_markup=get_main_keyboard()
                         )
from aiogram import F
from aiogram.fsm.context import FSMContext
@dp.message(F.text == "Заказать сайт")
async def start_order(message: types.Message, state: FSMContext):
    await state.set_state(OrderForm.site)
    await message.answer("Расскажите какой сайт Вам нужен?",
                         reply_markup=get_cancel_keyboard())
# Что делать после получения ответа на вопрос какой сайт нужен 
@dp.message(OrderForm.site)
async def order_site(message: types.Message, state: FSMContext):
    if message.text == "Отменить":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_main_keyboard())
        return
    await state.update_data(site=message.text)
    await state.set_state(OrderForm.budget)
    await message.answer("Какой бюджет планируете выделить на проект?",
                         reply_markup=get_cancel_keyboard())
@dp.message(OrderForm.name)
async def order_name(message: types.Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await state.set_state(OrderForm.contact)
    await message.answer("Укажите свой номер телефона:",
                         reply_markup=get_cancel_keyboard())

@dp.message(OrderForm.contact)
async def order_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
# настраиваем вебхук, т.е. связываем бота с нашим веб-сервером
# без этой функции он не будет работать в фоновом режиме
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен на {WEBHOOK_URL}")
# создаем веб приложение
from aiohttp import web    
app = web.Application()
# Настраиваем обработчик вебхуков
from aiogram.webhook.aiohttp_server import SimpleRequestHandler    
webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
# Регистрируем путь для вебхуков
webhook_requests_handler.register(app, path=WEBHOOK_PATH)
import asyncio
# Регистрируем функции запуска 
app.on_startup.append(lambda _: asyncio.create_task(on_startup()))
# новое
# Настраиваем приложение с диспетчером
from aiogram.webhook.aiohttp_server import setup_application  
setup_application(app, dp, bot=bot)    
# Получаем порт из переменных окружения Render
port = int(os.getenv("PORT", "8080"))
# Запускаем веб-сервер
web.run_app(app, host="0.0.0.0", port=port) 
