import os, telebot, requests, time, io
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Premium Bot is Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
# تأكد أن هذا المفتاح صحيح تماماً كما في الصورة
RAPID_API_KEY = "aa1507e20amshee6699c484a24e7p147a28jsnd64b686f700e"
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 

bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. محرك جلب البيانات الذكي ---
def get_insta_data(url):
    api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"
    }
    try:
        response = requests.get(api_url, headers=headers, params={"url": url}, timeout=25)
        print(f"API Response: {response.text}") # هذا للتحقق من المشكلة في اللوج
        return response.json()
    except Exception as e:
        print(f"API Request Error: {e}")
        return None

# --- 4. نظام التحقق والترحيب ---
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
    if call.data == "v1":
        bot.send_message(call.message.chat.id, "<b>لم يتم التحقق ❌ يرجى المتابعة ثم التفعيل</b>", parse_mode='HTML')
    else:
        user_status[call.message.chat.id] = "verified"
        bot.send_message(call.message.chat.id, "<b>تم التفعيل ✅ أرسل الرابط</b>", parse_mode='HTML')

# --- 5. معالج التحميل (محاولة الرفع ثم الإرسال) ---
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_insta(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري جلب المقطع... ⏳</b>", parse_mode='HTML')
    data = get_insta_data(url)
    
    if not data:
        bot.edit_message_text("<b>نعتذر، لم نتمكن من الوصول للمقطع ❌</b>", user_id, prog.message_id, parse_mode='HTML')
        return

    # محاولة استخراج الرابط من أكثر من حقل محتمل (لأن الـ APIs تختلف)
    video_url = data.get('media') or data.get('url') or data.get('download_url')
    
    # إذا كان هناك ميديا متعددة (Carousel)
    if not video_url and data.get('links'):
        video_url = data['links'][0].get('url')

    if video_url:
        try:
            # محاولة 1: الرفع المباشر كملف (وهو ما تريده)
            video_content = requests.get(video_url, stream=True, timeout=30).content
            video_file = io.BytesIO(video_content)
            video_file.name = "instagram_video.mp4"
            
            bot.send_video(user_id, video_file, caption="<b>تم التحميل مباشرة ✅</b>", parse_mode='HTML')
            bot.delete_message(user_id, prog.message_id)
            return
        except Exception as e:
            # محاولة 2: إرسال الرابط المباشر إذا فشل الرفع (لضمان عمل البوت)
            print(f"Upload failed: {e}")
            bot.edit_message_text(f"<b>تعذر الرفع المباشر، يمكنك التحميل من هنا:</b>\n<a href='{video_url}'>🔗 اضغط هنا للتحميل</a>", user_id, prog.message_id, parse_mode='HTML')
            return

    bot.edit_message_text("<b>نعتذر، هذا النوع من المقاطع غير مدعوم حالياً ❌</b>", user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
