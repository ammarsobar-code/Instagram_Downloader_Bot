import os, telebot, requests
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Insta Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تمت المتابعة | Done", callback_data="check_1"))
    bot.send_message(user_id, f"⚠️ يرجى متابعة حسابي أولاً:\nPlease follow first:\n\n{SNAP_LINK}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تأكيد | Confirm", callback_data="check_final"))
        bot.send_message(user_id, f"❌ تأكد من المتابعة ثم اضغط تأكيد\nFollow then confirm:\n\n{SNAP_LINK}", reply_markup=markup)
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "✅ تم التفعيل! أرسل الرابط الآن")

@bot.message_handler(func=lambda message: True)
def handle_insta(message):
    if user_status.get(message.chat.id) != "verified":
        send_welcome(message)
        return

    url = message.text.strip()
    if "instagram.com" in url:
        prog = bot.reply_to(message, "⏳ جاري التحميل... | Downloading...")
        try:
            # استخدام API بديل يتجاوز حظر السيرفرات
            api_url = "https://api.cobalt.tools/api/json"
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            data = {"url": url, "vCodec": "h264"}
            
            response = requests.post(api_url, json=data, headers=headers).json()
            
            if response.get('status') == 'stream' or response.get('status') == 'redirect':
                bot.send_video(message.chat.id, response['url'], caption="✅ Done")
                bot.delete_message(message.chat.id, prog.message_id)
            elif response.get('status') == 'picker': # صور متعددة
                media = [types.InputMediaPhoto(item['url']) for item in response['picker']]
                bot.send_media_group(message.chat.id, media[:10])
                bot.delete_message(message.chat.id, prog.message_id)
            else:
                bot.edit_message_text("❌ لم نتمكن من جلب الفيديو، تأكد أن الحساب عام", message.chat.id, prog.message_id)
        except:
            bot.edit_message_text("❌ عذراً، الخدمة مشغولة حالياً", message.chat.id, prog.message_id)

keep_alive()
bot.infinity_polling()
