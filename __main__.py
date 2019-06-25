# __main__.py

import inspect
import logging

from .eventproducermeta import *
from .event import *

class Foo(EventProducer):
    on_update = Event(str)

    def __init__(self):
        pass

    @event(name='on_update', signature=str)
    def do_work(self):
        self.on_update('done')

    @event(name='on_update', signature=str)
    def do_more_work(self):
        self.on_update('really done')

    @event(name='on_call', signature=str)
    def __call__(self):
        self.on_call('asdfa')

if __name__ == '__main__':
    from datetime import datetime
    count = [0]

    def callback(owner: object, name: str) -> None:
        count[0] += 1

    total_time = datetime.now()
    
    max_iterations = 100000
    steps = 10000
    
    for event_count in range(steps, max_iterations+steps, steps):
        start_time = datetime.now()
        foo = Foo()


        for events in range(event_count):
            foo.on_update += callback

        # for event in range(event_count):
        foo.do_work()
        
        print((datetime.now() - start_time).total_seconds())

    print('Took {0} secs'.format(datetime.now() - total_time))
