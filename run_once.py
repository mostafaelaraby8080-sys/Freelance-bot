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
