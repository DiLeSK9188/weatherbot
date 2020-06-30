from datetime import datetime
from datetime import timedelta

class W_API:
    def __init__(self, place_name, owm, gmt):
        self.place_name = place_name
        self.gmt_delta = gmt
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
        time = tw + self.gmt_delta
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
