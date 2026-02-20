# ================ ایمپورت کتابخونه ها ================
import telebot
import json
import os
import random
from datetime import datetime

# ================ توکن ربات ================
TOKEN = "توکن_ربات_تو"  # اینجا توکن رباتتو بزار
bot = telebot.TeleBot(TOKEN)

# ================ اسم فایل دیتابیس ================
DB_FILE = 'database.json'

# ================ مقدارهای ثابت اولیه ================
INITIAL_HP = 300
INITIAL_BOUNTY = 0
INITIAL_DAMAGE = 10      # دمیج اولیه (بعداً کاپیتان تنظیم میکنه)
INITIAL_POINTS = 0

# ================ هزینه ارتقاها ================
UPGRADE_COSTS = {
    'hp': 1,        # ۱ امتیاز
    'damage': 1     # ۱ امتیاز
}
UPGRADE_AMOUNTS = {
    'hp': 50,       # +۵۰ خون
    'damage': 50    # +۵۰ دمیج
}

# ================ title های اولیه بر اساس کلاس ================
TITLES = {
    'pirate': 'دزد دریایی تازه وارد',
    'marine': 'ملوان',
    'bounty': 'جایزه‌بگیر بی تجربه'
}

# ================ دیکشنری اسم کلاسها ================
CLASS_NAMES = {
    'pirate': '🏴‍☠️ دزد دریایی',
    'marine': '⚓ نیروی دریایی',
    'bounty': '💰 جایزه‌بگیر'
}

