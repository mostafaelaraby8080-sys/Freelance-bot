"""فحص المنصات الثلاثة: بيطبع هل الاتصال شغال وكام مشروع اتسحب (من غير إرسال ولا تسجيل)."""
import requests

from common import HEADERS
from main import ALL_PLATFORMS


def check(module) -> None:
    print(f"\n=== {module.LABEL} ===")
    html = ""
    for url in module.LIST_URLS:
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            html = response.text
            print(f"Status: {response.status_code} | حجم الصفحة: {len(html)}")
        except requests.RequestException as error:
            print(f"❌ فشل الاتصال: {error}")
            return

    try:
        jobs = module.fetch_jobs()
    except Exception as error:
        print(f"❌ فشل السحب: {error}")
        return

    print(f"عدد المشاريع المسحوبة: {len(jobs)}")
    if not jobs:
        path = f"debug_{module.PLATFORM}.html"
        with open(path, "w", encoding="utf-8") as file:
            file.write(html)
        print(f"⚠️ مفيش مشاريع. حفظت الصفحة في {path} للفحص")
        return

    for job in jobs[:2]:
        try:
            module.enrich(job)
        except Exception as error:
            print(f"(تعذر جلب التفاصيل: {error})")
        print(f"\n[{job.raw_id}] {job.title}")
        print(f"الرابط: {job.link}")
        print(f"الميزانية: {job.budget or '-'} | المدة: {job.duration or '-'}")
        print(f"التفاصيل: {job.details[:150] or '-'}")


if __name__ == "__main__":
    for platform_module in ALL_PLATFORMS.values():
        check(platform_module)
