import os, telebot, requests, instaloader, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Downloader Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت والمحرك ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
L = instaloader.Instaloader()

user_status = {}

# --- 3. نظام التحقق والمتابعة (رسائل منفصلة) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    
    # رسالة الترحيب الأولى
    welcome_text = (
        "اهلا بك 👋🏼\n"
        "شكرا لاستخدامك بوت تحميل مقاطع الانستجرام \n"
        "أولا سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت\n\n"
        "Welcome 👋🏼\n"
        "Thank you for using Instagram Downloader Bot \n"
        "First, you'll need to follow my Snapchat account to activate the bot"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_follow = types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK)
    btn_confirm = types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="insta_step_1")
    markup.add(btn_follow)
    markup.add(btn_confirm)
    
    bot.send_message(user_id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    
    if call.data == "insta_step_1":
        # رسالة الاعتذار (منفصلة) كما طلبت
        fail_msg = (
            "نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻\n"
            "الرجاء الضغط على متابعة الحساب وسيتم توجيهك لسناب شات وبعد المتابعة اضغط على زر تفعيل البوت 🔓\n\n"
            "We apologize, but your Snapchat account follow request has not been verified. ❌👻\n"
            "Please click \"Follow Account\" and you will be redirected to Snapchat. After following, click the \"Activate\" button. 🔓"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="insta_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup)
        
    elif call.data == "insta_step_2":
        user_status[user_id] = "verified"
        success_text = (
            "تم تفعيل البوت بنجاح ✅\n"
            "الرجاء ارسال الرابط 🔗\n\n"
            "The bot has been successfully activated ✅ \n"
            "Please send the link 🔗"
        )
        bot.send_message(user_id, success_text)

# --- 4. معالج تحميل إنستجرام (فيديو، صور، ألبومات) ---
@bot.message_handler(func=lambda message: True)
def handle_insta(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "instagram.com" in url:
        # رسالة جاري التحميل
        loading_text = (
            "جاري التحميل ... ⏳\n"
            "Loading... ⏳"
        )
        prog = bot.reply_to(message, loading_text)
        
        try:
            # استخراج الكود من الرابط
            shortcode = url.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            # 1. إذا كان المنشور يحتوي على عدة صور/فيديوهات (Carousel)
            if post.typename == 'GraphSidecar':
                media_group = []
                for node in post.get_sidecar_nodes():
                    if node.is_video:
                        media_group.append(types.InputMediaVideo(node.video_url))
                    else:
                        media_group.append(types.InputMediaPhoto(node.display_url))
                bot.send_media_group(user_id, media_group[:10])
            
            # 2. إذا كان فيديو واحد (Reel)
            elif post.is_video:
                bot.send_video(user_id, post.video_url)
            
            # 3. إذا كانت صورة واحدة فقط
            else:
                bot.send_photo(user_id, post.url)
                
            # رسالة تم التحميل
            done_text = (
                "تم التحميل ✅\n"
                "Done ✅"
            )
            bot.send_message(user_id, done_text)
            bot.delete_message(user_id, prog.message_id)
            
        except Exception:
            # رسالة المشكلة التقنية
            error_tech = (
                "نعتذر منك نواجه الان مشكله تقنية وسيتم معالجتها في أقرب وقت ❌\n\n"
                "We apologize, we are currently experiencing a technical issue and it will be resolved as soon as possible ❌"
            )
            bot.edit_message_text(error_tech, user_id, prog.message_id)
    else:
        # رسالة الرابط غير الصحيح
        wrong_link = (
            "الرجاء ارسال رابط الصحيح ❌\n\n"
            "Please send the correct link ❌"
        )
        bot.reply_to(message, wrong_link)

# --- 5. التشغيل الآمن ---
if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling()
