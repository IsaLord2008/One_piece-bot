import telebot

# توکن رباتتو اینجا بذار
TOKEN = "8595594257:AAH73j8rqkvxCXdfr-HviOLphDU41f5Wqbk"
bot = telebot.TeleBot(TOKEN)

# اطلاعات بازیکن‌ها داخل حافظه
players = {}  # {user_id: {"name": str, "hp": int, "moves": {move: count}}}

# تنظیمات حرکات
moves_info = {
    "اتک_قوی": {"max": 1, "damage": 50},
    "اتک_معمولی": {"max": float("inf"), "damage": 15},
    "ایتوریو": {"max": 2, "damage": 30},
    "دفاع": {"max": 8, "damage": 0},       # فقط کاهش دمج
    "جاخالی": {"max": 5, "damage": 0},
    "ضدحمله": {"max": 1, "damage": 40}
}

# ثبت بازیکن
@bot.message_handler(commands=["join"])
def join_game(msg):
    user_id = msg.from_user.id
    if user_id not in players:
        players[user_id] = {"name": msg.from_user.first_name, "hp": 100, "moves": {k:0 for k in moves_info}}
        bot.reply_to(msg, f"{msg.from_user.first_name} وارد بازی شد! HP: 100")
    else:
        bot.reply_to(msg, "شما قبلا ثبت نام شده‌اید!")

# نمایش وضعیت بازیکن
@bot.message_handler(commands=["bag"])
def show_bag(msg):
    user_id = msg.from_user.id
    if user_id in players:
        p = players[user_id]
        status = f"🏴‍☠️ {p['name']}\nHP: {p['hp']}\nحرکات استفاده شده:"
        for m, c in p["moves"].items():
            status += f"\n- {m}: {c}/{moves_info[m]['max'] if moves_info[m]['max']!=float('inf') else '∞'}"
        bot.reply_to(msg, status)
    else:
        bot.reply_to(msg, "ابتدا با /join وارد بازی شوید.")

# اجرای حرکت
@bot.message_handler(commands=["move"])
def play_move(msg):
    try:
        args = msg.text.split()
        if len(args) < 2:
            bot.reply_to(msg, "مثال: /move ایتوریو")
            return
        move_name = args[1]
        user_id = msg.from_user.id
        if user_id not in players:
            bot.reply_to(msg, "ابتدا با /join وارد بازی شوید.")
            return
        if move_name not in moves_info:
            bot.reply_to(msg, "حرکت نامعتبر است!")
            return
        player = players[user_id]
        # چک سقف استفاده
        if player["moves"][move_name] >= moves_info[move_name]["max"]:
            bot.reply_to(msg, f"❌ حرکت {move_name} دیگر قابل استفاده نیست!")
            return
        # اجرا
        player["moves"][move_name] += 1
        dmg = moves_info[move_name]["damage"]
        player["hp"] -= dmg  # فعلاً فقط خودش کم میشه برای تست
        bot.send_message(msg.chat.id, f"{player['name']} حرکت {move_name} را اجرا کرد! دمج: {dmg} | HP فعلی: {player['hp']}")
    except Exception as e:
        bot.reply_to(msg, f"خطا: {e}")

bot.polling()
