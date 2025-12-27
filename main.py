import os, telebot, requests, time, io, yt_dlp, instaloader
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "Multi-Engine Bot Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت والمفاتيح ---
API_TOKEN = os.getenv('BOT_TOKEN')
RAPID_API_KEY = "aa1507e20amshee6699c484a24e7p147a28jsnd64b686f700e"
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 

bot = telebot.TeleBot(API_TOKEN)
L = instaloader.Instaloader()
user_status = {}

# --- 3. ترسانة المحركات (The Arsenal) ---

def engine_1_rapid(url):
    """المحرك الأول: البريميوم (RapidAPI)"""
    try:
        api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
        headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"}
        res = requests.get(api_url, headers=headers, params={"url": url}, timeout=15).json()
        return res.get('media') or res.get('url')
    except: return None

def engine_2_tikwm(url):
    """المحرك الثاني: السحابي العام (TikWM)"""
    try:
        res = requests.get(f"https://api.tikwm.com/api/instagram/post?url={url}", timeout=15).json()
        if res.get('code') == 0:
            return res['data'].get('play') or res['data'].get('images', [None])[0]
    except: return None

def engine_3_ytdlp(url):
    """المحرك الثالث: المكتبي القوي (yt-dlp)"""
    try:
        ydl_opts = {'format': 'best', 'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False).get('url')
    except: return None

# --- 4. نظام التحقق المصلح (يعمل 100%) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = "<b>اهلا بك 👋🏼\nيرجى متابعة السناب أولاً لتفعيل البوت</b>"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل 🔓 Activate", callback_data="v1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("v"))
def verify(call):
    user_id = call.message.chat.id
    if call.data == "v1":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل نهائي 🔓 Confirm", callback_data="v2"))
        bot.edit_message_text("<b>يرجى التأكد من المتابعة ثم الضغط على تفعيل نهائي ✅</b>", user_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
    elif call.data == "v2":
        user_status[user_id] = "verified"
        bot.edit_message_text("<b>تم التفعيل بنجاح ✅ أرسل الرابط الآن</b>", user_id, call.message.message_id, parse_mode='HTML')

# --- 5. معالج التحميل (نظام الفحص المتتابع) ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_insta(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    msg = bot.reply_to(message, "<b>جاري الفحص عبر 4 محركات مختلفة... ⏳</b>", parse_mode='HTML')
    
    # قائمة المحركات للتشغيل بالتتابع
    engines = [engine_1_rapid, engine_2_tikwm, engine_3_ytdlp]
    video_url = None

    for i, engine in enumerate(engines, 1):
        bot.edit_message_text(f"<b>جاري محاولة التحميل عبر المحرك ({i})... ⚙️</b>", user_id, msg.message_id, parse_mode='HTML')
        video_url = engine(url)
        if video_url:
            break

    if video_url:
        try:
            # محاولة الرفع المباشر من الذاكرة (Buffer)
            video_content = requests.get(video_url, stream=True, timeout=30).content
            video_file = io.BytesIO(video_content)
            video_file.name = "instagram_video.mp4"
            
            bot.send_video(user_id, video_file, caption="<b>تم التحميل بنجاح ✅</b>", parse_mode='HTML')
            bot.delete_message(user_id, msg.message_id)
            return
        except Exception as e:
            print(f"Upload error: {e}")

    # إذا فشلت كل المحركات في الرفع المباشر
    bot.edit_message_text("<b>نعتذر، الحماية قوية جداً على هذا المقطع أو السيرفر محظور حالياً ❌</b>", user_id, msg.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
