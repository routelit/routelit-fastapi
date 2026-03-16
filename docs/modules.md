# API Reference

This page contains the API reference documentation for the RouteLit FastAPI adapter.

## RouteLitFastAPIAdapter

::: routelit_fastapi.adapter.RouteLitFastAPIAdapter
handler: python
options:
members: - **init** - configure - configure_static_assets - route - stream_route - response - stream_response
show_root_heading: true
show_source: false
heading_level: 3

## CookieConfig

::: routelit_fastapi.adapter.CookieConfig
handler: python
options:
show_root_heading: true
show_source: false
heading_level: 3

## RunMode

::: routelit_fastapi.adapter.RunMode
handler: python
options:
show_root_heading: true
show_source: false
heading_level: 3

## RunModeEnum

::: routelit_fastapi.adapter.RunModeEnum
handler: python
options:
show_root_heading: true
show_source: false
heading_level: 3

## FastAPIRLRequest

::: routelit_fastapi.request.FastAPIRLRequest
handler: python
options:
members: - **init** - build - get_headers - get_path_params - get_referrer - get_json - get_files - is_json - is_multipart - get_query_param - get_query_param_list - get_session_id - get_pathname - get_host - method - ui_event - fragment_id
show_root_heading: true
show_source: false
heading_level: 3

## Exports

The following are exported from the `routelit_fastapi` package:

```python
from routelit_fastapi import (
    RouteLitFastAPIAdapter,  # Main adapter class
    RunMode,                  # Literal type for run modes
    RunModeEnum,              # Enum for run modes
    CookieConfig,             # TypedDict for cookie configuration
)
```
