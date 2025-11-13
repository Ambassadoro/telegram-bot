import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder

API_TOKEN = "7749915579:AAFdf8W1bu1fEvvzbkz5KeqNKbM_UykX4w0"
ADMIN_ID = 905012252

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- FSM для заказа ---
class OrderStates(StatesGroup):
    product = State()
    address = State()

# --- Создание таблицы заказов ---
async def init_db():
    async with aiosqlite.connect("orders.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product TEXT,
                address TEXT
            )
        """)
        await db.commit()

# --- Команда /start ---
@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🛍 Зробити замовлення")
    await message.answer(
        "Привіт. Я бот-помічник бренду Ressed. З моєю допомогою Ви зможете замовляти речі даного бренду без затримок в будь-яку точку Європи (тільки Новою Поштою).",
        reply_markup=kb.as_markup(resize_keyboard=True)
    )

# --- Кнопка "Зробити замовлення" ---
@dp.message(F.text == "🛍 Зробити замовлення")

async def ask_product(message: types.Message, state: FSMContext):
    await message.answer("Введіть назву позиції, яку бажаєте замовити:")
    await state.set_state(OrderStates.product)

# --- Ввод товара ---
@dp.message(OrderStates.product)
async def process_product(message: types.Message, state: FSMContext):
    await state.update_data(product=message.text)
    await message.answer("Чудово! Тепер введіть адресу доставки:")
    await state.set_state(OrderStates.address)

# --- Ввод адреса ---
@dp.message(OrderStates.address)
async def process_address(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product = data['product']
    address = message.text
    user_id = message.from_user.id

    # Сохранение в БД
    async with aiosqlite.connect("orders.db") as db:
        await db.execute(
            "INSERT INTO orders (user_id, product, address) VALUES (?, ?, ?)",
            (user_id, product, address)
        )
        await db.commit()

    # Ответ пользователю
    await message.answer("✅ Замовлення прийняте! Будьте з нами на зв'язку.")

    # Уведомление администратору
    admin_text = (
        f"Нове замовлення!\n"
        f"ID користувача: {user_id}\n"
        f"Товар: {product}\n"
        f"Адреса: {address}"
    )
    await bot.send_message(ADMIN_ID, admin_text)

    # Сброс состояния
    await state.clear()

# --- Запуск ---
async def main():
    await init_db()
    print("Бот запущений і готовий приймати замовлення!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
