import os, subprocess, shutil, telebot, time, sys
from telebot import types
from flask import Flask
from threading import Thread

def install_all_engines():
    print("🔄 Installing Mega Engines (yt-dlp, gallery-dl, instaloader)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    # إضافة yt-dlp للقائمة
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "gallery-dl", "instaloader", "pyTelegramBotAPI", "flask"])

install_all_engines()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"
app = Flask('')

@app.route('/')
def home(): return "Mega Downloader Bot is Online"

def run_flask(): app.run(host='0.0.0.0', port=8080)

def clean_dir():
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- محركات التحميل (الترتيب من الأقوى للأضعف) ---

def try_ytdlp(url):
    """المحرك 1: yt-dlp (الخيار الرقم 1 عالمياً)"""
    print(f"尝试 yt-dlp: {url}")
    # إعدادات yt-dlp للتحميل بأفضل جودة
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-o", f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "--no-playlist",
        "--merge-output-format", "mp4",
        url
    ]
    # إضافة الكوكيز إذا وجدت
    if os.path.exists("cookies.txt"):
        cmd.extend(["--cookies", "cookies.txt"])
        
    result = subprocess.run(cmd, capture_output=True, timeout=180)
    return result.returncode == 0

def try_gallery_dl(url):
    """المحرك 2: Gallery-dl (احتياطي متخصص للصور والألبومات)"""
    cmd = [sys.executable, "-m", "gallery_dl", "-d", DOWNLOAD_DIR]
    if os.path.exists("cookies.txt"):
        cmd.extend(["--cookies", "cookies.txt"])
    cmd.append(url)
    return subprocess.run(cmd, timeout=120).returncode == 0

def try_instaloader(url):
    """المحرك 3: Instaloader (تكتيك مختلف للـ Reels)"""
    try:
        shortcode = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
        cmd = [sys.executable, "-m", "instaloader", "--dirname-pattern=" + DOWNLOAD_DIR, "--", f"-{shortcode}"]
        return subprocess.run(cmd, timeout=120).returncode == 0
    except: return False

# --- المعالج الرئيسي ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_instagram_cascade(message):
    url = message.text.strip()
    status = bot.reply_to(message, "⏳ جاري التحميل بمحرك yt-dlp المطور...")
    clean_dir()

    # محاولة المحرك العملاق أولاً
    if try_ytdlp(url) and send_files(message.chat.id, status): return

    bot.edit_message_text("⏳ جاري تجربة المحركات الاحتياطية (Gallery-dl)...", message.chat.id, status.message_id)
    if try_gallery_dl(url) and send_files(message.chat.id, status): return

    bot.edit_message_text("⏳ محاولة أخيرة باستخدام Instaloader...", message.chat.id, status.message_id)
    if try_instaloader(url) and send_files(message.chat.id, status): return

    bot.edit_message_text("❌ للأسف، جميع المحاولات فشلت. قد يكون الرابط تالفاً أو يحتاج كوكيز متابعة للحساب.", message.chat.id, status.message_id)

def send_files(chat_id, status_msg):
    files_sent = False
    for root, _, filenames in os.walk(DOWNLOAD_DIR):
        for name in filenames:
            f_path = os.path.join(root, name)
            if name.endswith((".mp4", ".jpg", ".png", ".mov", ".webp")):
                with open(f_path, "rb") as f:
                    if name.endswith((".mp4", ".mov")):
                        bot.send_video(chat_id, f, caption="✅ تم التحميل بنجاح")
                    else:
                        bot.send_photo(chat_id, f, caption="✅ تم التحميل بنجاح")
                files_sent = True
    if files_sent:
        bot.delete_message(chat_id, status_msg.message_id)
    return files_sent

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling(timeout=20)
