import asyncio
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from telegram import Bot
from bot import get_config
from database import init_db
from main import run_cycle


# ==========================================
# 1. كود تشغيل التليجرام الأساسي
# ==========================================
async def run() -> None:
    token, chat_id = get_config()
    init_db()
    async with Bot(token=token) as bot:
        await run_cycle(bot, chat_id)


# ==========================================
# 2. كود جوجل (متروك كـ تعليق عشان ميعملش تداخل)
# ==========================================
# @retry(
#     stop=stop_after_attempt(5), 
#     wait=wait_exponential(multiplier=2, min=4, max=20), 
#     retry=retry_if_exception_type(requests.exceptions.HTTPError) 
# )
# def call_gemini_api(prompt):
#     url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY"
#     headers = {'Content-Type': 'application/json'}
#     data = {
#         "contents": [{"parts": [{"text": prompt}]}]
#     }
#     
#     print("جاري إرسال الطلب لجوجل...")
#     response = requests.post(url, headers=headers, json=data)
#     response.raise_for_status() 
#     return response.json()


# ==========================================
# 3. نقطة التشغيل (Main)
# ==========================================
if name == "main":
    # لو عايز تشغل كود التليجرام خلي السطر ده
    asyncio.run(run())
    
    # ولو عايز تجرب كود جوجل، شيل علامة الـ # من السطور دي
    # try:
    #     result = call_gemini_api("اكتب لي جملة ترحيبية")
    #     print("نجح الاتصال! النتيجة:")
    #     print(result)
    # except Exception as e:
    #     print(f"فشلت كل المحاولات بسبب: {e}")