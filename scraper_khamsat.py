"""خمسات: طلبات المجتمع (محاولة قدر الإمكان، الموقع محمي ضد الأدوات الآلية)."""
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from common import (
    MAX_DETAILS_LENGTH,
    Job,
    fetch_html,
    first_text_block_after_title,
    meta_description,
    page_lines,
    value_after,
)

PLATFORM = "khamsat"
LABEL = "خمسات"
FILTER_BY_KEYWORDS = True

BASE_URL = "https://khamsat.com"
LIST_URLS = [f"{BASE_URL}/community/requests"]
JOB_PATH_PATTERN = re.compile(r"^/community/requests/(\d+)")


def parse_listing(html: str) -> list[Job]:
    """استخراج (id, title, link) من صفحة طلبات المجتمع."""
    soup = BeautifulSoup(html, "html.parser")
    jobs: dict[str, Job] = {}

    for anchor in soup.find_all("a", href=True):
        path = urlparse(anchor["href"]).path
        match = JOB_PATH_PATTERN.match(path)
        title = anchor.get_text(" ", strip=True)
        if not match or not title:
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


def enrich(job: Job) -> None:
    html = fetch_html(job.link)
    lines = page_lines(html)
    details = meta_description(html) or first_text_block_after_title(html)
    job.details = details[:MAX_DETAILS_LENGTH]
    job.budget = value_after(lines, "الميزانية")
    job.duration = value_after(lines, "مدة التنفيذ")
