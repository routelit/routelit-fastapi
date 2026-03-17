"""
Example FastAPI application using RouteLit adapter.

This example demonstrates:
1. A counter application using the standard response() method
2. A streaming counter application using stream_response() method

Run with:
    uvicorn example:app --reload --port 8000

Then open http://localhost:8000 for the counter example
or http://localhost:8000/stream for the streaming example.
"""

# mypy: disable-error-code="import-untyped,attr-defined,no-any-return,unused-ignore,import-not-found"

import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import Response
from routelit import RouteLit, RouteLitBuilder

from routelit_fastapi import RouteLitFastAPIAdapter

# Create FastAPI app
app = FastAPI(
    title="RouteLit FastAPI Example",
    description="Example demonstrating RouteLit adapter with FastAPI",
)

# Create RouteLit instance
routelit = RouteLit()

# Create and configure the adapter
adapter = RouteLitFastAPIAdapter(routelit).configure(app)


# =============================================================================
# Example 1: Standard Counter with response()
# =============================================================================


def build_counter_view(rl: RouteLitBuilder) -> None:
    """
    Counter view function.

    Displays a counter with increment and decrement buttons.
    Uses session state to persist the counter value.
    """
    # Initialize counter in session state if not present
    if "counter" not in rl.session_state:
        rl.session_state["counter"] = 0

    counter = rl.session_state["counter"]

    rl.title("Counter Example")
    rl.markdown("### Standard Response Example")
    rl.markdown("This counter uses the standard `response()` method.")
    rl.hr()

    # Display counter value
    rl.markdown(f"## Count: **{counter}**")

    rl.hr()

    # Counter controls
    col1, col2, col3 = rl.columns(3)

    with col1:
        if rl.button("- Decrease", key="decrease"):
            rl.session_state["counter"] = counter - 1
            rl.rerun()

    with col2:
        if rl.button("Reset", key="reset"):
            rl.session_state["counter"] = 0
            rl.rerun()

    with col3:
        if rl.button("+ Increase", key="increase"):
            rl.session_state["counter"] = counter + 1
            rl.rerun()

    rl.markdown("---")
    rl.markdown("Try the [Streaming Counter Example](/stream) for a different experience!")


@app.api_route("/", methods=["GET", "POST"])
async def counter(request: Request) -> Response:
    """Standard counter endpoint using response()."""
    return await adapter.response(build_counter_view, request)


# =============================================================================
# Example 2: Streaming Counter with stream_response()
# =============================================================================


async def build_streaming_counter_view(rl: RouteLitBuilder) -> None:
    """
    Streaming counter view function.

    Displays a counter that can be incremented with streaming updates.
    """
    # Initialize counter in session state if not present
    if "stream_counter" not in rl.session_state:
        rl.session_state["stream_counter"] = 0

    counter = rl.session_state["stream_counter"]

    rl.title("Streaming Counter Example")
    rl.markdown("### Streaming Response Example")
    rl.markdown("This counter uses the `stream_response()` method to stream updates to the client.")
    rl.hr()

    # Display counter value
    rl.markdown(f"## Count: **{counter}**")

    rl.hr()

    # Counter controls
    col1, col2, col3 = rl.columns(3)

    with col1:
        if rl.button("increment", key="count5"):
            rl.session_state["stream_counter"] = rl.session_state["stream_counter"] + 1
            rl.rerun()

    with col2:
        if rl.button("Decrement", key="count10"):
            rl.session_state["stream_counter"] = rl.session_state["stream_counter"] - 1
            rl.rerun()

    with col3:
        if rl.button("Reset", key="reset_stream"):
            rl.session_state["stream_counter"] = 0
            rl.rerun()

    for i in range(0, counter):
        await asyncio.sleep(0.5)
        rl.text(f"Counting: {i + 1}")

    rl.markdown("---")
    rl.markdown("Go back to the [Standard Counter Example](/)")


@app.api_route("/stream", methods=["GET", "POST"])
async def streaming_counter(request: Request) -> Response:
    """Streaming counter endpoint using stream_response()."""
    return await adapter.stream_response(build_streaming_counter_view, request)


# =============================================================================
# Example 3: Using the route decorator
# =============================================================================


@adapter.route("/counter")
def counter_route(rl: RouteLitBuilder) -> None:
    """RouteLit route for the counter view using the route decorator."""
    build_counter_view(rl)


# Example using stream_route decorator
@adapter.stream_route("/stream-counter")
async def streaming_counter_route(rl: RouteLitBuilder) -> None:
    """RouteLit route for the streaming counter view."""
    await build_streaming_counter_view(rl)


# =============================================================================
# Run with: uvicorn example:app --reload --port 8000
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
