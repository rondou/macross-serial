import multiprocessing
import multiprocessing.managers
from typing import List, Union

from .util import Singleton


# Reference
#   https://gist.github.com/changyuheng/89062d639e40110c61c2f88018a8b0e5
q: List[multiprocessing.Queue] = list()


class QueueManager(multiprocessing.managers.BaseManager):

    def get_queue(self) -> multiprocessing.Queue:
        pass


delattr(QueueManager, 'get_queue')


def get_queue() -> multiprocessing.Queue:
    global q
    if not q:
        q.append(multiprocessing.Queue())
    return q[0]


def init_ipc_queue_manager_client():
    if not hasattr(QueueManager, 'get_queue'):
        QueueManager.register('get_queue')


def init_ipc_queue_manager_server():
    if not hasattr(QueueManager, 'get_queue'):
        QueueManager.register('get_queue', get_queue)


class DummyQueueManager(multiprocessing.managers.BaseManager):
    def connect(self):
        pass

    def get_queue(self):
        class DummyQueue:
            def put(self, progress: str):
                pass
        return DummyQueue()


class ProgressNotifier(metaclass=Singleton):
    def __init__(self, path: str):
        init_ipc_queue_manager_client()
        self.ipc_queue_manager_client: Union[DummyQueueManager, QueueManager] = \
            QueueManager(path, authkey=__package__.encode()) if path else DummyQueueManager(path)
        self.ipc_queue_manager_client.connect()

    def notify(self, progress: str):
        self.ipc_queue_manager_client.get_queue().put(progress)
