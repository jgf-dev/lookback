import asyncio


class TimelineBroadcaster:
    def __init__(self, max_queue_size: int = 100) -> None:
        self._subscribers: set[asyncio.Queue[dict]] = set()
        self._max_queue_size = max_queue_size

    def subscribe(self) -> asyncio.Queue[dict]:
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=self._max_queue_size)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict]) -> None:
        self._subscribers.discard(queue)

    async def publish(self, event: dict) -> None:
        for subscriber in list(self._subscribers):
            try:
                subscriber.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest event for slow subscribers, then enqueue latest.
                _ = subscriber.get_nowait()
                subscriber.put_nowait(event)
