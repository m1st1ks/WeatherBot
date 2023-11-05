import requests
from math import ceil
import os

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from mysql.connector import connect, Error

from create import bot
from config import host, user, password, db_name, fias_token, address


class RegistrationFSM(StatesGroup):
    join_name = State()
    join_district = State()
    join_city = State()


def get_fias(text, code):
    data = requests.get(
        f'https://kladr-api.ru/api.php?token={fias_token}&query={text}&contentType=city&typecode={code}'
        f'&withParent=1&limit=50').json()
    data = data.get('result')
    if len(data) == 1:
        return 0
    else:
        return data


async def registration(cb: types.CallbackQuery):
    await cb.answer()
    await RegistrationFSM.join_name.set()
    try:
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            table_query = f"""
            DELETE FROM users WHERE user_id = {cb.from_user.id};
            """
            with connection.cursor() as cursor:
                cursor.execute(table_query)
            connection.commit()
        await cb.message.edit_text('Как тебя зовут? ✍️')
    except Error as e:
        print(e)
        await bot.send_message(cb.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                'Повтори попытку или свяжитесь с администратором бота!')


async def name(msg: types.Message):
    await RegistrationFSM.next()
    text = msg.text
    try:
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            table_query = f"""
            INSERT INTO users VALUES(
            NULL, {msg.from_user.id}, '@{msg.from_user.username}', '{text}', NULL, NULL, NULL, NULL);
            """
            with connection.cursor() as cursor:
                cursor.execute(table_query)
            connection.commit()
        markup = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('Город ', callback_data='registration-district city')
        button2 = types.InlineKeyboardButton('Деревня ', callback_data='registration-district village')
        button3 = types.InlineKeyboardButton('Посёлок ', callback_data='registration-district settlement')
        markup.add(button1, button2, button3)
        await bot.send_message(msg.from_user.id, f'Отлично! В каком типе района ты живешь? 🏙️\n'
                                                 f'Если нет твоего типа, выбери <b>Город</b>',
                               reply_markup=markup)
    except Error as e:
        print(e)
        await bot.send_message(msg.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                 'Повтори попытку или свяжитесь с администратором бота!')


async def district(cb: types.CallbackQuery):
    await cb.answer()
    await RegistrationFSM.next()
    text = cb.data.split()[1]
    try:
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            table_query = f"""
            UPDATE users SET city_district = '{text}' WHERE user_id = {cb.from_user.id};
            """
            with connection.cursor() as cursor:
                cursor.execute(table_query)
            connection.commit()
        if text == 'city':
            ques = 'каком'
            dist = 'городе'
        elif text == 'village':
            ques = 'какой'
            dist = 'деревне'
        else:
            ques = 'каком'
            dist = 'посёлке'
        await cb.message.edit_text(f'Супер! В {ques} {dist} ты живешь? 🌍\n'
                                   f'Напиши в <b>Именительном падеже</b>\n'
                                   f'Пример: Москва')
    except Error as e:
        print(e)
        await bot.send_message(cb.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                'Повтори попытку или свяжитесь с администратором бота!')


def create_file(data, msg):
    with open(f'cache/{msg.from_user.id}.txt', 'w', encoding='utf-8') as f:
        for i in range(1, len(data)):
            if f"{data[i]['typeShort']}" in address:
                f.write(f"{data[i]['typeShort']}.{data[i]['name']}, "
                        f"{data[i]['parents'][0].get('name')} "
                        f"{data[i]['parents'][0].get('typeShort')}.\n")


