import asyncio

from faststream import FastStream

import worker.consumers  # noqa: F401
from events.broker import broker
from worker.expiration import run_expiration
from worker.relay import run_relay

app = FastStream(broker)

relay_task: asyncio.Task[None] | None = None
expiration_task: asyncio.Task[None] | None = None


@app.after_startup
async def start_background_tasks() -> None:
    global relay_task, expiration_task
    relay_task = asyncio.create_task(run_relay())
    expiration_task = asyncio.create_task(run_expiration())


@app.on_shutdown
async def stop_background_tasks() -> None:
    for task in (relay_task, expiration_task):
        if task is not None:
            task.cancel()
