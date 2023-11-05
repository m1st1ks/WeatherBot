from mysql.connector import connect, Error
from aiogram import types, Dispatcher

from create import bot
from config import host, user, password, db_name


async def profile(msg: types.Message):
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
                        text = ('Твоя анкета:\n'
                                f'Уникальный номер: {line[0]}\n'
                                f'Nickname: {line[2]}\n'
                                f'Имя: {line[3]}\n'
                                f'{line[4]}: {line[5]}\n'
                                f'Регион: {line[7]} {line[6]}.')
                        markup = types.InlineKeyboardMarkup(row_width=1)
                        button = types.InlineKeyboardButton('Изменить анкету 📝', callback_data='registration')
                        markup.add(button)
                        await bot.send_message(msg.from_user.id, text, reply_markup=markup)
                        break
                else:
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    button = types.InlineKeyboardButton('Регистрация', callback_data='registration')
                    markup.add(button)
                    await bot.send_message(msg.from_user.id, f'Ты пока не зарегистрирован.')
                    await bot.send_message(msg.from_user.id, f'Давай заполним несколько данных, '
                                                             f'чтобы создать твой профиль. 📝', reply_markup=markup)
                connection.commit()
    except Error as e:
        print(e)
        await bot.send_message(msg.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                 'Повтори попытку или свяжиcь с администратором бота!')


def reg_profile(dp: Dispatcher):
    dp.register_message_handler(profile, commands='profile')
