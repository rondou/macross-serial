import asyncio
import serial
import re
import io
import logging
import sys
from typing import Callable, List, Optional, Tuple

import aioserial

from .multiprocessing import ProgressNotifier


class StringIOQueue:

    def __init__(self, max_size: int):
        self.output = io.StringIO()
        self.max_size = max_size

    def clean(self):
        self.output.truncate(0)
        self.output.seek(0)

    def truncate_to_maxsize(self):
        if self.str_size() > self.max_size:
            pos = self.str_size() - self.max_size
            self.output.seek(pos)

            _last = self.output.readlines()
            self.clean()
            self.output.writelines(_last)

    def put(self, data: str):
        if len(data) > 0:
            self.output.write(data)
            self.truncate_to_maxsize()

    def str_size(self):
        return self.output.tell()


class AsyncSerial:

    def __init__(self, port: str, ipc_tunnel_address: str = ''):
        self.port: str = port
        self.baud: int = 115200
        self.serial_instance: aioserial.AioSerial = aioserial.AioSerial(self.port, self.baud)
        self.hooks: List[Tuple[Callable, str]] = []
        self.hook_repeat_count: int = 0

        self.load_buffer = StringIOQueue(4000)
        self.send_buffer = None

        self.progress_notifier: ProgressNotifier = ProgressNotifier(ipc_tunnel_address)

    @property
    def hooks(self) -> List[Tuple[Callable, str]]:
        return self.__hooks

    @hooks.setter
    def hooks(self, hooks: List[Tuple[Callable, str]]):
        self.__hooks = hooks

    def set_hook_repeat_count(self, count: int):
        self.hook_repeat_count = count

    def _read(self) -> str:
        try:
            data: str = self.serial_instance.read(self.serial_instance.in_waiting).decode(errors='ignore')
            return data
        except serial.SerialException as e:
            logging.getLogger(__package__).debug(e)

    def _write(self, data):
        try:
            n = self.serial_instance.write(data)
            if n == len(data):
                return  # Whole request satisfied

        except serial.SerialException as e:
            logging.getLogger(__package__).debug(e)

    def read_and_put_to_buffer(self) -> str:
        data: str = self._read()
        self.load_buffer.put(data=data)

        return data

    async def display_incomming_data(self):
        while True:
            data: str = self.read_and_put_to_buffer()
            print(data, end='')

            await asyncio.sleep(0.001)

    async def send_outgoing_data(self):
        while True:
            send_data = await self.send_buffer.get()
            self.send_buffer.task_done()

            data: str = self.read_and_put_to_buffer()
            print(data, end='')
            self.load_buffer.clean()

            self._write(send_data)
            await asyncio.sleep(0.001)

    async def execute_hooks(self):
        try:
            for invoke in self.hooks:
                progress_message: str = invoke[3] if len(invoke) > 3 else ''

                if len(invoke) > 2:
                    result = await asyncio.wait_for(invoke[0](invoke[1]), invoke[2])
                else:
                    result = await invoke[0](invoke[1])

                if progress_message:
                    rs = re.search(r'\\(\d+)', progress_message)
                    if rs and result:
                        g = int(rs.group(1))
                        progress_message = progress_message.replace("\\{}".format(g), result.group(g))
                    self.progress_notifier.notify(progress_message)
            while self.hook_repeat_count:
                for invoke in self.hooks:
                    if len(invoke) > 2:
                        await asyncio.wait_for(invoke[0](invoke[1]), invoke[2])
                    else:
                        await invoke[0](invoke[1])
                if self.hook_repeat_count > 0:
                    self.hook_repeat_count -= 1
        except asyncio.TimeoutError as e:
            logging.getLogger(__package__).exception(e)
            self.progress_notifier.notify('ERROR: TIMEOUT')
            raise
        except Exception as e:
            logging.getLogger(__package__).debug(e)
            self.progress_notifier.notify(f'ERROR: {type(e).__name__}: {e}')
            raise

    async def console(self):
        self.send_buffer = asyncio.Queue(loop=asyncio.get_running_loop())
        await asyncio.wait([
            self.display_incomming_data(),
            self.send_outgoing_data(),
            self.execute_hooks(),
        ], return_when=asyncio.FIRST_COMPLETED)
