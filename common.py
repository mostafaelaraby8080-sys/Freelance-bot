"""أدوات مشتركة بين كل المنصات: نموذج المشروع + تحميل الصفحات + استخراج النصوص."""
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.8",
}
REQUEST_TIMEOUT = 20
MAX_DETAILS_LENGTH = 1500


@dataclass
class Job:
    platform: str  # nafezly / mostaql / khamsat
    raw_id: str
    title: str
    link: str
    details: str = ""
    budget: str = ""
    duration: str = ""

    @property
    def id(self) -> str:
        """المعرّف الفريد داخل قاعدة البيانات (مع اسم المنصة لمنع التعارض)."""
        return f"{self.platform}:{self.raw_id}"


def fetch_html(url: str) -> str:
    """تحميل صفحة وإرجاع الـ HTML."""
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def page_lines(html: str) -> list[str]:
    """نص الصفحة كسطور نظيفة (بدون scripts و styles)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]


UNITS = {"يوم", "أيام", "يوماً", "يومًا", "أسبوع", "أسابيع", "شهر", "شهور", "أشهر", "ساعة", "ساعات"}


def value_after(lines: list[str], label: str) -> str:
    """القيمة اللي بعد عنوان معين (مثلاً: الميزانية ← $50 - $100)."""
    for index, line in enumerate(lines[:-1]):
        if line != label:
            continue
        value = lines[index + 1]
        # لو القيمة رقم والوحدة في السطر اللي بعده (20 ← أيام) نضمهم
        if value.isdigit() and index + 2 < len(lines):
            if lines[index + 2].split()[0] in UNITS:
                value = f"{value} {lines[index + 2]}"
        return value
    return ""


def section_after(lines: list[str], heading: str, stop_labels: set[str]) -> str:
    """نص القسم اللي تحت عنوان معين لحد أول عنوان من stop_labels."""
    for index, line in enumerate(lines):
        if line != heading:
            continue
        collected = []
        for next_line in lines[index + 1 :]:
            if next_line in stop_labels:
                break
            collected.append(next_line)
        if collected:
            return "\n".join(collected)
    return ""


def meta_description(html: str) -> str:
    """وصف الصفحة من meta (احتياطي لو فشل استخراج التفاصيل)."""
    soup = BeautifulSoup(html, "html.parser")
    for attrs in ({"property": "og:description"}, {"name": "description"}):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def first_text_block_after_title(html: str, min_len: int = 40) -> str:
    """احتياطي: أول فقرة نصية طويلة بعد العنوان الرئيسي (h1) في الصفحة."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    start = soup.find("h1")
    candidates = start.find_all_next(["p", "div"]) if start else soup.find_all(["p", "div"])
    for element in candidates:
        if element.find(["p", "div", "ul", "table"]):
            continue  # مش فقرة نهائية (جواها عناصر تانية)
        text = element.get_text(" ", strip=True)
        if len(text) >= min_len:
            return text
    return ""
