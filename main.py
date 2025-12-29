import os, subprocess, shutil, telebot, time, sys, json
from flask import Flask
from threading import Thread

# --- إضافة محرك FFmpeg برمجياً ---
def prepare_env():
    print("🔄 Installing & Configuring FFmpeg...")
    # تثبيت المكتبة التي توفر ffmpeg بشكل ثابت
    subprocess.check_call([sys.executable, "-m", "pip", "install", "static-ffmpeg"])
    # تشغيل الأمر لتجهيز الملفات التنفيذية
    import static_ffmpeg
    static_ffmpeg.add_paths() 
    print("✅ FFmpeg is ready to use.")

# استدعاء الوظيفة قبل أي شيء
prepare_env()

# ... (بقية كود البوت الذي أعطيتك إياه سابقاً)
import os, subprocess, shutil, telebot, time, sys, json
from flask import Flask
from threading import Thread

# --- 1. إعداد البيئة وتثبيت الأدوات ---
def prepare_env():
    print("🔄 Setting up Video Processing Factory...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    # تثبيت الأدوات مع التأكد من وجود ffprobe-linux للتعامل مع الأحجام
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "gallery-dl", "pyTelegramBotAPI", "flask"])

prepare_env()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"

# --- 2. وظيفة تحويل الكوكيز (JSON to Netscape) ---
def convert_json_to_netscape(json_file, output_file):
    try:
        if not os.path.exists(json_file): return
        with open(json_file, 'r') as f: cookies = json.load(f)
        with open(output_file, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                domain = c.get('domain', '')
                f.write(f"{domain}\tTRUE\t{c.get('path', '/')}\tTRUE\t{int(c.get('expirationDate', time.time()+31536000))}\t{c.get('name', '')}\t{c.get('value', '')}\n")
    except: pass

# --- 3. محرك التحميل مع الضغط التلقائي ---
def download_and_process(url):
    target = url.split('?')[0].strip()
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    
    # تحويل الكوكيز قبل البدء
    convert_json_to_netscape('cookies.json', 'cookies.txt')

    # إعدادات yt-dlp: إجبار جودة mp4 وضغط الفيديو إذا تجاوز 40 ميجا
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-o", f"{DOWNLOAD_DIR}/video.%(ext)s",
        "--format", "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--postprocessor-args", "ffmpeg:-vcodec libx264 -crf 28 -preset faster", # ضغط الفيديو لتقليل الحجم
        "--max-filesize", "45M", # الحد الأقصى قبل الرفض
        "--no-playlist",
        target
    ]
    
    if os.path.exists("cookies.txt"): cmd.extend(["--cookies", "cookies.txt"])
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

# --- 4. معالج البوت ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_insta(message):
    status = bot.reply_to(message, "⏳ جاري تحميل ومعالجة الفيديو (قد يتم ضغطه ليناسب تليجرام)...")
    
    if download_and_process(message.text):
        sent = False
        for root, _, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                path = os.path.join(root, file)
                if file.lower().endswith(('.mp4', '.mov')):
                    # التحقق من حجم الملف
                    file_size = os.path.getsize(path) / (1024 * 1024)
                    if file_size > 48:
                        bot.edit_message_text("⚠️ الفيديو كبير جداً (أكثر من 50 ميجا)، جاري إرساله كمستند...", message.chat.id, status.message_id)
                        with open(path, "rb") as f: bot.send_document(message.chat.id, f)
                    else:
                        with open(path, "rb") as f: bot.send_video(message.chat.id, f, supports_streaming=True)
                    sent = True
        
        if sent:
            bot.delete_message(message.chat.id, status.message_id)
            shutil.rmtree(DOWNLOAD_DIR)
            return

    bot.edit_message_text("❌ فشل المعالجة. المحرك لم يجد فيديو حقيقي أو تم حظر السيرفر.", message.chat.id, status.message_id)

app = Flask('')
@app.route('/')
def home(): return "Ready"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
bot.infinity_polling()
