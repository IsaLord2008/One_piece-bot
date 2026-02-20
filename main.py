import os
import telebot
import sqlite3
import random
from datetime import datetime
from dotenv import load_dotenv

# ----------------------------
# تنظیم توکن ربات (تلگرام)
# ----------------------------
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    import sys
    print("⚠️ توکن ربات تعریف نشده! فایل .env را بررسی کن.")
    sys.exit(1)
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ----------------------------
# ثابت‌های بازی
# ----------------------------
INITIAL_HP = 300
INITIAL_BOUNTY = 0
INITIAL_DAMAGE = 10
INITIAL_POINTS = 0

UPGRADE_COSTS = {'hp': 1, 'damage': 1}
UPGRADE_AMOUNTS = {'hp': 50, 'damage': 50}

TITLES = {
    'pirate': 'دزد دریایی تازه وارد',
    'marine': 'ملوان',
    'bounty': 'جایزه‌بگیر بی‌تجربه'
}
CLASS_NAMES = {
    'pirate': '🏴‍☠️ دزد دریایی',
    'marine': '⚓ نیروی دریایی',
    'bounty': '💰 جایزه‌بگیر'
}

# ----------------------------
# دیتابیس
# ----------------------------
class Database:
    def __init__(self, path='onepiece.db'):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS users (
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
                PRIMARY KEY (chat_id, user_id))''')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS groups (
                name TEXT,
                chat_id TEXT,
                owner TEXT,
                captain TEXT,
                right_hand TEXT,
                left_hand TEXT,
                group_bounty INTEGER,
                created_at TEXT,
                PRIMARY KEY (chat_id, name))''')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS requests (
                chat_id TEXT,
                group_name TEXT,
                user_id TEXT,
                username TEXT,
                name TEXT,
                message_id INTEGER,
                date TEXT
            )''')

    # ------------------------
    # کاربران
    # ------------------------
    def is_user_registered(self, chat_id, user_id):
        return self.conn.execute(
            'SELECT 1 FROM users WHERE chat_id=? AND user_id=?',
            (chat_id, user_id)
        ).fetchone() is not None

    def add_user(self, chat_id, user_id, name, username, class_, title, hp, damage, bounty, points, registered_at):
        with self.conn:
            self.conn.execute(
                'INSERT INTO users (chat_id, user_id, name, username, class, title, hp, damage, bounty, points, group_name, registered_at) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)',
                (chat_id, user_id, name, username, class_, title, hp, damage, bounty, points, registered_at)
            )

    def get_user(self, chat_id, user_id):
        return self.conn.execute(
            'SELECT * FROM users WHERE chat_id=? AND user_id=?',
            (chat_id, user_id)
        ).fetchone()

    def update_user_field(self, chat_id, user_id, field, value):
        """Only allow updating whitelisted fields!"""
        if field not in {'group_name', 'hp', 'damage', 'bounty', 'points', 'title'}:
            raise Exception('field not allowed')
        with self.conn:
            self.conn.execute(
                f'UPDATE users SET {field}=? WHERE chat_id=? AND user_id=?',
                (value, chat_id, user_id)
            )

    def set_user_group(self, chat_id, user_id, group_name):
        self.update_user_field(chat_id, user_id, 'group_name', group_name)

    # ------------------------
    # گروه‌ها
    # ------------------------
    def create_group(self, group_name, chat_id, owner_id):
        with self.conn:
            self.conn.execute(
                'INSERT INTO groups (name, chat_id, owner, captain, right_hand, left_hand, group_bounty, created_at) '
                'VALUES (?, ?, ?, NULL, NULL, NULL, 0, ?)',
                (group_name, chat_id, owner_id, str(datetime.now()))
            )

    def get_group(self, group_name, chat_id):
        return self.conn.execute(
            'SELECT * FROM groups WHERE name=? AND chat_id=?',
            (group_name, chat_id)
        ).fetchone()

    def get_group_by_role(self, chat_id, user_id, role):
        """role: 'owner', 'captain', 'right_hand', 'left_hand'"""
        q = f'SELECT * FROM groups WHERE chat_id=? AND {role}=?'
        return self.conn.execute(q, (chat_id, user_id)).fetchone()

    def set_group_role(self, group_name, chat_id, role, user_id):
        if role not in {'captain', 'right_hand', 'left_hand'}: raise Exception('role not allowed')
        with self.conn:
            self.conn.execute(
                f'UPDATE groups SET {role}=? WHERE name=? AND chat_id=?',
                (user_id, group_name, chat_id)
            )

    def update_group_bounty(self, group_name, chat_id, value):
        with self.conn:
            self.conn.execute(
                'UPDATE groups SET group_bounty=? WHERE name=? AND chat_id=?',
                (value, group_name, chat_id)
            )

    def get_groups_by_chat(self, chat_id):
        return self.conn.execute(
            'SELECT * FROM groups WHERE chat_id=?', (chat_id,)
        ).fetchall()

    # ------------------------
    # درخواست‌های عضویت
    # ------------------------
    def add_request(self, chat_id, group_name, user_id, username, name, message_id):
        with self.conn:
            self.conn.execute(
                'INSERT INTO requests (chat_id, group_name, user_id, username, name, message_id, date) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (chat_id, group_name, user_id, username, name, message_id, str(datetime.now()))
            )

    def get_pending_request(self, chat_id, group_name, message_id):
        return self.conn.execute(
            'SELECT * FROM requests WHERE chat_id=? AND group_name=? AND message_id=?',
            (chat_id, group_name, message_id)
        ).fetchone()

    def remove_request(self, chat_id, group_name, message_id):
        with self.conn:
            self.conn.execute(
                'DELETE FROM requests WHERE chat_id=? AND group_name=? AND message_id=?',
                (chat_id, group_name, message_id)
            )

    def has_pending_request(self, chat_id, group_name, user_id):
        return self.conn.execute(
            'SELECT 1 FROM requests WHERE chat_id=? AND group_name=? AND user_id=?',
            (chat_id, group_name, user_id)
        ).fetchone() is not None

    # ------------------------
    # اعضای گروه
    # ------------------------
    def add_member(self, chat_id, group_name, user_id):
        self.set_user_group(chat_id, user_id, group_name)

    def get_group_members(self, chat_id, group_name):
        return self.conn.execute(
            'SELECT * FROM users WHERE chat_id=? AND group_name=?',
            (chat_id, group_name)
        ).fetchall()

db = Database()

# ----------------------------
# تایید نقش/سطح دسترسی
# ----------------------------
def is_captain(chat_id, user_id):
    return db.get_group_by_role(chat_id, user_id, 'captain') is not None

def is_right_hand(chat_id, user_id):
    return db.get_group_by_role(chat_id, user_id, 'right_hand') is not None

def is_left_hand(chat_id, user_id):
    return db.get_group_by_role(chat_id, user_id, 'left_hand') is not None

def can_accept_member(chat_id, user_id):
    return is_captain(chat_id, user_id) or is_right_hand(chat_id, user_id) or is_left_hand(chat_id, user_id)

# ----------------------------
# دستورات بات
# ----------------------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.reply_to(
        m,
        "🎮 خوش آمدی به ربات وان‌پیس!\n"
        "کمک: /help"
    )

@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.reply_to(
        m,
        "📖 <b>راهنمای دستورات:</b>\n"
        "۱. ثبت‌نام (مالک روی کاربر ریپلای): /Welcome_To_Onepiece\n"
        "۲. ساخت گروه: /creategroup نام_گروه\n"
        "۳. عضویت: /joingroup نام_گروه\n"
        "۴. پروفایل: /wanted\n"
        "۵. مشاهده گروه: /groupinfo\n"
        "۶. تعیین نقش: /setcaptain، /setright، /setleft (با ریپلای)\n"
        "۷. پذیرش عضو: /accept (روی درخواست ریپلای)\n"
    )

@bot.message_handler(commands=['Welcome_To_Onepiece'])
def cmd_register(m):
    if m.chat.type == 'private' or not m.reply_to_message:
        bot.reply_to(m, "فقط در گروه و روی ریپلای!")
        return
    target = m.reply_to_message.from_user
    chat_id = str(m.chat.id)
    user_id = str(target.id)
    if db.is_user_registered(chat_id, user_id):
        bot.reply_to(m, f"{target.first_name} قبلاً ثبت‌نام کرده.")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    for k, v in CLASS_NAMES.items():
        markup.add(telebot.types.InlineKeyboardButton(v, callback_data=f"reg_{k}_{user_id}_{chat_id}"))
    bot.send_message(chat_id, f"👤 {target.first_name}\nکلاس را انتخاب کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reg_'))
def handle_class_choice(call):
    _, role, reg_user_id, chat_id = call.data.split('_')
    user_id = str(call.from_user.id)
    if user_id != reg_user_id:
        bot.answer_callback_query(call.id, "کاربر هدف نیستی!", show_alert=True)
        return
    if db.is_user_registered(chat_id, user_id):
        bot.answer_callback_query(call.id, "قبلاً ثبت‌نام کردی!", show_alert=True)
        return
    db.add_user(chat_id, user_id,
        call.from_user.first_name, call.from_user.username, role, TITLES[role],
        INITIAL_HP, INITIAL_DAMAGE, INITIAL_BOUNTY, INITIAL_POINTS, str(datetime.now())
    )
    bot.edit_message_text(
        f"✅ ثبت‌نام با موفقیت انجام شد!\n"
        f"کلاس: {CLASS_NAMES[role]}\n"
        f"لقب: {TITLES[role]}\n"
        f"برای عضویت به گروه: /joingroup نام_گروه",
        chat_id, call.message.message_id
    )

@bot.message_handler(commands=['wanted', 'bag'])
def cmd_wanted(m):
    chat_id = str(m.chat.id)
    user_id = str(m.from_user.id)
    user = db.get_user(chat_id, user_id)
    if not user:
        bot.reply_to(m, "اول باید ثبت‌نام کنی!")
        return
    text = f"""🏴‍☠️ <b>WANTED</b>
👤 <b>نام:</b> {user['name']}
🎭 <b>کلاس:</b> {CLASS_NAMES.get(user['class'], 'نامشخص')}
🏷️ <b>لقب:</b> {user['title']}
❤️ <b>HP:</b> {user['hp']}
⚔️ <b>دمیج:</b> {user['damage']}
💰 <b>بونتی:</b> {user['bounty']}
⭐ <b>امتیاز:</b> {user['points']}
👥 <b>گروه:</b> {user['group_name'] or 'عضو هیچ گروهی نیست'}"""
    bot.reply_to(m, text)

@bot.message_handler(commands=['creategroup'])
def cmd_creategroup(m):
    chat_id = str(m.chat.id)
    owner_id = str(m.from_user.id)
    parts = m.text.split(maxsplit=1)
    if len(parts) != 2:
        bot.reply_to(m, "استفاده: /creategroup نام_گروه")
        return
    group_name = parts[1].strip()
    if db.get_group(group_name, chat_id):
        bot.reply_to(m, "این گروه قبلاً ساخته شده.")
        return
    db.create_group(group_name, chat_id, owner_id)
    bot.reply_to(m, f"✅ گروه {group_name} با موفقیت ساخته شد! برای تعیین کاپیتان ریپلای بزن: /setcaptain")

@bot.message_handler(commands=['setcaptain', 'setright', 'setleft'])
def cmd_setrole(m):
    if not m.reply_to_message:
        bot.reply_to(m, "باید روی کاربر مورد نظر ریپلای کنی!")
        return
    cmd = m.text.split()[0][1:]  # setcaptain
    chat_id = str(m.chat.id)
    owner_id = str(m.from_user.id)
    target = m.reply_to_message.from_user
    group = None
    # فقط owner می‌تواند کاپیتان تعریف کند و فقط کاپیتان می‌تواند دست‌ها را انتخاب کند
    if cmd == "setcaptain":
        group = db.get_group_by_role(chat_id, owner_id, 'owner')
        role_db = "captain"
    elif cmd == "setright":
        group = db.get_group_by_role(chat_id, owner_id, 'captain')
        role_db = "right_hand"
    elif cmd == "setleft":
        group = db.get_group_by_role(chat_id, owner_id, 'captain')
        role_db = "left_hand"
    if not group:
        bot.reply_to(m, "دسترسی لازم نداری!")
        return
    if not db.is_user_registered(chat_id, str(target.id)):
        bot.reply_to(m, "کاربر عضو ثبت‌نام نشده.")
        return
    db.set_group_role(group['name'], chat_id, role_db, str(target.id))
    db.add_member(chat_id, group['name'], str(target.id))
    bot.reply_to(m, f"{target.first_name} به عنوان {role_db.replace('_', ' ')} انتخاب شد.")

@bot.message_handler(commands=['joingroup'])
def cmd_joingroup(m):
    chat_id = str(m.chat.id)
    user_id = str(m.from_user.id)
    if not db.is_user_registered(chat_id, user_id):
        bot.reply_to(m, "باید ابتدا ثبت‌نام کنی.")
        return
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(m, "استفاده: /joingroup نام_گروه")
        return
    group_name = parts[1].strip()
    if not db.get_group(group_name, chat_id):
        bot.reply_to(m, "این گروه ثبت نشده.")
        return
    if db.has_pending_request(chat_id, group_name, user_id):
        bot.reply_to(m, "درخواست شما در حال بررسی است.")
        return
    db.add_request(chat_id, group_name, user_id, m.from_user.username, m.from_user.first_name, m.message_id)
    bot.reply_to(m, "درخواست عضویت شما ثبت شد! برای پذیرش، مسئول گروه ریپلای بزند: /accept")

@bot.message_handler(commands=['accept'])
def cmd_accept(m):
    if not m.reply_to_message:
        bot.reply_to(m, "باید روی پیام درخواست عضویت ریپلای بزنی!")
        return
    chat_id = str(m.chat.id)
    user_id = str(m.from_user.id)
    if not can_accept_member(chat_id, user_id):
        bot.reply_to(m, "شما اجازه پذیرش عضو را ندارید.")
        return
    for group in db.get_groups_by_chat(chat_id):
        req = db.get_pending_request(chat_id, group['name'], m.reply_to_message.message_id)
        if req:
            db.add_member(chat_id, group['name'], req['user_id'])
            db.remove_request(chat_id, group['name'], m.reply_to_message.message_id)
            bot.reply_to(m, f"{req['name']} به گروه <b>{group['name']}</b> اضافه شد.")
            return
    bot.reply_to(m, "درخواست معتبر پیدا نشد.")

@bot.message_handler(commands=['groupinfo'])
def cmd_groupinfo(m):
    chat_id = str(m.chat.id)
    groups = db.get_groups_by_chat(chat_id)
    if not groups:
        bot.reply_to(m, "هنوز گروهی ساخته نشده.")
        return
    for group in groups:
        members = db.get_group_members(chat_id, group['name'])
        cap = db.get_user(chat_id, group['captain'])['name'] if group['captain'] else "نامشخص"
        right = db.get_user(chat_id, group['right_hand'])['name'] if group['right_hand'] else "ندارد"
        left = db.get_user(chat_id, group['left_hand'])['name'] if group['left_hand'] else "ندارد"
        members_text = '\n'.join(
            f"{'👑 ' if user['user_id']==group['captain'] else '•'} <b>{user['name']}</b>{f' (@{user['username']})' if user['username'] else ''}"
            for user in members
        ) or 'عضو ندارد.'
        msg = (
            f"<b>👥 گروه {group['name']}</b>\n"
            f"👑 کاپیتان: {cap}\n"
            f"✋ دست راست: {right}\n"
            f"✌️ دست چپ: {left}\n"
            f"💰 جایزه: {group['group_bounty']}\n"
            f"اعضا:\n{members_text}"
        )
        bot.reply_to(m, msg)

if __name__ == '__main__':
    print("🤖 ربات OnePiece آماده است!")
    while True:
        try:
            bot.infinity_polling()
        except Exception as ex:
            print("❗ خطا در polling:", ex) 
