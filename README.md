Eventing Subsystem
===

- [Introduction]
- [Enabling eventing for a python class]
- [Raising events]
- [Consuming events]
- [Errors]
- [Performance]
- [Examples]
- [Troubleshooting]

## Introduction
The _eventing_ _subsystem_ enables .NET like eventing from a python class.  I.e. a producer / consumer model, where consumers can register callback methods with the producer in which the producer will signal, or raise the event, invoking each registered callback method.  This eventing system is thread safe.

### Basic Idioms
1. Events are exposed publicly to consumers for the purpose of subscribing / unsubscribing
2. Events can only be raised by object owning the event
3. Events need to be easily discoverable by consumers
4. Events _must_ be thread safe

## Enabling eventing for a python class
The most common method for defining / enabling events in a python object is using the `event` method decorator

Defining events via the `event` decorator requires that the class derive from `EventProducer`.

You can either derive your object from `EventProducer`, like so:

```
class Producer(EventProducer):
    @event(name='on_work_complete', signature=str)
    def do_work_then_raise_event(self):
        external_param = 'foo'

        self.on_work_complete(external_param)
```

Or use the `event_producer` decorator, like so:

```
@event_producer`
class Producer:
    @event('on_work_complete', str)
    def do_work_then_raise_event(self):
        external_param = 'foo'

        self.on_work_complete(external_param)

```

### EventProducer
The `EventProducer` base class is a metaclass, which derives from `ABCMeta`.  Any object wishing to use the `@event` decorator must either:
A. Derive their class from `EventProducer`, or
B. use the `event_producer` class decorator.

If you wish to not derive from `EventProducer`, you can define the `Event` as a class descriptor (see [advanced]).

### Decorator signature
The `event` decorator requires two parameters: `name` and `signature`.  The `name` parameter defines the name of the event and the `signature` defines the event signature as a tuple of types (where ordering of types in the event signature is of importance).

The event `signature` is a tuple of types defining the event signature and parameter ordering.  It is perfectly valid to define the signature as None or be omitted altogether.  It is also valid to define the `signature` as a single type.  The `signature` is used by the event to valid both callback methods and event invocation calls for proper method signatures.

When raising an event, **the _eventing_subsystem_ will automatically pass the _sender_ (the object raising the event) as the first parameter to all registered callbacks.  When raising an event, it is not required to pass `self` as a parameter, nor define `self` in the event signature.**

For example, an event defined as `@event(name='on_event', signature=str)` would in turn require a callback signature of `def on_event_callback(sender, payload):`.  Furthermore, when raising the event, only `payload` would need to be passed as a parameter to the event object, when called.  E.g. `self.on_event('my payload')`.

### Advanced
A more advanced way to define / enable events in a python class, is as a class descriptor.  Defining events in this manner does _not_ require the class to be derived from `EventProducer`.  See [examples](#defining-an-event-using-a-class-descriptor) for more information.

## Raising events
To raise an event, the object owning the event can simply call the event, passing all required parameters to the event.  To reiterate, the object raising the event should **not** pass `self` as a parameter, since the _event_subsystem_ will take case of this automatically.  

It is important to note that while an event is exposed publicly to consumers, it can only be invoked by the object who initially created it (i.e. the owner).  __Attempting to raise an event outside the owning object will result in an `EventInvocationError`.__

## Consuming events
Consumers can subscribe, and unsubscribe, to events using the `+=` and `-=` operators exposed by the event.  The right hand side of the operator is expected to be the event callback method, or callable object.

For example:
```
def my_callback(sender, payload):
    sender.on_event -= my_callback

producer = Producer()
producer.on_event += my_callback
```

When an event is raised, **the _eventing_subsystem_ will automatically pass the _sender_ (the object raising the event) as the first parameter to all registered callbacks, plus any additional parameters defined in the event signature.**  For example, an event defined as `@event(name='on_event', signature=str)` would in turn require a callback signature of `def on_event_callback(sender, payload):`.  When looking to subscribe to an event, please make note of this behavior to avoid an `InvalidEventCallback` exception (or a `TypeError` exception when running in optimized mode).

### Sender
When an event is raise, and the callbacks invoked, the _event_subsystem_ will pass the sender object as the first parameter followed by any subsequent parameters passed to the event at the point of invocation.  Passing of the sender object is required to help consumers identify which instance of a producter object raised the event.

For example:
```
def on_event_callback(sender, payload):
    print('{} object raised an event'.format(sender)

producers = []

for _ in range(10):
    producer = Producer()
    producer.on_event += on_event_callback
    producers.append(producer)
```

In the above example, the consumer is registering the same callback with N number of producers.  Without the `sender` parameter, it would be impossible to identify which instance of `Producer` raised the event.

**The _eventing_subsystem_ will automatically pass the `sender` (the object raising the event) as the first parameter to all registered callbacks.  When raising an event, it is not required to pass `self` as a parameter, nor define `self` in the event signature.**

## Errors
In some cases the _eventing_subsystem_ will detected an invalid state.  In these cases, it will raise the appropriate exception.  Below are the exceptions that can be raised by the _eventing_subsystem_ and the reasons they would be raised.

+ `InvalidEventSignature` - Raised when an event is raised with set of paramters that does not match the defined event signature.
+ `EventRegistrationError` - Raised when an event callback defines a different set of parameters than what is defined in the event signature.  
+ `EventInvocationError` - Raised when a consumer attempts to raise (call) an event outside of the owning object.
+ `EventError` - The base class for all events raised by the _eventing_subsystem_.  This is helpful if you wish to catch all errors raised by the _eventing_subsystem_.

## Performance
Type checking of callback and invocation signatures have a performance impact.  When running in a production environment, it is strongly recommended that this module be run in optimized mode (i.e. `python -O`).

## Examples
### Defining an event using a decorator
```
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
    
>>> OUTPUT

Producer raised event foo
```

### Defining an event using a class descriptor
Plese refer to the ["Defining an event using a decorator" example](#defining-an-event-using-a-decorator) above.  The `Consumer` code and `__main__` code remains the same.
```
class Producer(object):
    on_work_complete = Event(str)

    # @event(name='on_work_complete', signature=str)
    def do_work_then_raise_event(self):
        external_param = 'foo'

        self.on_work_complete(external_param)

```
Note: the `Event` object take a param list of types.  In the example above, only one type is expected to be passed by the `Producer`

## Troubleshooting
Q: I defined my event using the decorator, but when I run my program an `AttributeError` is raised.  E.g:
```
AttributeError: 'Producer' object has no attribute 'on_work_complete'
```

A: Ensure your object derives from `EventProducer`.
