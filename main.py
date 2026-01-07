import os
import json
import telebot
import yt_dlp
import requests
import threading
import tempfile
import sys
import subprocess
import shutil
from flask import Flask
from telebot import types

# --- 1. سيرفر Flask للحفاظ على نشاط البوت على Render ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Instagram Downloader is Online", 200

# --- 2. إعدادات البوت ---
TOKEN = os.environ.get('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
JSON_COOKIES_PATH = "cookies.json"
bot = telebot.TeleBot(TOKEN)
user_status = {}

# --- 3. وظيفة التنظيف التلقائي ---
def auto_clean_environment():
    try:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
        if os.path.exists("downloads"):
            shutil.rmtree("downloads", ignore_errors=True)
        os.makedirs("downloads", exist_ok=True)
    except: pass

# --- 4. دالة تحويل الكوكيز ---
def prepare_cookies():
    if not os.path.exists(JSON_COOKIES_PATH):
        return None
    try:
        with open(JSON_COOKIES_PATH, 'r') as f:
            cookies_data = json.load(f)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        with open(tmp_file.name, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies_data:
                domain = c.get('domain', '')
                flag = "TRUE" if domain.startswith('.') else "FALSE"
                path = c.get('path', '/')
                secure = "TRUE" if c.get('secure', False) else "FALSE"
                expiry = int(c.get('expirationDate', 0))
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{c.get('name','')}\t{c.get('value','')}\n")
        return tmp_file.name
    except: return None

# --- 5. وظائف التحميل ---
def download_ytdlp(url, cookie_path):
    outtmpl = f"downloads/%(id)s.%(ext)s"
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'outtmpl': outtmpl,
        'cachedir': False
    }
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def download_cobalt(url):
    try:
        api_url = "https://api.cobalt.tools/api/json"
        res = requests.post(api_url, json={"url": url, "vQuality": "720"}, headers={"Accept": "application/json"})
        return res.json().get('url') if res.status_code == 200 else None
    except: return None

# --- 6. نظام التحقق والردود ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع إنستغرام\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "<b>Welcome 👋🏼</b>\n"
        "Thank you for using Instagram Downloader Bot\n"
        "<b>⚠️ First, you'll need to follow my Snapchat account to activate the bot</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="tt_step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "tt_step_1":
        fail_msg = "<b>نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="tt_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "tt_step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗</b>", parse_mode='HTML')

# --- 7. معالج الرسائل الرئيسي ---
@bot.message_handler(func=lambda m: True)
def handle_main(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "instagram.com" in url:
        status_msg = bot.reply_to(message, "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>", parse_mode='HTML')
        
        # محاولة 1: yt-dlp
        try:
            bot.edit_message_text("🚀 محاولة 1 (yt-dlp)...", message.chat.id, status_msg.message_id)
            c_path = prepare_cookies()
            file_path = download_ytdlp(url, c_path)
            with open(file_path, 'rb') as video:
                bot.send_video(user_id, video, caption="<b>✅ تم التحميل بنجاح</b>", parse_mode='HTML')
            os.remove(file_path)
            if c_path: os.remove(c_path)
            bot.delete_message(user_id, status_msg.message_id)
            auto_clean_environment()
            return
        except Exception as e:
            print(f"yt-dlp error: {e}")

        # محاولة 2: Cobalt API
        try:
            bot.edit_message_text("⚡ محاولة 2 (External API)...", message.chat.id, status_msg.message_id)
            video_link = download_cobalt(url)
            if video_link:
                bot.send_video(user_id, video_link, caption="<b>✅ تم التحميل (محرك احتياطي)</b>", parse_mode='HTML')
                bot.delete_message(user_id, status_msg.message_id)
                auto_clean_environment()
                return
        except: pass

        bot.edit_message_text("<b>نعتذر منك، فشل تحميل الرابط ❌</b>", message.chat.id, status_msg.message_id, parse_mode='HTML')
        auto_clean_environment()
    else:
        bot.reply_to(message, "<b>الرجاء ارسال رابط إنستغرام صحيح 🔗</b>", parse_mode='HTML')

# --- 8. التشغيل ---
def run_bot():
    auto_clean_environment()
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
