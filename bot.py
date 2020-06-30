# Version for github
import locale
import random
from datetime import datetime
from datetime import timedelta

import pyowm  # https://github.com/csparpa/pyowm
import telebot
from telebot import types

import config

from t import gr as rr
from pyowm.utils.config import get_default_config

config_dict = get_default_config()
config_dict['language'] = 'ru'  # your language here



print(rr.greeting)
bot = telebot.TeleBot(config.TOKEN)  # telegram bot API
owm = pyowm.OWM(config.APIkey_owm, config_dict)  # погодный API open weather map
locale.setlocale(locale.LC_ALL, "ru")
gmt0gmt2_delta = timedelta(hours=2)  # GMT+2
gmt0gmt3_delta = timedelta(hours=3)  # GMT+3

class W_API:
    def __init__(self, place_name):
        self.place_name = place_name
        self.mgr = owm.weather_manager()
        self.observation = self.mgr.weather_at_place(place_name)
        self.got_w = self.observation.weather
        self.t = self.got_w.temperature('celsius')['temp']

    def _get_fc_weather(self, d, h: int, m: int = 0, utc: int = 3):
        """
                :param d: forecast's day 'today' or 0, 'tomorrow' or 1, 'aftertomorrow' or 2, 3, 4, 5.
                :param h: hour for replace
                :param m: minute for replace
                :param utc: meridian (default 3)
                :return: self.aftertomorrow['time_replace'] type = datetime
        """
        self._init_forecast(d, h, m, utc)
        return self.fc_dictionary

    def _init_forecast(self, d, h: int, m: int = 0, utc: int = 3):
        """
        :param d: forecast's day 'today' or 0, 'tomorrow' or 1, 'aftertomorrow' or 2, 3, 4, 5.
        :param h: hour for replace
        :param m: minute for replace
        :param utc: meridian (default 3)
        :return: self.aftertomorrow['time_replace'] type = datetime
        """
        if d in [2, 'aftertomorrow']:
            day = 2
        elif d in [1, 'tomorrow']:
            day = 1
        else:
            day = d

        main = (datetime.now() + timedelta(days=day))
        time_replace = main.replace(hour=h + utc, minute=m)
        fc_got_weather = self.fc.get_weather_at(time_replace)
        fc_weather_code = fc_got_weather.weather_code
        fc_temperature = fc_got_weather.temperature('celsius')
        self.fc_dictionary = {'main': main,
                              'time_replace': time_replace,
                              'fc_got_weather': fc_got_weather,
                              'fc_weather_code': fc_weather_code,
                              'fc_temperature': fc_temperature,
                              }
        return self.fc_dictionary['time_replace']

    def icon_choice(self, d=0, h=0, m=0, now: bool = False):
        """
        Выбор эмодзи по condition code https://openweathermap.org/weather-conditions
        :param now:
        :param d: day
        :param h: hour
        :param m: minute
        :param now: if True or d and h and == 0 : weather now
        :return:
        """
        c = None

        if now == True:
            c = self.got_w.weather_code
        else:
            self._init_forecast(d, h)
            c = self.fc_dictionary['fc_weather_code']

        emojiicon = None
        # гроза:
        if c in [200, 201, 202, 210, 211, 212, 221, 230, 231, 232]:
            emojiicon = '⛈'
        # drizzle морось:
        elif c in [300, 301, 302, 310, 311, 312, 313, 314, 321]:
            emojiicon = '🌧'
        # light rain
        elif c in [500, 501]:
            emojiicon = '🌦'
        # rain
        elif c in [502, 503, 504, 520, 521, 522, 531]:
            emojiicon = '🌧'
        # freezing rain
        elif c == 511:
            emojiicon = '🌧❄️'
        # snow
        elif c in [600, 601, 602, 611, 612, 613, 615, 616, 620, 621, 622]:
            emojiicon = '🌨❄'
        # fog | atmosphere
        elif c in [701, 711, 721, 731, 741, 751, 761, 762, 771, 781]:
            emojiicon = '🌫'
        # clear sky | sunny
        elif c == 800:
            emojiicon = '☀'
        # few clouds
        elif c == 801:
            emojiicon = '🌤'
        # clouds 25-50%
        elif c == 802:
            emojiicon = '⛅️'
        # clouds 51-84%
        elif c == 803:
            emojiicon = '🌥'
        # overcast cliuds 85 - 100%
        elif c == 804:
            emojiicon = '☁️'
        else:
            emojiicon = ''

        return emojiicon

    def weather_now(self):
        # выбор совета в зависимсоти от температуры
        advice = None
        tw = self.got_w.reference_time(timeformat="date")
        time = tw + gmt0gmt3_delta
        if round(self.t) > 0 and round(self.t) <= 10:  # прохладно
            advice = f'На улице прохладно 😐 оденься потеплее '
        elif round(self.t) <= 0:  # мороз
            advice = f'На улице мороз🥶, одевайся как эскимос '
        elif round(self.t) > 10 and round(self.t) <= 25:  # комфортно
            advice = f'На улице комфортная температура  ☺️ одевайся как хочешь '
        elif round(self.t):  # жарко
            advice = f'На улице жара   🥵 спасайся в тени или дома, пей больше воды 💧  '
        result = f'{"-" * 20}\n{self.place_name}. 🌡 \nТекущаея температура:{round(self.t)}°C\n' \
                 f'{advice}' \
                 f'\nСкорость ветра:\t{self.got_w.wind()["speed"]} м/с, ' \
                 f'\n{self.got_w.detailed_status}{self.icon_choice(now=True)} \n' \
                 f'{time.strftime("%H:%M:%S|%d.%m.%Y %A")}' \
                 f'\n{"-" * 20}'
        return result

    def weather_fc_init(self):
        self.fc = self.mgr.forecast_at_place(self.place_name, "3h")
        self.f = self.fc.forecast
        self.f.actualize()

    def dict_fragment(self, d, h):
        return {'temp': self._get_fc_weather(d, h)['fc_temperature']['temp'],
                'd_status': self._get_fc_weather(d, h)['fc_got_weather'].detailed_status,
                'wind': self._get_fc_weather(d, h)['fc_got_weather'].wind()["speed"],
                'icon': self.icon_choice(d, h)
                }

    def str_fragment(self, phrase, code, this_day):
        return f'\n{"- " * 20}\n' \
               f'{phrase}, температура  будет  : {this_day[code]["temp"]} °C\n{this_day[code]["icon"]}' \
               f' {this_day[code]["d_status"]},\n' \
               f'🌬 скорость ветра: {this_day[code]["wind"]} метров в секунду  \n'

    def day_fragment(self, phrase, item_day):
        return f'{self.place_name}, {phrase}:  \n' \
               f'{self.str_fragment("утром в 8:00", "m", item_day)}' \
               f'{self.str_fragment("днём в 12:00", "a", item_day)}' \
               f'{self.str_fragment("вечером в 18:00", "e", item_day)}\n' \
               f'{"◾️" * 20}\n'

    def weather_tomorrow(self):
        this_day = {'m': self.dict_fragment(1, 8),
                    'a': self.dict_fragment(1, 12),
                    'e': self.dict_fragment(1, 18),
                    }
        return f'{self.place_name}, завтра:  \n' \
               f'{self.str_fragment("утром в 8:00", "m", this_day)}' \
               f'{self.str_fragment("днём в 12:00", "a", this_day)}' \
               f'{self.str_fragment("вечером в 18:00", "e", this_day)}'

    def next_days(self):
        time3 = (datetime.now() + timedelta(days=3)).replace(hour=8, minute=0)
        date3d = time3.strftime("%d.%m.%Y %A")
        this_day = {'m': self.dict_fragment(2, 8),
                    'a': self.dict_fragment(2, 12),
                    'e': self.dict_fragment(2, 18),
                    }
        rd3 = {'m': self.dict_fragment(3, 8),
               'a': self.dict_fragment(3, 12),
               'e': self.dict_fragment(3, 18),
               }

        return f'{self.day_fragment("послезавтра", this_day)}\n' \
               f'{self.day_fragment(date3d, rd3)}\n'

    dict = {}
