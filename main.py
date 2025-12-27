import os, telebot, requests, time, io
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Premium Uploader is Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت والـ API ---
API_TOKEN = os.getenv('BOT_TOKEN')
# المفتاح الذي أرسلته في الصورة
RAPID_API_KEY = "aa1507e20amshee6699c484a24e7p147a28jsnd64b686f700e"
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 

bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. محرك جلب الروابط المباشرة (Premium Engine) ---
def get_insta_direct(url):
    api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
    querystring = {"url": url}
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"
    }
    try:
        response = requests.get(api_url, headers=headers, params=querystring, timeout=20).json()
        return response
    except:
        return None

# --- 4. نظام التحقق والترحيب (أسلوبك الخاص) ---
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
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="v1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("v"))
def handle_verify(call):
    user_id = call.message.chat.id
    if call.data == "v1":
        bot.send_message(user_id, "<b>نعتذر منك لم يتم التحقق ❌👻\nيرجى المتابعة ثم الضغط على تفعيل</b>", parse_mode='HTML')
    elif call.data == "v2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅ أرسل الرابط الآن</b>", parse_mode='HTML')

# --- 5. معالج التحميل والرفع المباشر (الملف الحقيقي) ---
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_insta(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري جلب المقطع ورفعه مباشرة... ⏳</b>", parse_mode='HTML')
    
    data = get_insta_direct(url)
    
    if data and (data.get('media') or data.get('url')):
        try:
            # استخراج رابط الفيديو المباشر من الـ API
            video_url = data.get('media') or data.get('url')
            
            # الخطوة الأهم: تحميل الفيديو للسيرفر ثم رفعه لتليجرام كملف
            video_content = requests.get(video_url, stream=True, timeout=30).content
            video_file = io.BytesIO(video_content)
            video_file.name = "instagram_video.mp4"
            
            bot.send_video(user_id, video_file, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
            bot.delete_message(user_id, prog.message_id)
            return
        except Exception as e:
            print(f"Error: {e}")

    # رسالة الفشل النهائية
    bot.edit_message_text("<b>نعتذر، لم نتمكن من رفع الفيديو ❌\nتأكد أن المقطع عام وليس خاص.</b>", user_id, prog.
