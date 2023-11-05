import requests
import time

from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from mysql.connector import connect, Error

from create import bot
from config import ya_maps_token, ya_weather_token, condition, db_name, host, user, password


def get_geocode(text):
    data = requests.get(
        f'https://geocode-maps.yandex.ru/1.x/?apikey={ya_maps_token}&geocode={text}&format=json').json()
    data = data.get('response').get('GeoObjectCollection').get('featureMember')[0].get('GeoObject').get('Point').get(
        'pos')
    return data


def get_weather(url):
    data = requests.get(url=url, headers={'X-Yandex-API-Key': f'{ya_weather_token}'}).json()
    return data


async def weather_now(cb: types.CallbackQuery):
    await cb.answer()
    try:
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            update_table_query = f"""
            SELECT city, area, area_district FROM USERS WHERE user_id = {cb.from_user.id};
            """
            with connection.cursor() as cursor:
                cursor.execute(update_table_query)
                data = []
                for line in cursor.fetchall():
                    data.append(line)
            connection.commit()
        pos = get_geocode(f'{data[0][0]},+{data[0][1]}+{data[0][2]}').split()
        url = f'https://api.weather.yandex.ru/v2/forecast?lat={pos[1]}&lon={pos[0]}&hours=true'
        get_data = get_weather(url)
        geo_object, fact = get_data.get('geo_object'), get_data.get('fact')
        date_time = time.localtime(fact.get('uptime'))
        text = f"""
По данным Яндекс Погоды, в городе {geo_object.get('locality').get('name')} сейчас:

Время по МСК ⏰ - {date_time.tm_hour}:{date_time.tm_min}:{date_time.tm_sec}

Температура воздуха 🌡 - {fact.get('temp')}°C
Ощущается как {fact.get('feels_like')}°C

Погодные условия - {condition.get(fact.get('condition'))}
Давление - {fact.get('pressure_mm')}мм рт. ст.

Скорость ветра 🌀 - {fact.get('wind_speed')}м/с
Влажность 💧 - {fact.get('humidity')}%

"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('🔼 Меню', callback_data='menu')
        markup.add(button1)
        await cb.message.edit_text(text, reply_markup=markup)
    except Error as e:
        print(e)
        await bot.send_message(cb.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                'Повтори попытку или свяжитесь с администратором бота!')


async def weather_full_day(cb: types.CallbackQuery):
    await cb.answer()
    number = int(cb.data.split()[2])
    markup = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton('Утро', callback_data=f'weather time_of_day morning {number}')
    button2 = types.InlineKeyboardButton('День', callback_data=f'weather time_of_day day {number}')
    button3 = types.InlineKeyboardButton('Вечер', callback_data=f'weather time_of_day evening {number}')
    button4 = types.InlineKeyboardButton('Ночь', callback_data=f'weather time_of_day night {number}')
    if number == 0:
        button5 = types.InlineKeyboardButton('🔼 Меню', callback_data=f'menu')
        markup.add(button1, button2, button3, button4, button5)
    elif len(cb.data.split()) == 3:
        button5 = types.InlineKeyboardButton('◀ Назад', callback_data=f'weather week')
        button6 = types.InlineKeyboardButton('🔼 Меню', callback_data=f'menu')
        markup.add(button1, button2, button3, button4, button5, button6)
    else:
        button5 = types.InlineKeyboardButton('◀ Назад', callback_data=f'weather week')
        button6 = types.InlineKeyboardButton('🔼 Меню', callback_data=f'menu')
        markup.add(button1, button2, button3, button4, button5, button6)
    await cb.message.edit_text('Выбери время суток:', reply_markup=markup)


async def time_of_day(cb: types.CallbackQuery):
    await cb.answer()
    sel_time = cb.data.split()[2]
    number = int(cb.data.split()[3])
    try:
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            update_table_query = f"""
                SELECT city, area, area_district FROM USERS WHERE user_id = {cb.from_user.id};
                """
            with connection.cursor() as cursor:
                cursor.execute(update_table_query)
                data = []
                for line in cursor.fetchall():
                    data.append(line)
            connection.commit()
        pos = get_geocode(f'{data[0][0]},+{data[0][1]}+{data[0][2]}').split()
        url = f'https://api.weather.yandex.ru/v2/forecast?lat={pos[1]}&lon={pos[0]}&hours=true&limit=7'
        get_data = get_weather(url)
        forecasts = get_data.get('forecasts')[number]
        geo_object = get_data.get('geo_object')
        date_time = time.localtime(forecasts.get('date_ts'))
        text = f"""
