import os, telebot, requests, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "Direct Uploader Active"
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

# --- 3. وظيفة جلب الرابط المباشر الخام ---
def get_raw_url(url):
    try:
        # استخدام محرك Rapid السريع لجلب الرابط الخام
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
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="verify_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def handle_verify(call):
    user_id = call.message.chat.id
    if call.data == "verify_1":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="verify_2"))
        bot.send_message(user_id, "<b>نعتذر منك لم يتم التحقق ❌👻\nيرجى المتابعة ثم الضغط على تفعيل</b>", reply_markup=markup, parse_mode='HTML')
    elif call.data == "verify_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅ أرسل الرابط الآن</b>", parse_mode='HTML')

# --- 5. معالج الإرسال المباشر (Direct Video Streaming) ---
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_insta(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل المباشر... ⏳</b>", parse_mode='HTML')
    
    data = get_raw_url(url)
    
    if data:
        try:
            # معالجة الصور (ألبوم)
            if data.get('images'):
                media = [types.InputMediaPhoto(img) for img in data['images'][:10]]
                bot.send_media_group(user_id, media)
                bot.delete_message(user_id, prog.message_id)
                return

            # معالجة الفيديو (إرسال مباشر عبر التحميل المؤقت)
            video_url = data.get('play')
            if video_url:
                # هذه الخطوة هي السر: نطلب من تليجرام تحميل الفيديو من الرابط الخام فوراً
                bot.send_video(user_id, video_url, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML', timeout=60)
                bot.delete_message(user_id, prog.message_id)
                return
        except Exception as e:
            print(f"Error: {e}")

    # إذا فشل كل شيء
    bot.edit_message_text("<b>عذراً، تعذر رفع الفيديو مباشرة حالياً ❌\nتأكد أن الحساب عام (Public).</b>", user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=60)
