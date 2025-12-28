import os
import subprocess
import shutil
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def clean_downloads():
    for f in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(path):
            os.remove(path)


def download_with_parth_dl(url):
    try:
        result = subprocess.run(
            ["parth-dl", url, "-o", DOWNLOAD_DIR],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return None

        files = [
            os.path.join(DOWNLOAD_DIR, f)
            for f in os.listdir(DOWNLOAD_DIR)
        ]
        return files if files else None

    except Exception as e:
        print("parth-dl error:", e)
        return None


def download_with_gallery_dl(url):
    try:
        subprocess.run(
            ["gallery-dl", "-d", DOWNLOAD_DIR, url],
            check=True,
            timeout=60
        )

        files = []
        for root, _, filenames in os.walk(DOWNLOAD_DIR):
            for name in filenames:
                files.append(os.path.join(root, name))

        return files if files else None

    except Exception as e:
        print("gallery-dl error:", e)
        return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "instagram.com" not in url:
        await update.message.reply_text("❌ أرسل رابط إنستجرام فقط")
        return

    await update.message.reply_text("⏳ جاري التحميل...")

    clean_downloads()

    files = download_with_parth_dl(url)

    if not files:
        await update.message.reply_text("⚠️ المحاولة الأولى فشلت، جاري المحاولة الثانية...")
        files = download_with_gallery_dl(url)

    if not files:
        await update.message.reply_text("❌ فشل التحميل من إنستجرام")
        return

    for file_path in files:
        try:
            await update.message.reply_document(
                document=open(file_path, "rb")
            )
        except Exception:
            pass

    shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)


if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")  # حطه في Environment Variables

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
