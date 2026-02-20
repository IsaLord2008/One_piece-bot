import os
from dotenv import load_dotenv

load_dotenv()  # فایل .env رو می‌خونه
TOKEN = os.getenv("TOKEN")

print(TOKEN)  # فقط برای تست که درست خوند شده