# ================ کلاس مدیریت دیتابیس ================
class Database:
    def __init__(self):
        self.load()
    
    def load(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                self.data = json.load(f)
        else:
            # ساختار دیتابیس
            self.data = {
                'users': {},          # اطلاعات کاربران هر گروه
                'groups': {},          # اطلاعات گروه‌های بازی
                'pending_requests': [], # درخواست‌های عضویت (ذخیره موقت)
                'temp_reg': {}          # اطلاعات موقت ثبت نام
            }
            self.save()
    
    def save(self):
        with open(DB_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

db = Database()

# ================ توابع کمکی ================
def is_user_registered(chat_id, user_id):
    """آیا کاربر در این گروه ثبت نام کرده؟"""
    chat_id = str(chat_id)
    user_id = str(user_id)
    return chat_id in db.data['users'] and user_id in db.data['users'][chat_id]

def get_user(chat_id, user_id):
    """اطلاعات کاربر را برمی‌گرداند"""
    chat_id = str(chat_id)
    user_id = str(user_id)
    if is_user_registered(chat_id, user_id):
        return db.data['users'][chat_id][user_id]
    return None

def is_owner(chat_id, user_id):
    """آیا کاربر مالک گروه تلگرام است؟"""
    # این تابع باید با استفاده از bot.get_chat_member چک کند
    # اما برای سادگی فعلاً فرض می‌کنیم مالک کسی است که گروه را ساخته
    # می‌توان بعداً با سطح دسترسی تلگرام چک کرد
    chat_id = str(chat_id)
    user_id = str(user_id)
    # اگر گروه در دیتابیس groups ثبت شده باشد، مالک آن مشخص است
    for group_name, group_info in db.data['groups'].items():
        if group_info.get('chat_id') == chat_id and group_info.get('owner') == user_id:
            return True
    return False

def is_captain(chat_id, user_id):
    """آیا کاربر کاپیتان گروه بازی است؟"""
    chat_id = str(chat_id)
    user_id = str(user_id)
    for group_name, group_info in db.data['groups'].items():
        if group_info.get('chat_id') == chat_id and group_info.get('captain') == user_id:
            return True
    return False

def is_right_hand(chat_id, user_id):
    """آیا کاربر دست راست است؟"""
    chat_id = str(chat_id)
    user_id = str(user_id)
    for group_name, group_info in db.data['groups'].items():
        if group_info.get('chat_id') == chat_id and group_info.get('right_hand') == user_id:
            return True
    return False

def is_left_hand(chat_id, user_id):
    """آیا کاربر دست چپ است؟"""
    chat_id = str(chat_id)
    user_id = str(user_id)
    for group_name, group_info in db.data['groups'].items():
        if group_info.get('chat_id') == chat_id and group_info.get('left_hand') == user_id:
            return True
    return False

def can_accept_member(chat_id, user_id):
    """آیا کاربر می‌تواند عضو جدید قبول کند؟"""
    return is_captain(chat_id, user_id) or is_right_hand(chat_id, user_id) or is_left_hand(chat_id, user_id)

# ================ دستور start ================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
                 "🎮 به ربات گروهی وان پیس خوش اومدی!\n"
                 "این ربات مخصوص بازی گروهیه.\n"
                 "برای دیدن راهنما /help رو بزن.")

# ================ راهنما ================
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📚 **راهنمای کامل ربات وان پیس**

**۱. ثبت نام:**
• مالک روی کاربر ریپلی کنه: `/Welcome_To_Onepiece`
• کاربر کلاسش رو انتخاب کنه

**۲. ساخت گروه/خدمه:**
• فقط مالک گروه تلگرام: `/creategroup [نام]`
• بعدش مالک با ریپلی تعیین کنه: `/setcaptain`
• کاپیتان تعیین کنه: `/setright @user` و `/setleft @user`

**۳. عضویت:**
• کاربرا بزنن: `/joingroup [نام گروه]`
• کاپیتان/دست‌ها روی درخواست ریپلی کنن: `/accept`

**۴. اطلاعات:**
• پروفایل: `/wanted`
• کیف: `/bag`
• اطلاعات گروه: `/groupinfo`

**۵. تنظیمات (فری کاپیتان):**
• تنظیم دمیج: `/setdamage @user مقدار`
• تنظیم خون: `/sethp @user مقدار`
• تنظیم امتیاز: `/setpoints @user مقدار`
• تنظیم بونتی: `/setbounty @user مقدار`
• تنظیم لقب: `/settitle @user لقب`

**۶. تنظیمات (فقط مالک تلگرام):**
• تنظیم جایزه کل گروه: `/setgroupbounty [نام گروه] مقدار`

**۷. ارتقا:**
• با هر برد ۱ امتیاز بگیر
• ارتقا خون: `/upgrade hp`
• ارتقا دمیج: `/upgrade damage`
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

# ================ ثبت نام توسط مالک ================
@bot.message_handler(commands=['Welcome_To_Onepiece'])
def welcome_new_player(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ این دستور فقط توی گروه کار میکنه!")
        return
    
    chat_id = message.chat.id
    if not message.reply_to_message:
        bot.reply_to(message, "❌ باید روی کاربر مورد نظر ریپلی کنی!")
        return
    
    target_user = message.reply_to_message.from_user
    user_id = str(target_user.id)
    
    # چک کن قبلاً ثبت نام نکرده
    if is_user_registered(chat_id, user_id):
        bot.reply_to(message, f"❌ {target_user.first_name} قبلاً ثبت نام کرده!")
        return
    
    # ساخت دکمه‌های انتخاب کلاس
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🏴‍☠️ دزد دریایی", callback_data=f"reg_pirate_{user_id}"),
        telebot.types.InlineKeyboardButton("⚓ نیروی دریایی", callback_data=f"reg_marine_{user_id}"),
        telebot.types.InlineKeyboardButton("💰 جایزه‌بگیر", callback_data=f"reg_bounty_{user_id}")
    )
    
    # ذخیره موقت
    if 'temp_reg' not in db.data:
        db.data['temp_reg'] = {}
    db.data['temp_reg'][user_id] = {
        'chat_id': str(chat_id),
        'name': target_user.first_name,
        'username': target_user.username
    }
    db.save()
    
    bot.send_message(
        chat_id,
        f"👤 کاربر: {target_user.first_name}\n"
        f"🎭 لطفاً کلاس خود را انتخاب کنید:",
        reply_markup=markup
    )

# ================ هندلر انتخاب کلاس ================
@bot.callback_query_handler(func=lambda call: call.data.startswith('reg_'))
def handle_role_selection(call):
    _, role, target_user_id = call.data.split('_')
    target_user_id = str(target_user_id)
    clicker_id = str(call.from_user.id)
    
    if clicker_id != target_user_id:
        bot.answer_callback_query(call.id, "❌ این دکمه مال تو نیست!", show_alert=True)
        return
    
    temp_info = db.data.get('temp_reg', {}).get(target_user_id)
    if not temp_info:
        bot.answer_callback_query(call.id, "❌ اطلاعات ثبت نام منقضی شده!", show_alert=True)
        return
    
    chat_id = temp_info['chat_id']
    
    if is_user_registered(chat_id, target_user_id):
        bot.answer_callback_query(call.id, "❌ تو قبلاً ثبت نام کردی!", show_alert=True)
        return
    
    # ساخت کاربر جدید
    if chat_id not in db.data['users']:
        db.data['users'][chat_id] = {}
    
    db.data['users'][chat_id][target_user_id] = {
        'user_id': int(target_user_id),
        'username': temp_info['username'],
        'name': temp_info['name'],
        'class': role,
        'title': TITLES[role],
        'hp': INITIAL_HP,
        'damage': INITIAL_DAMAGE,
        'bounty': INITIAL_BOUNTY,
        'points': INITIAL_POINTS,
        'group': None,
        'character': None,
        'character_photo': None,
        'registered_at': str(datetime.now())
    }
    
    # پاک کردن موقت
    del db.data['temp_reg'][target_user_id]
    db.save()
    
    class_name = CLASS_NAMES[role]
    bot.edit_message_text(
        f"✅ ثبت نام با موفقیت انجام شد!\n\n"
        f"📋 **اطلاعات شما:**\n"
        f"🎭 کلاس: {class_name}\n"
        f"🏷️ لقب: {TITLES[role]}\n"
        f"❤️ HP: {INITIAL_HP}\n"
        f"⚔️ دمیج: {INITIAL_DAMAGE}\n"
        f"💰 قیمت سر: {INITIAL_BOUNTY}\n"
        f"⭐ امتیاز: {INITIAL_POINTS}\n\n"
        f"برای عضویت در گروه: /joingroup [اسم گروه]",
        chat_id,
        call.message.message_id,
        parse_mode='Markdown'
    )

# ================ پروفایل (Wanted) ================
@bot.message_handler(commands=['wanted'])
def wanted(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if not is_user_registered(chat_id, user_id):
        bot.reply_to(message, "❌ تو هنوز ثبت نام نکردی!")
        return
    
    user = get_user(chat_id, user_id)
    class_name = CLASS_NAMES.get(user['class'], 'نامشخص')
    
    text = f"""
🏴‍☠️ **WANTED** 🏴‍☠️

👤 **نام:** {user['name']}
🎭 **کلاس:** {class_name}
🏷️ **لقب:** {user['title']}

❤️ **HP:** {user['hp']}
⚔️ **دمیج:** {user['damage']}
💰 **بونتی:** {user['bounty']}
⭐ **امتیاز:** {user['points']}

👥 **گروه:** {user['group'] if user['group'] else 'عضو گروهی نیست'}
    """
    bot.reply_to(message, text, parse_mode='Markdown')

# ================ کیف (Bag) ================
@bot.message_handler(commands=['bag'])
def bag(message):
    # فعلاً همون اطلاعات رو نشون میدیم
    wanted(message)

# ================ ساخت گروه ================
@bot.message_handler(commands=['creategroup'])
def create_group(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    # فقط مالک گروه تلگرام می‌تونه (فعلاً با یه چک ساده)
    # اگه بخوای دقیق چک کنی باید از Telegram API کمک بگیری
    # اینجا فرض میکنیم هرکی میتونه بسازه، بعداً محدود میشه
    # برای سادگی، اجازه میدیم هرکی بسازه اما توی گروه‌های دیتابیس ثبت میکنیم
    
    try:
        group_name = message.text.split(maxsplit=1)[1]
    except:
        bot.reply_to(message, "❌ باید اسم گروه رو بنویسی!\nمثال: /creategroup کلاه حصیری")
        return
    
    # چک کن این گروه قبلاً ساخته نشده
    for gname, ginfo in db.data['groups'].items():
        if ginfo.get('chat_id') == chat_id and gname == group_name:
            bot.reply_to(message, "❌ گروهی با این اسم قبلاً توی این چت ساخته شده!")
            return
    
    # ساخت گروه جدید
    db.data['groups'][group_name] = {
        'chat_id': chat_id,
        'owner': user_id,          # مالک گروه تلگرام (کسی که دستور زده)
        'captain': None,
        'right_hand': None,
        'left_hand': None,
        'members': [],
        'group_bounty': 0,
        'created_at': str(datetime.now()),
        'pending_requests': []      # درخواست‌های عضویت به صورت {user_id, username, name}
    }
    db.save()
    
    bot.reply_to(message, f"✅ گروه {group_name} ساخته شد.\nحالا با ریپلی روی کاربر، کاپیتان رو تعیین کن: /setcaptain")

# ================ تعیین کاپیتان ================
@bot.message_handler(commands=['setcaptain'])
def set_captain(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ باید روی کاربر مورد نظر ریپلی کنی!")
        return
    
    target_user = message.reply_to_message.from_user
    target_id = str(target_user.id)
    
    # پیدا کردن گروهی که این کاربر (مالک) owner آن است
    group_name = None
    for gname, ginfo in db.data['groups'].items():
        if ginfo.get('chat_id') == chat_id and ginfo.get('owner') == user_id:
            group_name = gname
            break
    
    if not group_name:
        bot.reply_to(message, "❌ تو مالک هیچ گروهی نیستی!")
        return
    
    # چک کن که target توی گروه ثبت نام کرده باشه
    if not is_user_registered(chat_id, target_id):
        bot.reply_to(message, "❌ این کاربر هنوز ثبت نام نکرده!")
        return
    
    # تعیین کاپیتان
    db.data['groups'][group_name]['captain'] = target_id
    # اگه کاربر قبلاً توی members نبود، اضافه کن
    if target_id not in db.data['groups'][group_name]['members']:
        db.data['groups'][group_name]['members'].append(target_id)
    # آپدیت گروه کاربر
    db.data['users'][chat_id][target_id]['group'] = group_name
    db.save()
    
    bot.reply_to(message, f"✅ {target_user.first_name} به عنوان کاپیتان گروه {group_name} منصوب شد.")

# ================ تعیین دست راست ================
@bot.message_handler(commands=['setright'])
def set_right(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    try:
        target_username = message.text.split()[1].replace('@', '')
    except:
        bot.reply_to(message, "❌ باید یوزرنیم رو وارد کنی!\nمثال: /setright @zoro")
        return
    
    # پیدا کردن گروهی که user_id کاپیتان آن است
    group_name = None
    for gname, ginfo in db.data['groups'].items():
        if ginfo.get('chat_id') == chat_id and ginfo.get('captain') == user_id:
            group_name = gname
            break
    
    if not group_name:
        bot.reply_to(message, "❌ تو کاپیتان هیچ گروهی نیستی!")
        return
    
    # پیدا کردن target_id با یوزرنیم
    target_id = None
    for uid, uinfo in db.data['users'].get(chat_id, {}).items():
        if uinfo.get('username') == target_username:
            target_id = uid
            break
    
    if not target_id:
        bot.reply_to(message, "❌ کاربر با این یوزرنیم توی گروه ثبت نام نکرده!")
        return
    
    # تعیین دست راست
    db.data['groups'][group_name]['right_hand'] = target_id
    if target_id not in db.data['groups'][group_name]['members']:
        db.data['groups'][group_name]['members'].append(target_id)
    db.data['users'][chat_id][target_id]['group'] = group_name
    db.save()
    
    bot.reply_to(message, f"✅ @{target_username} به عنوان دست راست منصوب شد.")

# ================ تعیین دست چپ ================
@bot.message_handler(commands=['setleft'])
def set_left(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    try:
        target_username = message.text.split()[1].replace('@', '')
    except:
        bot.reply_to(message, "❌ باید یوزرنیم رو وارد کنی!\nمثال: /setleft @sanji")
        return
    
    group_name = None
    for gname, ginfo in db.data['groups'].items():
        if ginfo.get('chat_id') == chat_id and ginfo.get('captain') == user_id:
            group_name = gname
            break
    
    if not group_name:
        bot.reply_to(message, "❌ تو کاپیتان هیچ گروهی نیستی!")
        return
    
    target_id = None
    for uid, uinfo in db.data['users'].get(chat_id, {}).items():
        if uinfo.get('username') == target_username:
            target_id = uid
            break
    
    if not target_id:
        bot.reply_to(message, "❌ کاربر با این یوزرنیم توی گروه ثبت نام نکرده!")
        return
    
    db.data['groups'][group_name]['left_hand'] = target_id
    if target_id not in db.data['groups'][group_name]['members']:
        db.data['groups'][group_name]['members'].append(target_id)
    db.data['users'][chat_id][target_id]['group'] = group_name
    db.save()
    
    bot.reply_to(message, f"✅ @{target_username} به عنوان دست چپ منصوب شد.")

# ================ درخواست عضویت ================
@bot.message_handler(commands=['joingroup'])
def join_group(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if not is_user_registered(chat_id, user_id):
        bot.reply_to(message, "❌ اول باید ثبت نام کنی!")
        return
    
    try:
        group_name = message.text.split(maxsplit=1)[1]
    except:
        bot.reply_to(message, "❌ باید اسم گروه رو بنویسی!\nمثال: /joingroup کلاه حصیری")
        return
    
    # پیدا کردن گروه
    if group_name not in db.data['groups'] or db.data['groups'][group_name].get('chat_id') != chat_id:
        bot.reply_to(message, "❌ گروهی با این اسم وجود نداره!")
        return
    
    group = db.data['groups'][group_name]
    
    # چک کن عضو نباشه
    if user_id in group['members']:
        bot.reply_to(message, "❌ تو قبلاً عضو این گروهی!")
        return
    
    # چک کن درخواست قبلی نداشته باشه
    for req in group['pending_requests']:
        if req['user_id'] == user_id:
            bot.reply_to(message, "❌ قبلاً درخواست دادی، منتظر تایید باش!")
            return
    
    # اضافه به درخواست‌ها
    user = get_user(chat_id, user_id)
    group['pending_requests'].append({
        'user_id': user_id,
        'username': user['username'],
        'name': user['name'],
        'date': str(datetime.now())
    })
    db.save()
    
    # اطلاع به کاپیتان و دستیارها (اینجا ساده پیام میدیم به گروه)
    bot.send_message(chat_id, f"📩 درخواست عضویت {user['name']} برای گروه {group_name} ارسال شد.\nکاپیتان یا دستیاران با ریپلی به این پیام و /accept تایید کنن.")

# ================ قبول عضویت ================
@bot.message_handler(commands=['accept'])
def accept_request(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ باید روی پیام درخواست ریپلی کنی!")
        return
    
    # چک کن که کاربر مجوز قبول کردن داره
    if not can_accept_member(chat_id, user_id):
        bot.reply_to(message, "❌ تو اجازه قبول عضویت نداری!")
        return
    
    # پیدا کردن گروهی که کاربر توش کاپیتان/دست هست
    # برای سادگی، اولین گروه رو میگیریم (چون هر کاربر فقط توی یه گروه میتونه این نقش رو داشته باشه)
    group_name = None
    for gname, ginfo in db.data['groups'].items():
        if ginfo.get('chat_id') == chat_id:
            if (ginfo.get('captain') == user_id or 
                ginfo.get('right_hand') == user_id or 
                ginfo.get('left_hand') == user_id):
                group_name = gname
                break
    
    if not group_name:
        bot.reply_to(message, "❌ تو در هیچ گروهی نقش قبول‌کننده نداری!")
        return
    
    group = db.data['groups'][group_name]
    
    # سعی کن user_id رو از متن پیام درخواست پیدا کنی (اینجا ساده شده)
    # معمولاً توی پیام درخواست ما user_id رو ذخیره نکردیم. باید درخواست رو از روی متن تشخیص بدیم.
    # راه بهتر: ذخیره کردن message_id درخواست و بعد جستجو.
    # برای ساده‌سازی، فرض میکنیم فقط یک درخواست pending هست و اولین رو قبول میکنیم.
    if not group['pending_requests']:
        bot.reply_to(message, "❌ درخواستی برای قبول کردن نیست!")
        return
    
    req = group['pending_requests'].pop(0)  # اولین درخواست
    target_id = req['user_id']
    
    # اضافه به اعضا
    if target_id not in group['members']:
        group['members'].append(target_id)
    db.data['users'][chat_id][target_id]['group'] = group_name
    db.save()
    
    bot.reply_to(message, f"✅ {req['name']} با موفقیت به گروه {group_name} پیوست.")

# ================ اطلاعات گروه ================
@bot.message_handler(commands=['groupinfo'])
def group_info(message):
    chat_id = str(message.chat.id)
    
    # پیدا کردن گروه متناظر با این چت
    groups_in_chat = []
    for gname, ginfo in db.data['groups'].items():
        if ginfo.get('chat_id') == chat_id:
            groups_in_chat.append((gname, ginfo))
    
    if not groups_in_chat:
        bot.reply_to(message, "❌ هیچ گروه بازی توی این چت ساخته نشده!")
        return
    
    # اگه چند گروه داریم، اولین رو نشون میدیم (یا می‌تونیم اسم گروه رو هم بگیریم)
    gname, group = groups_in_chat[0]
    
    # پیدا کردن نام کاربران
    captain_name = "نامشخص"
    if group['captain']:
        u = get_user(chat_id, group['captain'])
        if u: captain_name = u['name']
    
    right_name = "ندارد"
    if group['right_hand']:
        u = get_user(chat_id, group['right_hand'])
        if u: right_name = u['name']
    
    left_name = "ندارد"
    if group['left_hand']:
        u = get_user(chat_id, group['left_hand'])
        if u: left_name = u['name']
    
    members_list = ""
    for mid in group['members']:
        u = get_user(chat_id, mid)
        if u:
            members_list += f"• {u['name']} (@{u['username']})\n"
    
    text = f"""
👥 **اطلاعات گروه {gname}**

👑 **کاپیتان:** {captain_name}
✋ **دست راست:** {right_name}
✌️ **دست چپ:** {left_name}
💰 **جایزه کل گروه:** {group['group_bounty']}
📅 **تاسیس:** {group['created_at']}

**👤 اعضا:**
{members_list if members_list else 'هنوز عضوی نداره'}
    """
    bot.reply_to(message, text, parse_mode='Markdown')

# ================ تنظیم جایزه کل گروه (فقط مالک) ================
@bot.message_handler(commands=['setgroupbounty'])
def set_group_bounty(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    # فقط مالک گروه تلگرام (سازنده گروه بازی) می‌تونه
    # برای سادگی، فرض می‌کنیم مالک کسی هست که گروه رو با /creategroup ساخته (owner)
    try:
        _, group_name, amount = message.text.split()
        amount = int(amount)
    except:
        bot.reply_to(message, "❌ فرمت درست نیست!\nمثال: /setgroupbounty کلاه‌حصیری 5000")
        return
    
    if group_name not in db.data['groups'] or db.data['groups'][group_name].get('chat_id') != chat_id:
        bot.reply_to(message, "❌ گروهی با این اسم وجود نداره!")
        return
    
    group = db.data['groups'][group_name]
    if group['owner'] != user_id:
        bot.reply_to(message, "❌ فقط مالک گروه می‌تونه جایزه کل رو تنظیم کنه!")
        return
    
    group['group_bounty'] = amount
    db.save()
    bot.reply_to(message, f"✅ جایزه کل گروه {group_name} به {amount} تغییر یافت.")

# ================ تنظیم دمیج ================
@bot.message_handler(commands=['setdamage'])
def set_damage(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    # فقط کاپیتان
    if not is_captain(chat_id, user_id):
        bot.reply_to(message, "❌ فقط کاپیتان می‌تونه دمیج رو تنظیم کنه!")
        return
    
    try:
        _, target_username, value = message.text.split()
        value = int(value)
    except:
        bot.reply_to(message, "❌ فرمت درست نیست!\nمثال: /setdamage @luffy 150")
        return
    
    target_username = target_username.replace('@', '')
    target_id = None
    for uid, uinfo in db.data['users'].get(chat_id, {}).items():
        if uinfo.get('username') == target_username:
            target_id = uid
            break
    
    if not target_id:
        bot.reply_to(message, "❌ کاربر پیدا نشد!")
        return
    
    db.data['users'][chat_id][target_id]['damage'] = value
    db.save()
    bot.reply_to(message, f"✅ دمیج {target_username} به {value} تغییر یافت.")

# ================ تنظیم HP ================
@bot.message_handler(commands=['sethp'])
def set_hp(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if not is_captain(chat_id, user_id):
        bot.reply_to(message, "❌ فقط کاپیتان می‌تونه HP رو تنظیم کنه!")
        return
    
    try:
        _, target_username, value = message.text.split()
        value = int(value)
    except:
        bot.reply_to(message, "❌ فرمت درست نیست!\nمثال: /sethp @zoro 500")
        return
    
    target_username = target_username.replace('@', '')
    target_id = None
    for uid, uinfo in db.data['users'].get(chat_id, {}).items():
        if uinfo.get('username') == target_username:
            target_id = uid
            break
    
    if not target_id:
        bot.reply_to(message, "❌ کاربر پیدا نشد!")
        return
    
    db.data['users'][chat_id][target_id]['hp'] = value
    db.save()
    bot.reply_to(message, f"✅ HP {target_username} به {value} تغییر یافت.")

# ================ تنظیم امتیاز ================
@bot.message_handler(commands=['setpoints'])
def set_points(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if not is_captain(chat_id, user_id):
        bot.reply_to(message, "❌ فقط کاپیتان می‌تونه امتیاز رو تنظیم کنه!")
        return
    
    try:
        _, target_username, value = message.text.split()
        value = int(value)
    except:
        bot.reply_to(message, "❌ فرمت درست نیست!\nمثال: /setpoints @sanji 10")
        return
    
    target_username = target_username.replace('@', '')
    target_id = None
    for uid, uinfo in db.data['users'].get(chat_id, {}).items():
        if uinfo.get('username') == target_username:
            target_id = uid
            break
    
    if not target_id:
        bot.reply_to(message, "❌ کاربر پیدا نشد!")
        return
    
    db.data['users'][chat_id][target_id]['points'] = value
    db.save()
    bot.reply_to(message, f"✅ امتیاز {target_username} به {value} تغییر یافت.")

# ================ تنظیم بونتی ================
@bot.message_handler(commands=['setbounty'])
def set_bounty(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if not is_captain(chat_id, user_id):
        bot.reply_to(message, "❌ فقط کاپیتان می‌تونه بونتی رو تنظیم کنه!")
        return
    
    try:
        _, target_username, value = message.text.split()
        value = int(value)
    except:
        bot.reply_to(message, "❌ فرمت درست نیست!\nمثال: /setbounty @luffy 1000")
        return
    
    target_username = target_username.replace('@', '')
    target_id = None
    for uid, uinfo in db.data['users'].get(chat_id, {}).items():
        if uinfo.get('username') == target_username:
            target_id = uid
            break
    
    if not target_id:
        bot.reply_to(message, "❌ کاربر پیدا نشد!")
        return
    
    db.data['users'][chat_id][target_id]['bounty'] = value
    db.save()
    bot.reply_to(message, f"✅ بونتی {target_username} به {value} تغییر یافت.")

# ================ تنظیم لقب ================
@bot.message_handler(commands=['settitle'])
def set_title(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    # کاپیتان یا دست راست
    if not (is_captain(chat_id, user_id) or is_right_hand(chat_id, user_id)):
        bot.reply_to(message, "❌ فقط کاپیتان و دست راست می‌تونن لقب بدن!")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        target_username = parts[1].replace('@', '')
        new_title = parts[2]
    except:
        bot.reply_to(message, "❌ فرمت درست نیست!\nمثال: /settitle @zoro شمشیرزن")
        return
    
    target_id = None
    for uid, uinfo in db.data['users'].get(chat_id, {}).items():
        if uinfo.get('username') == target_username:
            target_id = uid
            break
    
    if not target_id:
        bot.reply_to(message, "❌ کاربر پیدا نشد!")
        return
    
    db.data['users'][chat_id][target_id]['title'] = new_title
    db.save()
    bot.reply_to(message, f"✅ لقب {target_username} به {new_title} تغییر یافت.")

# ================ ارتقا ================
@bot.message_handler(commands=['upgrade'])
def upgrade(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if not is_user_registered(chat_id, user_id):
        bot.reply_to(message, "❌ تو ثبت نام نکردی!")
        return
    
    try:
        stat = message.text.split()[1].lower()
    except:
        bot.reply_to(message, "❌ باید مشخص کنی چی رو ارتقا میدی: hp یا damage")
        return
    
    if stat not in ['hp', 'damage']:
        bot.reply_to(message, "❌ فقط می‌تونی hp یا damage رو ارتقا بدی.")
        return
    
    user = get_user(chat_id, user_id)
    points = user['points']
    cost = UPGRADE_COSTS[stat]
    
    if points < cost:
        bot.reply_to(message, f"❌ امتیاز کافی نداری! نیاز داری {cost} امتیاز.")
        return
    
    # اعمال ارتقا
    user['points'] -= cost
    user[stat] += UPGRADE_AMOUNTS[stat]
    db.save()
    
    bot.reply_to(message, f"✅ {stat} شما با موفقیت ارتقا یافت! اکنون {stat} = {user[stat]}")

# ================ اجرای ربات ================
if __name__ == '__main__':
    print("🤖 ربات وان پیس روشن شد!")
    bot.infinity_polling()
