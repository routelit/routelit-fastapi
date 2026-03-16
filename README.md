# RouteLit FastAPI Adapter

[![Release](https://img.shields.io/github/v/release/routelit/routelit-fastapi)](https://img.shields.io/github/v/release/routelit/routelit-fastapi)
[![Build status](https://img.shields.io/github/actions/workflow/status/routelit/routelit-fastapi/main.yml?branch=main)](https://github.com/routelit/routelit-fastapi/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/routelit/routelit-fastapi/branch/main/graph/badge.svg)](https://codecov.io/gh/routelit/routelit-fastapi)
[![Commit activity](https://img.shields.io/github/commit-activity/m/routelit/routelit-fastapi)](https://img.shields.io/github/commit-activity/m/routelit/routelit-fastapi)
[![License](https://img.shields.io/github/license/routelit/routelit-fastapi)](https://img.shields.io/github/license/routelit/routelit-fastapi)


![Routelit](https://wsrv.nl/?url=res.cloudinary.com/rolangom/image/upload/v1747976918/routelit/routelit_c2otsv.png&w=300&h=300)

A FastAPI adapter for the RouteLit framework, enabling seamless integration of RouteLit's reactive UI components with FastAPI web applications.

## Installation

```bash
pip install routelit routelit-fastapi
```

## Usage

```python
from fastapi import FastAPI, Request
from routelit import RouteLit, RouteLitBuilder
from routelit_fastapi import RouteLitFastAPIAdapter

app = FastAPI()
routelit = RouteLit()
routelit_adapter = RouteLitFastAPIAdapter(routelit).configure(app)


def build_index_view(rl: RouteLitBuilder):
    rl.text("Hello, World!")


# Option 1: Traditional approach with explicit route registration
@app.api_route("/", methods=["GET", "POST"])
async def index(request: Request):
    return await routelit_adapter.response(build_index_view, request)


# Option 2: Simplified decorator approach
@routelit_adapter.route("/")
def index_view(rl: RouteLitBuilder):
    rl.text("Hello, World!")
```

## Quick Start

Here's a complete example:

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

# Option 1: Traditional approach
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

## Development Mode

For development with hot reloading of the frontend:

```python
adapter = RouteLitFastAPIAdapter(
    routelit,
    run_mode="dev_client",
    local_frontend_server="http://localhost:5173"
).configure(app)
```

## Streaming Support

For HTTP streaming responses (using JSONL streaming):

```python
# Option 1: Traditional approach
@app.api_route("/stream", methods=["GET", "POST"])
async def stream_endpoint(request: Request):
    return await adapter.stream_response(build_view, request)


# Option 2: Simplified decorator approach (recommended)
@adapter.stream_route("/stream")
async def stream_view(rl: RouteLitBuilder):
    for i in range(10):
        rl.text(f"Count: {i}")
```

## Configuration Options

- `static_path`: Custom path for static assets
- `template_path`: Custom path for templates
- `run_mode`: One of `"prod"`, `"dev_client"`, `"dev_components"`
- `local_frontend_server`: URL of local Vite dev server (for dev mode)
- `local_components_server`: URL of local components dev server (for dev mode)
- `cookie_config`: Custom cookie configuration

Maintained by [@rolangom](https://x.com/rolangom).

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
