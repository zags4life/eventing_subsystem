# eventproducermeta.py

from abc import ABCMeta
from .event import Event, _Event

class EventProducerMeta(type):
    def __new__(cls, name, bases, state):
        events_to_create = []

        for member in state.values():
            meta_events = getattr(member, '__events__', None)
            if meta_events is not None:
                for event_metadata in meta_events:
                    events_to_create.append(event_metadata)

        klass = type.__new__(cls, name, bases, state)

        for event, types in events_to_create:
            attr = klass.__dict__.get(event, None)
            
            if not event in klass.__dict__.keys():
                setattr(klass, event, Event(types))
            elif not isinstance(attr, Event):
                raise AttributeError(
                    "Class {0} already defines attribute '{1}', but '{1}' " \
                    'is a {2}, not an event.'.format(klass.__name__, event, type(attr).__name__))
                
        return klass

class AbstractEventProducerMeta(ABCMeta, EventProducerMeta):
    pass

class EventProducer(object, metaclass=AbstractEventProducerMeta):
    pass