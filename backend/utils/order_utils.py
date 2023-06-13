from backend.utils.snowflake import Snowflake, InvalidSystemClock

snowflake = Snowflake()


def get_goods_order_id():
    return f"G{snowflake.generate_id()}"
