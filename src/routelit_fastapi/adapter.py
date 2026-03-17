import importlib.resources as resources
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from routelit import COOKIE_SESSION_KEY, AssetTarget, RouteLit, ViewFn
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from .request import FastAPIRLRequest
from .utils import get_default_static_path, get_default_template_path


class CookieConfig(TypedDict, total=False):
    """Configuration for session cookies."""

    max_age: int | None
    expires: datetime | str | int | None
    path: str | None
    domain: str | None
    secure: bool
    httponly: bool
    samesite: Literal["lax", "strict", "none"] | None
    partitioned: bool


production_cookie_config: CookieConfig = {
    "secure": True,
    "samesite": "none",
    "httponly": True,
    "max_age": 60 * 60 * 24 * 1,  # 1 day
}

RunMode = Literal["prod", "dev_client", "dev_components"]
"""
The run mode for the RouteLitFastAPIAdapter.

- `prod`: Production mode.
- `dev_client`: Development mode for the client.
- `dev_components`: Development mode for the components.
"""


class RunModeEnum(Enum):
    PROD = "prod"
    DEV_CLIENT = "dev_client"
    DEV_COMPONENTS = "dev_components"


class RouteLitFastAPIAdapter:
    """
    A FastAPI adapter for the RouteLit framework, enabling seamless integration of RouteLit's reactive UI components with FastAPI web applications.
    """

    def __init__(
        self,
        routelit: RouteLit,
        *,
        static_path: str | None = None,
        template_path: str = get_default_template_path(),
        run_mode: RunMode = "prod",
        local_frontend_server: str | None = None,
        local_components_server: str | None = None,
        cookie_config: CookieConfig | None = None,
    ):
        """
        Initialize the RouteLitFastAPIAdapter.
        - When run_mode="prod", no need to specify local_frontend_server and local_components_server.
        - When run_mode="dev_client", you need to specify local_frontend_server.
        - When run_mode="dev_components", you need to specify local_components_server.

        Args:
            routelit (RouteLit): The RouteLit instance.
            static_path (Optional[str]): The path to the static js/css assets are.
            template_path (str): The path to the index.html template file. Default is in routelit package, so no need to specify.
            run_mode (RunMode): The run mode. Example: "prod", "dev_client", "dev_components".
            local_frontend_server (Optional[str]): The local vite frontend server. Example: "http://localhost:5173".
            local_components_server (Optional[str]): The local vite components server. Example: "http://localhost:5174".
            cookie_config (Optional[dict[str, Any]]): The cookie configuration. Default is production cookie config.
        """
        self.routelit = routelit
        self.static_path = static_path or get_default_static_path()
        self.template_path = template_path
        self.run_mode = run_mode
        self.local_frontend_server = local_frontend_server
        self.local_components_server = local_components_server
        self.cookie_config: CookieConfig = (
            {**production_cookie_config, **(cookie_config or {})} if run_mode == "prod" else {}
        )
        self.templates: Jinja2Templates | None = None
        self.app: FastAPI | None = None

    @classmethod
    def configure_static_assets(cls, app: FastAPI, asset_target: AssetTarget) -> None:
        """
        Configure static assets for a package.

        Args:
            app: The FastAPI application.
            asset_target: The asset target configuration.
        """
        package_name, path = asset_target["package_name"], asset_target["path"]
        assets_path = resources.files(package_name).joinpath(path)
        app.mount(
            f"/routelit/{package_name}",
            StaticFiles(directory=str(assets_path), check_dir=False),
        )

    def configure(self, app: FastAPI) -> "RouteLitFastAPIAdapter":
        """
        Configure the FastAPI application to use the RouteLitFastAPIAdapter.

        Args:
            app: The FastAPI application to configure.

        Returns:
            The RouteLitFastAPIAdapter instance.
        """
        # Store the FastAPI app for later use in route decorators
        self.app = app

        # Configure static files FIRST (specific routes)
        for static_path in self.routelit.get_builder_class().get_client_resource_paths():
            self.configure_static_assets(app, static_path)

        # Mount routelit static files SECOND (general route)
        app.mount(
            "/routelit",
            StaticFiles(directory=self.static_path, check_dir=False),
        )

        # Configure Jinja2 templates
        self.templates = Jinja2Templates(directory=self.template_path)

        return self

    async def _handle_get_request(self, view_fn: ViewFn, request: Request, **kwargs: Any) -> HTMLResponse:
        """
        Handle GET request and return HTML response.

        Args:
            view_fn: The view function.
            request: The FastAPI Request instance.
            **kwargs: Additional keyword arguments to pass to the view function.

        Returns:
            HTMLResponse with the rendered template.
        """
        if self.templates is None:
            raise RuntimeError("Templates not configured. Call configure() first.")  # noqa: TRY003

        rl_request = FastAPIRLRequest(request)
        await rl_request.build()

        rl_response = self.routelit.handle_get_request(view_fn, rl_request, **kwargs)

        response = self.templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "ROUTELIT_DATA": rl_response.get_str_json_elements(),
                "PAGE_TITLE": rl_response.head.title,
                "PAGE_DESCRIPTION": rl_response.head.description,
                "RUN_MODE": self.run_mode,
                "LOCAL_FRONTEND_SERVER": self.local_frontend_server,
                "LOCAL_COMPONENTS_SERVER": self.local_components_server,
                "default_vite_assets": self.routelit.default_client_assets(),
                "importmap_json": self.routelit.get_importmap_json(),
                "vite_assets": self.routelit.client_assets(),
                "extra_head_content": self.routelit.get_extra_head_content(),
                "extra_body_content": self.routelit.get_extra_body_content(),
            },
        )

        # Set session cookie
        response.set_cookie(
            COOKIE_SESSION_KEY,
            rl_request.get_session_id(),
            max_age=self.cookie_config.get("max_age"),
            expires=self.cookie_config.get("expires"),
            path=self.cookie_config.get("path"),
            domain=self.cookie_config.get("domain"),
            secure=self.cookie_config.get("secure", False),
            httponly=self.cookie_config.get("httponly", False),
            samesite=self.cookie_config.get("samesite"),
            partitioned=self.cookie_config.get("partitioned", False),
        )

        return response

    async def response(
        self,
        view_fn: ViewFn,
        request: Request,
        inject_builder: bool | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """
        Handle a request and return a response.

        Args:
            view_fn (ViewFn): The view function to handle the request.
            request (Request): The FastAPI request.
            inject_builder (Optional[bool]): Whether to inject the builder into the request.
            *args: Additional arguments to pass to the view function.
            **kwargs: Additional keyword arguments to pass to the view function.

        Returns:
            A FastAPI response.
        """
        rl_request = FastAPIRLRequest(request)
        await rl_request.build()

        if rl_request.method == "POST":
            actions = self.routelit.handle_post_request(view_fn, rl_request, inject_builder, *args, **kwargs)
            return JSONResponse(content=actions)
        else:
            return await self._handle_get_request(view_fn, request, **kwargs)

    async def stream_response(
        self,
        view_fn: ViewFn,
        request: Request,
        inject_builder: bool | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """
        Handle a request and return a streaming response.

        Args:
            view_fn (ViewFn): The view function to handle the request.
            request (Request): The FastAPI request.
            inject_builder (Optional[bool]): Whether to inject the builder into the request.
            *args: Additional arguments to pass to the view function.
            **kwargs: Additional keyword arguments to pass to the view function.

        Returns:
            A FastAPI streaming response.
        """
        rl_request = FastAPIRLRequest(request)
        await rl_request.build()

        if rl_request.method == "POST":
            stream = self.routelit.handle_post_request_stream_jsonl(
                view_fn, rl_request, inject_builder, *args, **kwargs
            )
            return StreamingResponse(
                stream,
                media_type="application/jsonlines",
            )
        else:
            return await self._handle_get_request(view_fn, request, **kwargs)

    def route(self, path: str, methods: list[str] | None = None) -> Callable[[ViewFn], None]:
        """
        Decorator to register a route with the adapter and FastAPI.

        Args:
            path: The URL path for the route.
            methods: List of HTTP methods to allow.

        Returns:
            A decorator function.

        Example:
            @adapter.route("/counter")
            def counter_view(rl: RouteLitBuilder) -> None:
                rl.markdown("Hello")
        """
        if methods is None:
            methods = ["GET", "POST"]

        def decorator(view_fn: ViewFn) -> None:
            if self.app is None:
                raise RuntimeError("Adapter not configured. Call configure() first.")  # noqa: TRY003

            async def endpoint(request: Request) -> Response:
                return await self.response(view_fn, request)

            # Register with FastAPI
            for method in methods:
                if method.upper() == "GET":
                    self.app.get(path)(endpoint)
                elif method.upper() == "POST":
                    self.app.post(path)(endpoint)
                else:
                    # For other methods, use the generic route
                    self.app.api_route(path, methods=[method])(endpoint)

        return decorator

    def stream_route(self, path: str, methods: list[str] | None = None) -> Callable[[ViewFn], None]:
        """
        Decorator to register a streaming route with the adapter and FastAPI.

        Args:
            path: The URL path for the route.
            methods: List of HTTP methods to allow.

        Returns:
            A decorator function.

        Example:
            @adapter.stream_route("/stream")
            async def stream_view(rl: RouteLitBuilder) -> None:
                for i in range(10):
                    rl.text(f"Count: {i}")
        """
        if methods is None:
            methods = ["GET", "POST"]

        def decorator(view_fn: ViewFn) -> None:
            if self.app is None:
                raise RuntimeError("Adapter not configured. Call configure() first.")  # noqa: TRY003

            async def endpoint(request: Request) -> Response:
                return await self.stream_response(view_fn, request)

            # Register with FastAPI
            for method in methods:
                if method.upper() == "GET":
                    self.app.get(path)(endpoint)
                elif method.upper() == "POST":
                    self.app.post(path)(endpoint)
                else:
                    self.app.api_route(path, methods=[method])(endpoint)

        return decorator
