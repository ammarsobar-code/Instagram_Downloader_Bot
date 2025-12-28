import os, subprocess, shutil, telebot, requests, io
from telebot import types
from flask import Flask
from threading import Thread
from moviepy import VideoFileClip

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Elite Bot is Running"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
DOWNLOAD_DIR = "downloads"
user_status = {}

# --- 3. وظائف التنظيف والضغط ---
def clean_downloads():
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def compress_if_needed(file_path):
    """ضغط الفيديو إذا كان حجمه أكبر من 45 ميجابايت لتجنب قيود تليجرام"""
    if file_path.endswith((".mp4", ".mov", ".m4v")):
        size = os.path.getsize(file_path)
        if size > 45 * 1024 * 1024:
            out_path = file_path.replace(".mp4", "_min.mp4")
            try:
                clip = VideoFileClip(file_path)
                clip.write_videofile(out_path, bitrate="1200k", codec="libx264", audio_codec="aac")
                clip.close()
                return out_path
            except: return file_path
    return file_path

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

# --- 5. معالج التحميل الرئيسي (باستخدام محرك gallery-dl) ---

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_instagram(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>", parse_mode='HTML')
    clean_downloads()

    try:
        # استخدام ملف الكوكيز إذا وجد لفك تشفير المقاطع الخاصة/الحساسة
        cmd = ["gallery-dl", "-d", DOWNLOAD_DIR, url]
        if os.path.exists("cookies.txt"):
            cmd.extend(["--cookies", "cookies.txt"])
            
        subprocess.run(cmd, timeout=120)

        files = []
        for root, _, filenames in os.walk(DOWNLOAD_DIR):
            for name in filenames:
                files.append(os.path.join(root, name))

        if not files:
            bot.edit_message_text("<b>نعتذر، الحساب خاص أو الرابط غير مدعوم ❌</b>", user_id, prog.message_id, parse_mode='HTML')
            return

        for f_path in files:
            # ضغط الفيديو إذا كان كبيراً
            final_file = compress_if_needed(f_path)
            with open(final_file, "rb") as f:
                # إرسال كفيديو إذا كان mp4، وإلا كوثيقة
                if f_path.endswith(".mp4"):
                    bot.send_video(user_id, f, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')
                else:
                    bot.send_photo(user_id, f, caption="<b>تم التحميل بواسطة ALL MEDIA ✅</b>", parse_mode='HTML')

        bot.delete_message(user_id, prog.message_id)
        bot.send_message(user_id, "<b>تم التحميل ✅\nDone ✅</b>", parse_mode='HTML')

    except Exception as e:
        bot.edit_message_text("<b>نعتذر، حدث خطأ أثناء المعالجة ❌</b>", user_id, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
