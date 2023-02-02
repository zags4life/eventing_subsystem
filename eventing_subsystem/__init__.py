''' eventing/__init__.py

Enables a consumer / producer model, where consumers can register a
callable method with the producer and the producer will signal, or raise
the event, invoking each callback method registered with the Event.

This class is thread safe.

Example:
from eventing_subsystem import event, EventProducer

class Producer(EventProducer):
    @event(name='on_work_complete', signature=str)
    def do_work_then_raise_event(self):
        external_param = 'foo'

        self.on_work_complete(external_param)

class Consumer(object):
    def __init__(self):
        self.producer = Producer()

        # Register event callback
        self.producer.on_work_complete += self.on_work_complete

    def do_work(self):
        self.producer.do_work_then_raise_event()

    def on_work_complete(self, owner, event_param):
        print('Producer raised event {}'.format(event_param))

        # Unregister the event (this is optional)
        self.producer.on_work_complete -= self.on_work_complete

if __name__ == '__main__':
    consumer = Consumer()

    consumer.do_work()
'''

import logging
LOGGER = logging.getLogger(__name__)

from .event import event, Event
from .eventerrors import EventError
from .eventproducermeta import (
    AbstractEventProducerMeta,
    EventProducerMeta,
    EventProducer,
)

__all__ = ['event', 'Event', 
    'EventProducer', 
    'EventProducerMeta', 
    'AbstractEventProducerMeta',
    'EventError']