# COMMANDS MESSAGE HANDLER
@bot.message_handler(commands=['start', 'refresh'])  # Decorator.
def commands_handler(message):
    # Keyboard SIMPLE
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # Клавиатура (Небольшие кнопки, два столбца.)
    item1 = types.KeyboardButton('🔴 кнопка 1')
    item2 = types.KeyboardButton('🔵 кнопка 2')
    item3 = types.KeyboardButton('🎲 Получить случайное число')
    item4 = types.KeyboardButton('🔙 назад')
    item5 = types.KeyboardButton('Погода')
    markup.add(item1, item2, item3, item4, item5)
    if message.text == '/refresh':  # Condition for command '/refresh'
        sti_ok = open('ok.webp', 'rb')
        bot.send_sticker(message.chat.id, sti_ok)
        sti_ok.close()
        bot.send_message(message.chat.id, 'кнопки добавлены/обновлены 😀', reply_markup=markup)
        return  # exit from the decorated function after this condition.
    # ------------------------------------------
    sti = open('sticker.webp', 'rb')  # открываем и читаем файл стикера 'rb' - чтение бинарного файла
    bot.send_sticker(message.chat.id, sti); sti.close()
    bot.send_message(message.chat.id, f'Привет, {message.chat.first_name}!', reply_markup=markup)
    print(bot.get_updates())


