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