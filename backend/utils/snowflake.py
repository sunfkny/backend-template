import os
import time
import uuid
from typing import Optional


class InvalidSystemClock(Exception):
    """
    时钟回拨异常
    """

    pass


class Snowflake:
    # 64位ID的划分
    WORKER_ID_BITS = 5
    DATACENTER_ID_BITS = 5
    SEQUENCE_BITS = 12

    # 最大取值计算
    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1
    MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1

    # 移位偏移计算
    WOKER_ID_SHIFT = SEQUENCE_BITS
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

    # 序号循环掩码
    SEQUENCE_MASK = (1 << SEQUENCE_BITS) - 1

    # Twitter元年时间戳
    TWEPOCH = 1288834974657

    def __init__(self, datacenter_id: Optional[int] = None, worker_id: Optional[int] = None):
        if worker_id is None:
            worker_id = os.getpid() % (2**self.WORKER_ID_BITS)
        if datacenter_id is None:
            datacenter_id = uuid.getnode() % (2**self.DATACENTER_ID_BITS)

        if worker_id > self.MAX_WORKER_ID or worker_id < 0:
            raise ValueError(f"Worker ID can't be greater than {self.MAX_WORKER_ID} or less than 0")

        if datacenter_id > self.MAX_DATACENTER_ID or datacenter_id < 0:
            raise ValueError(f"Data center ID can't be greater than {self.MAX_DATACENTER_ID} or less than 0")

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = 0
        self.last_timestamp = -1  # 上次计算的时间戳

    def timestamp_ms(self):
        """整数毫秒时间戳"""
        return int(time.time() * 1000)

    def generate_id(self):
        """获取新ID"""
        timestamp = self.timestamp_ms()

        # 时钟回拨
        if timestamp < self.last_timestamp:
            raise InvalidSystemClock(f"Clock is moving backwards, rejecting requests until {self.last_timestamp}")

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.SEQUENCE_MASK
            if self.sequence == 0:
                timestamp = self.till_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        new_id = (
            ((timestamp - self.TWEPOCH) << self.TIMESTAMP_LEFT_SHIFT)
            | (self.datacenter_id << self.DATACENTER_ID_SHIFT)
            | (self.worker_id << self.WOKER_ID_SHIFT)
            | self.sequence
        )
        return new_id

    def till_next_millis(self, last_timestamp: int):
        """
        等到下一毫秒
        """
        timestamp = self.timestamp_ms()
        while timestamp <= last_timestamp:
            timestamp = self.timestamp_ms()
        return timestamp
