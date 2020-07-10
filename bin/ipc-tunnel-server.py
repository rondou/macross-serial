#!/usr/bin/env python

import asyncio
import concurrent.futures
import queue
import threading
from typing import Any

import ipcq


def serve(term_ev: threading.Event):
    qms: ipcq.QueueManagerServer
    with ipcq.QueueManagerServer(address=ipcq.Address.AUTO, authkey=ipcq.AuthKey.DEFAULT) as qms:
        print(f"Server address: {qms.address}")

        while not term_ev.is_set():
            try:
                item: Any = qms.get_queue().get(timeout=0.1)
                print(f"{item}")
            except queue.Empty:
                continue


async def main():
    term_ev: threading.Event = threading.Event()
    executor: concurrent.futures.ThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor()

    asyncio.ensure_future(asyncio.get_running_loop().run_in_executor(executor, serve, term_ev))

    # Gracefully shut down
    try:
        await asyncio.get_running_loop().create_future()
    except asyncio.CancelledError:
        term_ev.set()
        executor.shutdown()
        raise


if __name__ == '__main__':
    asyncio.run(main())
