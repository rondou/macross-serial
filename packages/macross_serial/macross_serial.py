import asyncio
import importlib.metadata
import logging
import os
import sys

import plumbum.cli

from .validator import SerialValidator


class Macross(plumbum.cli.Application):
    """The Serial Console Program"""

    PROGNAME: str = 'macross-serial'
    VERSION: str = importlib.metadata.version('macross-serial')

    _debug: bool = False

    @plumbum.cli.switch(["-d", "--debug"])
    def set_debug(self):
        """Enable debug"""
        self._debug = True

    def main(self, *args):
        if self._debug:
            logging.getLogger(__package__).setLevel(logging.DEBUG)


@Macross.subcommand('run')
class MacrossRunScript(plumbum.cli.Application):

    _repeat_count: int = 0

    @plumbum.cli.switch('--repeat', int)
    def set_repeat_count(self, count):
        """set repeat times"""
        self._repeat_count = count

    def main(self, port, script_file, ipc_tunnel_address: str = ''):
        serial_validator = SerialValidator(
            port=port, script_path=script_file, repeat_count=self._repeat_count, ipc_tunnel_address=ipc_tunnel_address)

        try:
            asyncio.run(serial_validator.validate())
        except Exception as e:
            logging.getLogger(__package__).debug(e)
            return 1


@Macross.subcommand('list-port')
class MacrossListPort(plumbum.cli.Application):
    """List serial port name"""

    def main(self):
        if os.name == 'nt':  # sys.platform == 'win32':
            from serial.tools.list_ports_windows import comports
        elif os.name == 'posix':
            from serial.tools.list_ports_posix import comports
        else:
            raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))

        for info in comports():
            print(info.device)


def main() -> int:
    return Macross.run()


if __name__ == '__main__':
    sys.exit(main())
