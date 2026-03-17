"""
FastAPI example with RouteLit Mantine components.

This example demonstrates using the routelit-fastapi adapter with
routelit-mantine components for a modern UI.

Run with:
    uv run python examples/mantine_example.py

Open http://localhost:8000 in your browser.
"""

# mypy: disable-error-code="import-untyped,attr-defined,no-any-return,unused-ignore,import-not-found"

import time

import uvicorn
from fastapi import FastAPI
from routelit import RouteLit, RouteLitBuilder
from routelit_mantine import RLBuilder

from routelit_fastapi import RouteLitFastAPIAdapter

# Create FastAPI app
app = FastAPI()

# Initialize RouteLit with Mantine builder
rl = RouteLit(BuilderClass=RLBuilder)

# Configure FastAPI adapter
adapter = RouteLitFastAPIAdapter(rl).configure(app)


@rl.cache_data
def get_expensive_data() -> str:
    """Simulate expensive data fetch."""
    time.sleep(1)
    return "This data was cached after 1 second delay!"


@adapter.route("/")
def index_view(rl: RouteLitBuilder) -> None:
    """Home page demonstrating Mantine components."""
    rl.title("RouteLit FastAPI + Mantine")

    rl.header("Welcome to RouteLit FastAPI!")
    rl.subheader("With Mantine UI Components")

    rl.markdown("""
This example demonstrates the **routelit-fastapi** adapter with **routelit-mantine** components.

## Features:
- FastAPI integration
- Mantine UI components
- Session state management
- Caching
- Fragments
- Dialogs
""")

    # Text input
    name = rl.text_input(
        label="What is your name?",
        key="name",
        placeholder="Enter your name",
        default_value="",
    )
    rl.text(f"Hello, {name}!" if name else "")

    # Button with counter
    count = rl.session_state.get("count", 0)
    if rl.button("Increment counter"):
        rl.session_state["count"] = count + 1
        rl.rerun()
    rl.text(f"Counter: {count}")

    # Cached data
    rl.subheader("Cached Data Example")
    if rl.button("Fetch expensive data"):
        rl.session_state["show_data"] = True
        rl.rerun()
    if rl.session_state.get("show_data"):
        cached_data = get_expensive_data()  # type: ignore[call-arg]
        rl.text(str(cached_data) if cached_data else "Loading...")

    # Select
    color = rl.select(
        label="Favorite color",
        key="color",
        options=["Red", "Green", "Blue", "Yellow"],
        default_value="",
    )
    rl.text(f"Selected color: {color}" if color else "")

    # Checkbox
    agree = rl.checkbox("I agree to the terms", checked=False)
    if agree:
        rl.text("Thank you for agreeing!")

    # Columns layout
    rl.subheader("Layout Example")
    col1, col2, col3 = rl.columns(3)
    with col1:
        rl.text("Card 1, This is the first column")
    with col2:
        rl.text("Card 2, This is the second column")
    with col3:
        rl.text("Card 3, This is the third column")

    # Link
    rl.hr()
    rl.link("https://routelit.github.io/routelit/", "RouteLit Documentation", is_external=True)


@rl.fragment("counter_fragment")
def counter_fragment(rl: RouteLitBuilder) -> None:
    """Fragment demonstrating partial updates."""
    rl.subheader("Fragment Counter")

    count = rl.session_state.get("fragment_count", 0)
    rl.text(f"Fragment count: {count}")

    if rl.button("Increment in fragment"):
        rl.session_state["fragment_count"] = count + 1
        rl.rerun(scope="fragment")

    if rl.button("Reset fragment"):
        rl.session_state.pop("fragment_count", None)
        rl.rerun(scope="fragment")


@adapter.route("/fragment-demo")
def fragment_demo_view(rl: RouteLitBuilder) -> None:
    """Page demonstrating fragment updates."""
    rl.title("Fragment Demo")

    rl.header("Fragment Demo")
    rl.markdown("""
Fragments allow you to update only a portion of the page instead of the entire view.
This is useful for performance optimization.
""")

    # Render the fragment
    counter_fragment(rl)

    # Main page counter (independent)
    rl.subheader("Main Page Counter")
    count = rl.session_state.get("main_count", 0)
    rl.text(f"Main count: {count}")
    if rl.button("Increment main"):
        rl.session_state["main_count"] = count + 1
        rl.rerun()

    rl.link("/", "Back to home")


@rl.dialog("confirm_dialog")
def confirm_dialog(rl: RouteLitBuilder) -> None:
    """Confirmation dialog."""
    action = rl.session_state.get("dialog_action", "confirm")
    rl.header(f"Confirm {action}")
    rl.text(f"Are you sure you want to {action}?")

    if rl.button("Confirm"):
        rl.session_state["confirmed_action"] = action
        rl.rerun(scope="app")

    if rl.button("Cancel"):
        rl.rerun(scope="app")


@adapter.route("/dialog-demo")
def dialog_demo_view(rl: RouteLitBuilder) -> None:
    """Page demonstrating dialog usage."""
    rl.title("Dialog Demo")

    rl.header("Dialog Demo")
    rl.markdown("""
Dialogs are modal overlays that require user interaction before returning to the main content.
""")

    if rl.button("Delete item"):
        rl.session_state["dialog_action"] = "delete"
        confirm_dialog(rl)

    if rl.button("Archive item"):
        rl.session_state["dialog_action"] = "archive"
        confirm_dialog(rl)

    if rl.session_state.get("confirmed_action"):
        rl.text(f"Confirmed action: {rl.session_state['confirmed_action']}", color="green")

    rl.link("/", "Back to home")


@adapter.route("/form-demo")
def form_demo_view(rl: RouteLitBuilder) -> None:
    """Page demonstrating form handling."""
    rl.title("Form Demo")

    rl.header("Form Demo")

    with rl.form("contact_form"):
        name = rl.text_input(label="Name", required=True, key="name")
        email = rl.text_input(label="Email", type="email", required=True, key="email")
        message = rl.textarea(label="Message", rows=4, key="message")

        if rl.form_submit_button("Submit"):
            rl.session_state["form_submitted"] = True
            rl.session_state["form_data"] = {"name": name, "email": email, "message": message}
            rl.rerun()

    if rl.session_state.get("form_submitted"):
        data = rl.session_state.get("form_data", {})
        rl.text("Form submitted successfully!", color="green")
        rl.markdown(f"""
**Submitted Data:**
- Name: {data.get("name", "N/A")}
- Email: {data.get("email", "N/A")}
- Message: {data.get("message", "N/A")}
""")

    rl.link("/", "Back to home")


@adapter.stream_route("/stream-demo")
async def stream_demo_view(rl: RouteLitBuilder) -> None:
    """Streaming demo with async updates."""
    import asyncio

    rl.title("Stream Demo")
    rl.header("Streaming Demo")
    rl.text("Starting stream...")

    for i in range(10):
        await asyncio.sleep(0.5)
        rl.text(f"Step {i + 1}/10 completed")

    rl.text("Stream complete!", color="green")
    rl.link("/", "Back to home")


if __name__ == "__main__":
    print("Starting FastAPI server at http://localhost:8000")
    print("Available routes:")
    print("  - / (Home)")
    print("  - /fragment-demo (Fragment Demo)")
    print("  - /dialog-demo (Dialog Demo)")
    print("  - /form-demo (Form Demo)")
    print("  - /stream-demo (Stream Demo)")
    uvicorn.run(app, host="127.0.0.1", port=8000)
