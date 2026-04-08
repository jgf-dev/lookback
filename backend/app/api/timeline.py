import asyncio


class TimelineBroadcaster:
    def __init__(self) -> None:
        """
        Initialize the TimelineBroadcaster and prepare its subscriber storage.
        
        Sets self._subscribers to an empty set of asyncio.Queue[dict] instances used to track active subscribers for event broadcasting.
        """
        self._subscribers: set[asyncio.Queue[dict]] = set()

    def subscribe(self) -> asyncio.Queue[dict]:
        """
        Create and register a new subscriber queue for timeline events.
        
        Returns:
            asyncio.Queue[dict]: A queue that will receive published event dictionaries.
        """
        queue: asyncio.Queue[dict] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict]) -> None:
        """
        Remove a subscriber queue from the broadcaster.
        
        Parameters:
            queue (asyncio.Queue[dict]): Subscriber queue to remove. If the queue is not registered, this is a no-op.
        """
        self._subscribers.discard(queue)

    async def publish(self, event: dict) -> None:
        """
        Broadcasts an event to all currently registered subscriber queues.
        
        Parameters:
            event (dict): The event payload to be enqueued to each subscriber's queue.
        """
        for subscriber in list(self._subscribers):
            await subscriber.put(event)
