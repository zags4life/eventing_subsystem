# __main__.py

import inspect
import time

from abc import ABCMeta, abstractmethod
from .eventproducermeta import *
from .event import *

@event_producer
class BaseClass:
    @abstractmethod
    def do_more_work(self):
        pass

class OtherBaseClass:
    pass

class Foo(OtherBaseClass, BaseClass):
    on_update = Event(str)
    @event(name='on_update', signature=str)
    @event(name='on_call', signature=str)
    def __init__(self):
        pass

    def do_work(self):
        self.on_update('done')

    def do_more_work(self):
        self.on_update('really done', 'bad parameter')

    def __call__(self):
        self.on_call('asdfa')


if __name__ == '__main__':
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(name)-30s %(message)s'
    )
    count = [0]

    def callback(owner: object, name: str) -> None:
        count[0] += 1

    total_time = time.time()

    max_iterations = 50000 if __debug__ else 100000
    steps = 10000

    for event_count in range(steps, max_iterations+steps, steps):
        start_time = time.time()

        foo = Foo()

        for events in range(event_count):
            foo.on_update += callback

        foo.do_work()

        try:
            foo.do_more_work()
        except:
            pass
        else:
            raise AssertionError('Failed to throw exception for bad parameter')

        end_time = time.time() - start_time
        print(f"{event_count:>8} {end_time:,.5f}")
    print('Took {0:,.5f} secs'.format(time.time() - total_time))
