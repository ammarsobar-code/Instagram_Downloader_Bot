import os, telebot, requests, instaloader, time, yt_dlp
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Pro Live"
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

# --- 3. نظام التحقق والمتابعة (Bold + رسائل منفصلة) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "اهلا بك 👋🏼\n"
        "شكرا لاستخدامك بوت تحميل مقاطع الانستجرام\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "Welcome 👋🏼\n"
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
            "نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻\n"
            "<b>الرجاء الضغط على متابعة الحساب وبعد المتابعة اضغط على زر تفعيل البوت 🔓</b>\n\n"
            "We apologize, but your Snapchat account follow request has not been verified. ❌👻\n"
            "<b>Please click Follow Account and then click the Activate button. 🔓</b>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="insta_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "insta_step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗\n\nThe bot has been successfully activated ✅")

# --- 4. معالج التحميل الذكي (فيديو أو رابط مباشر) ---
@bot.message_handler(func=lambda message: True)
def handle_insta(message):
    user_id = message.chat.id
    url = message.text.strip()
    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "instagram.com" in url:
        prog = bot.reply_to(message, "جاري التحميل ... ⏳\nLoading... ⏳")
        try:
            ydl_opts = {'format': 'best', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
                
                # التعامل مع الألبومات
                if 'entries' in info:
                    media_group = []
                    for entry in info['entries'][:10]:
                        if entry.get('vcodec') != 'none':
                            media_group.append(types.InputMediaVideo(entry['url']))
                        else:
                            media_group.append(types.InputMediaPhoto(entry['url']))
                    bot.send_media_group(user_id, media_group)
                    bot.send_message(user_id, "تم التحميل ✅\nDone ✅")
                
                else:
                    try:
                        # محاولة إرسال الفيديو كملف
                        if info.get('vcodec') != 'none':
                            bot.send_video(user_id, video_url)
                        else:
                            bot.send_photo(user_id, video_url)
                        bot.send_message(user_id, "تم التحميل ✅\nDone ✅")
                        
                    except Exception:
                        # إذا كان الحجم كبيراً جداً (أكبر من 50MB)
                        over_size_text = (
                            "نظرا لان المقطع المرسل كبير جدا تم ارسال رابط تحميل مباشر 🔗✅\n"
                            "Due to the video size being too large, a direct download link has been sent 🔗✅\n\n"
                            f"<a href='{video_url}'>🔗 اضغط هنا للتحميل المباشر | Click here to download</a>"
                        )
                        bot.send_message(user_id, over_size_text, parse_mode='HTML')

            bot.delete_message(user_id, prog.message_id)

        except Exception:
            bot.edit_message_text("نعتذر منك نواجه مشكلة تقنية، تأكد أن الحساب عام وليس خاصاً ❌", user_id, prog.message_id)
    else:
        bot.reply_to(message, "الرجاء ارسال رابط صحيح ❌\nPlease send a valid link ❌")

# --- 5. التشغيل الآمن ---
if __name__ == "__main__":
    keep_alive()
    try:
        bot.remove_webhook()
    except:
        pass
    time.sleep(1)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
