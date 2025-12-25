import os
import telebot
from telebot import types
import requests
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask لإبقاء البوت نشطاً ---
app = Flask('')
@app.route('/')
def home(): return "Instagram Bot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت وتريف المتغيرات ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق والمتابعة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تمت المتابعة | Done", callback_data="check_1"))
    
    msg = f"⚠️ يرجى متابعة حسابي أولاً لتفعيل البوت:\nPlease follow my account first:\n\n{SNAP_LINK}"
    bot.send_message(user_id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تأكيد | Confirm", callback_data="check_final"))
        bot.send_message(user_id, f"❌ لم يتم التحقق بعد، تأكد من المتابعة ثم اضغط تأكيد\nVerification failed, make sure to follow then confirm:\n\n{SNAP_LINK}", reply_markup=markup)
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "✅ تم تفعيل البوت بنجاح! أرسل الرابط الآن\nBot activated successfully! Send the link now")
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)

# --- 4. معالج تحميل إنستجرام المطور ---
@bot.message_handler(func=lambda message: True)
def handle_instagram(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "instagram.com" in url:
        prog = bot.reply_to(message, "⏳ جاري التحميل... | Downloading...")
        try:
            # استخدام API متخصص وشامل للإنستجرام
            api_url = f"https://api.v1.savetube.me/info?url={url}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(api_url, headers=headers).json()
            
            if response.get('status') and response.get('data'):
                media_items = response['data']
                
                # الصور المتعددة أو الفيديوهات المتعددة
                if len(media_items) > 1:
                    media_group = []
                    for item in media_items[:10]:
                        if item.get('type') == 'video':
                            media_group.append(types.InputMediaVideo(item['url']))
                        else:
                            media_group.append(types.InputMediaPhoto(item['url']))
                    bot.send_media_group(user_id, media_group)
                else:
                    # فيديو أو صورة مفردة
                    m = media_items[0]
                    if m.get('type') == 'video':
                        bot.send_video(user_id, m['url'], caption="✅ تم التحميل بنجاح | Done")
                    else:
                        bot.send_photo(user_id, m['url'], caption="✅ تم التحميل بنجاح | Done")
                
                bot.delete_message(user_id, prog.message_id)
            else:
                bot.edit_message_text("❌ الحساب خاص أو الرابط غير مدعوم\nAccount is private or link unsupported", user_id, prog.message_id)
        
        except Exception:
            bot.edit_message_text(f"❌ خطأ تقني، جرب مرة أخرى\nTechnical Error, try again", user_id, prog.message_id)
    else:
        bot.reply_to(message, "❌ يرجى إرسال رابط إنستجرام صحيح\nPlease send a valid Instagram link")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
