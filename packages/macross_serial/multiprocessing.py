import multiprocessing.managers
from typing import Union

from .util import Singleton


class IPCManager(multiprocessing.managers.BaseManager):
    pass


IPCManager.register('queue')


class DummyIPCManager(multiprocessing.managers.BaseManager):
    def connect(self):
        pass

    def queue(self):
        class DummyQueue:
            def put(self, progress: str):
                print(progress)
                pass
        return DummyQueue()


class ProgressNotifier(metaclass=Singleton):
    def __init__(self, path: str):
        self.ipc_manager: Union[DummyIPCManager, IPCManager] = \
            IPCManager(path, authkey=__package__.encode()) if path else DummyIPCManager(path)
        self.ipc_manager.connect()

    def notify(self, progress: str):
        self.ipc_manager.queue().put(progress)
