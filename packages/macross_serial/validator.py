import asyncio
import csv
import json
import logging
import re
from typing import Callable, Pattern

from .async_serial import AsyncSerial


class SerialValidator:

    def __init__(self, port, script_path, repeat_count, ipc_tunnel_address: str = ''):
        script: list = self.parse_script(script_path=script_path)
        self.serial_instance: AsyncSerial = AsyncSerial(port, ipc_tunnel_address)
        self.serial_instance.set_hook_repeat_count(repeat_count)

        self.script_to_func_generator(script=script)

    @classmethod
    def translate_parameter(cls, parameter: list):
        translated = []

        for p in parameter:
            row = []
            if not len(p) or p[0].startswith('#'):
                continue

            if p[0] == 'send':
                row = [p[0], str.encode(p[1][1:-1].encode().decode('unicode_escape'))]
            elif p[0] == 'wait_for_str':
                row = [p[0], str(p[1][1:-1].encode().decode('unicode_escape'))]
            elif p[0] == 'wait_for_regex':
                row = [p[0], re.compile(r'{}'.format(p[1][2:-1]))]
            elif p[0] == 'wait_for_json':
                row = [p[0], str(p[1][1:-1].encode().decode('unicode_escape'))]
            elif p[0] == 'wait_for_second':
                row = [p[0], float(p[1])]
            else:
                pass
            if row:
                if len(p) > 2:
                    row.append(float(p[2]))
                if len(p) > 3:
                    row.append(p[3])
                translated.append(row)

        return translated

    def parse_script(self, script_path: str = None) -> list:
        with open(script_path) as tf:
            return self.translate_parameter(list(csv.reader(tf, delimiter='\t')))

    def script_to_func_generator(self, script: list):
        hooks = []

        for i in script:
            hook = [getattr(self, i[0]), i[1]]
            if len(i) > 2:
                hook.append(i[2])
            if len(i) > 3:
                hook.append(i[3])
            hooks.append(hook)

        self.serial_instance.hooks = hooks

    async def contains_regex(self, regex: Pattern):
        return self.contains(text=self.serial_instance.load_buffer.output.getvalue(), regex=regex)

    async def contains_string(self, mesg: str):
        return mesg if mesg in self.serial_instance.load_buffer.output.getvalue() else ''

    # TODO: Refine
    async def contains_json(self, text: str, scheme: dict, regex: Pattern = re.compile(r'^\s*{.*}\s*$')):
        for line in text.splitlines():
            if self.contains(text=line, regex=regex):
                try:
                    json_value = json.loads(line.strip())

                    for key in scheme.keys():
                        if scheme[key]['type'] == 'int':
                            if type(json_value[key]) != int:
                                return False
                        elif scheme[key]['type'] == 'float':
                            if type(json_value[key]) != float:
                                return False
                        elif scheme[key]['type'] == 'bool':
                            if type(json_value[key]) != bool:
                                return False
                        elif scheme[key]['type'] == 'str':
                            if type(json_value[key]) != str:
                                return False
                            if not self.contains(
                                    text=json_value[key], regex=re.compile(scheme[key].get('regex', r'.*'))):
                                return False

                    return json_value
                except Exception as e:
                    logging.getLogger(__package__).debug(e)

        return False

    async def wait_for_regex(self, regex: str):
        return await self.wait_for(lambda: self.contains_regex(re.compile(regex)))

    async def wait_for_str(self, mesg: str):
        return await self.wait_for(lambda: self.contains_string(mesg))

    # TODO: Refine
    async def wait_for_json(self, scheme: str, regex: str = r'^\s*\{.*\}\s*$'):
        try:
            return await self.wait_for(
                    lambda: self.contains_json(
                        self.serial_instance.load_buffer.output.getvalue(),
                        json.loads(scheme),
                        re.compile(regex)),
                    n_retry=180)
        except json.JSONDecodeError:
            pass

    @classmethod
    async def wait_for_second(cls, second: float):
        await asyncio.sleep(second)

    async def send(self, command: str):
        await self.serial_instance.send_buffer.put(command)
        await self.serial_instance.send_buffer.join()

    @staticmethod
    def contains(text: str, regex: Pattern):
        for line in text.splitlines():
            rs = regex.search(line)
            if bool(rs):
                return rs

    @staticmethod
    async def wait_for(predict: Callable, n_retry: int = -1, seconds: float = 0.01):
        content = None

        while n_retry:
            content = await predict()
            if content:
                break
            else:
                await asyncio.sleep(seconds)

            if n_retry > 0:
                n_retry -= 1

        return content

    async def validate(self):
        await self.serial_instance.console()
