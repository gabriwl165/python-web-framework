import asyncio
import signal


def run_app(app, host="127.0.0.1", port=8080, loop=None):
    """
    Function to run the application
    :params app ->Application
    :params host
    :params port
    :params loop
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    protocol = app._make_server()
    loop.run_until_complete(app.startup())

    server = loop.run_until_complete(
        loop.create_server(lambda: protocol, host=host, port=port)
    )

    loop.add_signal_handler(
        signal.SIGTERM, lambda: asyncio.ensure_future(app.shutdown())
    )

    try:
        print(f"Started server on {host}:{port}")
        loop.run_until_complete(server.serve_forever())
    except KeyboardInterrupt:
        # TODO: Graceful shutdown here
        loop.run_until_complete(app.shutdown())
        server.close()
        loop.stop()

