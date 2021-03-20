import os, telebot, requests, psycopg2, source_html
from datetime import date


token = os.environ['TOKEN']
bot = telebot.TeleBot(token)

connection, cursor = '',''
INIT_STATE, MAIN_STATE, CITY_STATE1, CITY_STATE2, MAP_STATE = 1, 2, 3, 4, 5
name = 'Введите название города на английском языке.'
back = 'Возвращаюсь в начало программы (все данные будут стерты). Наберите /start для получения ' \
       'инструкций.'
wrong = 'Неверно. Нажмите/Наберите Да или Нет'

def create_file(message):
    source = {
        "type": "FeatureCollection",
        "name": "Cities",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": []
    }
    cursor.execute(f'select * from features where user_id = {message.from_user.id}')
    for row in cursor:
        source["features"].append(
            {"type": "Feature", "properties": {"ID": row[0], "city": row[2], "date": row[3],
                                               "temp": row[6]}, "geometry": {"type": "Point",
                                                                           "coordinates": [row[4], row[5], 1.0]}})
    modified = source_html.html_2 % (message.from_user.id, str(source))
    with open(f'{message.from_user.id}.html', 'w') as outfile:
        outfile.write(source_html.html_1 + modified + source_html.html_3)
    with open(f'{message.from_user.id}.html', 'rb') as infile:
        bot.send_document(message.chat.id, infile)
    os.remove(f'{message.from_user.id}.html')
    # html_str = source_html.html_1 + modified + source_html.html_3
    # output = str.encode(html_str, 'utf-8')
    # bot.send_document(message.chat.id, output)

def api_process(t_message):
    def end(value):
        if value < 0:
            value = value * -1
        if value % 10 == 1 and value % 100 != 11:
            return ''
        else:
            for i in range(2, 5):
                if value % 10 == i and value % 100 != 10 + i:
                    return 'a'
            return 'oв'
    api_key = os.environ['API_KEY']
    api_url = os.environ['API_URL']
    params = {'q':t_message.text,'appid': api_key, 'units':'metric'}
    data = requests.get(api_url, params=params).json()
    curr_date = str(date.today())
    if data['cod'] != 200:
        fill_bad(t_message.from_user.id)
        return 'Город не найден, повторите ввод'
    else:
        fill_good(t_message.from_user.id)
        city = data['name']
        lat = data['coord']['lat']
        long = data['coord']['lon']
        temp = round(data['main']['temp'])
        save_state(t_message.from_user.id, CITY_STATE2)
        fill_source(t_message.from_user.id, city, lat, long, curr_date, temp)
        return 'Координаты города %s: долгота %.4f, широта %.4f\nТекущая дата: %s\n' \
               'Tемпература: %d градус%s Цельсия\n' % (city, lat, long, curr_date, temp, end(temp))

def save_state(user_id, state):
    cursor.execute(f'update user_state set user_state = {state} where user_id = {user_id}')
    connection.commit()
def show_state(user_id):
    cursor.execute(f'select exists(select 1 from user_state where user_id = {user_id} limit 1)')
    if not next(cursor)[0]:
        cursor.execute(f'insert into user_state values({user_id},{INIT_STATE})')
        connection.commit()
    cursor.execute(f'select user_state from user_state where user_id = {user_id}')
    return next(cursor)[0]

def fill_source(user_id, city, lat, long, curr_date, temp):
    cursor.execute(f"insert into features values (default, {user_id}, '{city}', '{curr_date}', {long}, {lat}, {temp})")
    connection.commit()
def del_source(user_id):
    cursor.execute(f'delete from features where user_id = {user_id}')
    connection.commit()

def cr_stat(user_id):
    cursor.execute(f'select exists(select 1 from stat where user_id = {user_id} limit 1)')
    if not next(cursor)[0]:
        cursor.execute(f'insert into stat values ({user_id}, 0,0)')
        connection.commit()
def del_stat(user_id):
    cursor.execute(f'delete from stat where user_id = {user_id}')
    connection.commit()
def fill_bad(user_id):
    cursor.execute(f'update stat set bad = bad + 1 where user_id = {user_id}')
    connection.commit()
def fill_good(user_id):
    cursor.execute(f'update stat set good = good + 1 where user_id = {user_id}')
    connection.commit()
def show_good_stat(user_id):
    cursor.execute(f'select good from stat where user_id = {user_id}')
    return next(cursor)[0]
def show_bad_stat(user_id):
    cursor.execute(f'select bad from stat where user_id = {user_id}')
    return next(cursor)[0]

