# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import pkg_resources

from plumbum import cli

from .validator import SerialValidator


class Macross(cli.Application):
    """The Serial Console Program"""

    PROGNAME: str = 'macross-serial'
    VERSION: str = pkg_resources.require('macross-serial')[0].version
    #VERSION: str = "0.0.1"


@Macross.subcommand('run')
class MacrossRunScript(cli.Application):
    _port: str = None
    _script_path: str = None

    @cli.switch('--port', str)
    def set_port(self, port):
        """set serial port name"""
        self._port = port

    @cli.switch('--script', str)
    def set_script(self, script_path):
        """set serial script path"""
        self._script_path = script_path

    def main(self):
        print('run script')
        serial_validator = SerialValidator(port=self._port, script_path=self._script_path)

        try:
            asyncio.run(serial_validator.validate())

        except Exception as e:
            print(e)


@Macross.subcommand('listport')
class MacrossListPort(cli.Application):
    """List serial port name"""

    def main(self):
        print('list port')
        if os.name == 'nt':  # sys.platform == 'win32':
            from serial.tools.list_ports_windows import comports
        elif os.name == 'posix':
            from serial.tools.list_ports_posix import comports
        #~ elif os.name == 'java':
        else:
            raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))

        for info in comports():
            port, desc, hwid = info
            print(port)


def main() -> int:
    Macross.run()


if __name__ == '__main__':
    sys.exit(main())
