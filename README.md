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

One important aspect of web development is handling dynamic URLs, and what I want to say is that it's normal to have these kinds of URLs.
```bash
/users/{id}
```

And then, we send a request like:
```bash 
GET /users/123456
```

And we need to be able to handle this ID as a parameter, for example:
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

And you might start to think, 'This is so complex; there must be some sophisticated business logic to implement it.' And voilà, this can be achieved by using regex in our `Router` class.
First, let's understand how regex works and how this can be achieved. We have two strings `"/users/{id}/"` and `"/users/12345/"`. Let's create a prototype:
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
- `()` Captures and stores whatever matches the pattern inside the parentheses.
- `.` Matches any character except a newline
- `+` A quantifier that matches one or more of the preceding token
- `?` Matches as few characters as possible (non-greedy match)."

But there's a better way to handle this regex. We have a feature called 'groups' that allows us to use the `groupdict()` method to get a dictionary. 
```json
{
  "id": "123"
}
```
And this helps us a lot! With this dictionary, we can deconstruct it using `**` and pass it as keyword arguments into our methods, routers, or controllers. 
Our new regex pattern will be (?P<id>.+?). Let's take a brief dive into this regex!
- `(?P<id>...)` Captures the matched content as id in our dictionary, just as we want.
- `.+?` Matches one or more characters, except for a newline, using a non-greedy approach.

```python
import re

match = re.match(r'^/users/(?P<id>[^/]+?)/$', "/users/123/")
match.groupdict()
"""
Our response should look like this:
{'id': '123'}
"""
```

And I know, you're probably thinking 'Oh god' after seeing this regex, but I'll try to make it as simple as I can!

`^/users/(?P<id>[^/]+?)/$`
- `^` Indicates the beginning of the string, meaning no characters can appear before `/users`
- `$` Indicates the end of the string, meaning no characters can appear after `/(?P<id>[^/]+?)/`
- `(?P<id>...)` Matches anything within this part of the regex and captures it as the group id, which we can reference as `<id>`.
- `[^/]+?` Matches one or more characters except for newlines and the slash `(/)`, in a non-greedy manner. 

So now we get it! We need to be able to pass something like `/users/{id}` and have it pre-compiled as the regex `^/users/(?P<id>[^/]+?)/$`.

Now, let's return to our Router class. We have an add method that will be responsible for receiving the URL and determining which method should be executed.

```python
    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler
```

Now, our dictionary needs to have the converted URL, not the original one. Let's start by creating a method that will convert these URLs for us.
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

Let's start with `pattern = re.compile(r"{(.*?)}")`. This code compiles a regex pattern to match any dynamic parts of the URL that should be variable.

For example, with URLs like `/users/{id}` or `/book/{name}`, we need to recognize that there is dynamic input between the `{}` brackets, and this regex helps us identify it.

```python
url_path = [
    pattern.sub(lambda m: f"(?P<{m.group(1)}>[^/]+?)", part)
    for part in url.split('/') if part
]
```

We'll split our URL into pieces by the slash (`/`). If any part of the URL matches our regex, it will be converted into our boilerplate format.

For example, `/book/{name}/action/{author}` would be transformed into `/book/(?P<name>[^/]+?)/action/(?P<author>[^/]+?)`.

Now, for the last part:
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

It basically adds a slash at the beginning or the end, if it was originally there. 
- `/book/{name}/action/{author}` -> `^/book/(?P<name>[^/]+?)/action/(?P<author>[^/]+?)$`
- `/book/{name}/action/{author}/` -> `^/book/(?P<name>[^/]+?)/action/(?P<author>[^/]+?)/$`
- `book/{name}/action/{author}/` -> `^book/(?P<name>[^/]+?)/action/(?P<author>[^/]+?)/$`

I highly suggest you debug and test this method on your own, it will make more sense when you see it working.

Now that we have a method to convert our path into a pre-compiled regex, we need to refactor the `add` method.
```python
    def add(self, path, methods_handler):
        self.mapping[self.parse_dynamic_url(path)] = methods_handler
```

