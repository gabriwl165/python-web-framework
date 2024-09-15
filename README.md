# A Python Web Framework

In this guide, we're going to create a web framework using `asyncio`, that will be covered in this whole article.

### Pre Requisites
* Python: 3.8.10
* Poetry: 1.7.1

When building a web framework, we can start with some key pillars, such as:
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
First, we begin by binding to the operating system to start our server.
```python
s.bind(('127.0.0.1', PORT))
```
Now, we can handle every request made to that IP and port. For example:

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
This piece of code is going to send a request to the specific socket we built.

But as you can see, this code has a significant problem: we can only handle one request at a time. 
Additionally, the time taken to transmit messages between the client and server will affect performance. 
This means we cannot scale this project to handle hundreds, let alone thousands, of requests in parallel because:

As we can see, this code is synchronous. 
```python
while True:
    data, addr = s.recvfrom(MAX)
```
Our code runs a synchronous `while true` loop and waits to receive a request from any source. 
This means that while we can handle one request, if another request is made before the server has finished processing the first, the new request will have to wait. 
Additionally, our code spends time waiting for data transmission.

```python
s.send(b'This is another message')
data = s.recv(MAX)
```
send and recv wait to send and receive data over the network, but this can be delegated to the operating system to handle.

Note: I am aware that we can use select to handle poll events, but that is not the focus of this guide.

So, let's start building a web server that can handle multiple requests and avoid wasting time on tasks that can be outsourced.
## Transport and Protocol

Currently in Python, there are many ways to handle parallel or concurrently processing, such as:

* Process (using the `multiprocessing` module)
* Thread (using the `threading` module)
* AsyncIO (using the `asyncio` module)

In this project, we will cover the usage of `asyncio`.


`AsyncIO` is a library for writing concurrent code using the async/await syntax. 
It serves as a foundation for multiple Python asynchronous frameworks that provide high-performance network and web servers.


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

This means that we can inherit from asyncio.Protocol, as long as we implement at least the `data_received` method. 
Before we begin, it's important to understand that the data received from the socket is actually in bytes, not strings. 
Therefore, we need to implement a way to convert this data, and we can use the `HttpRequestParser` from the `httptools` library.

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

Our `Server` class will handle any requests in the `data_received` method and use the `HttpRequestParser`
from the httptools library to convert the data for us. Now, let's start building it so we can test our class!

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

* `loop.create_server` is an asyncio function that creates a server object but doesn't start it immediately. Instead, it returns a coroutine.

* `lambda: protocol` is a lambda function that returns the protocol (our server) for each client connection. 

* `loop.run_until_complete(server.serve_forever())` is used to run the asyncio event loop continuously to handle incoming connections.

Now our server should be running without any problems. Let's make our first request to test it!


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

And now, if everything is OK, we can run our server and try to connect from our client. We should see the following on the terminal:
`Received:  b'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n'`

But this is not how a web framework should look! 
We need a way to create methods that will be triggered when a request comes in for a specific path. 
Let's start by adding some more attributes to our `Server` class
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

* `on_message_complete` will be triggered when the message has been fully processed.
 
But now, we need to create something that will help us handle the request, so we'll create our own `Request` class.
```python
class Request:

    def __init__(self, method, url, body):
        self.encoding = "utf-8"
        self.method = method
        self.url = url
        self.body = body
```

Simple, isn't it? :P But this approach helps us separate the responsibilities of our classes. 
Now, we can modify the `on_message_complete` method to:

```python
class Server(asyncio.Protocol):
    def on_message_complete(self):
        request = Request(
            method=self._request_parser.get_method().decode('utf-8'),
            url=self.url,
            body=self.body,
        )
```

Now, let's start building our `Router`. It will be responsible for handling requests and routing them to the correct method.
```python
class Router:
    def __init__(self):
        self.mapping = {}

    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler
```

With this class, we can add it to the `Server` and also create an `add_route` method.
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

