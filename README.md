
# A Python Web Framework

In this guide, we're going to create a web framework using `asyncio`, that will be covered in this whole article.

### Pre Requisites
* Python: 3.8.10
* Poetry: 1.7.1

Building a Web Framework, we can start with 
some pillars, such as:
* Transport and Protocol
* Request and Response objects
* Application and Url Dispatcher

## Web Server using socket

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

MAX = 65535
PORT = 8080

s.bind(('127.0.0.1', PORT))
print(f"Listening on {PORT}")
while True:
    data, addr = s.recvfrom(MAX)
    print("THe Client at", addr, 'received data:', repr(data))
    s.sendto(b'Your data has been received', addr)
```
first of all, we start making a bind into the operational system to start our server
```python
s.bind(('127.0.0.1', PORT))
```
now, we can handle every request made to that IP:PORT, for example:

```python
import socket, sys


MAX = 65535
PORT = 8080

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('127.0.0.1', PORT))

print("Client socket name: ", s.getsockname())

while True:
    s.send(b'This is another message')
    print(f"Waiting up to {delay} seconds")
    data = s.recv(MAX)
    break
print(f"The Server says", repr(data))
```
this piece of code are going to send a request into that specific socket that we built.

but as you can see, this code has a HUGE problem, we can only handle one request per time, we are also going to be affected in the time that the message got to be transmitted between the client and server.
This mean that we cannot scale this project to handle hundreds and not even close to thoudsands of request in parallel, because:

As we can see in, This code is synchronous 
```python
while True:
    data, addr = s.recvfrom(MAX)
