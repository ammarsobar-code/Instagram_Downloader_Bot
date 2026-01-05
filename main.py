import os, subprocess, shutil, telebot, time, sys, json
from flask import Flask
from threading import Thread

# --- 1. إعداد البيئة (تثبيت الأدوات و FFmpeg) ---
def prepare_env():
    print("🔄 Setting up Video Processing Factory...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        # إضافة static-ffmpeg لضمان وجود المحرك على سيرفر Render
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "gallery-dl", "pyTelegramBotAPI", "flask", "static-ffmpeg"])
        
        import static_ffmpeg
        static_ffmpeg.add_paths() 
        print("✅ FFmpeg & Tools are ready.")
    except Exception as e:
        print(f"⚠️ Env Setup Warning: {e}")

prepare_env()

# --- 2. وظيفة التنظيف التلقائي (Auto-Clean) ---
def reset_server_environment():
    """تنظيف شامل للمساحة والعمليات العالقة لضمان استمرار البوت"""
    try:
        # 1. مسح مجلد التحميلات تماماً
        if os.path.exists("downloads"):
            shutil.rmtree("downloads", ignore_errors=True)
        os.makedirs("downloads", exist_ok=True)
        
        # 2. تنظيف كاش yt-dlp
        subprocess.run([sys.executable, "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
        
        # 3. قتل عمليات المعالجة العالقة في الرام
        if os.name != 'nt':
            subprocess.run(["pkill", "-9", "-f", "yt-dlp"], stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-9", "-f", "ffmpeg"], stderr=subprocess.DEVNULL)
        print("🧹 System Reset Done")
    except:
        pass

# --- 3. إعدادات البوت وكوكيز إنستجرام ---
API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"

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

# --- 4. محرك التحميل مع الضغط ---
def download_and_process(url):
    # تنظيف قبل البدء لضمان مساحة فارغة
    reset_server_environment()
    
    target = url.split('?')[0].strip()
    convert_json_to_netscape('cookies.json', 'cookies.txt')

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-o", f"{DOWNLOAD_DIR}/video_%(id)s.%(ext)s",
        "--format", "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--postprocessor-args", "ffmpeg:-vcodec libx264 -crf 28 -preset faster",
        "--max-filesize", "45M",
        "--no-playlist",
        target
    ]
    
    if os.path.exists("cookies.txt"):
        cmd.extend(["--cookies", "cookies.txt"])
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

# --- 5. معالج البوت ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_insta(message):
    status = bot.reply_to(message, "⏳ جاري التحميل والمعالجة...")
    
    try:
        if download_and_process(message.text):
            sent = False
            for root, _, files in os.walk(DOWNLOAD_DIR):
                for file in files:
                    path = os.path.join(root, file)
                    if file.lower().endswith(('.mp4', '.mov')):
                        file_size = os.path.getsize(path) / (1024 * 1024)
                        if file_size > 48:
                            with open(path, "rb") as f: bot.send_document(message.chat.id, f)
                        else:
                            with open(path, "rb") as f: bot.send_video(message.chat.id, f, supports_streaming=True)
                        sent = True
            
            if sent:
                bot.delete_message(message.chat.id, status.message_id)
            else:
                bot.edit_message_text("❌ لم يتم العثور على ملف فيديو مدعوم.", message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ فشل التحميل. قد يكون الحساب خاصاً أو الرابط غير صالح.", message.chat.id, status.message_id)
    
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ حدث خطأ تقني أثناء المعالجة.")
    
    finally:
        # التنظيف النهائي فوراً بعد الإرسال
        reset_server_environment()

# --- 6. السيرفر والتشغيل ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Engine Active"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    reset_server_environment() # تنظيف عند البدء
    bot.infinity_polling(timeout=20, long_polling_timeout=10, restart_on_change=False)
