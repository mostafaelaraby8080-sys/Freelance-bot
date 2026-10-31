# Freelance Bot

بوت تيليجرام بيراقب نفذلي ومستقل وخمسات، وبيكتب عرض تقديم بالذكاء الاصطناعي ويبعتهولك.

## التشغيل
1. انسخ `.env.example` باسم `.env` واملأه.
2. `python -m venv venv` ثم فعّله.
3. `pip install -r requirements.txt`
4. `python check_platforms.py`  (فحص المنصات من غير إرسال)
5. `python main.py`  (تشغيل مستمر)

## على GitHub Actions
أضف الأسرار: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY, GEMINI_MODEL, FREELANCER_PROFILE
