from telebot import TeleBot,types
import os
from dotenv import load_dotenv
import requests
import db_api
import time

load_dotenv()

TG_BOT_TOKEN = os.getenv('TG_TOKEN')
BITLY_TOKEN = os.getenv('BITLY_TOKEN')
BITLY_URL = os.getenv('BITLY_URL')
WELCOME_MESSAGE = '''
Hey! I can shorten links and many more

👉 Send long url https://www.chelseafc.com/en
    receive short https://bit.ly/2FUgzLF
    
👉 Send short url bit.ly/2FUgzLf
    receive clicks count
    
👉 Also you can use buttons to see help again or top links by clicks count
'''
ABOUT = 'about me'
TOP_LINKS = 'see top links'
TOP_24 = 'top24'
TOP_ALL = 'top_all'
CLICKS_COUNT = '👉 Clicks count = '
LINK_CLICKS_COUNT = '- clicks count for {}={}'

bot = TeleBot(TG_BOT_TOKEN)

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton(text=ABOUT))
    markup.add(types.KeyboardButton(text=TOP_LINKS))
    return markup

def get_top_links_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='top links (24 hours)', callback_data=TOP_24))
    markup.add(types.InlineKeyboardButton(text='top links (all time)', callback_data=TOP_ALL))
    return markup

def get_timestamp():
    return int(time.time())

def get_headers(token):
    headers = {'content-type':'application/json','Authorization':f'Bearer {token}'}
    return headers

def shorten_url(link):
    url = BITLY_URL + 'shorten'
    headers = get_headers(BITLY_TOKEN)
    data = f'{{ "long_url": "{link}", "domain": "bit.ly", "group_guid": "Bp43hhcliR5" }}'

    response = requests.post(url=url, headers=headers, data=data)
    if response.ok:
        bitly_data = response.json()
        return bitly_data['link']
    else:
        return None

def get_clicks_count(link):
    # only paid plan feature
    url = BITLY_URL + f'bitlinks{link}/clicks/summary'

    # print(f'url in get_clicks: {url}')
    headers = get_headers(BITLY_TOKEN)
    params = (
        ('unit', 'month'),
        ('units', '-1'),
    )
    response = requests.get(url=url, headers=headers,params=params)
    # print(response.json())
    if response.ok:
        bitly_data = response.json()
        return bitly_data['total_clicks']

def clicks_updater():
    while True:
        print('updater start')
        offset = 0
        while True:
            rows = db_api.get_links(offset=offset)

            if not rows:
                break

            for old_clicks, link in rows:
                print('get clicks count for ', link)
                clicks_count = get_clicks_count(link)

                if isinstance(clicks_count, int) and clicks_count != old_clicks:
                    db_api.update_link_clicks(link,clicks_count)

            offset += 10

        print('update done. Next in 30 min')
        time.sleep(60*30)

@bot.message_handler(commands=['start','help'])
def start_handler(msg):
    keyboard = get_main_keyboard()
    bot.send_message(msg.chat.id, text=WELCOME_MESSAGE, reply_markup=keyboard, disable_web_page_preview=True)

@bot.message_handler(regexp=f'^{ABOUT}$')
def about_handler(msg):
    bot.reply_to(msg, text=WELCOME_MESSAGE,disable_web_page_preview=True)

@bot.message_handler(regexp=f'^{TOP_LINKS}$')
def top_links_handler(msg):
    keboard = get_top_links_keyboard()
    bot.send_message(msg.chat.id, text='choose period',reply_markup=keboard)

@bot.message_handler()
def messages_handler(msg):
    link_url = msg.text[6:] if msg.text.startswith('https://bit.ly') else msg.text

    # print(link_url)

    clicks_count = get_clicks_count(link_url)

    if isinstance(clicks_count, int):
        response = CLICKS_COUNT + str(clicks_count)
        db_api.update_link_clicks(link_url,clicks_count)
    else:
        text = 'https://' + msg.text if not msg.text.startswith('https://') else msg.text
        short_link = shorten_url(text)

        if short_link:
            response = short_link
            db_api.create_link_record(msg.from_user.id, text, short_link[6:], get_timestamp())
        else:
            response = 'PLs provide valid URL'

    bot.reply_to(msg, text=response)

@bot.callback_query_handler(func=lambda call:TOP_24 in call.data)
def top_24_handler(call):
    timestamp = get_timestamp()
    created_after = timestamp - 86400
    stats = db_api.get_top_links(call.from_user.id, created_after=created_after)
    response = ''
    for link, clicks in stats:
        response += LINK_CLICKS_COUNT.format(link,clicks)
        response += '\n'

    bot.send_message(call.from_user.id, text=response, disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call:TOP_ALL in call.data)
def top_all_handler(call):
    stats = db_api.get_top_links(call.from_user.id)
    response = ''
    for link, clicks in stats:
        response += LINK_CLICKS_COUNT.format(link, clicks)
        response += '\n'

    bot.send_message(call.from_user.id, text=response, disable_web_page_preview=True)

bot.polling()