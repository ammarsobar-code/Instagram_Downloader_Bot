import os, telebot, requests, time, io
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "Direct Video Uploader is Online"
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

# --- 3. وظيفة جلب الرابط المباشر ---
def get_insta_data(url):
    try:
        # نستخدم API خارجي لجلب رابط الفيديو الخام
        api_url = f"https://api.tikwm.com/api/instagram/post?url={url}"
        res = requests.get(api_url, timeout=15).json()
        if res.get('code') == 0:
            return res['data']
    except: return None

# --- 4. نظام التحقق (أسلوبك الخاص) ---
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
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="v1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("v"))
def verify(call):
    if call.data == "v1":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="v2"))
        bot.send_message(call.message.chat.id, "<b>نعتذر منك لم يتم التحقق ❌👻\nيرجى المتابعة ثم الضغط على تفعيل</b>", reply_markup=markup, parse_mode='HTML')
    else:
        user_status[call.message.chat.id] = "verified"
        bot.send_message(call.message.chat.id, "<b>تم تفعيل البوت بنجاح ✅ أرسل الرابط الآن</b>", parse_mode='HTML')

# --- 5. المعالج الذكي (التحميل ثم الرفع المباشر) ---
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_insta(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل المباشر... ⏳</b>", parse_mode='HTML')
    
    data = get_insta_data(url)
    if not data:
        bot.edit_message_text("<b>نعتذر، لم نتمكن من الوصول للمقطع ❌</b>", user_id, prog.message_id, parse_mode='HTML')
        return

    try:
        # حالة الصور (ألبوم)
        if data.get('images'):
            media = [types.InputMediaPhoto(img) for img in data['images'][:10]]
            bot.send_media_group(user_id, media)
            bot.delete_message(user_id, prog.message_id)
            return

        # حالة الفيديو (السر هنا: التحميل للسيرفر ثم الرفع لتليجرام)
        video_url = data.get('play')
        if video_url:
            # تحميل الفيديو إلى ذاكرة السيرفر مؤقتاً
            video_content = requests.get(video_url, stream=True, timeout=30).content
            video_file = io.BytesIO(video_content)
            video_file.name = "video.mp4"
            
            # رفع الملف مباشرة كفيديو
            bot.send_video(user_id, video_file, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
            bot.delete_message(user_id, prog.message_id)
            return

    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text("<b>نعتذر منك، حدث خطأ أثناء الرفع ❌</b>", user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