def selection_button(page, last_page, msg):
    page, last_page = int(page), int(last_page)
    buttons = []
    array = []
    with open(f'cache/{msg.from_user.id}.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        line = lines[i][:-1]
        array.append(line)
    if 1 == page == last_page:
        for i in range(len(array)):
            buttons.append([types.InlineKeyboardButton(array[i],
                                                       callback_data=f'registration-selection_city {array.index(array[i])}')])
    elif page == 1 and page != last_page:
        for i in range(0, 10):
            buttons.append([types.InlineKeyboardButton(array[i],
                                                       callback_data=f'registration-selection_city {array.index(array[i])}')])
        buttons.append(
            [types.InlineKeyboardButton(f'➡️', callback_data=f'registration-choose_page {page + 1} {last_page}')])
    elif 1 < page < last_page:
        for i in range((page - 1) * 10, page * 10):
            buttons.append([types.InlineKeyboardButton(array[i],
                                                       callback_data=f'registration-selection_city {array.index(array[i])}')])
        buttons.append(
            [types.InlineKeyboardButton(f'⬅️️', callback_data=f'registration-choose_page {page - 1} {last_page}'),
             types.InlineKeyboardButton(f'➡️', callback_data=f'registration-choose_page {page + 1} {last_page}')])
    else:
        for i in range((page - 1) * 10, len(array)):
            buttons.append([types.InlineKeyboardButton(array[i],
                                                       callback_data=f'registration-selection_city {array.index(array[i])}')])
        buttons.append(
            [types.InlineKeyboardButton(f'⬅️️', callback_data=f'registration-choose_page {page - 1} {last_page}')])
    return buttons


async def choose_page(cb: types.CallbackQuery):
    await cb.answer()
    page, last_page = cb.data.split()[1], cb.data.split()[2]
    buttons = selection_button(page, last_page, cb)
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await cb.message.edit_text(f'Выбери свой район из выпадающего списка:\n'
                               f'Страница {page}/{last_page}', reply_markup=markup)


async def city(msg: types.Message, state: FSMContext):
    await state.finish()
    text = msg.text
    try:
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            select_table_query = f"""
            SELECT city_district FROM users WHERE user_id = {msg.from_user.id};
            """
            with connection.cursor() as cursor:
                cursor.execute(select_table_query)
                dist = cursor.fetchone()[0]
            connection.commit()
        if dist == 'city':
            code = 1
        elif dist == 'village':
            code = 4
        else:
            code = 2
        data = get_fias(text, code)
        if data == 0:
            await RegistrationFSM.join_city.set()
            await bot.send_message(msg.from_user.id, f'Такого района нет в России! Попробуй еще раз 🌍\n'
                                                     f'Напиши название в <b>Именительном падеже</b>\n'
                                                     f'Пример: Москва')
        else:
            create_file(data, msg)
            with open(f'cache/{msg.from_user.id}.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            buttons = selection_button(1, ceil(len(lines) / 10), msg)
            markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
            await bot.send_message(msg.from_user.id, f'Выбери свой район из выпадающего списка:\n'
                                                     f'Страница 1/{ceil(len(lines) / 10)}', reply_markup=markup)
    except Error as e:
        print(e)
        await bot.send_message(msg.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                 'Повтори попытку или свяжитесь с администратором бота!')


async def selection_city(cb: types.CallbackQuery):
    await cb.answer()
    array = []
    with open(f'cache/{cb.from_user.id}.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        line = lines[i][:-1]
        array.append(line)
    text = array[int(cb.data.split()[1])]
    text = text.split()
    sel_city, area, area_district = text[0], text[1], text[2][:-1]
    sel_city = sel_city.split('.')[1][:-1]
    try:
        os.remove(f'cache/{cb.from_user.id}.txt')
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            update_table_query = f"""
                                        UPDATE users SET city = '{sel_city}', area_district = '{area_district}', 
                                        area = '{area}' WHERE user_id = {cb.from_user.id};
                                        """
            with connection.cursor() as cursor:
                cursor.execute(update_table_query)
            connection.commit()
        markup = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('Перейти к погоде', callback_data='menu')
        markup.add(button1)
        await cb.message.edit_text('Ты зарегистрировался! Теперь тебе доступен раздел погоды🌤️☀️\n'
                                   'Перейти в профиль - /profile', reply_markup=markup)
    except Error as e:
        print(e)
        await bot.send_message(cb.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                'Повтори попытку или свяжитесь с администратором бота!')


def reg_registration(dp: Dispatcher):
    dp.register_callback_query_handler(registration, text='registration')
    dp.register_message_handler(name, state=RegistrationFSM.join_name)
    dp.register_callback_query_handler(district, Text(startswith='registration-district'),
                                       state=RegistrationFSM.join_district)
    dp.register_message_handler(city, state=RegistrationFSM.join_city)
    dp.register_callback_query_handler(selection_city, Text(startswith='registration-selection_city'))
    dp.register_callback_query_handler(choose_page, Text(startswith='registration-choose_page'))
