import asyncio

import pytest


@pytest.fixture
def event_loop():
    """Create a fresh event loop for each test and ensure proper cleanup."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    # Cancel all pending tasks before closing the loop
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

    # Let cancelled tasks run one loop iteration
    loop.run_until_complete(asyncio.sleep(0))

    # Close the loop
    loop.close()
    asyncio.set_event_loop(None)
