# --- معالج تحميل إنستجرام المحدث ---
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
            # استخدام API بديل ومستقر للانستا
            api_url = f"https://api.v1.savetube.me/info?url={url}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(api_url, headers=headers).json()
            
            if response.get('status') and response.get('data'):
                media_items = response['data']
                
                # إذا كان بوست صور متعددة
                if len(media_items) > 1:
                    media_group = []
                    for item in media_items[:10]:
                        if item.get('type') == 'video':
                            media_group.append(types.InputMediaVideo(item['url']))
                        else:
                            media_group.append(types.InputMediaPhoto(item['url']))
                    bot.send_media_group(user_id, media_group)
                else:
                    # فيديو واحد أو صورة واحدة
                    m_url = media_items[0]['url']
                    if media_items[0].get('type') == 'video':
                        bot.send_video(user_id, m_url, caption="✅ تم التحميل | Done")
                    else:
                        bot.send_photo(user_id, m_url, caption="✅ تم التحميل | Done")
                
                bot.delete_message(user_id, prog.message_id)
            else:
                bot.edit_message_text("❌ الرابط غير مدعوم أو الحساب خاص\nLink not supported or private", user_id, prog.message_id)
        except Exception as e:
            print(f"Error: {e}") # سيظهر لك في سجلات Render
            bot.edit_message_text("❌ عذراً، الـ API يواجه ضغطاً حالياً\nAPI is busy, try again", user_id, prog.message_id)
