import multiprocessing
import multiprocessing.managers


class MyManager(multiprocessing.managers.BaseManager):
    pass


def get_queue():
    global q
    return q


q = multiprocessing.Queue()
MyManager.register('queue', get_queue)

if __name__ == '__main__':
    with MyManager(authkey='macross_serial'.encode()) as manager:
        print(f"Server address: {manager.address}")
        while True:
            print(f"{manager.queue().get()}")
