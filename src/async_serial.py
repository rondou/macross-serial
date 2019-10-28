# -*- coding: utf-8 -*-
import asyncio
import serial
import io

import aioserial

from typing import Optional, List, Callable


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

    def __init__(self, port: str):
        self.port: str = port
        self.baud: int = 115200
        self.serial_instance: aioserial.AioSerial = aioserial.AioSerial(self.port, self.baud)
        self.hooks: Optional[List[List[Callable, str]]] = None

        self.load_buffer = StringIOQueue(4000)
        self.send_buffer = None

    @property
    def hooks(self) -> Optional[List[Callable]]:
        return self.__hooks

    @hooks.setter
    def hooks(self, hooks: Optional[List[Callable]]):
        self.__hooks = hooks

    def _read(self) -> str:
        try:
            data: str = self.serial_instance.read(self.serial_instance.in_waiting).decode(errors='ignore')

        except serial.SerialException as e:
            print(e)

        return data

    def _write(self, data):
        try:
            n = self.serial_instance.write(data)
            if n == len(data):
                return  # Whole request satisfied

        except serial.SerialException as e:
            print(e)

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
            print("================================")
            print("send =====", send_data)
            print("================================")

            data: str = self.read_and_put_to_buffer()
            print(data, end='')
            self.load_buffer.clean()

            self._write(send_data)
            await asyncio.sleep(5)

    async def execute_hooks(self):
        while True:
            for invoke in self.hooks:
                await invoke[0](*invoke[1:])
                #await invoke()
            await asyncio.sleep(2)

    async def console(self):
        self.send_buffer = asyncio.Queue(loop=asyncio.get_running_loop())
        await asyncio.wait([
            self.display_incomming_data(),
            self.send_outgoing_data(),
            self.execute_hooks(),
        ])


if __name__ == '__main__':
    pass