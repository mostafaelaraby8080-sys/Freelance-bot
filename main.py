import asyncio
import logging
import os
import re

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

import scraper_khamsat
import scraper_mostaql
import scraper_nafezly
from ai_writer import generate_proposal
from bot import get_config
from common import Job
from database import count_seen_jobs, init_db, is_job_seen, mark_job_seen

ALL_PLATFORMS = {
    module.PLATFORM: module
    for module in (scraper_nafezly, scraper_mostaql, scraper_khamsat)
}

CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_MINUTES", "5")) * 60
MAX_JOBS_PER_PLATFORM = int(os.getenv("MAX_JOBS_PER_PLATFORM", "5"))
DELAY_BETWEEN_JOBS_SECONDS = 3
MAX_DETAILS_IN_MESSAGE = 600
TELEGRAM_LIMIT = 4000

# المشاريع اللي مفيهاش أي كلمة من دي هتتجاهل (للمنصات اللي فلترتها شغالة).
KEYWORDS = [
    "برمج", "موقع", "مواقع", "تطبيق", "ويب", "متجر", "سكريبت", "بوت",
    "قاعدة بيانات", "لارافيل", "ووردبريس", "فرونت", "باك اند", "html",
    "api", "python", "react", "node", "laravel", "wordpress", "next.js",
]

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
# مهم: لوج httpx بيطبع رابط الطلب وفيه توكن البوت
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("freelance-bot")


def enabled_platforms() -> list:
    """المنصات المفعّلة من متغير PLATFORMS (الافتراضي: الكل)."""
    names = os.getenv("PLATFORMS", ",".join(ALL_PLATFORMS)).split(",")
    return [ALL_PLATFORMS[n.strip()] for n in names if n.strip() in ALL_PLATFORMS]


def is_relevant(job: Job, module) -> bool:
    """هل المشروع في مجالك؟ (فلترة بالكلمات المفتاحية)."""
    if not module.FILTER_BY_KEYWORDS or not KEYWORDS:
        return True
    text = f"{job.title} {job.details}".lower()
    for keyword in KEYWORDS:
        if keyword.isascii():
            # الكلمات الإنجليزية لازم تكون كلمة كاملة (عشان api ما تطابقش capital)
            if re.search(rf"(?<![a-z]){re.escape(keyword)}(?![a-z])", text):
                return True
        elif keyword in text:
            return True
    return False


def format_message(job: Job, proposal: str, label: str) -> str:
    """تجهيز نص الإشعار."""
    lines = [
        f"🔔 مشروع جديد على {label}",
        "",
        f"📌 العنوان: {job.title}",
    ]
    if job.budget:
        lines.append(f"💰 الميزانية: {job.budget}")
    if job.duration:
        lines.append(f"⏱ المدة: {job.duration}")
    lines.append(f"🌐 المنصة: {label}")
    if job.details:
        lines += ["", f"📝 التفاصيل:\n{job.details[:MAX_DETAILS_IN_MESSAGE]}"]
    lines += ["", f"✍️ العرض الجاهز:\n{proposal}"]
    return "\n".join(lines)[:TELEGRAM_LIMIT]


def build_keyboard(job: Job) -> InlineKeyboardMarkup:
    """زر يفتح صفحة المشروع للتقديم."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔗 افتح المشروع وقدّم", url=job.link)]]
    )


def seed_platform(module) -> None:
    """أول تشغيل لمنصة: نسجل المشاريع الحالية بدون إرسال (عشان ما نغرقكش)."""
    jobs = module.fetch_jobs()
    for job in jobs:
        mark_job_seen(job.id, job.title)
    logger.info("[%s] أول تشغيل: تم تسجيل %d مشروع بدون إرسال", module.LABEL, len(jobs))


def collect_new_jobs(module) -> list[Job]:
    """المشاريع الجديدة فقط (بحد أقصى لكل دورة)."""
    jobs = module.fetch_jobs()
    new_jobs = [job for job in jobs if not is_job_seen(job.id)]
    return new_jobs[:MAX_JOBS_PER_PLATFORM]


async def process_job(bot: Bot, chat_id: str, module, job: Job) -> None:
    """معالجة مشروع واحد: تفاصيل، فلترة، عرض، إرسال، تسجيل."""
    try:
        await asyncio.to_thread(module.enrich, job)
    except Exception as error:
        logger.warning("[%s] تعذر جلب التفاصيل (%s)، هكمل بالمتاح", module.LABEL, error)

    if not is_relevant(job, module):
        mark_job_seen(job.id, job.title)
        logger.info("[%s] تجاهل (خارج المجال): %s", module.LABEL, job.title)
        return

    proposal = await asyncio.to_thread(
        generate_proposal,
        job.title,
        job.details,
        module.LABEL,
        job.budget,
        job.duration,
    )
    await bot.send_message(
        chat_id=chat_id,
        text=format_message(job, proposal, module.LABEL),
        reply_markup=build_keyboard(job),
        disable_web_page_preview=True,
    )
    # التسجيل بعد نجاح الإرسال فقط، عشان لو فشل نحاول تاني في الدورة الجاية
    mark_job_seen(job.id, job.title)
    logger.info("[%s] تم الإرسال: %s", module.LABEL, job.title)


async def check_platform(bot: Bot, chat_id: str, module) -> None:
    """فحص منصة واحدة."""
    if count_seen_jobs(module.PLATFORM) == 0:
        await asyncio.to_thread(seed_platform, module)
        return

    jobs = await asyncio.to_thread(collect_new_jobs, module)
    logger.info("[%s] مشاريع جديدة: %d", module.LABEL, len(jobs))

    for job in jobs:
        try:
            await process_job(bot, chat_id, module, job)
        except TelegramError as error:
            logger.error("[%s] فشل الإرسال على تيليجرام: %s", module.LABEL, error)
        except Exception as error:
            logger.error("[%s] فشلت معالجة %s: %s", module.LABEL, job.id, error)
        await asyncio.sleep(DELAY_BETWEEN_JOBS_SECONDS)


async def run_cycle(bot: Bot, chat_id: str) -> None:
    """دورة فحص لكل المنصات (فشل منصة ما بيوقفش الباقي)."""
    for module in enabled_platforms():
        try:
            await check_platform(bot, chat_id, module)
        except Exception as error:
            logger.error("[%s] فشل الفحص: %s", module.LABEL, error)


async def main() -> None:
    token, chat_id = get_config()
    init_db()

    async with Bot(token=token) as bot:
        names = "، ".join(m.LABEL for m in enabled_platforms())
        await bot.send_message(chat_id=chat_id, text=f"🚀 بدأت مراقبة: {names}")

        while True:
            await run_cycle(bot, chat_id)
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت")
