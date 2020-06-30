# Version for github
import locale
import random
from datetime import timedelta
import pyowm  # https://github.com/csparpa/pyowm
import telebot
from telebot import types
import config
from t import gr as rr
from pyowm.utils.config import get_default_config
from wapi import W_API

config_dict = get_default_config()
config_dict['language'] = 'ru'  # your language here
print(rr.greeting)
bot = telebot.TeleBot(config.TOKEN)  # telegram bot API
owm = pyowm.OWM(config.APIkey_owm, config_dict)  # погодный API open weather map
locale.setlocale(locale.LC_ALL, "ru")
gmt0gmt2_delta = timedelta(hours=2)  # GMT+2
gmt0gmt3_delta = timedelta(hours=3)  # GMT+3


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
            wapi = W_API(message.text, owm, gmt=gmt0gmt3_delta, )
            w_now = wapi.weather_now()
            keyboard_next.add(b1, b2)
            bot.reply_to(message, w_now)
            bot.send_message(message.chat.id, 'На когда прогноз? ', reply_markup=keyboard_next)
        except Exception as e:
            bot.reply_to(message,
                         f'Ой😰, ПРОИЗОШЛА ОШИБКА\nили  города/страны под названием {message.text}, '
                         f'к сожалению, нет в базе.'
                         f' Предлагаю вам посмотреть погоду в Киеве:  \n{W_API("Киев", owm,  gmt=gmt0gmt3_delta).weather_now()}')

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
                forecast = W_API(call.data.split(',')[1], owm,  gmt=gmt0gmt3_delta)
                forecast.weather_fc_init()  # инициализация данных для прогноза
                bot.send_message(call.message.chat.id, forecast.weather_tomorrow())

            elif call.data.split(',')[0] == 'week':  # На пять дней вперед
                forecast_5 = W_API(call.data.split(',')[1], owm,  gmt=gmt0gmt3_delta)
                forecast_5.weather_fc_init()
                bot.send_message(call.message.chat.id, forecast_5.next_days())
    except Exception as e:
        print(repr(e))


bot.polling(none_stop=True)
# f'{message.first_name}: \n{message.text}'
