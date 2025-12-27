import os, telebot, requests, time, io
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
RAPID_API_KEY = "aa1507e20amshee6699c484a24e7p147a28jsnd64b686f700e"
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 

bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. وظيفة جلب البيانات ---
def get_insta_data(url):
    api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"
    }
    try:
        response = requests.get(api_url, headers=headers, params={"url": url}, timeout=25)
        return response.json()
    except:
        return None

# --- 4. نظام التحقق المصلح ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = "<b>اهلا بك 👋🏼\nيرجى متابعة السناب أولاً لتفعيل البوت</b>"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل 🔓 Activate", callback_data="check_v1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def verify(call):
    user_id = call.message.chat.id
    if call.data == "check_v1":
        # عند الضغط لأول مرة، نرسل رسالة تطلب منه التأكد ثم الضغط على التفعيل النهائي
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل نهائي 🔓 Confirm", callback_data="check_v2"))
        bot.edit_message_text("<b>يرجى التأكد من المتابعة ثم الضغط على تفعيل نهائي ✅</b>", user_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
    
    elif call.data == "check_v2":
        # هنا يتم التفعيل الحقيقي
        user_status[user_id] = "verified"
        bot.answer_callback_query(call.id, "تم التفعيل بنجاح!")
        bot.edit_message_text("<b>تم التفعيل بنجاح ✅ أرسل رابط المقطع الآن</b>", user_id, call.message.message_id, parse_mode='HTML')

# --- 5. معالج التحميل ---
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_insta(message):
    user_id = message.chat.id
    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل المباشر... ⏳</b>", parse_mode='HTML')
    data = get_insta_data(message.text.strip())
    
    if data:
        try:
            video_url = data.get('media') or data.get('url') or data.get('download_url')
            if not video_url and data.get('links'):
                video_url = data['links'][0].get('url')

            if video_url:
                video_content = requests.get(video_url, stream=True, timeout=30).content
                video_file = io.BytesIO(video_content)
                video_file.name = "video.mp4"
                bot.send_video(user_id, video_file, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
                bot.delete_message(user_id, prog.message_id)
                return
        except:
            pass

    bot.edit_message_text("<b>نعتذر، فشل التحميل ❌ تأكد أن الحساب عام.</b>", user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
