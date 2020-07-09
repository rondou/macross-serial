import multiprocessing
import multiprocessing.managers
from typing import List


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


if __name__ == '__main__':
    init_ipc_queue_manager_server()

    manager: QueueManager
    with QueueManager(authkey='macross_serial'.encode()) as manager:
        print(f"Server address: {manager.address}")
        while True:
            print(f"{manager.get_queue().get()}")


# Reference and Usage:
#   https://gist.github.com/changyuheng/89062d639e40110c61c2f88018a8b0e5
