import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()


def get_config() -> tuple[str, str]:
    """قراءة الإعدادات من متغيرات البيئة والتحقق من وجودها."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise ValueError(
            "تأكد من وجود TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID في ملف .env"
        )
    return token, chat_id


async def send_message(bot: Bot, chat_id: str, text: str) -> None:
    """إرسال رسالة نصية إلى المستخدم."""
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        print("✅ تم إرسال الرسالة بنجاح")
    except TelegramError as error:
        print(f"❌ فشل الإرسال: {error}")


async def main() -> None:
    token, chat_id = get_config()
    bot = Bot(token=token)
    await send_message(bot, chat_id, "البوت يعمل بنجاح ✅")


if __name__ == "__main__":
    asyncio.run(main())