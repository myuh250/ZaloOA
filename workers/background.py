import asyncio


class BackgroundTaskManager:
    """Thin wrapper around asyncio to allow DI and future swapping to a queue."""

    def run(self, coro_func, *args, **kwargs):
        asyncio.create_task(coro_func(*args, **kwargs))


