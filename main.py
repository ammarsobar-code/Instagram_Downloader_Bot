import os, subprocess, shutil, telebot, requests, io, time, sys
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. تحديث وتثبيت المكتبات تلقائياً لضمان العمل المستمر ---
def update_and_install():
    print("🔄 Checking for updates and installing requirements...")
    # تحديث pip أولاً
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    # تثبيت وتحديث الأدوات الأساسية
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "gallery-dl", "moviepy==2.2.1", "pyTelegramBotAPI", "flask"])

update_and_install()

from moviepy import VideoFileClip

# --- 2. إعدادات السيرفر والبوت ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Elite Bot is Running"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"
user_status = {}

def clean_downloads():
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- 3. نظام التحقق والمتابعة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع الانستجرام\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "<b>Welcome 👋🏼</b>\n"
        "<b>⚠️ First, follow my Snapchat to activate</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="ins_step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "ins_step_1":
        fail_msg = "<b>نعتذر منك لم يتم التحقق ❌👻</b>\nالرجاء المتابعة ثم اضغط <b>تفعيل البوت 🔓</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="ins_step_2"))
        bot.edit_message_text(fail_msg, user_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
    elif call.data == "ins_step_2":
        user_status[user_id] = "verified"
        bot.edit_message_text("<b>تم تفعيل البوت بنجاح ✅ أرسل الرابط الآن</b>", user_id, call.message.message_id, parse_mode='HTML')

# --- 4. معالج التحميل الرئيسي مع دعم الكوكيز ---
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_instagram(message):
    user_id = message.chat.id
    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    url = message.text.strip()
    prog = bot.reply_to(message, "<b>جاري التحميل باستخدام الكوكيز... ⏳</b>", parse_mode='HTML')
    clean_downloads()

    try:
        # بناء الأمر لاستخدام الكوكيز والتحديث المستمر عبر تشغيله كموديول بايثون
        cmd = [sys.executable, "-m", "gallery_dl", "-d", DOWNLOAD_DIR]
        
        # التأكد من مسار ملف الكوكيز
        cookie_path = "cookies.txt"
        if os.path.exists(cookie_path):
            cmd.extend(["--cookies", cookie_path])
            print(f"🍪 Using cookies from {cookie_path}")
        else:
            print("⚠️ No cookies.txt found, attempting public download")
            
        cmd.append(url)
        
        # تنفيذ التحميل
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        files = []
        for root, _, filenames in os.walk(DOWNLOAD_DIR):
            for name in filenames:
                files.append(os.path.join(root, name))

        if not files:
            error_log = result.stderr if result.stderr else "Unknown error"
            print(f"Download Error: {error_log}")
            bot.edit_message_text("<b>نعتذر، الحساب خاص أو الرابط غير مدعوم ❌</b>\nتأكد من تحديث ملف cookies.txt", user_id, prog.message_id, parse_mode='HTML')
            return

        for f_path in files:
            with open(f_path, "rb") as f:
                if f_path.lower().endswith((".mp4", ".mov", ".m4v")):
                    bot.send_video(user_id, f, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
                else:
                    bot.send_photo(user_id, f, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')

        bot.delete_message(user_id, prog.message_id)

    except Exception as e:
        bot.edit_message_text(f"<b>حدث خطأ: {str(e)} ❌</b>", user_id, prog.message_id, parse_mode='HTML')

# --- 5. تشغيل البوت ---
if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("🤖 Bot is ready and listening...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Network error: {e}")
            time.sleep(5)
