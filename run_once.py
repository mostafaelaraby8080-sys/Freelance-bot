import asyncio
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from telegram import Bot
from bot import get_config
from database import init_db
from main import run_cycle

async def run() -> None:
    token, chat_id = get_config()
    init_db()
    async with Bot(token=token) as bot:
        await bot.send_message(chat_id=chat_id, text="البوت اشتغل بنجاح من GitHub Actions! 🚀")
        await run_cycle(bot, chat_id)

if __name__ == "__main__":
    asyncio.run(run())
