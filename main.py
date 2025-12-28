import os, subprocess, shutil, telebot, time, sys
from telebot import types
from flask import Flask
from threading import Thread

# تثبيت المحركات الأساسية لضمان التغطية الشاملة
def install_tools():
    print("🔄 Updating All Free Engines...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gallery-dl", "instaloader", "pyTelegramBotAPI", "flask"])

install_tools()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"
app = Flask('')

@app.route('/')
def home(): return "Multi-Engine System Active"

def run_flask(): app.run(host='0.0.0.0', port=8080)

def clean_dir():
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- قائمة المحركات المتسلسلة ---

def try_method_1(url):
    """المحاولة 1: Gallery-dl مع الكوكيز (الأقوى للحسابات الخاصة)"""
    cmd = [sys.executable, "-m", "gallery_dl", "-d", DOWNLOAD_DIR]
    if os.path.exists("cookies.txt"):
        cmd.extend(["--cookies", "cookies.txt"])
    cmd.append(url)
    return subprocess.run(cmd, timeout=120).returncode == 0

def try_method_2(url):
    """المحاولة 2: Instaloader (تكتيك مختلف للروابط العامة)"""
    try:
        shortcode = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
        cmd = [sys.executable, "-m", "instaloader", "--dirname-pattern=" + DOWNLOAD_DIR, "--", f"-{shortcode}"]
        return subprocess.run(cmd, timeout=120).returncode == 0
    except: return False

def try_method_3(url):
    """المحاولة 3: استخراج الفيديو المباشر (Direct Stream)"""
    # هذا المحرك يحاول تجاوز الحماية بطلب الملف مباشرة من خوادم إنستجرام
    cmd = [sys.executable, "-m", "gallery_dl", "--get-urls", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode == 0 and len(result.stdout) > 5

# --- المعالج الرئيسي ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_instagram(message):
    url = message.text.strip()
    status = bot.reply_to(message, "⏳ جاري الفحص بالمحرك 1 (الرئيسي)...")
    clean_dir()

    # نظام التعاقب: إذا فشل الأول، ينتقل للثاني تلقائياً
    if try_method_1(url) and send_files(message.chat.id, status): return

    bot.edit_message_text("⏳ فشل المحرك 1، جاري المحاولة بالمحرك 2 (البديل)...", message.chat.id, status.message_id)
    if try_method_2(url) and send_files(message.chat.id, status): return

    bot.edit_message_text("⏳ محاولة أخيرة عبر محرك استخراج الروابط المباشرة...", message.chat.id, status.message_id)
    if try_method_3(url) and send_files(message.chat.id, status): return

    bot.edit_message_text("❌ جميع المحاولات المجانية فشلت. الأسباب المحتملة:\n1- الحساب خاص والكوكيز لا تتابعه.\n2- إنستجرام حظر IP السيرفر (Render).", message.chat.id, status.message_id)

def send_files(chat_id, status_msg):
    files_sent = False
    for root, _, filenames in os.walk(DOWNLOAD_DIR):
        for name in filenames:
            if name.endswith((".mp4", ".jpg", ".png", ".mov")):
                with open(os.path.join(root, name), "rb") as f:
                    bot.send_video(chat_id, f) if name.endswith(".mp4") else bot.send_photo(chat_id, f)
                files_sent = True
    if files_sent:
        bot.delete_message(chat_id, status_msg.message_id)
    return files_sent

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling(timeout=20)
