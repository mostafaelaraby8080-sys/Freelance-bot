"""فحص صفحة طلب واحدة من خمسات لمعرفة مكان التفاصيل (للتشخيص فقط)."""
import json
import re

from bs4 import BeautifulSoup

from common import fetch_html
import scraper_khamsat as khamsat


def main() -> None:
    jobs = khamsat.fetch_jobs()
    if not jobs:
        print("مفيش طلبات اتسحبت")
        return

    job = jobs[0]
    html = fetch_html(job.link)
    with open("debug_khamsat_detail.html", "w", encoding="utf-8") as file:
        file.write(html)

    soup = BeautifulSoup(html, "html.parser")
    print("الطلب:", job.title)
    print("حجم الصفحة:", len(html))
    print("title:", soup.title.get_text(strip=True) if soup.title else None)
    h1 = soup.find("h1")
    print("h1:", h1.get_text(" ", strip=True)[:100] if h1 else None)

    print("\nmeta tags:")
    for tag in soup.find_all("meta"):
        key = tag.get("property") or tag.get("name")
        if key and ("description" in key or "title" in key):
            print(f"  {key} = {(tag.get('content') or '')[:100]!r}")

    print("\nJSON-LD:", len(soup.find_all("script", type="application/ld+json")))

    print("\nأطول 12 فقرة نصية في الصفحة:")
    blocks = []
    for element in soup.find_all(["p", "div", "article", "section"]):
        if element.find(["p", "div", "ul", "table", "article", "section"]):
            continue
        text = re.sub(r"\s+", " ", element.get_text(" ", strip=True))
        if len(text) >= 30:
            blocks.append((len(text), element.name, " ".join(element.get("class", [])), text))
    for length, name, classes, text in sorted(blocks, reverse=True)[:12]:
        print(f"  [{name}.{classes[:40]}] {length} حرف: {text[:90]}")


if __name__ == "__main__":
    main()