# ----------------------------------------TEXT MESSAGE HANDLER------------------------------------------------
@bot.message_handler(content_types=['text'])
def text_handler(message):
    text = message.text

    def catch_town(message):

        try:
            keyboard_next = types.InlineKeyboardMarkup()
            b1 = types.InlineKeyboardButton('погода на завтра', callback_data=f'nextd,{message.text}')
            b2 = types.InlineKeyboardButton('погода на 5 дней', callback_data=f'week,{message.text}')
            wapi = W_API(message.text)
            w_now = wapi.weather_now()
            keyboard_next.add(b1, b2)
            bot.reply_to(message, w_now)
            bot.send_message(message.chat.id, 'На когда прогноз? ', reply_markup=keyboard_next)
        except Exception as e:
            bot.reply_to(message,
                         f'Ой😰, ПРОИЗОШЛА ОШИБКА\nили  города/страны под названием {message.text}, '
                         f'к сожалению, нет в базе.'
                         f' Предлагаю вам посмотреть погоду в Киеве:  \n{W_API("Киев").weather_now()}')

    if text == "Погода":
        msg = bot.send_message(message.chat.id, 'Напишите страну или город')
        bot.register_next_step_handler(msg, catch_town)
        return
    elif text == 'pythonprogrammer':
        # Inline keyboard (ADMIN)
        markup2 = types.InlineKeyboardMarkup(row_width=2)  # разметка инлайн кнопок
        i_button1 = types.InlineKeyboardButton('💎API telegram💎',
                                               'https://core.telegram.org/bots/api#inlinekeyboardmarkup')  # инлайн кнопка
        i_button2 = types.InlineKeyboardButton('🧪pyTelegramBotAPI⚙',
                                               'https://github.com/eternnoir/pyTelegramBotAPI#types')
        i_button3 = types.InlineKeyboardButton('CallBack button', callback_data='123')
        markup2.add(i_button1, i_button2, i_button3)
        # Сообщение с инлайн клавиатурой
        bot.send_message(message.chat.id, '*Это меню админа:*',
                         reply_markup=markup2, parse_mode='Markdown')
        return

    elif text == '🎲 Получить случайное число':
        bot.send_message(message.chat.id, f"Вот ваше случайное число: ```{random.randint(0, 1000)}```",
                         parse_mode='Markdown')
        return
    elif text == '🔙 назад':
        bot.send_message(message.chat.id, 'кнопки удалены используйте команды [/]',
                         reply_markup=types.ReplyKeyboardRemove())
        return
    elif message.chat.type == 'private':
        if text == '🔴 кнопка 1':
            bot.send_message(message.chat.id, 'Это красная кнопка!')
            # return
        elif text == '🔵 кнопка 2':
            bot.send_message(message.chat.id, 'Это синяя кнопка!')
            # return
        else:
            sti = open('pum.webp', 'rb')
            bot.send_sticker(message.chat.id, sti); sti.close()
            bot.send_message(message.chat.id, '\nЧеловек, я тебя не понял! Попробуй ввести команду /start или  /refresh  для отображения клавиатуры управления')
            bot.reply_to(message, f'{message.text}?...')
            (ch_id, str_msg) = (-1001253711693, f'@{message.chat.username}\n {message.chat.first_name} \nsay: {message.text}')
            bot.send_message(ch_id, str_msg, disable_notification=True)


# --------------------------------CALLBACK HANDLER-------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True, )
def callback_inline(call):
    try:
        if call.message:
            if call.data == '123':
                bot.send_message(call.message.chat.id, '`Some result \n...`', parse_mode='markdown')
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🆗',
                                      reply_markup=None)
                bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text='ALERT!!!', )
                return

            elif call.data.split(',')[0] == 'nextd':  # На следующий день погода
                forecast = W_API(call.data.split(',')[1])
                forecast.weather_fc_init()  # инициализация данных для прогноза
                bot.send_message(call.message.chat.id, forecast.weather_tomorrow())

            elif call.data.split(',')[0] == 'week':  # На пять дней вперед
                forecast_5 = W_API(call.data.split(',')[1])
                forecast_5.weather_fc_init()
                bot.send_message(call.message.chat.id, forecast_5.next_days())
    except Exception as e:
        print(repr(e))


bot.polling(none_stop=True)
# f'{message.first_name}: \n{message.text}'
