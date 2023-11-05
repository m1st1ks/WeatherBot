from mysql.connector import connect, Error
from aiogram import types, Dispatcher

from create import bot
from config import host, user, password, db_name


async def menu(cb: types.CallbackQuery):
    await cb.answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton('Погода сейчас', callback_data='weather now')
    button2 = types.InlineKeyboardButton('Погода на сегодня', callback_data='weather full_day 0')
    button3 = types.InlineKeyboardButton('Погода на неделю', callback_data='weather week')
    markup.add(button1, button2, button3)
    await cb.message.edit_text(f'Интересует погода на сегодня?', reply_markup=markup)


async def start(msg: types.Message):
    await msg.bot.set_my_commands([
        types.BotCommand('start', 'Запуск бота'),
        types.BotCommand('help', 'Помощь с ботом'),
        types.BotCommand('profile', 'Ваш профиль'),
        types.BotCommand('confidentiality', 'Политика конфиденциальности Бота')])
    try:
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            table_query = f"""
            SELECT * FROM users;
            """
            with connection.cursor() as cursor:
                cursor.execute(table_query)
                data = []
                for line in cursor.fetchall():
                    data.append(line)
                    if msg.from_user.id in line:
                        markup = types.InlineKeyboardMarkup(row_width=1)
                        button1 = types.InlineKeyboardButton('Погода сейчас', callback_data='weather now')
                        button2 = types.InlineKeyboardButton('Погода на сегодня', callback_data='weather full_day 0')
                        button3 = types.InlineKeyboardButton('Погода на неделю', callback_data='weather week')
                        markup.add(button1, button2, button3)
                        await bot.send_message(msg.from_user.id,
                                               f'Приветствую, {line[3]}! 😊\n'f'Интересует погода на сегодня?',
                                               reply_markup=markup)
                        break
                else:
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    button = types.InlineKeyboardButton('Регистрация', callback_data='registration')
                    markup.add(button)
                    await bot.send_message(msg.from_user.id, f'Приветствую, новый пользователь! 💯🎉\n'
                                                             f'Ты пока не зарегистрирован.')
                    await bot.send_message(msg.from_user.id, f'Давай заполним несколько данных, '
                                                             f'чтобы создать твой профиль. 📝', reply_markup=markup)
    except Error as e:
        print(e)
        await bot.send_message(msg.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                 'Повтори попытку или свяжиcь с администратором бота!')


async def confidentiality(msg: types.Message):
    with open(f'confidentiality.txt', 'r', encoding='utf-8') as f:
        data = f.read()
    await bot.send_message(msg.from_user.id, data)


async def helper(msg: types.Message):
    text = '''
    Привет! 👋 Я здесь, чтобы помочь тебе с разными вопросами и задачами. 
Я могу предоставлять информацию, помогать с поиском еще многое другое! 😊🤖
    '''
    await bot.send_message(msg.from_user.id, text)


def reg_start(dp: Dispatcher):
    dp.register_message_handler(start, commands='start')
    dp.register_message_handler(helper, commands='help')
    dp.register_message_handler(confidentiality, commands='confidentiality')
    dp.register_callback_query_handler(menu, text='menu')
