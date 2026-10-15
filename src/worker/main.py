import asyncio

from faststream import FastStream

from events.broker import broker
from worker.relay import run_relay

app = FastStream(broker)


@app.after_startup
async def start_relay() -> None:
    global relay_task
    relay_task = asyncio.create_task(run_relay())


@app.on_shutdown
async def stop_relay() -> None:
    if relay_task is not None:
        relay_task.cancel()
