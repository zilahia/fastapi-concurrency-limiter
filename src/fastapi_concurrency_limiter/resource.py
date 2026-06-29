import asyncio


class Resource:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._semaphore = asyncio.Semaphore(capacity)
