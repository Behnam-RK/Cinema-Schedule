from telepot import Bot as Telepot_Bot, glance, message_identifier,\
                           origin_identifier
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.helper import Answerer
from telepot.loop import MessageLoop
from sqlalchemy.sql import func
from datetime import datetime
from threading import Timer
from random import shuffle
from math import sqrt
from pprint import pprint
from bs4 import BeautifulSoup
import requests
import re
import traceback

from models import User, Chat, User_Chat, Message, Cinema, Error


class Bot:
    def __init__(self, token, session, data=dict()):
        self.bot = Telepot_Bot(token)
        self.answerer = Answerer(self.bot)
        self.session = session

        self.data = data


    def run(self):
        MessageLoop(self.bot, 
                        {'chat': self.on_chat_message, 
                         'callback_query': self.on_callback_query}
                        #  'inline_query': self.on_inline_query, 
                        #  'chosen_inline_result': self.on_chosen_inline_result}
                   ).run_as_thread()


    def register_user_chat(self, user, chat):
        user_chat = User_Chat()
        user_chat.user = user
        user_chat.chat = chat
        self.session.add(user_chat)
        self.session.commit()

        return user_chat


    def register_user(self, msg):
        user_id = msg['from'].get('id')
        username = msg['from'].get('username', '')
        full_name = msg['from'].get('first_name', '') + ' ' + msg['from'].get('last_name', '')
        user = User(user_id=user_id, username=username, full_name=full_name)
        self.session.add(user)
        self.session.commit()

        return user


    def register_chat(self, msg):
        chat_id = msg['chat'].get('id')
        chat_type = msg['chat'].get('type')
        title = msg['chat'].get('title')
        chat = Chat(chat_id=chat_id, chat_type=chat_type, title=title)
        self.session.add(chat)
        self.session.commit()

        return chat


    def get_user_chat(self, msg):
        user_id = msg['from'].get('id')
        chat_id = msg['chat'].get('id')
        
        user = self.session.query(User).filter(User.user_id == user_id).first()
        if user is None:
            user = self.register_user(msg)

        chat = self.session.query(Chat).filter(Chat.chat_id == chat_id).first()
        if chat is None:
            chat = self.register_chat(msg)

        user_chat = self.session.query(User_Chat).filter(User_Chat.user_id == user.id, User_Chat.chat_id == chat.id).first()
        if user_chat is None:
            user_chat = self.register_user_chat(user, chat)

        return user_chat


    def register_msg(self, msg, user_chat):
        content_type, chat_type, chat_id = glance(msg)
        text = msg['text']
        message = Message(content_type=content_type, text=text)
        self.session.add(message)
        user_chat.messages.append(message)
        self.session.commit()

        return message


    def get_soup(self, url):
        try:
            response = requests.get(url)
            content = response.content
        except:
            try:
                url = url.replace('https', 'http')
                response = requests.get(url)
                content = response.content
            except:
                raise Exception('networking error')

        # print('Fetched!')
        soup = BeautifulSoup(content, 'html.parser')
        # print('Parsed!')

        return soup


    def msg_splitter(self, msg):
        if len(msg) > 4095:
            for i in range(4095, 0, -1):
                if msg[i] == '\n':
                    split_pos = i
                    break
            return [msg[:split_pos]] + self.msg_splitter(msg[split_pos:])
        else:
            return [msg]


    def send_long_msg(self, chat_id, msg):
        messages = self.msg_splitter(msg)

        for msg in messages:
            self.bot.sendMessage(chat_id, msg)


    def get_cinema_list(self, req_city=r'.*'):
        cinema_list_url = self.data['urls']['cinema_list']
        soup = self.get_soup(cinema_list_url)

        cinemas_data = soup.find_all('div', class_='right')

        for cinema_data in cinemas_data:
            url = cinema_data.h2.a['href']
            cid = re.search(r'cid=(\d*)&', url).group(1)
            title = cinema_data.h2.a.string
            address = cinema_data.contents[4]
            phones = list()
            for data in cinema_data.contents[5:]:
                if data.find('و') and data.find('و') != -1:
                    data_splitted_list = data.split('و')
                    for d in data_splitted_list:
                        digits = re.findall(r'[۰۱۲۳۴۵۶۷۸۹0-9]', str(d))
                        if len(digits) > 6:
                            cleaned_phone = re.sub(r'(\d)\s(\d)', '\g<1>-\g<2>', str(d))
                            cleaned_phone = re.sub(r'[^۰۱۲۳۴۵۶۷۸۹0-9–\-]', '', str(cleaned_phone))
                            cleaned_phone = cleaned_phone.replace('–', '-')
                            dash_idx = cleaned_phone.find('-')
                            if dash_idx != -1:
                                if len(cleaned_phone[:dash_idx]) > len(cleaned_phone[dash_idx + 1:]):
                                    cleaned_phone = cleaned_phone[dash_idx + 1:] + '-' + cleaned_phone[:dash_idx]
                            phones.append(cleaned_phone)
                
                else:
                    digits = re.findall(r'[۰۱۲۳۴۵۶۷۸۹0-9]', str(data))
                    if len(digits) > 6:
                        cleaned_phone = re.sub(r'(\d)\s(\d)', '\g<1>-\g<2>', str(data))
                        cleaned_phone = re.sub(r'[^۰۱۲۳۴۵۶۷۸۹0-9–\-]', '', str(cleaned_phone))
                        cleaned_phone = cleaned_phone.replace('–', '-')
                        dash_idx = cleaned_phone.find('-')
                        if dash_idx != -1:
                            if len(cleaned_phone[:dash_idx]) > len(cleaned_phone[dash_idx + 1:]):
                                cleaned_phone = cleaned_phone[dash_idx + 1:] + '-' + cleaned_phone[:dash_idx]
                        phones.append(cleaned_phone)

            phone = '\n‏'.join(phones)
            city = re.search(r'^(.*?)\s-', address).group(1)
            url = url.replace('./', self.data['urls']['cinema_prefix'])
            url = re.sub(r'&t=.*$', '', url)
            if re.search(req_city, city):
                cinema = self.session.query(Cinema).filter(Cinema.cid == cid).first()

                if cinema:
                    if cinema.title != title or cinema.address != address or cinema.phone != phone or cinema.city != city:
                        cinema.title = title
                        cinema.address = address
                        cinema.phone = phone
                        cinema.city = city
                        self.session.add(cinema)

                else:
                    cinema = Cinema(cid=cid, title=title, city=city, address=address, phone=phone, url=url)
                    self.session.add(cinema)

        self.session.commit()

        if req_city == r'^(?!تهران).*?$':
            cinema_list = self.session.query(Cinema).filter(Cinema.city != u'تهران').order_by(Cinema.city).all()

        elif req_city == r'.*':
            cinema_list = self.session.query(Cinema).order_by(Cinema.city).all()

        else:
            cinema_list = self.session.query(Cinema).filter(Cinema.city == req_city).order_by(Cinema.city).all()

        return cinema_list


    def compose_cinema_list_msg(self, cinema_list):
        emojis = self.data['emojis']
        # border = emojis['heavy_minus_sign'] * 12
        alert = '\n\n‏{list_emoji}شماره سینمای موردنظر خود را وارد کنید{list_emoji}\n\n'\
                            .format(list_emoji=emojis['memo'])
        cinema_list_msg = alert

        city = None
        for cinema in cinema_list:
            if city != cinema.city:
                city = cinema.city
                cinema_list_msg += '\n{city}:\n'.format(city=city)

            cinema_list_msg += '     /{cid}. {title}\n'\
                                .format(cid=cinema.cid, 
                                        title=cinema.title)

        cinema_list_msg += alert
        
        return cinema_list_msg


    def get_cinema_info(self, cid):
        cinema = self.session.query(Cinema).filter(Cinema.cid == cid).first()
        if cinema is None:
            raise Exception('cinema does not exist')

        soup = self.get_soup(cinema.url)

        cinema_info = dict()

        cinema_title = soup.find(class_='cinema-title').text.strip()

        cinema_info['cinema_title'] = cinema_title
        cinema_info['cid'] = cid
        cinema_info['url'] = cinema.url
        cinema_info['address'] = cinema.address
        cinema_info['phone'] = cinema.phone
        cinema_info['screening_movies'] = list()

        movies = soup.find_all('div', class_='showtime--items_step')

        for movie in movies:
            movie_dic = dict()

            meta = movie.contents[1].find('div', class_='name').span.text.strip()
            title, director = re.search(r"^(.*?)\s\s+(.*?)$", meta, flags=re.DOTALL).group(1, 2)
            art_experience = movie.contents[1].find('span', {'data-ballon': 'هنر و تجربه'})

            movie_dic['title'] = title.strip()
            movie_dic['director'] = director.replace('کارگردان: ', '').strip()
            movie_dic['art_experience'] = True if art_experience else False
            movie_dic['showdates'] = list()

            dates = movie.contents[3].find_all('div', class_='showtime--panel_group')

            for date in dates:
                showdate_dic = dict()

                d = date.header.text.strip()

                showdate_dic['date'] = d
                showdate_dic['showtimes'] = list()

                showtimes = date.contents[3].find_all('div', class_='ticket-card_time ')

                for showtime in showtimes:
                    showtime_dic = dict()

                    time = showtime.contents[1].text.strip()
                    price = showtime.contents[5].text.strip()

                    showtime_dic['time'] = time
                    showtime_dic['price'] = price
                    
                    showdate_dic['showtimes'].append(showtime_dic)
                    
                movie_dic['showdates'].append(showdate_dic)
                
            cinema_info['screening_movies'].append(movie_dic)

        return cinema, cinema_info


    def compose_cinema_msg(self, cinema_info):
        emojis = self.data['emojis']

        cinema_title = cinema_info['cinema_title']

        cinema_msg = '{cinema_emoji}برنامه روز های آتی {cinema_title} به شرح زیر است:\n\n'\
                        .format(cinema_emoji=emojis['white_medium_star'], 
                                cinema_title=cinema_title)

        screening_movies = cinema_info['screening_movies']

        for movie in screening_movies:
            title = 'فیلم: ' + movie['title']
            director = 'کارگردان: ' + movie['director']
            description = '\n{art_experience_emoji} هنر و تجربه'.format(art_experience_emoji=emojis['performing_arts']) if movie['art_experience'] else ''

            separator = emojis['heavy_minus_sign'] * 12
            cinema_msg += '‏{separator}\n{title_emoji} {title}{description}\n{director_emoji} {director}\n'\
                            .format(separator=separator, 
                                    title_emoji=emojis['clapper_board'], 
                                    title=title, 
                                    description=description, 
                                    director_emoji=emojis['speech_balloon'], 
                                    director=director)

            showdates = movie['showdates']

            for showdate in showdates:
                date = showdate['date']
                
                cinema_msg += '\n{date_emoji} {date}'\
                                .format(date_emoji=emojis['calendar'], 
                                        date=date)

                showtimes = showdate['showtimes']

                for showtime in showtimes:
                    time = showtime['time'] 
                    price = showtime['price']

                    cinema_msg += '\n{time_emoji} {time} --- {price_emoji}{price}'\
                                    .format(time_emoji=emojis['alarm_clock'], 
                                            price_emoji=emojis['heavy_dollar_sign'], 
                                            time=time, 
                                            price=price)

                cinema_msg += '\n'

            cinema_msg += '\n'

        address = cinema_info['address'] if cinema_info['address'] != '' else 'ثبت نشده!'
        phone = cinema_info['phone'] if cinema_info['phone'] != '' else 'ثبت نشده!'

        cinema_msg += '‏{separator}\n{address_emoji} آدرس: \n‏{address}\n{phone_emoji} تلفن: \n‏{phone}\n'\
                        .format(separator=separator, 
                                address_emoji=emojis['taxi'], 
                                address=address, 
                                phone_emoji=emojis['telephone_receiver'], 
                                phone=phone)

        cinema_url = cinema_info['url']

        cinema_msg += '‏{separator}\n{ticket_emoji} برای خرید بلیت به لینک زیر مراجعه کنید: \n{cinema_url}\n\n'\
                        .format(separator=separator, 
                                ticket_emoji=emojis['ticket'], 
                                cinema_url=cinema_url)
        cinema_msg += '{list_emoji} لیست سینماهای تهران: /list1\n{list_emoji} لیست سینماهای شهرستان ها: /list2'\
                        .format(list_emoji=emojis['memo'])

        return cinema_msg


    def on_chat_message(self, msg):
        self.session.commit()

        content_type, chat_type, chat_id = glance(msg)
        # print('Chat:', content_type, chat_type, chat_id)
        # pprint(msg)
        user_chat = self.get_user_chat(msg)
        message = self.register_msg(msg, user_chat)

        if content_type != 'text':
            reply = self.data['drafts']['invalid_input']
            self.bot.sendMessage(chat_id, reply)
            reply = self.data['drafts']['usage']
            self.bot.sendMessage(chat_id, reply)
            message.replied = 1
            self.session.add(message)
            self.session.commit()
            return

        msg['text'] = msg['text'].lower()

        if msg['text'] == '/start':
            message.is_valid = 1
            reply = self.data['drafts']['welcome']
            self.bot.sendMessage(chat_id, reply)
            reply = self.data['drafts']['usage']
            self.bot.sendMessage(chat_id, reply)
            message.replied = 1
            self.session.add(message)
            self.session.commit()

        elif msg['text'] == '/help':
            message.is_valid = 1
            reply = self.data['drafts']['usage']
            self.bot.sendMessage(chat_id, reply)
            message.replied = 1
            self.session.add(message)
            self.session.commit()

        elif msg['text'] == '/list1':
            message.is_valid = 1
            try:
                cinema_list = self.get_cinema_list(u'تهران')

            except Exception as error:
                reply = self.data['drafts']['error']
                self.bot.sendMessage(chat_id, reply)
                message.replied = 1

                tb = traceback.format_exc()
                e = Error(type=str(error), traceback=tb)
                e.message = message
                self.session.add(e)

            else:
                cinema_list_msg = self.compose_cinema_list_msg(cinema_list)
                reply = cinema_list_msg
                self.send_long_msg(chat_id, reply)
                message.replied = 1

            finally:
                self.session.add(message)
                self.session.commit()

        elif msg['text'] == '/list2':
            message.is_valid = 1
            try:
                cinema_list = self.get_cinema_list(r'^(?!تهران).*?$')

            except Exception as error:
                reply = self.data['drafts']['error']
                self.bot.sendMessage(chat_id, reply)
                message.replied = 1

                tb = traceback.format_exc()
                e = Error(type=str(error), traceback=tb)
                e.message = message
                self.session.add(e)

            else:
                cinema_list_msg = self.compose_cinema_list_msg(cinema_list)
                reply = cinema_list_msg
                self.send_long_msg(chat_id, reply)
                message.replied = 1

            finally:
                self.session.add(message)
                self.session.commit()

        elif msg['text'].isdigit() or (msg['text'][0] == '/' and msg['text'][1:].isdigit()):
            message.is_valid = 1
            if msg['text'][0] == '/':
                msg['text'] = msg['text'][1:]
            cid = int(msg['text'])
            try:
                cinema, cinema_info = self.get_cinema_info(cid)
            except Exception as error:
                if str(error) == 'networking error':
                    reply = self.data['drafts']['error']

                elif str(error) == 'cinema does not exist':
                    reply = self.data['drafts']['invalid_input']

                else:
                    reply = self.data['drafts']['error']

                self.bot.sendMessage(chat_id, reply)
                message.replied = 1

                tb = traceback.format_exc()
                e = Error(type=str(error), traceback=tb)
                e.message = message
                self.session.add(e)

            else:
                cinema_msg = self.compose_cinema_msg(cinema_info)
                self.send_long_msg(chat_id, cinema_msg)
                message.cinema = cinema
                message.replied = 1
                
            finally:
                self.session.add(message)
                self.session.commit()

        else:
            pass


    def on_callback_query(self, msg):
        self.session.commit()

        query_id, chat_id, data = glance(msg, flavor='callback_query')
        # print('Callback query:', query_id, chat_id, data)
        # pprint(msg)
