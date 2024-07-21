
# A Python Web Framework

Building a Web Framework, we can start with 
some pillars, such as:
* Transport and Protocol
* Request and Response objects
* Application and Url Dispatcher
* Exception Handling
* Middleware

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

### This code is synchronous
As we can see in 
```python
while True:
    data, addr = s.recvfrom(MAX)
```
Our code make a synchronous while true, and wait for receive a request from anything, meaning that we can make a request, but if we make another before the server is done with the first, this request will need to wait

### Our code spend time waiting for transmittion
As we can see in 

```python
s.send(b'This is another message')
data = s.recv(MAX)
```
`send` and `recv` wait for send and receive that in the network, and this can be delegate to the OS handle those things

So, lets start builing a web server that can handle multiple requests and do not waste time with things that can be outsourced
## Transport and Protocol

Currently in python, has many ways to handle parallel process, such as:

* Process (multiprocessing)
* Thread (threading)
* AsyncIO (asyncio)

In the project we are going to cover the usage with asyncio.

AsyncIO is a library to write concurrent code using the async/await syntax. asyncio is used as a foundation for multiple Python asynchronous frameworks that provide high-performance network and web-servers.


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

So it means that, we can inherit this asyncio.Protocol, since we implement at least `data_received`, so, before we beginwe need to know that the data received in the socket, is actually bytes, nor string, so we need to implement a way to convert this data, and we can use `HttpRequestParser` from `httptools`

```python
class Server(asyncio.Protocol, HttpParserMixin):
    def __init__(self, loop, app):
        self._encoding = "utf-8"
        self._request_parser =  HttpRequestParser(self)

    def data_received(self, data):
        self._request_parser.feed_data(data)
```