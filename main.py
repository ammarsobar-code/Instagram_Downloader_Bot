import os, telebot, requests, io, time
from telebot import types
from flask import Flask
from threading import Thread
from yt_dlp import YoutubeDL
from moviepy import VideoFileClip  # تم تصحيح هذا السطر للعمل مع الإصدار الجديد

# --- 1. سيرفر Flask للحفاظ على نشاط البوت ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Ultra Bot is Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
RAPID_API_KEY = "aa1507e20amshee6699c484a24e7p147a28jsnd64b686f700e"
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. وظائف التحميل والضغط ---

def compress_video(input_path, output_path):
    """ضغط الفيديو لتقليل الحجم قبل الرفع"""
    try:
        clip = VideoFileClip(input_path)
        # خفض الجودة لضمان قبول تليجرام للملف (تحت 50 ميجا)
        clip.write_videofile(output_path, bitrate="1200k", codec="libx264", audio_codec="aac")
        clip.close()
        return True
    except: return False

def get_video_data(url):
    """محرك جلب الروابط (يدعم الكوكيز و API)"""
    try:
        api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
        headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"}
        res = requests.get(api_url, headers=headers, params={"url": url}, timeout=15).json()
        if res.get('media'): return res['media']
    except: pass
    
    try:
        ydl_opts = {'format': 'best', 'quiet': True, 'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None}
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False).get('url')
    except: return None

# --- 4. نظام التحقق والمتابعة (نفس أسلوبك بالضبط) ---

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
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="ins_step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "ins_step_1":
        fail_msg = (
            "<b>نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻</b>\n"
            "الرجاء الضغط على متابعة الحساب وسيتم توجيهك لسناب شات وبعد المتابعة اضغط على زر <b>تفعيل البوت 🔓</b>\n\n"
            "<b>We apologize, but your Snapchat account follow request has not been verified. ❌👻</b>\n"
            "Please click Follow Account and you will be redirected to Snapchat. After following, click the <b>Activate</b> button. 🔓"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="ins_step_2"))
        bot.edit_message_text(fail_msg, user_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
    elif call.data == "ins_step_2":
        user_status[user_id] = "verified"
        bot.edit_message_text("<b>تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗\n\n<b>The bot has been successfully activated ✅</b></b>", user_id, call.message.message_id, parse_mode='HTML')

# --- 5. معالج التحميل الرئيسي ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_instagram(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>", parse_mode='HTML')
    video_url = get_video_data(url)

    if video_url:
        try:
            head = requests.head(video_url)
            file_size = int(head.headers.get('Content-Length', 0))

            if file_size > 48 * 1024 * 1024:
                bot.edit_message_text("<b>الفيديو كبير جداً، جاري ضغطه لتقليل الحجم... ⚙️</b>", user_id, prog.message_id, parse_mode='HTML')
                temp_in, temp_out = f"in_{user_id}.mp4", f"out_{user_id}.mp4"
                
                with open(temp_in, 'wb') as f: f.write(requests.get(video_url).content)
                
                if compress_video(temp_in, temp_out):
                    with open(temp_out, 'rb') as f:
                        bot.send_video(user_id, f, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
                else:
                    bot.send_message(user_id, f"<b>تعذر الضغط، الرابط المباشر:</b>\n{video_url}")
                
                for f in [temp_in, temp_out]: 
                    if os.path.exists(f): os.remove(f)
            else:
                video_res = requests.get(video_url).content
                bot.send_video(user_id, io.BytesIO(video_res), caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')

            bot.send_message(user_id, "<b>تم التحميل ✅\nDone ✅</b>", parse_mode='HTML')
            bot.delete_message(user_id, prog.message_id)
            return
        except: pass

    bot.edit_message_text("<b>نعتذر، الحساب خاص أو الرابط غير مدعوم ❌</b>", user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
