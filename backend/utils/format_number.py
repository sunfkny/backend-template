from decimal import Decimal

from django.utils import translation


def aggregate_decimal_quantize(value: dict | int | float | Decimal, digits: int = 2) -> str:
    if isinstance(value, dict):
        value = sum(i for i in value.values() if isinstance(i, int | float | Decimal))
    return f"{value:.{digits}f}"


def intword(
    value: float | int | Decimal | str | None,
    digits: int = 2,
    use_chinese_units: bool = True,
) -> str:
    if not value:
        return "0"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    intword_suffix = ((3, "K"), (6, "M"), (9, "B"), (12, "T"))
    if use_chinese_units:
        current_language = translation.get_language()
        if current_language == "zh-hans":
            intword_suffix = ((4, "万"), (8, "亿"), (12, "兆"), (16, "京"))
        if current_language == "zh-hant":
            intword_suffix = ((4, "萬"), (8, "億"), (12, "兆"), (16, "京"))

    min_exponent = intword_suffix[0][0]
    format_str = f".{digits}f"
    abs_value = abs(value)
    formatted_num = f"{value:{format_str}}"
    suffix = ""

    if abs_value >= 10**min_exponent:
        for exponent, _suffix in reversed(intword_suffix):
            if abs_value >= 10**exponent:
                value = value / 10**exponent
                formatted_num = f"{value:{format_str}}"
                suffix = _suffix
                break

    if formatted_num.endswith(".00"):
        formatted_num = formatted_num[:-3]
    elif formatted_num.endswith("0"):
        formatted_num = formatted_num[:-1]
    return formatted_num + suffix
