# -*- coding: utf-8 -*-
import json
import re
import csv
import asyncio
from json import JSONDecodeError
from typing import Optional, List, Callable, Pattern

from .tsv_parser import get_tsv_files_path
from .async_serial import AsyncSerial


class SerialValidator:

    def __init__(self, port, script_path):
        script: list = SerialValidator.parser_script(script_path=script_path)

        self.serial_instance: AsyncSerial = AsyncSerial(port)
        self.script_to_func_generator(script=script)

    @staticmethod
    def translate_parameter(parameter: list):
        translated = []

        for p in parameter:
            sub = None
            if p[0] == 'send':
                sub = [p[0], str.encode(p[1][1:-1].encode().decode('unicode_escape'))]
            elif p[0] == 'wait_for_str':
                sub = [p[0], str(p[1][1:-1].encode().decode('unicode_escape'))]
            elif p[0] == 'wait_for_regex':
                sub = [p[0], re.compile(r'{}'.format(p[1][2:-1]))]
            elif p[0] == 'wait_for_json':
                sub = [p[0], str(p[1][1:-1].encode().decode('unicode_escape'))]
            elif p[0] == 'wait_for_time':
                sub = [p[0], int(p[1])]
            else:
                pass

            # append Timeout if exist
            if len(p) >= 3:
                sub.append(int(p[2]))
            else:
                sub.append(180)  # Time out default 3 minute

            translated.append(sub)

        return translated

    @staticmethod
    def parser_script(script_path: str = None) -> list:
        path = script_path if script_path else get_tsv_files_path()[0]

        with open(path) as tf:
            reader = list(csv.reader(tf, delimiter='\t'))
            if reader[0][0] == 'ACTION' and reader[0][1] == 'CONTENT':
                return SerialValidator.translate_parameter(reader[1:])

        return None

    def script_to_func_generator(self, script: list):
        hooks = []

        for i in script:
            if i[0] == 'wait_for_str':
                hooks.append([self.wait_for_string, *i[1:]])

            elif i[0] == 'wait_for_regex':
                hooks.append([self.wait_for_regex, *i[1:]])

            elif i[0] == 'send':
                hooks.append([self.send_command, *i[1:]])

            elif i[0] == 'wait_for_json':
                hooks.append([self.wait_for_json, *i[1:]])

            elif i[0] == 'wait_for_time':
                hooks.append([self.wait_for_time, *i[1:]])

        self.serial_instance.hooks = hooks

    async def nothing(self):
        return False

    async def contains_regex(self, regex: Pattern):
        return SerialValidator.contains(text=self.serial_instance.load_buffer.output.getvalue(), regex=regex)

    async def contains_string(self, mesg: str):
        return mesg in self.serial_instance.load_buffer.output.getvalue()

    @staticmethod
    async def contains_json(text: str, scheme: dict, regex: Pattern=re.compile(r'^\s*\{.*\}\s*$')):
        for line in text.splitlines():
            if SerialValidator.contains(text=line, regex=regex):
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
                            if not SerialValidator.contains(text=json_value[key], regex=re.compile(scheme[key].get('regex', r'.*'))):
                                return False

                    return True
                except Exception as e:
                    continue

        return False

    async def wait_for_time(self, *args):
        return await SerialValidator.wait_for(lambda: self.nothing(), n_retry=args[0])

    async def wait_for_regex(self, *args):
        return await SerialValidator.wait_for(lambda: self.contains_regex(re.compile(args[0])), n_retry=args[1])

    async def wait_for_string(self, *args):
        return await SerialValidator.wait_for(lambda: self.contains_string(args[0]), n_retry=args[1])

    async def wait_for_json(self, *args, regex: str=r'^\s*\{.*\}\s*$'):
        try:
            return await SerialValidator.wait_for(lambda: SerialValidator.contains_json(
                self.serial_instance.load_buffer.output.getvalue(),
                json.loads(args[0]),
                re.compile(regex)), n_retry=args[1])
        except JSONDecodeError:
            return False

    async def send_command(self, *args):
        await self.serial_instance.send_buffer.put(args[0])
        await self.serial_instance.send_buffer.join()

    @staticmethod
    def contains(text: str, regex: Pattern) -> bool:
        print("\n======= text ======== ")
        print(text)
        print("======= end  ========")
        for line in text.splitlines():
            if bool(regex.search(line)):
                return True
        return False

    @staticmethod
    async def wait_for(predict: Callable, n_retry: int = -1, seconds: int = 1):
        result: bool = False

        while True:
            if n_retry == 0:
                break

            if await predict():
                print("get string !!!")
                result = True
                break
            else:
                await asyncio.sleep(seconds)

            if n_retry > 0:
                n_retry -= 1

        return result

    async def validate(self):
        await self.serial_instance.console()


def main() -> int:
    serial_validator = SerialValidator(port='/dev/cu.usbserial')
    serial_console_future: asyncio.Future = asyncio.ensure_future(serial_validator.validate())

    ret: int = 0

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(serial_console_future)
        loop.close()
    except Exception as e:
        print(e)
        ret = 1

    return ret


if __name__ == '__main__':
    main()
