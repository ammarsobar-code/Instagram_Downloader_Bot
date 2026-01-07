import os
import json
import telebot
import yt_dlp
import requests
import threading
import tempfile
from flask import Flask

# --- إعدادات السيرفر (Render) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!", 200

# --- إعدادات البوت ---
# تأكد من إضافة BOT_TOKEN في Environment Variables على Render
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("Error: BOT_TOKEN variable not found!")
    
bot = telebot.TeleBot(TOKEN)
JSON_COOKIES_PATH = "cookies.json"

# --- دالة تحويل الكوكيز من JSON إلى Netscape (عشان yt-dlp يفهمها) ---
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
                name = c.get('name', '')
                value = c.get('value', '')
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
        return tmp_file.name
    except Exception as e:
        print(f"Cookie conversion error: {e}")
        return None

# --- المصدر 1: yt-dlp (داخلي) ---
def download_ytdlp(url, cookie_path):
    outtmpl = f"downloads/%(id)s.%(ext)s"
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'outtmpl': outtmpl,
    }
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- المصدر 2: Cobalt API (خارجي) ---
def download_cobalt(url):
    api_url = "https://api.cobalt.tools/api/json"
    payload = {"url": url, "vQuality": "720"}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get('url')
    return None

# --- معالج رسائل إنستغرام ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_insta(message):
    url = message.text.strip()
    status_msg = bot.reply_to(message, "⏳ جاري المعالجة...")
    
    # 1. محاولة yt-dlp
    try:
        bot.edit_message_text("🚀 محاولة 1 (yt-dlp)...", message.chat.id, status_msg.message_id)
        c_path = prepare_cookies()
        file_path = download_ytdlp(url, c_path)
        
        with open(file_path, 'rb') as video:
            bot.send_video(message.chat.id, video)
        
        os.remove(file_path)
        if c_path: os.remove(c_path)
        bot.delete_message(message.chat.id, status_msg.message_id)
        return
    except Exception as e:
        print(f"yt-dlp error: {e}")

    # 2. محاولة Cobalt API
    try:
        bot.edit_message_text("⚡ محاولة 2 (External API)...", message.chat.id, status_msg.message_id)
        video_link = download_cobalt(url)
        if video_link:
            bot.send_video(message.chat.id, video_link)
            bot.delete_message(message.chat.id, status_msg.message_id)
            return
    except Exception as e:
        print(f"API error: {e}")

    bot.edit_message_text("❌ فشلت جميع المحاولات لهذا الرابط.", message.chat.id, status_msg.message_id)

# --- تشغيل السيرفر والبوت معاً ---
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    # تشغيل البوت في Thread منفصل
    threading.Thread(target=run_bot).start()
    
    # تشغيل Flask على البورت المخصص من Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
