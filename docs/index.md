# RouteLit FastAPI Adapter

[![Release](https://img.shields.io/github/v/release/routelit/routelit-fastapi)](https://img.shields.io/github/v/release/routelit/routelit-fastapi)
[![Build status](https://img.shields.io/github/actions/workflow/status/routelit/routelit-fastapi/main.yml?branch=main)](https://github.com/routelit/routelit-fastapi/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/routelit/routelit-fastapi/branch/main/graph/badge.svg)](https://codecov.io/gh/routelit/routelit-fastapi)
[![Commit activity](https://img.shields.io/github/commit-activity/m/routelit/routelit-fastapi)](https://img.shields.io/github/commit-activity/m/routelit/routelit-fastapi)
[![License](https://img.shields.io/github/license/routelit/routelit-fastapi)](https://img.shields.io/github/license/routelit/routelit-fastapi)

A FastAPI adapter for the RouteLit framework, enabling seamless integration of RouteLit's reactive UI components with FastAPI web applications.

## Installation

```bash
pip install routelit routelit-fastapi
```

## Quick Start

Here's a complete example to get you started:

```python
from fastapi import FastAPI, Request
import uvicorn
from routelit import RouteLit, RouteLitBuilder
from routelit_fastapi import RouteLitFastAPIAdapter

# Create FastAPI app
app = FastAPI()

# Create RouteLit instance
routelit = RouteLit()

# Create and configure the adapter
adapter = RouteLitFastAPIAdapter(routelit).configure(app)

# Define your view function
def build_hello_view(rl: RouteLitBuilder):
    name = rl.text_input(label="What is your name", placeholder="John", default_value="")
    rl.write(f"Hello {name}")
    if rl.button("Submit"):
        rl.write("Thanks for your submission!")

# Option 1: Traditional approach with explicit route registration
@app.api_route("/", methods=["GET", "POST"])
async def hello(request: Request):
    return await adapter.response(build_hello_view, request)

# Option 2: Simplified decorator approach (recommended)
@adapter.route("/")
def hello_view(rl: RouteLitBuilder):
    name = rl.text_input(label="What is your name", placeholder="John", default_value="")
    rl.write(f"Hello {name}")
    if rl.button("Submit"):
        rl.write("Thanks for your submission!")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Features

- **Framework Agnostic**: Works seamlessly with FastAPI
- **Declarative UI**: Build interfaces using simple Python functions with a builder pattern
- **Interactive Components**: Buttons, forms, inputs, selects, checkboxes, containers, columns, etc.
- **State Management**: Built-in session state management with cookie-based sessions
- **Reactive Updates**: Automatic UI updates based on user interactions
- **HTTP Streaming**: Support for streaming responses using JSONL
- **Development Mode**: Hot reloading support for frontend development

## Usage

### Basic Route Registration

You can register routes in two ways:

**Option 1: Traditional Approach**

```python
@app.api_route("/counter", methods=["GET", "POST"])
async def counter(request: Request):
    return await adapter.response(build_counter_view, request)
```

**Option 2: Simplified Decorator (Recommended)**

```python
@adapter.route("/counter")
def counter_view(rl: RouteLitBuilder):
    if "counter" not in rl.session_state:
        rl.session_state["counter"] = 0

    counter = rl.session_state["counter"]
    rl.markdown(f"## Count: {counter}")

    if rl.button("Increment", key="inc"):
        rl.session_state["counter"] = counter + 1
        rl.rerun()
```

### Streaming Routes

For HTTP streaming responses using JSONL:

```python
# Traditional approach
@app.api_route("/stream", methods=["GET", "POST"])
async def stream_endpoint(request: Request):
    return await adapter.stream_response(build_stream_view, request)

# Simplified decorator (recommended)
@adapter.stream_route("/stream")
async def stream_view(rl: RouteLitBuilder):
    for i in range(10):
        rl.text(f"Count: {i}")
```

### Development Mode

For development with hot reloading of the frontend:

```python
adapter = RouteLitFastAPIAdapter(
    routelit,
    run_mode="dev_client",
    local_frontend_server="http://localhost:5173"
).configure(app)
```

## Configuration Options

When creating the adapter, you can configure the following options:

| Parameter                 | Type                   | Default             | Description                                         |
| ------------------------- | ---------------------- | ------------------- | --------------------------------------------------- |
| `static_path`             | `str \| None`          | Auto-detected       | Custom path for static assets                       |
| `template_path`           | `str`                  | Auto-detected       | Custom path for templates                           |
| `run_mode`                | `str`                  | `"prod"`            | One of `"prod"`, `"dev_client"`, `"dev_components"` |
| `local_frontend_server`   | `str \| None`          | `None`              | URL of local Vite dev server (for dev mode)         |
| `local_components_server` | `str \| None`          | `None`              | URL of local components dev server (for dev mode)   |
| `cookie_config`           | `CookieConfig \| None` | Production defaults | Custom cookie configuration                         |

### Run Modes

- **`prod`**: Production mode with secure cookie settings
- **`dev_client`**: Development mode for the client with hot reloading
- **`dev_components`**: Development mode for the components

### Cookie Configuration

In production mode, the default cookie configuration is:

```python
{
    "secure": True,
    "samesite": "none",
    "httponly": True,
    "max_age": 60 * 60 * 24 * 1,  # 1 day
}
```

You can override these settings:

```python
adapter = RouteLitFastAPIAdapter(
    routelit,
    cookie_config={
        "secure": False,
        "max_age": 3600,  # 1 hour
    }
).configure(app)
```

## API Reference

For detailed API documentation, see the [Modules](modules.md) page.

## Example Application

Check out the [example application](https://github.com/routelit/routelit-fastapi/tree/main/src/example) in the repository for a complete working example with:

- Counter example using standard responses
- Streaming counter example with real-time updates
- Multiple route patterns

## License

Apache-2.0 License

## Maintainer

Maintained by [@rolangom](https://x.com/rolangom).
