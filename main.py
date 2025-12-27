import os, telebot, requests, io, yt_dlp, instaloader
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحماية من الإغلاق ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Downloader is Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. محركات التحميل (المكتبتين فقط) ---

def engine_ytdlp(url):
    """المحرك الأول: yt-dlp"""
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')
    except: return None

def engine_instaloader(url):
    """المحرك الثاني: instaloader"""
    try:
        L = instaloader.Instaloader()
        # استخراج الـ shortcode من الرابط
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if post.is_video:
            return post.video_url
        return post.url
    except: return None

# --- 4. خطوات التفعيل (بأسلوب عباراتك) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع الانستجرام\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("step_"))
def handle_verify(call):
    user_id = call.message.chat.id
    if call.data == "step_1":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="step_2"))
        bot.edit_message_text("<b>نعتذر منك لم يتم التحقق ❌👻\nيرجى المتابعة ثم الضغط على تفعيل البوت 🔓</b>", 
                              user_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
    elif call.data == "step_2":
        user_status[user_id] = "verified"
        bot.edit_message_text("<b>تم تفعيل البوت بنجاح ✅ أرسل الرابط الآن</b>", user_id, call.message.message_id, parse_mode='HTML')

# --- 5. معالج التحميل المباشر ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_download(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل المباشر... ⏳</b>", parse_mode='HTML')
    
    # محاولة المحرك الأول
    video_url = engine_ytdlp(url)
    
    # إذا فشل، محاولة المحرك الثاني
    if not video_url:
        video_url = engine_instaloader(url)

    if video_url:
        try:
            # التحميل إلى الذاكرة للرفع المباشر
            response = requests.get(video_url, stream=True, timeout=30)
            video_file = io.BytesIO(response.content)
            video_file.name = "video.mp4"
            
            bot.send_video(user_id, video_file, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
            bot.delete_message(user_id, prog.message_id)
            return
        except Exception as e:
            print(f"Error: {e}")

    bot.edit_message_text("<b>نعتذر، الحماية قوية على هذا المقطع ❌\nتأكد أن الحساب عام وليس خاص.</b>", user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
