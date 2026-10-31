"""مستقل: قسم البرمجة والتطوير."""
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from common import (
    MAX_DETAILS_LENGTH,
    Job,
    fetch_html,
    meta_description,
    page_lines,
    section_after,
    value_after,
)

PLATFORM = "mostaql"
LABEL = "مستقل"
# القسم نفسه برمجة، فمش محتاجين فلترة بالكلمات المفتاحية
FILTER_BY_KEYWORDS = False

BASE_URL = "https://mostaql.com"
LIST_URLS = ["https://mostaql.com/projects/development"]
JOB_PATH_PATTERN = re.compile(r"^/project/(\d+)")

DETAILS_HEADING = "تفاصيل المشروع"
STOP_LABELS = {
    "حالة المشروع",
    "تاريخ النشر",
    "الميزانية",
    "مدة التنفيذ",
    "المهارات",
    "صاحب المشروع",
    "تقدم للمشروع",
    "العروض المقدمة",
}


def parse_listing(html: str) -> list[Job]:
    """استخراج (id, title, link) من صفحة قائمة المشاريع."""
    soup = BeautifulSoup(html, "html.parser")
    jobs: dict[str, Job] = {}

    for anchor in soup.find_all("a", href=True):
        path = urlparse(anchor["href"]).path
        match = JOB_PATH_PATTERN.match(path)
        title = anchor.get_text(" ", strip=True)
        # نتجاهل الروابط اللي نصها مقتطف من التفاصيل مش العنوان
        if not match or not title or title.startswith(DETAILS_HEADING):
            continue

        job_id = match.group(1)
        if job_id not in jobs or len(title) > len(jobs[job_id].title):
            jobs[job_id] = Job(
                platform=PLATFORM,
                raw_id=job_id,
                title=title,
                link=urljoin(BASE_URL, path),
            )

    return list(jobs.values())


def fetch_jobs() -> list[Job]:
    jobs: dict[str, Job] = {}
    for url in LIST_URLS:
        for job in parse_listing(fetch_html(url)):
            jobs.setdefault(job.raw_id, job)
    return list(jobs.values())


def parse_details(html: str) -> dict[str, str]:
    """استخراج العنوان والميزانية والمدة والتفاصيل من صفحة المشروع."""
    lines = page_lines(html)
    details = section_after(lines, DETAILS_HEADING, STOP_LABELS) or meta_description(html)
    details = re.sub(rf"^{DETAILS_HEADING}\s*:?\s*", "", details).strip()

    duration = value_after(lines, "مدة التنفيذ")
    if duration.isdigit():  # مستقل بيحسب المدة بالأيام
        duration = f"{duration} {'يوم' if duration == '1' else 'أيام'}"

    h1 = BeautifulSoup(html, "html.parser").find("h1")
    return {
        "title": h1.get_text(" ", strip=True) if h1 else "",
        "details": details[:MAX_DETAILS_LENGTH],
        "budget": value_after(lines, "الميزانية"),
        "duration": duration,
    }


def enrich(job: Job) -> None:
    data = parse_details(fetch_html(job.link))
    if data["title"]:
        job.title = data["title"]
    job.details = data["details"]
    job.budget = data["budget"]
    job.duration = data["duration"]
