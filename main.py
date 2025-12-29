import os, subprocess, shutil, telebot, time, sys, json
from flask import Flask
from threading import Thread

# --- 1. وظيفة تحويل الكوكيز (JSON to Netscape) ---
def convert_json_to_netscape(json_file, output_file):
    try:
        if not os.path.exists(json_file): return
        with open(json_file, 'r') as f: cookies = json.load(f)
        with open(output_file, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                domain = c.get('domain', '')
                flag = "TRUE" if domain.startswith('.') else "FALSE"
                path = c.get('path', '/')
                secure = "TRUE" if c.get('secure') else "FALSE"
                expiry = int(c.get('expirationDate', time.time() + 31536000))
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{c.get('name', '')}\t{c.get('value', '')}\n")
        print("✅ Cookies converted successfully.")
    except Exception as e: print(f"❌ Cookie error: {e}")

# --- 2. إعداد البيئة وتثبيت المكتبات اللازمة للمعالجة ---
def prepare_env():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    # إضافة imageio-ffmpeg لضمان دمج الصوت والصورة بشكل صحيح
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "gallery-dl", "pyTelegramBotAPI", "flask", "imageio-ffmpeg"])
    if os.path.exists('cookies.json'):
        convert_json_to_netscape('cookies.json', 'cookies.txt')

prepare_env()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"

# --- 3. محرك التحميل المطور (إجبار دمج الفيديو) ---
def try_engines(url):
    target = url.split('?')[0].strip()
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    
    print(f"🚀 Processing Video: {target}")
    
    # محرك yt-dlp مع إعدادات دمج الفيديو (mp4)
    cmd1 = [
        sys.executable, "-m", "yt_dlp",
        "-o", f"{DOWNLOAD_DIR}/video.%(ext)s",
        "--merge-output-format", "mp4", # إجبار الدمج في ملف mp4 واحد
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", # اختيار أفضل جودة mp4
        "--no-playlist",
        target
    ]
    
    if os.path.exists("cookies.txt"):
        cmd1.extend(["--cookies", "cookies.txt"])
    
    result = subprocess.run(cmd1, capture_output=True)
    if result.returncode == 0: return True

    # محرك احتياطي في حال فشل الأول
    cmd2 = [sys.executable, "-m", "gallery_dl", "-d", DOWNLOAD_DIR, target]
    if os.path.exists("cookies.txt"): cmd2.insert(4, "--cookies")
    if os.path.exists("cookies.txt"): cmd2.insert(5, "cookies.txt")
    
    return subprocess.run(cmd2).returncode == 0

# --- 4. معالج البوت ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_insta(message):
    status = bot.reply_to(message, "⏳ جاري معالجة الفيديو بجودة عالية...")
    
    if try_engines(message.text):
        files_sent = False
        for root, _, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                path = os.path.join(root, file)
                if file.lower().endswith(('.mp4', '.mov', '.m4v')):
                    with open(path, "rb") as f:
                        bot.send_video(message.chat.id, f, supports_streaming=True)
                    files_sent = True
                elif file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # لا نرسل الصور إلا إذا لم نجد فيديوهات (للألبومات)
                    if not any(f.endswith('.mp4') for f in files):
                        with open(path, "rb") as f:
                            bot.send_photo(message.chat.id, f)
                        files_sent = True
        
        if files_sent:
            bot.delete_message(message.chat.id, status.message_id)
            shutil.rmtree(DOWNLOAD_DIR)
            return

    bot.edit_message_text("❌ فشل التحميل كفيديو. قد يكون الرابط تالفاً أو يحتاج لتحديث الكوكيز.", message.chat.id, status.message_id)

# تشغيل السيرفر
app = Flask('')
@app.route('/')
def home(): return "Video Engine Active"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
bot.infinity_polling()