```
Our code make a synchronous while true, and wait for receive a request from anything, meaning that we can make a request, but if we make another before the server is done with the first, this request will need to wait
Our code spend time waiting for Transmission.

```python
s.send(b'This is another message')
data = s.recv(MAX)
```
`send` and `recv` wait for send and receive that in the network, and this can be delegate to the OS handle those things

And, i know that we can use `select` to handle `poll` events, but it's not the focus of this guide.

So, lets start builing a web server that can handle multiple requests and do not waste time with things that can be outsourced
## Transport and Protocol

Currently in python, has many ways to handle parallel process, such as:

* Process (multiprocessing)
* Thread (threading)
* AsyncIO (asyncio)

In the project we are going to cover the usage with asyncio.

AsyncIO is a library to write concurrent code using the async/await syntax. asyncio is used as a foundation for multiple Python asynchronous frameworks that provide high-performance network and web-servers.


<a id="asyncio.Protocol_documentation"></a>
Let's start reading about asyncio.Protocol documentation:
```python
Interface for stream protocol.
The user should implement this interface. 
They can inherit from
this class but don't need to.  
The implementations here do nothing (they don't raise exceptions).

When the connection is made successfully, connection_made() is
called with a suitable transport object.  Then data_received()
will be called 0 or more times with data (bytes) received from the
transport; finally, connection_lost() will be called exactly once
with either an exception object or None as an argument.

    State machine of calls:

    start -> CM [-> DR*] [-> ER?] -> CL -> end

    * CM: connection_made()
    * DR: data_received()
    * ER: eof_received()
    * CL: connection_lost()
```

So it means that, we can inherit this asyncio.Protocol, since we implement at least `data_received`, so, before we begin, 
we need to know that the data received in the socket, is actually bytes, nor string, so we need to implement a way to convert this data, 
and we can use `HttpRequestParser` from `httptools`

```python
import asyncio
from httptools import HttpRequestParser

class Server(asyncio.Protocol):
    def __init__(self):
        self.encoding = "utf-8"
        self._request_parser = HttpRequestParser(self)

    def data_received(self, data):
        print("Received: ", data)
        self._request_parser.feed_data(data)
```

Our `Server` class is going to handle any request on the `data_received` method and use `HttpRequestParser` from `httptools` to convert this data for us.
But now, we can start to build him to test our class!

<a id="main_method_v1"></a>
```python
import asyncio

loop = asyncio.get_event_loop()
protocol = Server()
server = loop.run_until_complete(
    loop.create_server(lambda: protocol, host='127.0.0.1', port=8080)
)
loop.run_until_complete(server.serve_forever())
```

* `loop.create_server` is an asyncio function that creates a server object but does not start it immediately. Instead, it returns a coroutine

* `lambda: protocol` is a lambda function that returns the `protocol` (our server) to each client connection 

* `loop.run_until_complete(server.serve_forever())` is used to run the asyncio event loop for incoming connections

Now our server should be running without any problem, let's make our first request to test him!.


```python
import asyncio

async def main():
    message = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    reader, writer = await asyncio.open_connection('127.0.0.1', 8080)

    print(f'Send: {message}')
    writer.write(message.encode())

    data = await reader.read(100)
    print(f'Received: {data.decode()}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
```

And now, if it's everything OK, we can run our server, and try to connect from our client, and we should see on the terminal
`Received:  b'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n'`

But, this is not how a web framework looks like!.
We need a way to create method that will be trigger as a request come asking for that path.
Let's start adding some mora attribute for our `Server` class
```python
class Server(asyncio.Protocol):
    def __init__(self):
        self.encoding = "utf-8"
        self.url = None
        self.body = None
        self._request_parser = HttpRequestParser(self)
    
    def on_url(self, url):
        self.url = url.decode('utf-8')

    def data_received(self, data):
        self._request_parser.feed_data(data)
    
    def on_body(self, data):
        self.body = data
        
    def on_message_complete(self):
        print("Message Finished!")
```

* `on_message_complete` is going to be triggered when the message is fully processed
 
But now, we need to create something that can help us to handle the request, so we're going to create our own `Request` class
```python
class Request:

    def __init__(self, method, url, body):
        self.encoding = "utf-8"
        self.method = method
        self.url = url
        self.body = body
```

Simple, isn't it? :P, but this can help us to separate the responsibility of the classes.
now we can change the `on_message_complete` to:
```python
class Server(asyncio.Protocol):
    def on_message_complete(self):
        request = Request(
            method=self._request_parser.get_method().decode('utf-8'),
            url=self.url,
            body=self.body,
        )
```

Now, let's start building out `Router` it's going to be responsible to handle the request and to distribute to the correct method
```python
class Router:
    def __init__(self):
        self.mapping = {}

    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler
```

with this class, we can add him at `Server` and a `add_route` method as well
```python
class Server(asyncio.Protocol):
    def __init__(self):
        self.encoding = "utf-8"
        self.url = None
        self.body = None
        self._request_parser =  HttpRequestParser(self)
        self.router = Router()
    # ....
    def add_route(self, path: str, methods_handler: dict):
        self.router.add(path, methods_handler)
```

Now, as we have our `Server` instance from [here](#main_method_v1)
We can pass this instance to `hello_world_app`, like this example.
```python
def hello_world_app(server: Server):
    async def hello_world(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body}")

    server.add_route("/hello_world", {"GET": hello_world})
```

And we can add `hello_world_app` right after instantiate the Server object

```python
loop = asyncio.get_event_loop()
protocol = Server()

hello_world_app(protocol)

server = loop.run_until_complete(
    loop.create_server(lambda: protocol, host='127.0.0.1', port=8080)
)
loop.run_until_complete(server.serve_forever())
```

We're close to make our first test! Let's just add some pieces of code at our `Server` class:
```python
class Server(asyncio.Protocol):
    def on_message_complete(self):
        request = Request(
            method=self._request_parser.get_method().decode('utf-8'),
            url=self.url,
            body=self.body,
        )
        self.router.dispatch(request)
```
On our `Router` class:
```python
class Router:
    def __init__(self, loop):
        self.mapping = {}
        self.loop: asyncio.AbstractEventLoop = loop

    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler

    def dispatch(self, request: Request):
        handlers = self.mapping.get(request.url, None)
        if not handlers:
            return
        method_handler = handlers.get(request.method, None)
        if not method_handler:
            return

        self.loop.create_task(method_handler(request))
```

`dispatch` is going to handle the request, and see if there's any route if the current url that was send from the client.
After find it, it's going to see if there's a method to handle for that specific HTTP method (e.g. GET, POST, PUT).
After this we are going to create a task in the event loop to run the method for us, but take a look, now our `Router` class is required to receive the event loop as a instance parameter, so we need to change our `Server` class again:

```python
class Server(asyncio.Protocol):
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.encoding = "utf-8"
        self.url = None
        self.body = None
        self._request_parser = HttpRequestParser(self)
        self.router = Router(self.loop)
```

Now, let's change a little bit our client method so send a request to our `/hello_world` route:
```python
async def main():
    message = 'GET /hello_world HTTP/1.1\r\nHost: example.com\r\n\r\n'
    # ....

if __name__ == "__main__":
    asyncio.run(main())
```

And, if it's everything fine, you should see in the terminal 
```bash
Handle: GET /hello_world None
```

## Response class 

But as we've seen, we're currently get `None` as response of our end point, but what if we want to response a text or even a JSON? 
this is not possible, so we need to refactor somethings to be able to response them.

First of all, let's create our own class Response:
```python
import json
from typing import Any
from http.server import BaseHTTPRequestHandler


class Response:

    def __init__(
            self,
            status_code: int,
            body: Any
    ):
        self.status_code = status_code
        self.body = body
        self.version = "1.1"
        self.content_type = "application/json"
```
* `status_code`: will be our status code that we want to response.
* `body`: is going to be the body that we want to response.
* `version`: is going to be fixed HTTP version 1.1.
* `content_type`: also, is going to be fixed as the mime type for application/json 

Now, we need to make a method that will convert this response into a compatible string with a socket connection.

```python
    def __str__(self):
        status_msg, _ = BaseHTTPRequestHandler.responses.get(self.status_code)
        messages = [
            f"HTTP/{self.version} {self.status_code} {status_msg}",
            f"Content-Type: {self.content_type}",
            f"Content-Length: {len(self.body)}",
            f"Connection: close"
        ]

        if self.body is None:
            return "\n".join(messages)

        if isinstance(self.body, str):
            messages.append("\n" + self.body)
        elif isinstance(self.body, dict):
            messages.append("\n" + json.dumps(self.body))

        return "\n".join(messages)
```
The hardest part of this snippet is `BaseHTTPRequestHandler.responses`, but i'm going to take a brief explanation.
```python
status_msg, status_description = BaseHTTPRequestHandler.responses.get(200)
status_msg -> OK
status_description -> Request fulfilled, document follows

status_msg, status_description = BaseHTTPRequestHandler.responses.get(404)
status_msg -> Not Found
status_description -> Nothing matches the given URI
```

Basically, it just return for us the HTTP message and description for each HTTP status codes, so we can attach into our response.
And that's it! Now we just need to change our `hello_world` route:

```python
def hello_world_app(server: Server):
    async def hello_world(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body}")
        return Response(
            200,
            {
                "hello": "back"
            }
        )

    server.add_route("/hello_world", {"GET": hello_world})
```

## Request Handler

Now, to keep our support to responses, we need to change the way that we make request handle's, first of all, we need to change our `Server` class:
```python
from typing import Optional

class Server(asyncio.Protocol):
    def __init__(self, loop=None):
        # ...
        self.transport: Optional[asyncio.Transport] = None
    
    def connection_made(self, transport):
        self.transport = transport

```

As we've read in the begging [here](#asyncio.Protocol_documentation) `When the connection is made successfully, connection_made() is
called with a suitable transport object`, on the `connection_made` our parameter is an instance of asyncio.Transport, which represents the communication channel to the client.

But, we need to take out the responsibility to handle and process the request from the `Router`, since her unique responsibility must be handle URL's path's
```python
class Router:
    def __init__(self, loop, handler):
        # ...
        self.callback_handler = handler
    
    # ...
    async def dispatch(self, request: Request):
        handlers = self.mapping.get(request.url, None)
        if not handlers:
            return
        method_handler = handlers.get(request.method, None)
        if not method_handler:
            return

        await self.callback_handler(method_handler, request)
```

But, what is `self.callback_handler`?, this is going to be our callback method that the Router will trigger when the method for that route is found and must process the request.
So we need to transport this responsibility to `Server` class

```python
from traceback import format_exception
class Server(asyncio.Protocol):
    def __init__(self, loop=None):
        # ...
        self.router = Router(self.loop, self.request_callback_handler)

    async def request_callback_handler(self, method, request):
        try:
            resp = await method(request)
        except Exception as exc:
            resp = format_exception(exc)

        if not isinstance(resp, Response):
            raise RuntimeError(f"expect Response instance but got {type(resp)}")

        self.response_writer(resp)    

```

Our `request_callback_handler` method is going to be triggred from `Router` sending us the request and the method that must be used to process him.
Her response is needed to be send to `response_writer` that we're going to see below.


```python
    def response_writer(self, response):
        self.transport.write(str(response).encode(self.encoding))
        self.transport.close()
```

`response_writer` is a method that will receive our response and write it inside the socket connection to the client, and then, close it.
One good advise, let's assume is this between time the client hangup? so our `self.transport` will keep with a disconnected socket, and this can be avoided implementing `connection_lost`:

```python
    def connection_lost(self, *args):
        self.transport = None
```

## Handling Request with body

Currently, our server does not handle so well requests with some body, so we need to fix it.
Firstm let's build a simple POST request with a body

```python
async def send_post():
    message_template = (
        'POST /hello_world HTTP/1.1\r\n'
        'Host: example.com\r\n'
        'Content-Type: application/json\r\n'
        'Content-Length: {}\r\n'
        '\r\n'
        '{}'
    )

    # Define the JSON data to send in the body of the POST request
    body = json.dumps({
        'key1': 'value1',
        'key2': 'value2'
    })
    content_length = len(body)
    message = message_template.format(content_length, body)

    reader, writer = await asyncio.open_connection('127.0.0.1', 8080)

    # Send the POST request
    writer.write(message.encode())
    await writer.drain()

    # Read the response
    response = await reader.read(1024)
    print('Received:', response.decode())

    # Close the connection
    writer.close()
    await writer.wait_closed()
```
In our `Server` class we need to change the `on_body` method, to this:
```python
    def on_body(self, data):
        self.body = data.decode(self.encoding)
```

The main reason it's because the request come in bytes, so it must be converted to string.
The `on_message_complete` also need to be changed to handle JSON nor string.
```python
    def on_message_complete(self):
        request = Request(
            method=self._request_parser.get_method().decode('utf-8'),
            url=self.url,
            body=json.loads(self.body),
        )
        self.loop.create_task(self.router.dispatch(request))
```
`json.loads` convert string body into JSON (e.g. dict in python)
So now, we can add a new route to handle the POST request.
```python
def hello_world_app(server: Server):
    async def hello_world(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body}")
        return Response(
            200,
            {
                "hello": "world"
            }
        )

    async def process_request(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body!s}")
        return Response(
            200,
            {
                **request.body,
                'hello': 'back'
            }
        )

    server.add_route("/hello_world", {
        "GET": hello_world,
        "POST": process_request
    })
```
We're adding a new request handler to all POST requests into `/hello_world` 
```python
{
    **request.body,
    'hello': 'back'
}
```
This piece of code is unpacking the request body dictionary and adding a new field with `'hello': 'back'`.

But, there's a problem (always has), our `Response` class does not handle so well responses with bodies, so we need to make a brief fix.
```python
    def __str__(self):
        # ...
        body = self.body
        if isinstance(body, dict):
            body = json.dumps(body)
        if not body:
            body = ''    
        
        messages = [
            f"HTTP/{self.version} {self.status_code} {status_msg}",
            f"Content-Type: {self.content_type}",
            f"Content-Length: {len(body)}",
            f"Connection: close"
        ]

        if not body:
            return "\n".join(messages)

        # ...
```
We're validating if the body is a dictionary, so we need to `json` library to convert it to a string for us. and also avoid use `len()` with None.

So, now, if we test to send a request to our server.
Our client console might look like this:

```bash
Received: HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 53
Connection: close

{"key1": "value1", "key2": "value2", "hello": "back"}
```

And our server:
```bash
Handle: POST /hello_world {'key1': 'value1', 'key2': 'value2'}
```

So, IT WORKS! We're sending a 
```JSON
POST /hello_world
{
  "key1": "value1", 
  "key2": "value2"
}
```
And our end point is adding the field `'hello': 'back'` to the body that was send in the request as a response to the client.
```JSON
{
  "key1": "value1", 
  "key2": "value2", 
  "hello": "back"
}
```


## Handling Not Found Routes

In our Router class, the code should look like this

```python
class Router:
    def __init__(self, loop, handler):
        self.mapping = {}
        self.callback_handler = handler
        self.loop: asyncio.AbstractEventLoop = loop

    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler

    async def dispatch(self, request: Request):
        handlers = self.mapping.get(request.url, None)
        if not handlers:
            return
        method_handler = handlers.get(request.method, None)
        if not method_handler:
            return

        await self.callback_handler(method_handler, request)
```

The main problem is the `return` keyword, basicly, if the code returns, 
in no point we're closing the connection with the client, meaning that the connection will keep open forever. 

So we have two ways to deal with this problem:
* Give for our Router `class` another callback function, that will close the connection
* Refactor our `Router` to be extended from `Server`, so we can use `self` to call the close connection from the `Server`.

In this guide we're going to follow the second options.

So, let's begin from removing `self.router` from our `Server` constructor 
```python
self.router = Router(self.request_callback_handler)
```

In `on_message_complete` and `add_route`, let's just change from
```python
- self.loop.create_task(self.router.dispatch(request))
+ self.loop.create_task(self.dispatch(request))
```
```python
- self.router.add(path, methods_handler)
+ self.add(path, methods_handler)
```

Since we don't have `self.router` anymore.

In our `Server` class, let's extend it from our `Router`

```python
class Server(asyncio.Protocol, Router):
    # ...
```
Now our class have all method inherited, it means, durying execution of `Server` if the method within `Router` is called, it can call a method from `Server` without any problem, since they're "mixed"

But since our `Server` already has `__init__` method, `Router` cannot have the same method implemented, so we need to catch 
* self.mapping
and add into the constructor from `Server`, that should look like this:
```python
    def __init__(self, loop=None):
        self.mapping = {}
        self.loop = loop or asyncio.get_event_loop()
        self.encoding = "utf-8"
        self.url = None
        self.body = None
        self._request_parser = HttpRequestParser(self)
        self.transport: Optional[asyncio.Transport] = None
```

So, let's start refactoring `Router` to call `Server` methods.
```python
class Router:
    # Removed __init__ method
    
    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler

    async def dispatch(self, request: Request):
        handlers = self.mapping.get(request.url, None)
        if not handlers:
            await self.response_writer(Response(
              404,
                {
                    'message': f'Not Found'
                }
            ))
        method_handler = handlers.get(request.method, None)
        if not method_handler:
            await self.response_writer(Response(
                404,
                {
                    'message': f'Not Found'
                }
            ))

        await self.request_callback_handler(method_handler, request)
```

`self.response_writer` and `self.request_callback_handler`, both are implemented in super class, let's asusme like this, so `Router` is calling a method that is implemented in a class that extended her, it basicly means that `Router` is a mixin class.

So, let's test by sending a simple POST Request to a route that don't exists in our project:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"key1": "value1", "key2": "value2"}' http://127.0.0.1:8080/not_created
```

And your response should be:
```json
{"message": "Not Found"}
```






