from decimal import Decimal


def aggregate_decimal_quantize(value: dict | int | float | Decimal) -> Decimal:
    if isinstance(value, dict):
        value = sum(i for i in value.values() if isinstance(i, (int, float, Decimal)))
    if isinstance(value, (int, float)):
        value = Decimal(value)
    return value.quantize(Decimal("0.01"))


def chinese_format_number(num: float | Decimal):
    if not isinstance(num, (float, Decimal)):
        return ""
    if num == 0:
        return "0"
    if num >= 100000000:
        formatted_num = "{:.2f}".format(num / 100000000)
        suffix = "亿"
    elif num >= 10000:
        formatted_num = "{:.2f}".format(num / 10000)
        suffix = "万"
    else:
        formatted_num = "{:.2f}".format(num)
        suffix = ""
    if formatted_num.endswith(".00"):
        formatted_num = formatted_num[:-3]
    elif formatted_num.endswith("0"):
        formatted_num = formatted_num[:-1]
    return formatted_num + suffix
