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


def test_intword():
    test_cases_en = [
        (9.9, "9.9"),
        (999, "999"),
        (1000, "1K"),
        (1200, "1.2K"),
        (1230, "1.23K"),
        (1235, "1.24K"),
        (1000000, "1M"),
        (1200000, "1.2M"),
        (1230000, "1.23M"),
        (1235000, "1.24M"),
        (1000000000, "1B"),
        (1200000000, "1.2B"),
        (1230000000, "1.23B"),
        (1235000000, "1.24B"),
        (1000000000000, "1T"),
        (1200000000000, "1.2T"),
        (1230000000000, "1.23T"),
        (1235000000000, "1.24T"),
        (None, "0"),
        ("invalid", "invalid"),
    ]
    test_cases_zh_hans = [
        (9.9, "9.9"),
        (999, "999"),
        (10000, "1万"),
        (12000, "1.2万"),
        (12300, "1.23万"),
        (12350, "1.24万"),
        (100000000, "1亿"),
        (120000000, "1.2亿"),
        (123000000, "1.23亿"),
        (123500000, "1.24亿"),
        (1000000000000, "1兆"),
        (1200000000000, "1.2兆"),
        (1230000000000, "1.23兆"),
        (1235000000000, "1.24兆"),
        (10000000000000000, "1京"),
        (12000000000000000, "1.2京"),
        (12300000000000000, "1.23京"),
        (12350000000000000, "1.24京"),
    ]
    test_cases_zh_hant = [
        (9.9, "9.9"),
        (999, "999"),
        (10000, "1萬"),
        (12000, "1.2萬"),
        (12300, "1.23萬"),
        (12350, "1.24萬"),
        (100000000, "1億"),
        (120000000, "1.2億"),
        (123000000, "1.23億"),
        (123500000, "1.24億"),
        (1000000000000, "1兆"),
        (1200000000000, "1.2兆"),
        (1230000000000, "1.23兆"),
        (1235000000000, "1.24兆"),
        (10000000000000000, "1京"),
        (12000000000000000, "1.2京"),
        (12300000000000000, "1.23京"),
        (12350000000000000, "1.24京"),
    ]
    test_cases = {
        "en-us": test_cases_en,
        "zh-hans": test_cases_zh_hans,
        "zh-hant": test_cases_zh_hant,
    }
    for language, cases in test_cases.items():
        with translation.override(language):
            for value, expected in cases:
                result = intword(value, digits=2)
                assert result == expected, f"Failed for language={language}, value={value}: expected {expected}, got {result}"
