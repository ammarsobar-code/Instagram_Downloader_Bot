import os, subprocess, shutil, telebot, time, sys, json
from flask import Flask
from threading import Thread

# --- 1. وظيفة تحويل الكوكيز من JSON إلى Netscape ---
def convert_json_to_netscape(json_file, output_file):
    try:
        with open(json_file, 'r') as f:
            cookies = json.load(f)
        with open(output_file, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                domain = c.get('domain', '')
                # تحويل القيمة المنطقية إلى TRUE/FALSE نصية
                flag = "TRUE" if domain.startswith('.') else "FALSE"
                path = c.get('path', '/')
                secure = "TRUE" if c.get('secure') else "FALSE"
                # وقت الانتهاء (إذا لم يوجد نضع وقتاً بعيداً)
                expiry = int(c.get('expirationDate', time.time() + 31536000))
                name = c.get('name', '')
                value = c.get('value', '')
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
        print("✅ Cookies converted to Netscape format.")
    except Exception as e:
        print(f"❌ Cookie conversion failed: {e}")

# --- 2. إعداد البيئة وتثبيت الأدوات ---
def prepare_env():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "gallery-dl", "instaloader", "pyTelegramBotAPI", "flask"])
    
    # تحويل ملف الكوكيز إذا كان موجوداً بصيغة JSON
    if os.path.exists('cookies.json'):
        convert_json_to_netscape('cookies.json', 'cookies.txt')

prepare_env()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"

# --- 3. محركات التحميل ---
def try_engines(url):
    target = url.split('?')[0].strip() # تنظيف الرابط
    if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
    
    # المحرك 1: yt-dlp
    print(f"Running Engine 1 (yt-dlp) for: {target}")
    cmd1 = [sys.executable, "-m", "yt_dlp", "-o", f"{DOWNLOAD_DIR}/%(title)s.%(ext)s", "--no-playlist", target]
    if os.path.exists("cookies.txt"): cmd1.extend(["--cookies", "cookies.txt"])
    if subprocess.run(cmd1).returncode == 0: return True

    # المحرك 2: gallery-dl
    print("Running Engine 2 (gallery-dl)")
    cmd2 = [sys.executable, "-m", "gallery_dl", "-d", DOWNLOAD_DIR]
    if os.path.exists("cookies.txt"): cmd2.extend(["--cookies", "cookies.txt"])
    cmd2.append(target)
    if subprocess.run(cmd2).returncode == 0: return True

    return False

# --- 4. معالج البوت ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_insta(message):
    status = bot.reply_to(message, "⏳ جاري التحميل بأقوى المحركات...")
    if try_engines(message.text):
        for root, _, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                path = os.path.join(root, file)
                with open(path, "rb") as f:
                    if file.lower().endswith(('.mp4', '.mov')):
                        bot.send_video(message.chat.id, f)
                    else:
                        bot.send_photo(message.chat.id, f)
        shutil.rmtree(DOWNLOAD_DIR)
        bot.delete_message(message.chat.id, status.message_id)
    else:
        bot.edit_message_text("❌ فشل التحميل. الحساب خاص أو الرابط غير مدعوم.", message.chat.id, status.message_id)

# تشغيل Flask للبقاء حياً على Render
app = Flask('')
@app.route('/')
def home(): return "Bot is Live"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
bot.infinity_polling()
