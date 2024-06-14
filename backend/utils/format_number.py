from decimal import Decimal


def aggregate_decimal_quantize(value: dict | int | float | Decimal, digits: int = 2) -> str:
    if isinstance(value, dict):
        value = sum(i for i in value.values() if isinstance(i, int | float | Decimal))
    if isinstance(value, int | float):
        value = Decimal(value)
    return f"{value:.{digits}f}"


def intword(
    value: float | int | Decimal | str | None,
    digits: int = 1,
    comma: bool = False,
    chinese: bool = False,
) -> str:
    if not value:
        return "0"

    if chinese:
        intword_suffix = ((3, "K"), (6, "M"), (9, "B"), (12, "T"))
        max_exponent = intword_suffix[0][0]
        min_exponent = intword_suffix[-1][0]
        max_suffix = intword_suffix[-1][1]
    else:
        intword_suffix = ((4, "万"), (8, "亿"), (12, "兆"), (16, "京"))
        max_exponent = intword_suffix[0][0]
        min_exponent = intword_suffix[-1][0]
        max_suffix = intword_suffix[-1][1]

    if comma:
        format_str = f",.{digits}f"
    else:
        format_str = f".{digits}f"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    abs_value = abs(value)

    if abs_value < 10**min_exponent:
        return f"{value:{format_str}}"

    if abs_value > 10**max_exponent:
        value = value / 10**max_exponent
        return f"{value:{format_str}}{max_suffix}"

    for exponent, suffix in reversed(intword_suffix):
        if abs_value >= 10**exponent:
            value = value / 10**exponent
            return f"{value:{format_str}}{suffix}"

    return str(value)
