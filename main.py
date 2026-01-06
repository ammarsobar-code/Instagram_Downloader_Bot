import os, shutil, telebot, time, sys, json, subprocess
from flask import Flask
from threading import Thread

# --- إعدادات البوت ---
# سيحاول الكود جلب التوكن من إعدادات السيرفر (Environment Variables)
# إذا لم تكن قد وضعتها في السيرفر، ضع التوكن مكان كلمة Your_Token_Here
API_TOKEN = os.getenv('BOT_TOKEN') 
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"

# --- وظائف النظام والتنظيف ---
def reset_server_environment():
    """حذف الملفات القديمة لتوفير المساحة ومنع الأخطاء"""
    try:
        if os.path.exists(DOWNLOAD_DIR):
            shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        # تنظيف كاش yt-dlp لمنع تراكم الملفات المؤقتة
        subprocess.run(["python3", "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
    except:
        pass

def convert_json_to_netscape(json_file, output_file):
    """تحويل الكوكيز لتجاوز حظر إنستجرام"""
    try:
        if not os.path.exists(json_file): return False
        with open(json_file, 'r') as f: cookies = json.load(f)
        with open(output_file, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                domain = c.get('domain', '')
                path = c.get('path', '/')
                expires = int(c.get('expirationDate', time.time() + 31536000))
                name = c.get('name', '')
                value = c.get('value', '')
                f.write(f"{domain}\tTRUE\t{path}\tTRUE\t{expires}\t{name}\t{value}\n")
        return True
    except: return False

def download_video(url):
    """محرك التحميل الأساسي"""
    reset_server_environment()
    target = url.split('?')[0].strip()
    use_cookies = convert_json_to_netscape('cookies.json', 'cookies.txt')

    cmd = [
        "python3", "-m", "yt_dlp",
        "-o", f"{DOWNLOAD_DIR}/video_%(id)s.%(ext)s",
        "--format", "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--max-filesize", "48M",
        "--no-playlist",
        target
    ]
    if use_cookies: cmd.extend(["--cookies", "cookies.txt"])
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

# --- معالجة رسائل التيليجرام ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_insta(message):
    status = bot.reply_to(message, "⏳ جاري تحميل الفيديو، انتظر قليلاً...")
    try:
        if download_video(message.text):
            sent = False
            for file in os.listdir(DOWNLOAD_DIR):
                if file.lower().endswith(('.mp4', '.mov')):
                    path = os.path.join(DOWNLOAD_DIR, file)
                    with open(path, "rb") as v:
                        bot.send_video(message.chat.id, v, supports_streaming=True)
                    sent = True
                    break
            if sent:
                bot.delete_message(message.chat.id, status.message_id)
            else:
                bot.edit_message_text("❌ لم أتمكن من العثور على ملف الفيديو بعد تحميله.", message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ فشل التحميل. تأكد أن الرابط عام وليس لحساب خاص.", message.chat.id, status.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ فني: {str(e)}")
    finally:
        reset_server_environment()

# --- سيرفر Flask للبقاء حياً على Render ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Active!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- نقطة التشغيل الرئيسية ---
if __name__ == "__main__":
    # 1. تشغيل السيرفر في الخلفية
    Thread(target=run_flask).start()
    
    # 2. حل مشكلة Error 409 (حذف أي جلسات معلقة)
    print("🧹 Cleaning up old sessions...")
    bot.remove_webhook()
    time.sleep(1)
    
    # 3. تشغيل البوت
    print("🚀 Bot is starting now...")
    reset_server_environment()
    bot.infinity_polling(skip_pending=True)
