import os, telebot, requests, time, io
from telebot import types
from flask import Flask
from threading import Thread
from yt_dlp import YoutubeDL

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Elite Bot is Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
# المفتاح من صورتك الأولى
RAPID_API_KEY = "aa1507e20amshee6699c484a24e7p147a28jsnd64b686f700e"
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. محرك التحميل الذكي (API + Cookies) ---

def get_video_data(url):
    # المحرك 1: RapidAPI (سريع جداً)
    try:
        api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
        headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"}
        res = requests.get(api_url, headers=headers, params={"url": url}, timeout=15).json()
        if res.get('media'): return {'play': res['media']}
    except: pass

    # المحرك 2: yt-dlp مع الكوكيز (للمقاطع الحساسة والخاصة)
    try:
        ydl_opts = {
            'format': 'best', 'quiet': True, 'no_warnings': True,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {'play': info['url']}
    except: return None

# --- 4. نظام التحقق والمتابعة (نفس أسلوبك) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع الانستجرام\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "<b>Welcome 👋🏼</b>\n"
        "<b>⚠️ First, follow my Snapchat to activate</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="ins_step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "ins_step_1":
        fail_msg = (
            "<b>نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻</b>\n"
            "الرجاء الضغط على متابعة الحساب وبعد المتابعة اضغط على زر <b>تفعيل البوت 🔓</b>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="ins_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "ins_step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗</b>", parse_mode='HTML')

# --- 5. المعالج النهائي للرفع المباشر ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_insta(message):
    user_id = message.chat.id
    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل المباشر... ⏳\nLoading... ⏳</b>", parse_mode='HTML')
    data = get_video_data(message.text.strip())

    if data and data.get('play'):
        try:
            # تحميل الفيديو للسيرفر ثم الرفع المباشر
            video_content = requests.get(data['play'], timeout=60).content
            video_file = io.BytesIO(video_content)
            video_file.name = "instagram_video.mp4"
            
            bot.send_video(user_id, video_file, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
            bot.delete_message(user_id, prog.message_id)
            bot.send_message(user_id, "<b>تم التحميل ✅\nDone ✅</b>", parse_mode='HTML')
            return
        except: pass

    bot.edit_message_text("<b>نعتذر، المقطع محمي أو حجمه كبير ❌</b>", user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=20)
