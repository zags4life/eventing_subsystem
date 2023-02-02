# eventproducermeta.py

from abc import ABCMeta
import inspect

from . import LOGGER as logger
from .event import Event, EVENTS_FUNC_ATTR

class EventProducerMeta(type):
    '''Eventing subsystem metaclass required for the @event decorator'''
    def __new__(cls, name, bases, state):
        # Create a dictionary of events to create, where the key is the event
        # name and the value is the callback signature
        events_to_create = {}

        # Iterate through all members and create a list of all events that
        # have been registered via the @event decorator.
        for member in state.values():
            # If the member contains EVENTS_FUNC_ATTR, then add the
            # events from EVENTS_FUNC_ATTR to our list of events to create.
            meta_events = getattr(member, EVENTS_FUNC_ATTR, None)
            if meta_events is not None:
                # EVENTS_FUNC_ATTR is a list; iterate through all event metadata
                for event_name, event_signature in meta_events:
                    if event_name not in events_to_create:
                        events_to_create[event_name] = event_signature
                    elif event_name not in events_to_create and not events_to_create[event_name]:
                        events_to_create[event_name] = event_signature
                    else:
                        if not isinstance(events_to_create[event_name], tuple):
                            events_to_create[event_name] = (events_to_create[event_name],)
                        if not isinstance(event_signature, tuple):
                            event_signature = (event_signature,)

                        if events_to_create[event_name] != event_signature:
                            logger.warning(
                                f'{name}.{event_name} already defined with ' \
                                f'signature {events_to_create[event_name]}.  ' \
                                f'Cannot redefine {name}.{event_name} with signature ' \
                                f'{event_signature}'
                            )

        # Before creating the Event objects, we need to create the class.
        klass = type.__new__(cls, name, bases, state)

        # Iterate through the dictionary of events to create.
        for event, types in events_to_create.items():
            # Check to see if the class already contains a class attribute with
            # the same name as the event we are about to create.  If not,
            # create the Event as a class attribute.
            if not event in klass.__dict__.keys():
                setattr(klass, event, Event(types))
            else:
                # The class already contains an attribute with the same name
                # the event.  Verify the class attribute is of type Event,
                # otherwise, raise an exception.
                #
                # NB: The Event class is a class descriptor and calling
                #     getattr will invoke Event.__get__, which will create
                #     an underlying _Event object unnecessarily.  Because of
                #     this behavior, we need to directly access the class
                #     objects __dict__.
                if not isinstance(klass.__dict__.get(event), Event):
                    attr = klass.__dict__[event]

                    raise AttributeError(
                        f"{name}.{event} already defined, " \
                        f"but {event} is a {type(attr).__name__}, " \
                        "not an event."
                    )
        return klass


class AbstractEventProducerMeta(ABCMeta, EventProducerMeta):
    pass


class EventProducer(object, metaclass=AbstractEventProducerMeta):
    pass
    

def event_producer(cls):
    '''Class decorator that ensures the class is an EventProducer, which is
    required to use the eventing subsystem.
    '''
    # Extract the class objects mro
    mro = list(inspect.getmro(cls))

    # Iterate through the classes mro.  If any base classes are already
    # an EventProducer, return cls (i.e. do nothing).
    # NB: We could use 'any' rather than using a for loop, but we can achieve
    # performance improvements if we early exit.    
    for klass in mro:
        if type(klass) == type(EventProducer):
            return cls
    
    # If we reach this point, the object is NOT an EventProducer.  Modify the
    # classes mro to include EventProducer
    new_class = type(
        cls.__name__, 
        tuple(mro[1:-1] + [EventProducer, mro[-1]]), 
        dict(cls.__dict__)
    )
    return new_class