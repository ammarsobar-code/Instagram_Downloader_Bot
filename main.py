import os, telebot, requests, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحماية من الإغلاق ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Triple Engine Online"
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

# --- 3. وظائف المحركات المتعددة ---

def engine_1_tikwm(url):
    """المحرك الأول: الأسرع (Instagram API)"""
    try:
        res = requests.get(f"https://api.tikwm.com/api/instagram/post?url={url}", timeout=10).json()
        if res.get('code') == 0:
            data = res['data']
            if data.get('images'): return ("images", data['images'])
            return ("video", data['play'])
    except: return None

def engine_2_snap(url):
    """المحرك الثاني: بديل ذكي في حال تعطل الأول"""
    try:
        # واجهة برمجية بديلة متخصصة في الـ Reels
        res = requests.get(f"https://api.vkrdownloader.com/server?v={url}", timeout=10).json()
        if res.get('data'):
            return ("video", res['data']['url'])
    except: return None

# --- 4. نظام التحقق والترحيب (أسلوبك الخاص) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع الانستجرام\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "<b>Welcome 👋🏼</b>\n"
        "<b>⚠️ First, you'll need to follow my Snapchat account</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="verify_step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_step"))
def handle_verify(call):
    user_id = call.message.chat.id
    if call.data == "verify_step_1":
        fail_msg = (
            "<b>نعتذر منك لم يتم التحقق من متابعتك ❌👻</b>\n"
            "الرجاء المتابعة ثم اضغط على زر <b>تفعيل البوت 🔓</b>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="verify_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "verify_step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅ أرسل الرابط الآن</b>", parse_mode='HTML')

# --- 5. معالج التحميل الذكي (التتابع Fallback) ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def download_manager(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>", parse_mode='HTML')

    # محاولة المحرك الأول (TikWM)
    result = engine_1_tikwm(url)
    
    # محاولة المحرك الثاني إذا فشل الأول
    if not result:
        bot.edit_message_text("<b>جاري استخدام المحرك الاحتياطي... ⚙️</b>", user_id, prog.message_id, parse_mode='HTML')
        result = engine_2_snap(url)

    # تنفيذ الإرسال المباشر
    if result:
        m_type, m_data = result
        try:
            if m_type == "images":
                media = [types.InputMediaPhoto(img) for img in m_data[:10]]
                bot.send_media_group(user_id, media)
            else:
                bot.send_video(user_id, m_data, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
            
            bot.delete_message(user_id, prog.message_id)
            return
        except Exception as e:
            print(f"Error sending: {e}")

    # إذا فشلت كل الـ APIs، نستخدم نظام الـ DDL المباشر كحل نهائي (يعرض الفيديو في التليجرام)
    fallback_url = url.replace("instagram.com", "ddinstagram.com")
    error_msg = (
        "<b>نعتذر، واجه السيرفر ضغطاً كبيراً ❌</b>\n\n"
        "<b>لكن يمكنك المشاهدة والتحميل من هنا مباشرة:</b>\n"
        f"🔗 <a href='{fallback_url}'>اضغط هنا للمشاهدة المباشرة</a>"
    )
    bot.edit_message_text(error_msg, user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
