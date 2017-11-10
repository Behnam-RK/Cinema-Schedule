import time
import config
from Bot import Bot
from models import init_models

data = dict(
    urls = dict(
        cinema_prefix = 'https://www.cinematicket.org/',
        cinema_list = 'https://www.cinematicket.org/?p=cinema'
    ),
    drafts = dict(
        welcome = 'خوش آمدید!\nبوسیله ی این ربات شما می توانید از برنامه اکران سینما های سراسر کشور مطلع شوید و در صورت تمایل برای رزرو بلیت اقدام کنید.',
        usage = 'برای دریافت لیست سینماهای تهران /list1 را وارد کنید.\nبرای دریافت لیست سینماهای شهرستان ها /list2 را وارد کنید.\nو سپس برای مشاهده برنامه اکران هر سینما شماره سینما (که در لیست نوشته شده) را ارسال کنید.\nو برای دریافت دوباره این راهنما /help را وارد کنید.',
        invalid_input = 'ورودی شما نامعتبر است!',
        error = 'خطایی در حین عملیات رخ داده است! لطفا مدتی بعد تلاش کنید و یا مشکل را به ادمین ربات گزارش کنید.\n(آی دی ادمین در بیوی ربات قرار دارد)'
    ),
    emojis = dict(
        movie_camera = '\U0001F3A5',
        clapper_board = '\U0001F3AC',
        alarm_clock = '\U000023F0',
        stopwatch = '\U000023F1',
        black_telephone = '\U0000260E',
        white_medium_star = '\U00002B50',
        heavy_minus_sign = '\U00002796',
        cinema = '\U0001F3A6',
        top_hat = '\U0001F3A9',
        ticket = '\U0001F3AB',
        performing_arts = '\U0001F3AD',
        speech_balloon = '\U0001F4AC',
        heavy_dollar_sign = '\U0001F4B2',
        money_bag = '\U0001F4B0',
        floppy_disk = '\U0001F4BE',
        calendar = '\U0001F4C5',
        tear_off_calendar = '\U0001F4C6',
        pushpin = '\U0001F4CC',
        telephone_receiver = '\U0001F4DE',
        memo = '\U0001F4DD',
        thought_balloon = '\U0001F4AD',
        bicyclist = '\U0001F6B4',
        taxi = '\U0001F695',
        oncoming_taxi = '\U0001F696'
    )
)

if __name__ == '__main__':
    session = init_models(config.db_engine_url)

    bot = Bot(config.token, session, data)
    bot.run()
    print('Listening ...')

    while True:
        time.sleep(10)
