import os, telebot, requests, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر ويب ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Fixed Bot is Online"
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

# --- 3. محركات التحميل الجديدة (تتجاوز الحظر) ---

def get_insta_content(url):
    """المحرك الجديد: يستخدم API وسيط قوي جداً"""
    try:
        # نحن نستخدم هنا API سريع وقوي يتجاوز حماية انستا
        api_url = f"https://api.tikwm.com/api/instagram/post?url={url}"
        response = requests.get(api_url, timeout=15).json()
        if response.get('code') == 0:
            return response['data']
    except Exception as e:
        print(f"API Error: {e}")
    return None

def get_fallback_link(url):
    """المحرك البديل: إذا فشل الأول، نستخدم محول روابط مباشر مخصص للتليجرام"""
    # خدمة ddl-insta هي الأفضل حالياً لعرض الفيديوهات داخل التليجرام
    return url.replace("instagram.com", "ddinstagram.com")

# --- 4. أوامر التحقق (أسلوبك الخاص) ---
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
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="insta_verify"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "insta_verify")
def handle_verify(call):
    user_status[call.message.chat.id] = "verified"
    bot.send_message(call.message.chat.id, "<b>تم التفعيل بنجاح ✅ أرسل الرابط الآن</b>", parse_mode='HTML')

# --- 5. معالج التحميل (الخطة القوية) ---
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_download(message):
    user_id = message.chat.id
    url = message.text.strip()
    
    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري جلب المقطع من السيرفر... ⏳</b>", parse_mode='HTML')

    # محاولة جلب البيانات عبر الـ API
    data = get_insta_content(url)
    
    if data:
        try:
            # إذا كان ألبوم صور
            if data.get('images'):
                media = [types.InputMediaPhoto(img) for img in data['images'][:10]]
                bot.send_media_group(user_id, media)
            # إذا كان فيديو
            elif data.get('play'):
                bot.send_video(user_id, data['play'], caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
            
            bot.delete_message(user_id, prog.message_id)
            return
        except:
            pass

    # إذا فشل الـ API (بسبب حجم الملف أو حظر الرابط)، نستخدم نظام الـ Embed الذكي
    backup_url = get_fallback_link(url)
    fallback_text = (
        "<b>نعتذر، واجهنا صعوبة في رفع الفيديو مباشرة ❌</b>\n\n"
        "<b>لكن يمكنك مشاهدته أو تحميله عبر الرابط التالي:</b>\n"
        f"🔗 <a href='{backup_url}'>اضغط هنا (رابط مباشر)</a>"
    )
    # ملاحظة: عند إرسال رابط ddinstagram، تليجرام سيظهر الفيديو تلقائياً في المعاينة
    bot.edit_message_text(fallback_text, user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
