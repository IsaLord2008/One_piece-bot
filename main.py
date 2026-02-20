import os
from dotenv import load_dotenv
import telebot

load_dotenv()  # فایل .env رو می‌خونه
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, " سلام بچه ها به وانپیس رول خوش اومدید")

bot.polling()
