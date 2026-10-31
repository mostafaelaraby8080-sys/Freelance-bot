import asyncio

from telegram import Bot

from bot import get_config
from database import init_db
from main import run_cycle


async def run() -> None:
    token, chat_id = get_config()
    init_db()
    async with Bot(token=token) as bot:
        await run_cycle(bot, chat_id)


if __name__ == "__main__":
    asyncio.run(run())

import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# دالة الاتصال بجوجل مع إعدادات إعادة المحاولة
@retry(
    stop=stop_after_attempt(5), # هيحاول 5 مرات كحد أقصى
    wait=wait_exponential(multiplier=2, min=4, max=20), # هيستنى 4 ثواني، بعدين 8، بعدين 16... إلخ
    retry=retry_if_exception_type(requests.exceptions.HTTPError) # هيعيد المحاولة لو حصل خطأ في الـ HTTP
)
def call_gemini_api(prompt):
    # هتحط هنا الـ URL بتاع جوجل والـ Headers والـ Data بتاعتك
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    print("جاري إرسال الطلب لجوجل...")
    response = requests.post(url, headers=headers, json=data)
    
    # لو السيرفر رد بخطأ 503 أو غيره، هيرمي Exception عشان دالة الـ retry تشتغل
    response.raise_for_status() 
    
    return response.json()


def main():
    try:
        # استدعاء الدالة
        result = call_gemini_api("اكتب لي جملة ترحيبية")
        print("نجح الاتصال! النتيجة:")
        print(result)
        
        # هنا ممكن تضيف كود إرسال الرسالة لتليجرام
        # send_to_telegram(...)
        
    except Exception as e:
        print(f"فشلت كل المحاولات بسبب: {e}")

if name == "main":
    main()