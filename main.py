import os, shutil, telebot, time, sys, json
from flask import Flask
from threading import Thread
import subprocess

# --- إعدادات البيئة ---
# سيحاول البوت أخذ التوكن من إعدادات السيرفر، إذا لم يجده سيستخدم التوكن المكتوب يدوياً
API_TOKEN = os.getenv('BOT_TOKEN') or "ضع_هنا_توكن_بوتك_إذا_لم_تضعه_في_الإعدادات"
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"

# تأكد من وجود مجلد التحميل
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- وظائف المساعدة ---
def reset_server_environment():
    """تنظيف الملفات المؤقتة لتوفير المساحة"""
    try:
        if os.path.exists(DOWNLOAD_DIR):
            shutil.rmtree(DOWNLOAD_DIR)
        os.makedirs(DOWNLOAD_DIR)
        # تنظيف كاش yt-dlp
        subprocess.run(["python3", "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Cleanup error: {e}")

def convert_json_to_netscape(json_file, output_file):
    """تحويل الكوكيز من صيغة JSON إلى Netscape التي يفهمها yt-dlp"""
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

def download_and_process(url):
    reset_server_environment()
    target = url.split('?')[0].strip()
    
    # محاولة استخدام الكوكيز إذا كانت موجودة
    use_cookies = convert_json_to_netscape('cookies.json', 'cookies.txt')

    cmd = [
        "python3", "-m", "yt_dlp",
        "-o", f"{DOWNLOAD_DIR}/video_%(id)s.%(ext)s",
        "--format", "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--max-filesize", "48M", # لتجنب تجاوز حدود تيليجرام
        "--no-playlist",
        target
    ]
    
    if use_cookies:
        cmd.extend(["--cookies", "cookies.txt"])
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

# --- معالج الرسائل ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_insta(message):
    status = bot.reply_to(message, "⏳ جاري معالجة الرابط...")
    
    try:
        if download_and_process(message.text):
            for file in os.listdir(DOWNLOAD_DIR):
                path = os.path.join(DOWNLOAD_DIR, file)
                if file.lower().endswith(('.mp4', '.mov')):
                    with open(path, "rb") as f:
                        bot.send_video(message.chat.id, f, supports_streaming=True)
                    break
            bot.delete_message(message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ فشل التحميل (قد يكون الحساب خاصاً أو الفيديو طويلاً جداً).", message.chat.id, status.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ: {str(e)}")
    finally:
        reset_server_environment()

# --- تشغيل السيرفر (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("🚀 Bot is starting...")
    bot.infinity_polling()
