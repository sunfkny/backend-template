from backend.utils.snowflake import InvalidSystemClockError, Snowflake

snowflake = Snowflake()


def get_goods_order_id():
    return f"G{snowflake.generate_id()}"
