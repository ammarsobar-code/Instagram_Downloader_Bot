import requests
import tempfile
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = "aa1507e20amshee6699c484a24e7p147a28jsnd64b686f700e"
RAPIDAPI_HOST = "instagram-video-image-downloader.p.rapidapi.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("مرحباً! أرسل رابط إنستجرام وسأحمله لك عبر RapidAPI 🚀")

@dp.message()
async def handle_instagram(message: Message):
    url = message.text.strip()
    await message.answer("🔄 جاري التحميل من RapidAPI...")

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    api_url = f"https://{RAPIDAPI_HOST}/i?url={url}"
    
    try:
        response = requests.get(api_url, headers=headers).json()
        if "media" not in response or not response["media"]:
            await message.answer("❌ لم يتم العثور على وسائط.")
            return

        tmpdir = tempfile.TemporaryDirectory()
        files = []

        for idx, item in enumerate(response["media"]):
            media_url = item["url"]
            ext = "mp4" if "video" in item["type"] else "jpg"
            filepath = os.path.join(tmpdir.name, f"{idx}.{ext}")
            r = requests.get(media_url)
            with open(filepath, "wb") as f:
                f.write(r.content)
            files.append(filepath)

        for f in files:
            if f.endswith(".mp4"):
                await message.answer_video(open(f, "rb"))
            else:
                await message.answer_photo(open(f, "rb"))

    except Exception as e:
        await message.answer(f"❌ حدث خطأ أثناء التحميل: {e}")
