import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# المتغيرات البيئية
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APP_URL = os.environ.get("APP_URL")  # رابط HTTPS للبوت على Render

# إنشاء Flask app
flask_app = Flask(__name__)

# إنشاء Telegram bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# مثال على أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 البوت شغال عبر Webhook!")

app.add_handler(CommandHandler("start", start))

# استقبال Webhook من Telegram
@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.update_queue.put_nowait(update)
    return "ok"

# ضبط Webhook عند Start
async def on_startup(app):
    await app.bot.set_webhook(f"{APP_URL}/{BOT_TOKEN}")

app.post_init = on_startup

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
