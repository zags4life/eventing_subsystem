# invalideventsignature.py

class EventError(Exception):
    pass

class InvalidEventSignature(EventError):
    pass

class InvalidEventCallback(EventError):
    pass
    
class EventInvocationError(EventError):
    pass