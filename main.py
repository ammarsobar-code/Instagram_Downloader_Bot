import os, telebot, requests, time, yt_dlp
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر ويب (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Pro is Online"
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

# --- 3. وظيفة التحميل الأقوى (Ultra Engine) ---
def fetch_instagram_data(url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        # تقمص شخصية متصفح حقيقي لتجاوز الحماية
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'add_header': ['Referer:https://www.instagram.com/','Accept-Language:en-US,en;q=0.9'],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except:
        return None

# --- 4. أوامر الترحيب والتحقق (أسلوبك الخاص) ---
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
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="insta_verify_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("insta_verify"))
def handle_verify(call):
    user_id = call.message.chat.id
    if call.data == "insta_verify_1":
        fail_msg = (
            "<b>نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻</b>\n"
            "الرجاء الضغط على متابعة الحساب وبعد المتابعة اضغط على زر <b>تفعيل البوت 🔓</b>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="insta_verify_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "insta_verify_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗</b>", parse_mode='HTML')

# --- 5. معالج التحميل الرئيسي ---
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_download(message):
    user_id = message.chat.id
    url = message.text.strip()
    
    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>", parse_mode='HTML')

    # محاولة التحميل باستخدام المحرك الأقوى
    info = fetch_instagram_data(url)
    
    if info:
        try:
            # إذا كان ألبوم (صور/فيديوهات متعددة)
            if 'entries' in info:
                media_group = []
                for entry in info['entries'][:10]:
                    if entry.get('vcodec') != 'none':
                        media_group.append(types.InputMediaVideo(entry['url']))
                    else:
                        media_group.append(types.InputMediaPhoto(entry['url']))
                bot.send_media_group(user_id, media_group)
            else:
                # فيديو مفرد أو صورة مفردة
                if info.get('vcodec') != 'none':
                    bot.send_video(user_id, info['url'], caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
                else:
                    bot.send_photo(user_id, info['url'])
            
            bot.delete_message(user_id, prog.message_id)
            return
        except Exception as e:
            print(f"Send Error: {e}")

    # --- الحل الأخير (إذا فشل السيرفر في الرفع) ---
    # نستخدم نظام ddinstagram الذي يحل مشاكل الحظر والرفع
    dd_url = url.replace("instagram.com", "ddinstagram.com")
    fallback_text = (
        "<b>نعتذر، واجه السيرفر صعوبة في معالجة الفيديو مباشرة ❌</b>\n\n"
        "<b>لكن لا تقلق، يمكنك تحميله من الرابط المباشر أدناه:</b>\n"
        f"🔗 <a href='{dd_url}'>اضغط هنا للتحميل أو المشاهدة</a>"
    )
    bot.edit_message_text(fallback_text, user_id, prog.message_id, parse_mode='HTML', disable_web_page_preview=False)

# --- 6. تشغيل البوت ---
if __name__ == "__main__":
    keep_alive()
    print("Bot is running...")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception:
            time.sleep(5)