Now that we have our `Server` instance from [here](#main_method_v1) we can pass this instance to `hello_world_app`, as shown in the example below.
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

We're close to making our first test! Let's just add a few more pieces of code to our `Server` class:
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

`dispatch` will handle the request and check if there’s a route matching the URL sent by the client. 
If a matching route is found, it will then determine if there’s a method available to handle the specific HTTP method (e.g., GET, POST, PUT). Once identified, a task will be created in the event loop to run the corresponding method. 
Note that our `Router` class now requires the event loop as an instance parameter, so we’ll need to modify our `Server` class accordingly

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

Now, let's modify our client method slightly to send a request to our `/hello_world` route:
```python
async def main():
    message = 'GET /hello_world HTTP/1.1\r\nHost: example.com\r\n\r\n'
    # ....

if __name__ == "__main__":
    asyncio.run(main())
```

And if everything is fine, you should see the following in the terminal: 
```bash
Handle: GET /hello_world None
```

## Response class 

But as we've seen, we're currently getting `None` as the response from our endpoint. 
But what if we want to return a text or even a JSON response? This isn't possible with the current setup, so we need to refactor some parts of our code to make this possible.

First, let's create our own `Response` class:
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
* `status_code`: This will be the status code that we want to return.
* `body`: This will be the body of the response.
* `version`: This will be the fixed HTTP version, set to 1.1.
* `content_type`: This will also be fixed, set to the MIME type for `application/json`. 

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
The most challenging part of this snippet is `BaseHTTPRequestHandler.responses`, but I'll provide a brief explanation.
```python
status_msg, status_description = BaseHTTPRequestHandler.responses.get(200)
status_msg -> OK
status_description -> Request fulfilled, document follows

status_msg, status_description = BaseHTTPRequestHandler.responses.get(404)
status_msg -> Not Found
status_description -> Nothing matches the given URI
```

Basically, it just returns the HTTP message and description for each status code, allowing us to include them in our response. 
And that's it! Now we just need to update our `hello_world` route:

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

Now, to maintain support for responses, we need to modify the way we handle requests. 
First, we need to update our `Server` class:
```python
from typing import Optional

class Server(asyncio.Protocol):
    def __init__(self, loop=None):
        # ...
        self.transport: Optional[asyncio.Transport] = None
    
    def connection_made(self, transport):
        self.transport = transport

```

As mentioned at the beginning, [here](#asyncio.Protocol_documentation) When the connection is made successfully,  `connection_made()` is
called with a suitable transport object, on the `connection_made` our parameter is an instance of asyncio.Transport, which represents the communication channel to the client.

However, we need to remove the responsibility of handling and processing requests from the `Router`, as its sole responsibility should be managing URL paths.
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

But what is `self.callback_handler`? This will be our callback method that the `Router` will trigger when the appropriate method for that route is found and needs to process the request. 
Therefore, we need to transfer this responsibility to the `Server` class.

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

Our `request_callback_handler` method will be triggered by the `Router`, sending us the request and the method that should be used to process it. 
The response then needs to be sent to the `response_writer`, which we'll cover below.

```python
    def response_writer(self, response):
        self.transport.write(str(response).encode(self.encoding))
        self.transport.close()
```

`response_writer` is a method that receives our response, writes it to the socket connection to the client, and then closes the connection. 
One important piece of advice: what if, during this time, the client hangs up? In that case, `self.transport` would be left with a disconnected socket. 
This can be prevented by implementing the `connection_lost` method.

```python
    def connection_lost(self, *args):
        self.transport = None
```

## Handling Request with body

Currently, our server doesn't handle requests with a body very well, so we need to fix that. 
First, let's build a simple POST request with a body.

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
In our `Server` class, we need to update the `on_body` method to the following:
```python
    def on_body(self, data):
        self.body = data.decode(self.encoding)
```

The main reason is that the request comes in as bytes, so it must be converted to a string. 
The `on_message_complete` method also needs to be updated to handle both JSON and strings.
```python
    def on_message_complete(self):
        request = Request(
            method=self._request_parser.get_method().decode('utf-8'),
            url=self.url,
            body=json.loads(self.body),
        )
        self.loop.create_task(self.router.dispatch(request))
```
`json.loads` converts the string body into JSON (e.g., a dictionary in Python). 
Now, we can add a new route to handle the POST request.
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
We're adding a new request handler for all POST requests to `/hello_world`. 
```python
{
    **request.body,
    'hello': 'back'
}
```
This piece of code unpacks the request body dictionary and adds a new field with `'hello': 'back'`.

However, there's a problem (there always is): our `Response` class doesn't handle responses with bodies very well, so we need to make a quick fix.
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
We're validating whether the body is a dictionary, and if it is, we need to use the `json` library to convert it to a string. Additionally, we should avoid using `len()` on `None`.

Now, if we test sending a request to our server, our client console might look like this:

```bash
Received: HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 53
Connection: close

{"key1": "value1", "key2": "value2", "hello": "back"}
```

And our server might look like this:
```bash
Handle: POST /hello_world {'key1': 'value1', 'key2': 'value2'}
```

So, IT WORKS! We're successfully sending a request. 
```JSON
POST /hello_world
{
  "key1": "value1", 
  "key2": "value2"
}
```
And our endpoint is adding the field `'hello': 'back'` to the body that was sent in the request, and returning it as a response to the client.
```JSON
{
  "key1": "value1", 
  "key2": "value2", 
  "hello": "back"
}
```


## Handling Not Found Routes

In our `Router` class, the code should look like this:

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

The main problem lies with the `return` keyword. 
Essentially, if the code returns, there’s no point where we close the connection with the client, meaning the connection will remain open indefinitely. 

We have two options to address this problem:
* Provide our `Router` class with another callback function to close the connection.
* Refactor our `Router` class to extend from `Server`, allowing us to use `self` to call the connection close method directly from the `Server`.

In this guide, we’ll follow the second option.

So, let’s start by removing `self.router` from our `Server` constructor.
```python
self.router = Router(self.request_callback_handler)
```

In the `on_message_complete` and `add_route` methods, let's simply change from:
```python
- self.loop.create_task(self.router.dispatch(request))
+ self.loop.create_task(self.dispatch(request))
```
```python
- self.router.add(path, methods_handler)
+ self.add(path, methods_handler)
```

Since we no longer have `self.router`, let's extend our `Server` class from our `Router` class.

```python
class Server(asyncio.Protocol, Router):
    # ...
```
Now that our class has inherited all methods, it means that during the execution of `Server`, if a method within `Router` is called, it can invoke a method from `Server` without any issues, since they're now integrated.

However, since our `Server` class already has an `__init__` method, the `Router` class cannot implement the same method. 
Therefore, we need to capture `self.mapping` and add it to the constructor of `Server`, which should look like this:
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

So, let's begin refactoring the `Router` to call `Server` methods.
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

`self.response_writer` and `self.request_callback_handler` are both implemented in the superclass. 
In this case, `Router` is calling a method that is implemented in a class that extends it, which essentially makes `Router` a mixin class.

Now, let's test this by sending a simple POST request to a route that doesn't exist in our project:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"key1": "value1", "key2": "value2"}' http://127.0.0.1:8080/not_created
```

And your response should be:
```json
{"message": "Not Found"}
```

## Handling Dynamic URL's

But one thing, that's something in web development, is to handle dynamic URL's, and what can i want to talk? it's that it's normal to have this kind of URL
```bash
/users/{id}
```

and then we send a 
```bash 
GET /users/123456
```

and we need to be able to handle this id as a parameter, for example

```python
    async def process_dynamic_url(request: Request, name: str):
        try:
            return Response(
                200,
                {
                    'msg': f'Hello {name}'
                }
            )
        except Exception as e:
            print(e)

    server.add_route("/hello_world/{name}", {
        "GET": process_dynamic_url
    })
```

And you should start to thing "this is so complex, it might have some awesome business logic to implement it", and TCHARAM, this can be achieve by implementing regex on our `Router` class

First, let's understand how regex works and how this can be achieved, we have two strings `"/users/{id}/"` and `"/users/12345/"`, let's make a prototype:
```python
import re
match = re.match(r'/users/(.+?)/', "/users/123/")
match.groups()
"""
Should return:
('123',)
"""
```
A simple dive into `r'/users/(.+?)/'`:
- `()` this means that whatever matches the pattern inside the parentheses will be captured and stored
- `.` this means any character except a newline
- `+` this quantifier matches one or more of the preceding token
- `?` which means it will match as many characters as possible

But, there's a better way to deal with this regex, currently we have a feature called "groups", that makes us be able to use a 
`groupdict()` method and got an dict as 
```json
{
  "id": "123"
}
```
and this help us a lot! since with this JSON we can be able to desconstruct the JSON with `**` and pass as kwargs into our methods/router/controller!
our boilerplate will be `(?P<id>.+?)`, and let's make a brief dive into this regex!
- `(?P<id>...)` makes us match the code as `id` into our JSON, just like we want
- `.+?` makes us match one or more of character except a newline

```python
import re

match = re.match(r'^/users/(?P<id>[^/]+?)/$', "/users/123/")
match.groupdict()
"""
Our response should look like this:
{'id': '123'}
"""
```

And i know, now you're problably "oh god" after see this regex, but i'll try make the easiest that i can do!

`^/users/(?P<id>[^/]+?)/$`
- `^` means that's the begging of the string, meaning that cannot has any character before `/users`
- `$` means like the same, but cannot has any other character after `/(?P<id>[^/]+?)/`
- `(?P<id>...)` means that all match that has in this part of the regex will be matched as group `id` as we can see `<id>`
- `[^/]+?` means that we want to match one or more characters, except new lines and slash (`/`) 

So, now we got it! we need to be able to pass something like `/users/{id}` and get a regex pre-compiled as `^/users/(?P<id>[^/]+?)/$`.

So let's comeback to our `Router` class, and we have this `add` method that will be responsible for get the URL and the method should be executed:

```python
    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler
```

Now our dict need to has our converted URL, and not the original URL, let's start by creating a method that will convert those URL's for us:
```python
    def parse_dynamic_url(self, url):
        leading_slash = url.startswith('/')
        trailing_slash = url.endswith('/')
        url = url.strip('/')

        pattern = re.compile(r"{(.*?)}")

        url_path = [
            pattern.sub(lambda m: f"(?P<{m.group(1)}>[^/]+?)", part)
            for part in url.split('/') if part
        ]

        path = '/' + '/'.join(url_path) if leading_slash else '/'.join(url_path)
        if trailing_slash and not path.endswith('/'):
            path += '/'

        return f"^{path}$"
```

Let's start by `pattern = re.compile(r"{(.*?)}")` this piece of code will make a regex already compiled to match for path in the URL that sould be dynamic!
For example `/users/{id}` or `/book/{name}`, we need to be able to now that has a dynamic input between `{}`, and this is the purpose of it!

```python
url_path = [
    pattern.sub(lambda m: f"(?P<{m.group(1)}>[^/]+?)", part)
    for part in url.split('/') if part
]
```

will split by slash (`/`) our URL in piece and if there's a part of the URL that match with our regex, it will be converted to our boilerplate!
for example `/book/{name}/action/{author}` -> `/book/(?P<name>[^/]+?)/action/(?P<author>[^/]+?)`

Now, the last part:
```python
def parse_dynamic_url(self, url):
        leading_slash = url.startswith('/')
        trailing_slash = url.endswith('/')
        ...
        path = '/' + '/'.join(url_path) if leading_slash else '/'.join(url_path)
        if trailing_slash and not path.endswith('/'):
            path += '/'

        return f"^{path}$"
```

it basicly add slash in the begging or in the end back if you did it 
- `/book/{name}/action/{author}` -> `^/book/(?P<name>[^/]+?)/action/(?P<author>[^/]+?)$`
- `/book/{name}/action/{author}/` -> `^/book/(?P<name>[^/]+?)/action/(?P<author>[^/]+?)/$`
- `book/{name}/action/{author}/` -> `^book/(?P<name>[^/]+?)/action/(?P<author>[^/]+?)/$`

I hardly suggest you debug and test this method by your own, it will makes more sense when you see it working.

Now that we have method to convert our path into a regex pre-compiled, we have to refactor `add` method:
```python
    def add(self, path, methods_handler):
        self.mapping[self.parse_dynamic_url(path)] = methods_handler
```

On our `dispatch` method, we need to handle the request and iterate over our mapping array with our endpoints and match them with our regex, if not matched, we move for the next on unless we find it ou return for the client an `404` not found. 
```python
    async def dispatch(self, request: Request):
        # Iterate through the compiled patterns
        for url, pattern in self.mapping.items():
            match = re.match(url, request.url)
            if not match:
                continue
    
            params = match.groupdict()
            handler = self.mapping[url].get(request.method)
    
            if handler:
                await self.request_callback_handler(handler, request, **params)
                return
        # Handle 404 Not Found if no matching route or method is found
        await self.response_writer(
            Response(
                404,
                {'message': 'Not Found'}
            )
        )
```
Since matched with our regex, we can use `match.groupdict()` to get an dict back with our groups! and them pass with kwargs into our route.

And, that's it! Now we just need to add a new route into our hello_world file (`python_web_framework/src/routes/hello_world.py`)

```python
    async def process_dynamic_url(request: Request, name: str):
        try:
            return Response(
                200,
                {
                    'msg': f'Hello {name}'
                }
            )
        except Exception as e:
            print(e)
    
    server.add_route("/hello_world/{name}", {
        "GET": process_dynamic_url
    })
```

With our new route done, we can test on our terminal with:
```bash
curl -X GET http://127.0.0.1:8080/hello_world/Gabs
{"msg": "Hello Gabs"}
```

And that's it! Now you have your own simple Python framework. I hope this guide helped you understand how this type of framework works under the hood.






