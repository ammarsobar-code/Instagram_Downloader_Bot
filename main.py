import os, subprocess, shutil, telebot, time, sys, requests
from flask import Flask
from threading import Thread

# تثبيت وتحديث كافة المحركات لضمان أعلى أداء
def install_engines():
    print("🔄 Installing Mega Engines...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "gallery-dl", "instaloader", "pyTelegramBotAPI", "flask", "requests"])

install_engines()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"
app = Flask('')

@app.route('/')
def home(): return "Multi-Engine Bot is Running"

def clean_dir():
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# دالة تنظيف الروابط من الزوائد التي تسبب أخطاء (مثل ?igsh=)
def clean_url(url):
    return url.split('?')[0].split('&')[0].strip()

# --- المحركات المجانية المتسلسلة ---

def engine_yt_dlp(url):
    """المحرك الأقوى: yt-dlp مع دعم الكوكيز"""
    print(f"🚀 Trying yt-dlp: {url}")
    cmd = [sys.executable, "-m", "yt_dlp", "-o", f"{DOWNLOAD_DIR}/%(title)s.%(ext)s", "--no-playlist", url]
    if os.path.exists("cookies.txt"):
        cmd.extend(["--cookies", "cookies.txt"])
    return subprocess.run(cmd, capture_output=True, timeout=120).returncode == 0

def engine_gallery_dl(url):
    """المحرك الثاني: gallery-dl (ممتاز للألبومات)"""
    print(f"🚀 Trying gallery-dl: {url}")
    cmd = [sys.executable, "-m", "gallery_dl", "-d", DOWNLOAD_DIR]
    if os.path.exists("cookies.txt"):
        cmd.extend(["--cookies", "cookies.txt"])
    cmd.append(url)
    return subprocess.run(cmd, capture_output=True, timeout=120).returncode == 0

def engine_instaloader(url):
    """المحرك الثالث: Instaloader (بديل سريع)"""
    print(f"🚀 Trying Instaloader...")
    try:
        shortcode = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
        cmd = [sys.executable, "-m", "instaloader", "--dirname-pattern=" + DOWNLOAD_DIR, "--", f"-{shortcode}"]
        return subprocess.run(cmd, capture_output=True, timeout=120).returncode == 0
    except: return False

# --- معالج الرسائل ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_instagram(message):
    raw_url = message.text.strip()
    target_url = clean_url(raw_url) # تنظيف الرابط فوراً
    
    status = bot.reply_to(message, "⏳ جاري محاولة التحميل بأقوى المحركات المجانية...")
    clean_dir()

    # محاولة المحركات بالتسلسل (yt-dlp -> gallery-dl -> instaloader)
    success = False
    if engine_yt_dlp(target_url):
        success = True
    elif engine_gallery_dl(target_url):
        success = True
    elif engine_instaloader(target_url):
        success = True

    if success:
        files_found = False
        for root, _, filenames in os.walk(DOWNLOAD_DIR):
            for name in filenames:
                f_path = os.path.join(root, name)
                if name.lower().endswith((".mp4", ".mov", ".jpg", ".jpeg", ".png", ".webp")):
                    with open(f_path, "rb") as f:
                        if name.lower().endswith((".mp4", ".mov")):
                            bot.send_video(message.chat.id, f, caption="✅ تم التحميل بواسطة المحرك المتعدد")
                        else:
                            bot.send_photo(message.chat.id, f, caption="✅ تم التحميل بواسطة المحرك المتعدد")
                    files_found = True
        
        if files_found:
            bot.delete_message(message.chat.id, status.message_id)
            return

    bot.edit_message_text("❌ فشلت جميع المحاولات المجانية. قد يكون الحساب خاصاً جداً أو الكوكيز انتهت صلاحيتها.", message.chat.id, status.message_id)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
