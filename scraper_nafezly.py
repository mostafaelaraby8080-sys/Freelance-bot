"""نفذلي: القراءة من قناة تيليجرام العامة (بدون حظر)."""
import re

from bs4 import BeautifulSoup

from common import MAX_DETAILS_LENGTH, Job, fetch_html

PLATFORM = "nafezly"
LABEL = "نفذلي"
FILTER_BY_KEYWORDS = True

BASE_URL = "https://nafezly.com"
CHANNEL_URL = "https://t.me/s/Nafezly"
LIST_URLS = [CHANNEL_URL]

JOB_PATH_PATTERN = re.compile(r"/project/(\d+)")
TITLE_PATTERN = re.compile(r"عنوان المشروع\s*:\s*(.*?)\s*تفاصيل المشروع\s*:")
DETAILS_PATTERN = re.compile(
    r"تفاصيل المشروع\s*:\s*(.*?)"
    r"(?:\s*الميزانية\s*:|\s*مدة التنفيذ\s*:|\s*رابط المشروع\s*:|$)"
)
BUDGET_PATTERN = re.compile(
    r"الميزانية\s*:\s*(.*?)(?:\s*مدة التنفيذ\s*:|\s*رابط المشروع\s*:|$)"
)
DURATION_PATTERN = re.compile(r"مدة التنفيذ\s*:\s*(.*?)(?:\s*رابط المشروع\s*:|$)")


def _first_group(pattern: re.Pattern, text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def parse_jobs(html: str) -> list[Job]:
    """استخراج المشاريع من منشورات القناة."""
    soup = BeautifulSoup(html, "html.parser")
    jobs: dict[str, Job] = {}

    for message in soup.select(".tgme_widget_message_wrap"):
        text_element = message.select_one(".tgme_widget_message_text")
        if not text_element:
            continue
        text = text_element.get_text(" ", strip=True)

        job_id, link = None, None
        for anchor in message.select("a[href]"):
            href = anchor.get("href", "")
            match = JOB_PATH_PATTERN.search(href)
            if match:
                job_id, link = match.group(1), href
                break

        if not job_id:
            match = JOB_PATH_PATTERN.search(text)
            if not match:
                continue
            job_id = match.group(1)
            link = f"{BASE_URL}/project/{job_id}"

        title = _first_group(TITLE_PATTERN, text)
        if not title:
            continue

        jobs[job_id] = Job(
            platform=PLATFORM,
            raw_id=job_id,
            title=title,
            link=link,
            details=_first_group(DETAILS_PATTERN, text)[:MAX_DETAILS_LENGTH],
            budget=_first_group(BUDGET_PATTERN, text),
            duration=_first_group(DURATION_PATTERN, text),
        )

    return list(jobs.values())


def fetch_jobs() -> list[Job]:
    return parse_jobs(fetch_html(CHANNEL_URL))


def enrich(job: Job) -> None:
    """تفاصيل المنشور كاملة في القناة أصلاً، فمفيش حاجة إضافية نجيبها."""
    return None
