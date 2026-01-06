# استخدام نسخة بايثون رسمية
FROM python:3.9-slim

# تثبيت FFmpeg داخل نظام السيرفر مباشرة
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات البوت
COPY . .

# أمر تشغيل البوت
CMD ["python", "main.py"]