In our `dispatch` method, we need to handle the request by iterating over our mapping array of endpoints and matching each one with our regex. 
If there's no match, we move to the next endpoint until we find a match or return a `404 Not Found` to the client. 
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
Once a match is found with our regex, we can use `match.groupdict()` to get a dictionary with our captured groups. Then, we pass it as keyword arguments (`kwargs`) into our route.

And that's it! Now, we just need to add a new route to our `hello_world` file `(python_web_framework/src/routes/hello_world.py)`.

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

With our new route created, we can test it in our terminal with:
```bash
curl -X GET http://127.0.0.1:8080/hello_world/Gabs
{"msg": "Hello Gabs"}
```

## Let's make some refactors

When we're building a route, we come across with som boiler plates, like this:
```python
def hello_world_app(server: Server):
    async def hello_world(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body}")

    server.add_route("/hello_world", {"GET": hello_world})
```

But, nowadays, this is not the standard for many framework that provide routing system for us, like FastAPI:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
```

So, what can we do to improve our library? Maybe provide an object that provide us @Get, @Post, @Put like all other framework, instead of `server.add_route("/hello_world", {"GET": hello_world})`, that we used to do before, so let's begin!

First, out `main.py` should look like this:
```python
from python_web_framework.src.app import App
from routes.hello_world import hello_world_app

app = App()


if __name__ == "__main__":
    hello_world_app(app)
    app.start('127.0.0.1', 8080)
```

What we can do to make this happen? let's begin from building our App class:
First, we need to create our constructor, it will instantiate all objects that is necessary
```python
class App:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.server = Server(self.loop)
        self.socket = None
```

- `self.loop` will handle the current loop in our process from asyncio
- `self.server` will handle our `Server` class that we've built
- `self.socket` will handle our binding into the operational system 

So, with all this attributes instantiate, we can start build our decorators, let's from a simple `POST`, because the rest will be the same boiler plate

```python
class App:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.server = Server(self.loop)
        self.socket = None

    def post(self, path):
        def decorator(func):
            self.server.add_route(path, "POST", func)
            return func
        return decorator
```

Basically, our `post` method return another method, that we can call it for `decorator`, `wrapper`, there's many ways to call it.
Our self.server.add_route is doing all the jobs though, so let's dive into what our `Server` class is doing!

Our `add_route` is going to look like this:
```python
    def add_route(self, path: str, methods_handler: dict):
        self.add(path, methods_handler)
```

But now we need to add the HTTP Status also (e.g. POST, GET, PUT, etc), so let's make like this:
```python
    def add_route(self, path: str, method: str, handler: Callable):
        self.add(path, method, handler)
```

But this little change affect our `Router` class, so we need to make some refactors there too.
The fist change is going to be our `add` method, that look like this:
```python
    def add(self, path, methods_handler):
        self.mapping[self.parse_dynamic_url(path)] = methods_handler
```

Let's change it from a dict to a list of sets, since now we need to match the URL + HTTP method, dict will not help us so much.
```python
    def add(self, path: str, method: str, handler: Callable):
        self.mapping.append((self.parse_dynamic_url(path), method, handler))
```
But, change it from a dict to a list will impact that we need to change our `Server` class, that used to look like this:
```python
class Server(asyncio.Protocol, Router):
    def __init__(self, loop=None):
        self.mapping = {}
        self.loop = loop or asyncio.get_event_loop()
        self.encoding = "utf-8"
        self.url = None
        self.body = None
        self.transport: Optional[asyncio.Transport] = None
        self._request_parser = HttpRequestParser(self)
```

To it
```python
class Server(asyncio.Protocol, Router):
    def __init__(self, loop=None):
        self.mapping = []
        self.loop = loop or asyncio.get_event_loop()
        self.encoding = "utf-8"
        self.url = None
        self.body = None
        self.transport: Optional[asyncio.Transport] = None
        self._request_parser = HttpRequestParser(self)
