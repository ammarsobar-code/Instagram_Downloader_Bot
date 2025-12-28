import asyncio
import os
import tempfile
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
import instaloader

TOKEN = "YOUR_BOT_TOKEN"
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("مرحباً! أرسل لي رابط إنستجرام وسأحمله لك من أي مصدر ممكن. 🚀")

async def download_from_instaloader(url):
    """يحاول تحميل المنشور عبر Instaloader"""
    L = instaloader.Instaloader()
    try:
        shortcode = url.rstrip("/").split("/")[-1]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        tmpdir = tempfile.TemporaryDirectory()
        L.download_post(post, target=tmpdir.name)
        # البحث عن الملفات (صور/فيديو)
        files = [os.path.join(tmpdir.name, f) for f in os.listdir(tmpdir.name)]
        return files
    except Exception:
        return None

async def download_from_rapidapi(url):
    """يحاول تحميل المنشور عبر RapidAPI"""
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"
    }
    api_url = f"https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index?url={url}"
    try:
        response = requests.get(api_url, headers=headers).json()
        files = []
        # يمكن أن يكون الفيديو أو صورة
        if "media" in response:
            tmpdir = tempfile.TemporaryDirectory()
            for idx, item in enumerate(response["media"]):
                media_url = item["url"]
                ext = "mp4" if "video" in item["type"] else "jpg"
                filepath = os.path.join(tmpdir.name, f"{idx}.{ext}")
                r = requests.get(media_url)
                with open(filepath, "wb") as f:
                    f.write(r.content)
                files.append(filepath)
            return files
        return None
    except Exception:
        return None

@dp.message()
async def handle_instagram(message: Message):
    url = message.text.strip()
    await message.answer("🔄 جاري محاولة التحميل من Instaloader...")
    files = await download_from_instaloader(url)

    if not files:
        await message.answer("⚡ فشل التحميل من Instaloader، سأحاول RapidAPI...")
        files = await download_from_rapidapi(url)

    if not files:
        await message.answer("❌ للأسف لم أتمكن من تحميل المحتوى من أي مصدر.")
        return

    for f in files:
        if f.endswith(".mp4"):
            await message.answer_video(open(f, "rb"))
        else:
            await message.answer_photo(open(f, "rb"))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
