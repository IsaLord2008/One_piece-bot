import os
import telebot
import sqlite3
import random
from datetime import datetime
from dotenv import load_dotenv

# ------------- بارگذاری توکن امن از .env -------------
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise Exception("توکن ربات در فایل .env یافت نشد!")
bot = telebot.TeleBot(TOKEN)

# ------------- تنظیمات ثابت بازی -------------
INITIAL_HP = 300
INITIAL_BOUNTY = 0
INITIAL_DAMAGE = 10
INITIAL_POINTS = 0

UPGRADE_COSTS = {'hp': 1, 'damage': 1}
UPGRADE_AMOUNTS = {'hp': 50, 'damage': 50}

TITLES = {
    'pirate': 'دزد دریایی تازه وارد',
    'marine': 'ملوان',
    'bounty': 'جایزه‌بگیر بی تجربه'
}
CLASS_NAMES = {
    'pirate': '🏴‍☠️ دزد دریایی',
    'marine': '⚓ نیروی دریایی',
    'bounty': '💰 جایزه‌بگیر'
}

# ------------- دیتابیس SQLITE -------------
class Database:
    def __init__(self, path='onepiece.db'):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                chat_id TEXT,
                user_id TEXT,
                name TEXT,
                username TEXT,
                class TEXT,
                title TEXT,
                hp INTEGER,
                damage INTEGER,
                bounty INTEGER,
                points INTEGER,
                group_name TEXT,
                registered_at TEXT,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                name TEXT PRIMARY KEY,
                chat_id TEXT,
                owner TEXT,
                captain TEXT,
                right_hand TEXT,
                left_hand TEXT,
                group_bounty INTEGER,
                created_at TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                chat_id TEXT,
                group_name TEXT,
                user_id TEXT,
                username TEXT,
                name TEXT,
                message_id INTEGER,
                date TEXT
            )
        ''')
        self.conn.commit()

    # ------------- متدهای کاربران -------------
    def is_user_registered(self, chat_id, user_id):
        c = self.conn.cursor()
        c.execute('SELECT 1 FROM users WHERE chat_id=? AND user_id=?', (chat_id, user_id))
        return c.fetchone() is not None

    def add_user(self, chat_id, user_id, name, username, class_, title, hp, damage, bounty, points, registered_at):
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO users (chat_id, user_id, name, username, class, title, hp, damage, bounty, points, group_name, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
        ''', (chat_id, user_id, name, username, class_, title, hp, damage, bounty, points, registered_at))
        self.conn.commit()

    def get_user(self, chat_id, user_id):
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE chat_id=? AND user_id=?', (chat_id, user_id))
        return c.fetchone()

    def update_user(self, chat_id, user_id, field, value):
        c = self.conn.cursor()
        c.execute(f'UPDATE users SET {field}=? WHERE chat_id=? AND user_id=?', (value, chat_id, user_id))
        self.conn.commit()

    def set_user_group(self, chat_id, user_id, group_name):
        self.update_user(chat_id, user_id, 'group_name', group_name)

    # ------------- متدهای گروه‌ها -------------
    def create_group(self, group_name, chat_id, owner):
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO groups 
            (name, chat_id, owner, captain, right_hand, left_hand, group_bounty, created_at)
            VALUES (?, ?, ?, NULL, NULL, NULL, 0, ?)
        ''', (group_name, chat_id, owner, str(datetime.now())))
        self.conn.commit()

    def get_group(self, group_name, chat_id):
        c = self.conn.cursor()
        c.execute('SELECT * FROM groups WHERE name=? AND chat_id=?', (group_name, chat_id))
        return c.fetchone()

    def get_group_by_role(self, chat_id, user_id, role):
        # کاپیتان / دست چپ / راست
        c = self.conn.cursor()
        c.execute(f'SELECT * FROM groups WHERE chat_id=? AND {role}=?', (chat_id, user_id))
        return c.fetchone()

    def set_group_role(self, group_name, role, user_id):
        c = self.conn.cursor()
        c.execute(f'UPDATE groups SET {role}=? WHERE name=?', (user_id, group_name))
        self.conn.commit()

    def update_group_bounty(self, group_name, value):
        c = self.conn.cursor()
        c.execute('UPDATE groups SET group_bounty=? WHERE name=?', (value, group_name))
        self.conn.commit()

    def get_groups_by_chat(self, chat_id):
        c = self.conn.cursor()
        c.execute('SELECT * FROM groups WHERE chat_id=?', (chat_id,))
        return c.fetchall()

    # ------------- متدهای عضویت و درخواست -------------
    def add_request(self, chat_id, group_name, user_id, username, name, message_id):
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO requests (chat_id, group_name, user_id, username, name, message_id, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, group_name, user_id, username, name, message_id, str(datetime.now())))
        self.conn.commit()

    def get_pending_request(self, chat_id, group_name, message_id):
        c = self.conn.cursor()
        c.execute('SELECT * FROM requests WHERE chat_id=? AND group_name=? AND message_id=?',
                  (chat_id, group_name, message_id))
        return c.fetchone()

    def remove_request(self, chat_id, group_name, message_id):
        c = self.conn.cursor()
        c.execute('DELETE FROM requests WHERE chat_id=? AND group_name=? AND message_id=?',
                  (chat_id, group_name, message_id))
        self.conn.commit()

    def has_pending_request(self, chat_id, group_name, user_id):
        c = self.conn.cursor()
        c.execute('SELECT 1 FROM requests WHERE chat_id=? AND group_name=? AND user_id=?',
                  (chat_id, group_name, user_id))
        return c.fetchone() is not None

    # ------------- متدهای اعضای گروه -------------
    def add_member(self, chat_id, group_name, user_id):
        self.set_user_group(chat_id, user_id, group_name)
        # می‌توان اعضای گروه را با join در user جستجو کرد

    def get_group_members(self, chat_id, group_name):
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE chat_id=? AND group_name=?', (chat_id, group_name))
        return c.fetchall()

db = Database()

# ------------- توابع نقش و مجوزها -------------
def is_captain(chat_id, user_id):
    return db.get_group_by_role(chat_id, user_id, 'captain') is not None

def is_right_hand(chat_id, user_id):
    return db.get_group_by_role(chat_id, user_id, 'right_hand') is not None

def is_left_hand(chat_id, user_id):
    return db.get_group_by_role(chat_id, user_id, 'left_hand') is not None

def can_accept_member(chat_id, user_id):
    return is_captain(chat_id, user_id) or is_right_hand(chat_id, user_id) or is_left_hand(chat_id, user_id)

# ------------- دستورات بات -------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "🎮 به ربات گروهی وان پیس خوش اومدی!\n"
        "برای راهنما: /help")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📚 راهنمای ربات:
۱. ثبت‌نام (مالک روی کاربر ریپلای کند): /Welcome_To_Onepiece
۲. ساخت گروه: /creategroup نام
۳. عضویت: /joingroup نام
۴. پروفایل: /wanted
۵. کاپیتان/دستیارها: /accept
بقیه دستورات مدیریتی مشابه نسخه قدیمی
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['Welcome_To_Onepiece'])
def welcome_new_player(message):
    if message.chat.type == 'private' or not message.reply_to_message:
        bot.reply_to(message, "این دستور فقط توی گروه و روی ریپلای کار می‌کند!")
        return
    target = message.reply_to_message.from_user
    user_id = str(target.id)
    chat_id = str(message.chat.id)
    if db.is_user_registered(chat_id, user_id):
        bot.reply_to(message, f"{target.first_name} قبلاً ثبت نام کرده!")
        return
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for k, v in CLASS_NAMES.items():
        markup.add(telebot.types.InlineKeyboardButton(v, callback_data=f"reg_{k}_{user_id}_{chat_id}"))
    bot.send_message(chat_id, f"👤 {target.first_name}\n🎭 لطفاً کلاس رو انتخاب کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reg_'))
def handle_role_selection(call):
    _, role, target_user_id, chat_id = call.data.split('_')
    user_id = str(call.from_user.id)
    if user_id != target_user_id:
        bot.answer_callback_query(call.id, "مال تو نیست", show_alert=True)
        return
    if db.is_user_registered(chat_id, user_id):
        bot.answer_callback_query(call.id, "قبلاً ثبت‌نام کردی!", show_alert=True)
        return
    db.add_user(
        chat_id, user_id,
        call.from_user.first_name, call.from_user.username, role, TITLES[role],
        INITIAL_HP, INITIAL_DAMAGE, INITIAL_BOUNTY, INITIAL_POINTS,
        str(datetime.now())
    )
    bot.edit_message_text(
        f"✅ ثبت نام با موفقیت انجام شد!\n"
        f"🎭 کلاس: {CLASS_NAMES[role]}\n"
        f"🏷️ لقب: {TITLES[role]}\n"
        f"برای عضویت: /joingroup نام_گروه",
        chat_id, call.message.message_id
    )

@bot.message_handler(commands=['wanted', 'bag'])
def wanted(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    user = db.get_user(chat_id, user_id)
    if not user:
        bot.reply_to(message, "اول ثبت‌نام کن!")
        return
    text = f"""🏴‍☠️ WANTED 🏴‍☠️
👤 نام: {user['name']}
🎭 کلاس: {CLASS_NAMES.get(user['class'], 'نامشخص')}
🏷️ لقب: {user['title']}
❤️ HP: {user['hp']}
⚔️ دمیج: {user['damage']}
💰 بونتی: {user['bounty']}
⭐ امتیاز: {user['points']}
👥 گروه: {user['group_name'] or 'عضو هیچ گروهی نیست'}"""
    bot.reply_to(message, text)

@bot.message_handler(commands=['creategroup'])
def create_group(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    try:
        group_name = message.text.split(maxsplit=1)[1]
    except:
        bot.reply_to(message, "نام گروه را وارد کن. /creategroup نام")
        return
    if db.get_group(group_name, chat_id):
        bot.reply_to(message, "این گروه قبلاً ساخته شده")
        return
    db.create_group(group_name, chat_id, user_id)
    bot.reply_to(message, f"✅ گروه {group_name} ساخته شد. ریپلای روی کاربر: /setcaptain")

@bot.message_handler(commands=['setcaptain', 'setright', 'setleft'])
def set_roles(message):
    if not message.reply_to_message:
        bot.reply_to(message, "باید ریپلای کنی!")
        return
    role_cmd = message.text.split()[0][1:]
    role_db = {'setcaptain': "captain", 'setright': "right_hand", 'setleft': "left_hand"}[role_cmd]
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    group = db.get_group_by_role(chat_id, user_id, 'owner' if role_db == "captain" else 'captain')
    if not group:
        bot.reply_to(message, "دسترسی نداری!")
        return
    target = message.reply_to_message.from_user
    if not db.is_user_registered(chat_id, str(target.id)):
        bot.reply_to(message, "کاربر عضو نیست!")
        return
    db.set_group_role(group['name'], role_db, str(target.id))
    db.add_member(chat_id, group['name'], str(target.id))
    bot.reply_to(message, f"{target.first_name} {role_db} شد.")

@bot.message_handler(commands=['joingroup'])
def join_group(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    if not db.is_user_registered(chat_id, user_id):
        bot.reply_to(message, "ثبت‌نام نکردی!")
        return
    try:
        group_name = message.text.split(maxsplit=1)[1]
    except:
        bot.reply_to(message, "اسم گروه را وارد کن /joingroup گروه")
        return
    if not db.get_group(group_name, chat_id):
        bot.reply_to(message, "گروهی یافت نشد!")
        return
    if db.has_pending_request(chat_id, group_name, user_id):
        bot.reply_to(message, "درخواست در حال بررسی است.")
        return
    db.add_request(chat_id, group_name, user_id, message.from_user.username, message.from_user.first_name, message.message_id)
    bot.reply_to(message, f"درخواست عضویت ارسال شد! مسئولین گروه با ریپلای روی این پیام /accept بزنند.")

@bot.message_handler(commands=['accept'])
def accept_request(message):
    if not message.reply_to_message:
        bot.reply_to(message, "باید روی پیام درخواست عضویت ریپلای کنی!")
        return
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    if not can_accept_member(chat_id, user_id):
        bot.reply_to(message, "دسترسی پذیرش عضویت نداری!")
        return
    # جستجو میان درخواست‌های این گروه و این چت بر اساس message_id
    for group in db.get_groups_by_chat(chat_id):
        req = db.get_pending_request(chat_id, group['name'], message.reply_to_message.message_id)
        if req:
            db.add_member(chat_id, group['name'], req['user_id'])
            db.remove_request(chat_id, group['name'], message.reply_to_message.message_id)
            bot.reply_to(message, f"{req['name']} به گروه {group['name']} اضافه شد.")
            return
    bot.reply_to(message, "درخواست معتبر پیدا نشد!")

@bot.message_handler(commands=['groupinfo'])
def group_info(message):
    chat_id = str(message.chat.id)
    groups = db.get_groups_by_chat(chat_id)
    if not groups:
        bot.reply_to(message, "گروهی ساخته نشده.")
        return
    for group in groups:
        members = db.get_group_members(chat_id, group['name'])
        cap = db.get_user(chat_id, group['captain'])['name'] if group['captain'] else "نامشخص"
        right = db.get_user(chat_id, group['right_hand'])['name'] if group['right_hand'] else "ندارد"
        left = db.get_user(chat_id, group['left_hand'])['name'] if group['left_hand'] else "ندارد"
        text = f"""👥 گروه {group['name']}
👑 کاپیتان: {cap}
✋ دست راست: {right}
✌️ دست چپ: {left}
💰 جایزه گروه: {group['group_bounty']}
اعضا:\n""" + '\n'.join(f"• {u['name']} (@{u['username'] or '---'})" for u in members)
        bot.reply_to(message, text)

# سایر دستورات مدیریتی (setdamage/setbounty/settitle/upgrade...) را مشابه همین، با db.update_user و ایمنی مناسب پیاده کنید.

if __name__ == '__main__':
    print("🤖 ربات وان پیس آنلاین شد!")
    bot.infinity_polling()