По данным Яндекс Погоды  на {date_time.tm_mday}.{date_time.tm_mon}, в городе {geo_object.get('locality').get('name')}:

Дата 📅 - <b>{date_time.tm_mday}.{date_time.tm_mon}.{date_time.tm_year}</b>
Восход солнца - {forecasts.get('rise_begin')}-{forecasts.get('sunrise')}
Закат солнца - {forecasts.get('sunset')}-{forecasts.get('set_end')}


"""
        if sel_time == 'morning':
            text += '<b>Утро - 06:00-11:00</b>'
        elif sel_time == 'day':
            text += '<b>День - 12:00-17:00</b>'
        elif sel_time == 'evening':
            text += '<b>Вечер - 18:00-21:00</b>'
        else:
            text += '<b>Ночь - 22:00-05:00</b>'
        text += f"""
Максимальная температура воздуха 🌡⤴ - {forecasts.get('parts').get(sel_time).get('temp_max')}°C
Минимальная температура воздуха 🌡⤵ - {forecasts.get('parts').get(sel_time).get('temp_min')}°C
Средняя температура воздуха 🌡 - {forecasts.get('parts').get(sel_time).get('temp_avg')}°C

Погодные условия - {condition.get(forecasts.get('parts').get(sel_time).get('condition'))}
Вероятность выпадения осадков - {forecasts.get('parts').get(sel_time).get('prec_prob')}%
Ультрафиолетовый индекс - {forecasts.get('parts').get(sel_time).get('uv_index')}

Скорость ветра 🌀 - {forecasts.get('parts').get(sel_time).get('wind_speed')}м/с
Влажность 💧 - {forecasts.get('parts').get(sel_time).get('humidity')}%
"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        button1 = types.InlineKeyboardButton('◀ Назад', callback_data=f'weather full_day {number}')
        button2 = types.InlineKeyboardButton('🔼 Меню', callback_data='menu')
        markup.add(button1, button2)
        await cb.message.edit_text(text, reply_markup=markup)
    except Error as e:
        print(e)
        await bot.send_message(cb.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                'Повтори попытку или свяжитесь с администратором бота!')


async def weather_week(cb: types.CallbackQuery):
    await cb.answer()
    try:
        with connect(
                host=host,
                user=user,
                password=password,
                database=db_name
        ) as connection:
            update_table_query = f"""
            SELECT city, area, area_district FROM USERS WHERE user_id = {cb.from_user.id};
            """
            with connection.cursor() as cursor:
                cursor.execute(update_table_query)
                data = []
                for line in cursor.fetchall():
                    data.append(line)
            connection.commit()
        pos = get_geocode(f'{data[0][0]},+{data[0][1]}+{data[0][2]}').split()
        url = f'https://api.weather.yandex.ru/v2/forecast?lat={pos[1]}&lon={pos[0]}&hours=true&limit=7'
        get_data = get_weather(url)
        forecasts = get_data.get('forecasts')
        buttons = []
        for i in range(7):
            date_time = time.localtime(forecasts[i].get('date_ts'))
            buttons.append([types.InlineKeyboardButton(f'{date_time.tm_mday}.{date_time.tm_mon}.{date_time.tm_year}',
                                                       callback_data=f'weather full_day {i} week')])
        buttons.append([types.InlineKeyboardButton('🔼 Меню', callback_data='menu')])
        markup = types.InlineKeyboardMarkup(row_width=1, inline_keyboard=buttons)
        await cb.message.edit_text('Выбери день недели:', reply_markup=markup)
    except Error as e:
        print(e)
        await bot.send_message(cb.from_user.id, 'Упс! Ошибка при подключении к серверу... 🙊 \n'
                                                'Повтори попытку или свяжитесь с администратором бота!')


def reg_weather(dp: Dispatcher):
    dp.register_callback_query_handler(weather_now, text='weather now')
    dp.register_callback_query_handler(weather_full_day, Text(startswith='weather full_day'))
    dp.register_callback_query_handler(time_of_day, Text(startswith='weather time_of_day'))
    dp.register_callback_query_handler(weather_week, text='weather week')
