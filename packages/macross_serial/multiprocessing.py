import multiprocessing
import queue
from typing import Union

import ipcq

from .util import Singleton


class DummyQueueManagerClient(ipcq.QueueManagerClient):
    def get_queue(self, *args, **kwargs) -> 'DummyQueue':
        return DummyQueue()


class DummyQueue(queue.Queue):
    def put(self, *args, **kwargs):
        pass


class ProgressNotifier(metaclass=Singleton):
    def __init__(self, path: str):
        self.qmc: Union[DummyQueueManagerClient, ipcq.QueueManagerClient] = \
            ipcq.QueueManagerClient(path, authkey=ipcq.AuthKey.DEFAULT) if path else DummyQueueManagerClient(path)
        self.qmc.connect()

    def notify(self, progress: str):
        self.qmc.get_queue().put(progress)
