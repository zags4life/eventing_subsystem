# event.py

import inspect
from threading import Lock

from .eventerrors import *

class _Event:
    def __init__(self, owner, *signature):
        # Possible states:
        # 1) signature is empty or none -> set signature to an empty tuple
        # 2) signature is passes as tuple or list, rather than a param list
        #   a) if the first index of signature is a list or tuple, set types
        #      to the first index of signature
        #   b) if the first parameter is None -> set signature to an empty tuple
        #   c) if first parameter is a type, reset signature to a tuple containing
        #      the type
        # 3) signature is a valid tuple, use signature as is.

        if not signature:
            signature = ()
        elif len(signature) == 1:
            _type = signature[0]
            if isinstance(_type, (list, tuple)):
                signature = _type
            else:
                signature = () if _type is None else (_type,)

        assert all(isinstance(t, type) for t in signature)

        self.__owner = owner
        self.__signature = signature
        self.__lock = Lock()
        self.__callbacks = []

        assert self.__owner, 'event owner cannot be None'

    def __call__(self, *args):
        '''Call operator used to invoke, or raise, the event.  Raising the
        event will invoke all registered callbacks.
        
        NB: events can only be raised by the owning object.  I.e. this object
            is not callable outside of the owning object
        '''

        # Ensure the caller is the owner of the event
        caller = inspect.currentframe().f_back.f_locals.get('self')
        if not (caller and caller is self.__owner):
            raise EventInvocationError(
                'Cannot raise event outside the owning class.'
            )

        # Ensure the arguments match the expected list of types.
        #
        # NB: This is a performance hit.  We only want to do this when
        #     running in debug mode
        if __debug__:
            if not all(isinstance(a, t) for t, a in zip(self.__signature, args)) \
                    or len(args) != len(self.__signature):

                raise InvalidEventSignature(
                    "Failed to raise event; unexpected event signature.  Expected " \
                    "event signature '({0})', but was given '({1})'.".format(
                        ', '.join([t.__name__ for t in self.__signature]),
                        ', '.join([type(a).__name__ for a in args])))

        # The list of callbacks can be accessed from other threads.  For safety
        # and speed create a copy of the list of callbacks, while under lock,
        # then call each callback contained in the copied list outside the lock.
        # This also ensures that a callback is allowed to unregister itself 
        # from the event without creating deadlock.
        with self.__lock:
            callbacks = self.__callbacks[:]

        # For each callback method, invoke the method, passing
        # args as parameters.  Note, the first parameter is the owning object.
        for callback in callbacks:
            callback(self.__owner, *args)

    def __iadd__(self, callback) -> object:
        '''The add and assign (+=) operator used for adding callbacks 
        to the event.
        '''
        self.register_callback(callback)
        return self

    def __isub__(self, callback) -> object:
        '''The -= operator of removing callbacks from the event'''
        self.unregister_callback(callback)
        return self

    def register_callback(self, callback) -> None:
        '''Register a callback with this event.  The registered callback will 
        be invoked whenever event is raised.  
        
        Note: callers can also use the '+=' operator to add callbacks.
        
        Parameters:
        callback - a callback method to register with the event, which will be
                invoke everytime the event is raised.
                
        Returns - None
        '''
        # Ensure callback is callable
        if not (callback and callable(callback)):
            raise EventRegistrationError('Event callback must be callable')

        # Verify the callbacks method signature matches the expected signature.
        # Note, we cannot validate types, since this is python, but we can
        # validate length now, and validate types when the event is invoked
        #
        # NB: This is a big performance hit.  We only want to do this when
        #     running in debug mode
        if __debug__:
            if (len(inspect.signature(callback).parameters) !=
                    (len(self.__signature) + 1)):

                raise EventRegistrationError(
                    'Invalild callback signature.  ' \
                    f'Expected {len(self.__signature) + 1} parameters, but ' \
                    f'{len(inspect.signature(callback).parameters)} were ' \
                    f'defined.  Note: the first parameter for any event ' \
                    f'callback is the owning object.' 
                )

        # Add the callback to our list of callbacks (under lock)
        with self.__lock:
            self.__callbacks.append(callback)

    def unregister_callback(self, callback) -> None:
        '''Unregister the callback from this event.'''
        with self.__lock:
            try:
                self.__callbacks.remove(callback)
            except ValueError as e:
                pass

    def clear(self):
        '''Clear all callbacks from the callbacks list'''
        with self.__lock:
            self.__callbacks = []


class Event:
    def __init__(self, *types):
        self.__types = types
        self.__lookup = {}

    def __get__(self, instance, owner):
        if instance not in self.__lookup:
            self.__lookup[instance] = _Event(instance, *self.__types)
        return self.__lookup[instance]


EVENTS_FUNC_ATTR = '__events__'

def event(name, signature=None):
    '''event decorator used to define events in a class.

    This decorator requires consuming classes to dervice from EventProducer
    or use the metaclass EventProducerMeta
        
    Parameters:
        name - a string representing the name of the event
        signature - a tuple of types defining event signature.

    Note: 
    The first parameter for every event callback is the sender object,
    which is not required to be defined in the signature. Furthermore, it is
    perfectly valid to define the signature as a single type, as None, or 
    omitted altogether.
    
    Example:
        class Producer(EventProducer):
            @event(name='on_update_event', signature=str)
            def do_work(self):
                self.on_update_event('complete')

        def on_update_callback(caller, msg):
            print(msg)

        producer = Producer()
        producer.on_update_event += on_update_callback

        producer.do_work()
    '''
    def wrapper(func):
        # Get the functions events list, or create one if one does not exist.
        func.__events__ = getattr(func, EVENTS_FUNC_ATTR, [])
        func.__events__.append((name, signature))
        return func
    return wrapper