# eventproducermeta.py

from abc import ABCMeta
from .event import Event, _Event

class EventProducerMeta(type):
    '''Eventing subsystem metaclass required for the @event decorator'''
    def __new__(cls, name, bases, state):
        events_to_create = []

        # Iterate through all members and create a list of all events that
        # have been registered via the @event decorator.
        for member in state.values():

            # If the member contains an '__events__' attribute, then
            # contains events that need to be created.
            meta_events = getattr(member, '__events__', None)
            if meta_events is not None:
                assert isinstance(meta_events, list)

                # __events__ attribute is a list; iterate through all event metadata
                for event_metadata in meta_events:
                    events_to_create.append(event_metadata)

        # Before creating the Event objects, we need to create the class.
        klass = type.__new__(cls, name, bases, state)

        # Iterate through the list of events to create.
        # NB: Each item in the list is a 2d tuple containing the
        #     event name (as a string) and a tuple of types.
        for event, types in events_to_create:
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
                    raise AttributeError(
                        "Class {0} already defines attribute '{1}', but " \
                        '{1} is a {2}, not an event.'.format(
                            klass.__name__, event, type(attr).__name__
                        )
                    )
        return klass

class AbstractEventProducerMeta(ABCMeta, EventProducerMeta):
    pass

class EventProducer(object, metaclass=AbstractEventProducerMeta):
    pass