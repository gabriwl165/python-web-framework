import asyncio
import json


async def send_get():
    message = 'GET /hello_world HTTP/1.1\r\nHost: example.com\r\n\r\n'
    reader, writer = await asyncio.open_connection('127.0.0.1', 8080)

    print(f'Send: {message}')
    writer.write(message.encode())

    data = await reader.read(900)
    print(f'Received: {data.decode()}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()


async def send_post():
    message_template = (
        'PUT /hello_world HTTP/1.1\r\n'
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


if __name__ == "__main__":
    asyncio.run(send_post())
