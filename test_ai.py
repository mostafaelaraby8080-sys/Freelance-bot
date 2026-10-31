import sys

from ai_writer import generate_proposal, get_client


def list_models() -> None:
    """عرض موديلات flash المتاحة لمفتاحك."""
    for model in get_client().models.list():
        if "flash" in model.name:
            print(model.name)


def main() -> None:
    title = "تصميم وبرمجة موقع لمطعم مع نظام طلب أونلاين"
    details = (
        "أحتاج موقع لمطعم يعرض المنيو بالصور ويسمح للعميل بطلب الوجبات "
        "وإرسال الطلب على واتساب، والموقع لازم يكون سريع ومتوافق مع الموبايل."
    )
    print(generate_proposal(title, details))


if __name__ == "__main__":
    if sys.argv[1:] == ["models"]:
        list_models()
    else:
        main()