```

So, let's go back to our `Router` class, because we didnt finished yet. Our `dispatch` method that used to look like this:
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

Since now our `mapping` it's a list, not a dict anymore, the follow code will not work anymore:
```python
    for url, pattern in self.mapping.items():
                match = re.match(url, request.url)
                if not match:
                    continue
    
                params = match.groupdict()
                handler = self.mapping[url].get(request.method)
    
                if handler:
                    await self.request_callback_handler(handler, request, **params)
                    return
```

So, one the way to deal with this problem, since we have the `request: Request` it's:
```python
    handler = [
        (handler, re.match(path, request.url))
        for path, method, handler in self.mapping
        if re.match(path, request.url) and
           method == request.method
    ]
```

`self.mapping` likely contains a list of tuples. Each tuple represents a route and consists of three elements
- `path` (the URL pattern),
- `method` (the HTTP method like GET, POST),
- `handler` (the function or class that will handle the request if the route matches)
- `request.url` is the URL of the incoming HTTP request.
- `request.method` is the HTTP method of the incoming request (e.g., GET, POST).
- `re.match()` is a regular expression function used to check if a URL matches a specific pattern, since our `add` method makes a `self.parse_dynamic_url` before add inside the list.

With `handler` we can know if there is a route with this pattern, so we can check after the list comprehension and response if not found:

```python
    if not handler:
        await self.response_writer(
            Response(
                404,
                {'message': 'Not Found'}
            )
        )
        return
```

If is everything OK, we can pass the request to our `request_callback_handler` from `Server`, that we're going to refactor also:

```python
    handle, match = handler[0]
    params = match.groupdict()
    if handler:
        await self.request_callback_handler(handle, request, **params)
        return
```

Back to our `Server` class, we need to make some adjust in `request_callback_handler` 
Our method used to look like this:
```python
    async def request_callback_handler(self, method, request, **kwargs):
        try:
            resp = await method(request, **kwargs)
        except Exception as exc:
            resp = format_exception(exc)

        if not isinstance(resp, Response):
            raise RuntimeError(f"expect Response instance but got {type(resp)}")

        self.response_writer(resp)
```

But i encounter a problem, if `format_exception(exc)` had some exception, we weren't handling it, making our socket to still connect and never relase the connection, so, we need to add another try/catch to handle it

```python
    async def request_callback_handler(self, method, request, **kwargs):
        try:
            try:
                resp = await method(request, **kwargs)
            except Exception as exc:
                resp = format_exception(exc)

            if not isinstance(resp, Response):
                raise RuntimeError(f"expect Response instance but got {type(resp)}")

            self.response_writer(resp)
        except Exception as _:
            self.response_writer(Response(
                500,
                {
                    'message': "Unexpected error"
                }
            ))
```

So, basically, we've refactored our `Server` and `Router` class to handle this new approach.

Back to our `App` class, we can add another decorator to handle another kind of HTTP methods:
```python
class App:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.server = Server(self.loop)
        self.socket = None

    def get(self, path):
        def decorator(func):
            self.server.add_route(path, "GET", func)
            return func
        return decorator

    def post(self, path):
        def decorator(func):
            self.server.add_route(path, "POST", func)
            return func
        return decorator

    def put(self, path):
        def decorator(func):
            self.server.add_route(path, "PUT", func)
            return func
        return decorator
```

With all of it done, there is just one last thing, how can we do to make this true? `app.start('127.0.0.1', 8080)`

We just need to extract the old code that used to look like this:
```python
    server = loop.run_until_complete(
        loop.create_server(lambda: protocol, host='127.0.0.1', port=8080)
    )
    loop.run_until_complete(server.serve_forever())
```

To inside our method that can be called `start`
```python

    def start(self, host, port):
        self.socket = self.loop.run_until_complete(
            self.loop.create_server(lambda: self.server, host=host, port=port)
        )
        print(f"Server started on {host}:{port}")
        self.loop.run_until_complete(self.socket.serve_forever())
```
 And that it's, we've refactored our framework to look like more with a standard industry that we've seen

And that's it! Now you have your own simple Python framework. I hope this guide helped you understand how this type of framework works under the hood.






