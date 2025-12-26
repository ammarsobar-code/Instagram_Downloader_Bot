import os, telebot, requests, time, yt_dlp
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت على Render ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Ultra Bot is Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
# تأكد من وضع التوكن في Environment Variables باسم BOT_TOKEN
API_TOKEN = os.getenv('BOT_TOKEN') 
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. وظائف التحميل المتعددة ---

def fetch_insta_api(url):
    """المحرك الأول: API خارجي سريع"""
    try:
        api_url = f"https://api.tikwm.com/api/instagram/post?url={url}"
        res = requests.get(api_url, timeout=12).json()
        if res.get('code') == 0:
            return res['data']
    except: return None

def fetch_insta_ytdlp(url):
    """المحرك الثاني: yt-dlp القوي"""
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'cachedir': False
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except: return None

# --- 4. نظام التحقق والمتابعة (أسلوبك الخاص) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع الانستجرام\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "<b>Welcome 👋🏼</b>\n"
        "Thank you for using Instagram Downloader Bot\n"
        "<b>⚠️ First, you'll need to follow my Snapchat account to activate the bot</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="insta_step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "insta_step_1":
        fail_msg = (
            "<b>نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻</b>\n"
            "الرجاء الضغط على متابعة الحساب وبعد المتابعة اضغط على زر <b>تفعيل البوت 🔓</b>\n\n"
            "<b>We apologize, but your Snapchat account follow request has not been verified. ❌👻</b>\n"
            "Please click Follow Account and then click the <b>Activate</b> button. 🔓"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="insta_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "insta_step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗\n\nThe bot has been successfully activated ✅</b>", parse_mode='HTML')

# --- 5. معالج التحميل الرئيسي ---

@bot.message_handler(func=lambda message: True)
def handle_insta_download(message):
    user_id = message.chat.id
    url = message.text.strip()
    
    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "instagram.com" in url:
        prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>", parse_mode='HTML')
        
        # --- المرحلة 1: محاولة الـ API السريع ---
        data = fetch_insta_api(url)
        if data:
            try:
                if data.get('images'):
                    media = [types.InputMediaPhoto(img) for img in data['images'][:10]]
                    bot.send_media_group(user_id, media)
                else:
                    bot.send_video(user_id, data['play'], caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
                bot.delete_message(user_id, prog.message_id)
                return
            except: pass

        # --- المرحلة 2: محاولة yt-dlp (المحرك الأقوى) ---
        info = fetch_insta_ytdlp(url)
        if info:
            try:
                video_url = info.get('url')
                if info.get('vcodec') != 'none':
                    bot.send_video(user_id, video_url, caption="<b>تم التحميل بواسطة المحرك الاحترافي ✅</b>", parse_mode='HTML')
                else:
                    bot.send_photo(user_id, video_url)
                bot.delete_message(user_id, prog.message_id)
            except:
                # رابط مباشر للمساحات الكبيرة
                over_size_text = (
                    "<b>نظرا لان المقطع المرسل كبير جدا تم ارسال رابط تحميل مباشر 🔗✅</b>\n\n"
                    f"<a href='{info.get('url')}'>🔗 اضغط هنا للتحميل المباشر</a>"
                )
                bot.edit_message_text(over_size_text, user_id, prog.message_id, parse_mode='HTML')
        else:
            error_tech = (
                "<b>نعتذر منك نواجه الان مشكله تقنية وسيتم معالجتها في أقرب وقت ❌</b>\n\n"
                "<b>We apologize, we are experiencing a technical issue ❌</b>"
            )
            bot.edit_message_text(error_tech, user_id, prog.message_id, parse_mode='HTML')
    else:
        bot.reply_to(message, "<b>الرجاء ارسال رابط صحيح ❌\nPlease send a valid link ❌</b>", parse_mode='HTML')

# --- 6. التشغيل الآمن والذكي ---
if __name__ == "__main__":
    keep_alive()
    print("Instagram Bot is Starting...")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(5) # منع الـ Conflict وتكرار الخطأ
