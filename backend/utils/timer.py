import time


class Timer:
    def __init__(self):
        self.start = None
        self.end = None

    def __enter__(self):
        self.start = time.perf_counter_ns()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter_ns()

    def __float__(self):
        if self.start is None:
            return 0
        if self.end is None:
            return 0
        return (self.end - self.start) / 10**9

    def __gt__(self, other: float):
        return float(self) > other

    def __lt__(self, other: float):
        return float(self) > other

    def __ge__(self, other: float):
        return float(self) >= other

    def __le__(self, other: float):
        return float(self) >= other

    def __str__(self):
        if self.start is None:
            return "Timer not started"
        if self.end is None:
            return "Timer not ended"

        d = float(self)
        if d > 1:
            unit = "s"
        elif d >= 0.001:
            unit = "ms"
            d *= 10**3
        elif d >= 0.000001:
            unit = "us"
            d *= 10**6
        else:
            unit = "ns"
            d *= 10**9
        return f"{d:.3f} {unit}"