attempt = 0
while attempt <= 3:
    attempt += 1
    try:
        connection = psycopg2.connect(database=os.environ['DB'], user=os.environ['DB_USER'],
                                      password=os.environ['DB_PASSWORD'])
        cursor = connection.cursor()
        @bot.message_handler(func=lambda message: show_state(message.from_user.id) == INIT_STATE)
        def init(message):
            del_stat(message.from_user.id)
            cr_stat(message.from_user.id)
            del_source(message.from_user.id)
            if message.text != '/start':
                bot.reply_to(message, 'Введите /start')
            else:
                markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
                btns = ["Да", "Нет", "Стат.", "/start"]
                markup.add(*btns)
                intro = f'Здравствуйте, {message.from_user.first_name}.\n\n' \
                        f'Позвольте представиться, \n' \
                        f'меня зовут TentativeBot1: Geography, я принимаю на ввод названия городов, ' \
                        f'вывожу их географические координаты, текущую дату и актуальную температуру в них, ' \
                        f'после этого могу показать где они расположены на карте.\n\n' \
                        f'Нажмите/Наберите "Да" для ввода города или "Стат." для вывода статистики'
                bot.send_message(message.chat.id, intro, reply_markup=markup)
                save_state(message.from_user.id, MAIN_STATE)
        @bot.message_handler(func=lambda message: show_state(message.from_user.id) == MAIN_STATE)
        def main_handler(message):
            if message.text == '/start':
                bot.send_message(message.chat.id, back)
                save_state(message.from_user.id, INIT_STATE)
            elif message.text.lower() == 'да':
                bot.send_message(message.chat.id, name)
                save_state(message.from_user.id, CITY_STATE1)
            elif message.text == 'Стат.':
                stat_ans = 'Количество верно введенных названий: %d\nКоличество не верно введенных ' \
                           'названий: %d\n\nНажмите/Наберите "Да" для ввода города, /start для возвращения ' \
                           'в начало программы (все данные будут стерты).' \
                           % (show_good_stat(message.from_user.id), show_bad_stat(message.from_user.id))
                bot.send_message(message.chat.id, stat_ans)
            else:
                bot.reply_to(message,
                             'Неверно. Нажмите/Наберите "Да" для ввода города, "Стат." для вывода статистики, '
                             '/start для возврата в начало программы')
        @bot.message_handler(func=lambda message: show_state(message.from_user.id) == CITY_STATE1)
        def city_handler1(message):
            if message.text == '/start':
                bot.send_message(message.chat.id, back)
                save_state(message.from_user.id, INIT_STATE)
            elif message.text == 'Стат.':
                stat_ans = 'Количество верно введенных названий: %d\nКоличество не верно введенных ' \
                           'названий: %d\n\nВведите название города или нажмите/наберите /start для ' \
                           'возвращения в начало программы (все данные будут стерты).' \
                           % (show_good_stat(message.from_user.id),show_bad_stat(message.from_user.id))
                bot.send_message(message.chat.id, stat_ans)
            else:
                ans = api_process(message)
                bot.reply_to(message, ans)
                if show_state(message.from_user.id) == CITY_STATE2:
                    bot.send_message(message.chat.id, "Повторить? Да или Нет?")
        @bot.message_handler(func=lambda message: show_state(message.from_user.id) == CITY_STATE2)
        def city_handler2(message):
            if message.text == '/start':
                bot.send_message(message.chat.id, back)
                save_state(message.from_user.id, INIT_STATE)
            elif message.text == 'Стат.':
                stat_ans = 'Количество верно введенных названий: %d\nКоличество не верно введенных ' \
                           'названий: %d\n\nНажите/Наберите "Да", "Нет" или /start для возвращения ' \
                           'в начало программы (все данные будут стерты).' \
                           % (show_good_stat(message.from_user.id),show_bad_stat(message.from_user.id))
                bot.send_message(message.chat.id, stat_ans)
            else:
                if message.text.lower() == 'да':
                    bot.send_message(message.chat.id, name)
                    save_state(message.from_user.id, CITY_STATE1)
                elif message.text.lower() == 'нет':
                    ans = "Показать карту с введенными городами? Да или Нет?\n\n" \
                          "Внимание! Тестировано только для Windows.\n" \
                          "Карта должна открыться в окне браузера на компьютере где запущен код бота,\n" \
                          "если не открылась то свяжитесь c разработчиком."
                    bot.send_message(message.chat.id, ans)
                    save_state(message.from_user.id, MAP_STATE)
                else:
                    bot.reply_to(message, wrong)
        @bot.message_handler(func=lambda message: show_state(message.from_user.id) == MAP_STATE)
        def map_handler2(message):
            if message.text == '/start':
                bot.send_message(message.chat.id, back)
                save_state(message.from_user.id, INIT_STATE)
            elif message.text == 'Стат.':
                stat_ans = 'Количество верно введенных названий: %d\nКоличество не верно введенных названий: ' \
                           '%d\n\nНажите/Наберите "Да", "Нет" или /start для возвращения в начало программы' \
                           '(все данные будут стерты).' \
                           % (show_good_stat(message.from_user.id),show_bad_stat(message.from_user.id))
                bot.send_message(message.chat.id, stat_ans)
            else:
                if message.text.lower() == 'да':
                    ans1 = 'Карта должна открыться в окне браузера.\n ' \
                           'Нажмите/Наберите "Да" для повторного ввода данных, "Стат." для вывода статистики, ' \
                           '/start для возвращения в начало программы (все данные будут стерты).'
                    bot.send_message(message.chat.id, ans1)
                    save_state(message.from_user.id, MAIN_STATE)
                    create_file(message)
                elif message.text.lower() == 'нет':
                    ans2 = 'Нажмите/Наберите "Да" для повторного ввода данных, "Стат." для вывода статистики, ' \
                           '/start для возвращения в начало программы (все данные будут стерты).'
                    bot.send_message(message.chat.id, ans2)
                    save_state(message.from_user.id, MAIN_STATE)
                else:
                    bot.reply_to(message, wrong)
        break
    except psycopg2.Error:
        if attempt <= 3:
            pass
        else:
            @bot.message_handler(func=lambda message: True)
            def failure_ans(message):
                ans = 'Нет соединения с базой данных. Повторите позднее'
                bot.send_message(message.chat.id, ans)

bot.polling()