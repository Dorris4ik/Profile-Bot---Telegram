from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ContentType
import Config as token
import sqlite3 as sq

bot = Bot(token=token.Token, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())
db = sq.connect('database.db')
cur = db.cursor()

async def on_startup(_):
    await db_start()

class Feor(StatesGroup):
    Profile_name = State()
    Profile_age = State()
    Profile_Description = State()

async def db_start():
    cur.execute("CREATE TABLE IF NOT EXISTS accounts("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "tg_id INTEGER,"
                "profile_name TEXT,"
                "age INTEGER, "
                "description_text TEXT ) ")
    db.commit()

edit_profile = InlineKeyboardMarkup(row_width=1)
edit_profile.add(InlineKeyboardButton(text='Edit profile', callback_data='edit'))

@dp.callback_query_handler(state='*')
async def callback_query_keyboard(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'edit':
       await bot.send_message(chat_id=callback_query.from_user.id, text='What is your name?')
       await Feor.Profile_name.set()

@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.answer("Hi! I'm profile bot.")

@dp.message_handler(commands=['profile'])
async def profile(message: types.Message):
    user_id = message.from_user.id
    user = cur.execute("SELECT * FROM accounts WHERE tg_id == '{}'".format(user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO accounts (tg_id) VALUES ({})".format(user_id))
        db.commit()
        await message.answer('What is your name?')
        await Feor.Profile_name.set()
    else:
        name = cur.execute("SELECT profile_name FROM accounts WHERE tg_id == '{}'".format(user_id)).fetchone()[0]
        age = cur.execute("SELECT age FROM accounts WHERE tg_id == '{}'".format(user_id)).fetchone()[0]
        description = cur.execute("SELECT description_text FROM accounts WHERE tg_id == '{}'".format(user_id)).fetchone()[0]
        await message.answer(f"<b>Your name:</b> {name}\n"
                             f"<b>Your age:</b> {age}\n"
                             f"\n"
                             f"<b>Your description:</b>\n"
                             f"{description}", reply_markup=edit_profile)
        

@dp.message_handler(state=Feor.Profile_name)
async def new_profile(message: types.Message, state: FSMContext):
    text = message.text
    user_id = message.from_user.id
    chat_id = message.chat.id
    cur.execute("UPDATE accounts SET profile_name = '{}' WHERE tg_id == '{}'".format(text, user_id))
    db.commit()
    await message.answer('Fine. How old are you?')
    await Feor.Profile_age.set()

@dp.message_handler(state=Feor.Profile_age)
async def age_profile(message: types.Message, state: FSMContext):
    try:
        text = int(message.text)
        user_id = message.from_user.id
        chat_id = message.chat.id
        cur.execute("UPDATE accounts SET age = '{}' WHERE tg_id == '{}'".format(text, user_id))
        db.commit()
        await Feor.Profile_Description.set()
        await message.answer('Enter your profile description:')
    except ValueError:
        await message.answer("Enter a number!")

@dp.message_handler(state=Feor.Profile_Description)
async def desc_profile(message: types.Message, state: FSMContext):
    text = message.html_text
    user_id = message.from_user.id
    chat_id = message.chat.id
    cur.execute("UPDATE accounts SET description_text = '{}' WHERE tg_id == '{}'".format(text, user_id))
    db.commit()
    await state.finish()
    await profile(message)


if __name__ == '__main__':
    print('Бот успешно запущен')
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
