# event.py

import inspect
from threading import Lock

from .invalideventsignature import *

class MyLock(object):
    def __init__(self, thread_safe=True):
        self.lock = Lock()
        self.thread_safe = thread_safe

    def __enter__(self):
        if self.thread_safe:
            self.lock.acquire()
        return self

    def __exit__(self, *args):
        if self.thread_safe:
            self.lock.release()
        return

class _Event(object):
    
    def __init__(self, owner, *signature):
        # It is possible that the caller will pass the signature as a tuple rather than a param list.
        # To acount for this

        # Possible states:
        # 1) signature is empty or none -> set signature to an empty tuple
        # 2) signature is passes as tuple or list, rather than a param list
        #   a) if the first index on signature is a list or tuple, reset types
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
        '''Calling the event will signal all registered callbacks.

        Example:
            def callback(event_name, payload):
                print(event_name, payload)

            my_event = Event(str, str)
            my_event.non_callable() += callback

            my_event(event_name='test callback', payload='this is my payload')
        '''

        caller = inspect.currentframe().f_back.f_locals.get('self')
        if not (caller and caller is self.__owner):
            raise EventInvocationError('Cannot raise event outside the owning class.')

        # Ensure the arguments match the expect list of types.
        #
        # NB: This is a slight performance hit.  We only want to do this when
        #     running in debug mode
        if __debug__:
            if not all(isinstance(a, t) for t, a in zip(self.__signature, args)) \
                    or len(args) != len(self.__signature):

                raise InvalidEventSignature(
                    "Cannot raise event; unexpected event signature.  Expected " \
                    "event signature '({1})', but was given '({1})'.".format(
                        ', '.join([t.__name__ for t in self.__signature]),
                        ', '.join([type(a).__name__ for a in args])))

        # The list of callbacks can be accessed from other threads.  For safety
        # and speed create a copy of the list of callbacks, while under lock,
        # then call each callback contained in the copied list outside the lock.
        with self.__lock:
            callbacks = self.__callbacks[:]

        # For each callback method, invoke the method, passing
        # args as parameters.
        for callback in callbacks:
            callback(self.__owner, *args)

    def __iadd__(self, callback):
        if not (callback and callable(callback)):
            raise InvalidEventCallback('Event callback must be callable')

        # Verify the callbacks method signature matches the expected signature.
        # Note, we cannot validate types, since this is python, but we can
        # validate length now, and validate types when the event is invoked
        #
        # NB: This is a big performance hit.  We only want to do this when
        #     running in debug mode
        if __debug__:
            if (len(inspect.signature(callback).parameters) !=
                (len(self.__signature) + 1)):

                raise InvalidEventCallback(
                    'Callback has an invalid signature.  ' \
                    'Expected {} parameters, but {} were defined.  ' \
                    'Note, the first parameter passed to the callback is the ' \
                    'calling object.'.format(
                        len(self.__signature) + 1,
                        len(inspect.signature(callback).parameters)
                    )
                )

        # Add the callback to our list of callbacks (under lock)
        with self.__lock:
            self.__callbacks.append(callback)
        return self

    def __isub__(self, callback):
        with self.__lock:
            try:
                self.__callbacks.remove(callback)
            except ValueError as e:
                pass
        return self

    def clear(self):
        '''Clear all callbacks from the callbacks list'''
        with self.__lock:
            self.__callbacks = []


class Event(object):
    def __init__(self, *types):
        self.__types = types
        self.__lookup = {}

    def __get__(self, instance, owner):
        if instance not in self.__lookup:
            self.__lookup[instance] = _Event(instance, *self.__types)
        return self.__lookup[instance]
