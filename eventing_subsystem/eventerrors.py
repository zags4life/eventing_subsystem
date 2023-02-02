# invalideventsignature.py

class EventError(Exception):
    pass

class InvalidEventSignature(EventError):
    pass

class EventRegistrationError(EventError):
    pass
    
class EventInvocationError(EventError):
    pass