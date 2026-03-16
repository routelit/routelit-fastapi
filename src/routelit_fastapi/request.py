import contextlib
import json
import uuid
from collections.abc import Mapping
from io import IOBase
from typing import Any, cast

from fastapi import Request
from routelit import COOKIE_SESSION_KEY, RouteLitRequest


class FastAPIRLRequest(RouteLitRequest):
    """
    Implements the RouteLitRequest interface for FastAPI.

    Usage:
        1. Create instance: rl_request = FastAPIRLRequest(request)
        2. Call build(): await rl_request.build()
        3. Use with RouteLit handlers: routelit.handle_post_request(..., rl_request, ...)

    The build() method must be called before using the request with RouteLit handlers.
    It pre-processes all async operations (body parsing, file extraction, ui_event parsing).
    """

    def __init__(self, request: Request):
        self.request = request
        self.__default_session_id = str(uuid.uuid4())
        self._json_data: dict[str, Any] | None = None
        self._form_data: dict[str, Any] | None = None
        self._files: list[IOBase] | None = None
        self._built = False

        # Initialize parent class attributes - will be properly set in build()
        self._ui_event: Any | None = None
        self._fragment_id: str | None = None

    async def build(self) -> None:
        """
        Pre-process all async operations for the request.

        This method must be called before using the request with RouteLit handlers.
        It handles:
        - JSON body parsing
        - Multipart form data parsing
        - File extraction from multipart forms
        - UI event parsing from the request body

        After calling this method, the request is ready to be used with:
        - routelit.handle_get_request()
        - routelit.handle_post_request()
        - routelit.handle_post_request_stream_jsonl()
        """
        if self._built:
            return

        self._built = True
        content_type = self.request.headers.get("content-type", "")

        # Parse body based on content type
        if "application/json" in content_type:
            self._json_data = await self.request.json()
        elif "multipart/form-data" in content_type:
            form = await self.request.form()
            self._form_data = dict(form)

            # Extract files from form data
            files: list[IOBase] = []
            for key, value in form.multi_items():
                # Check if value is a file upload (has filename attribute)
                if key == "files" and hasattr(value, "filename") and value.filename:
                    # Store filename on the file object for later access
                    file_obj = cast(IOBase, value.file)
                    file_obj.filename = value.filename  # type: ignore[attr-defined]
                    files.append(file_obj)
            self._files = files if files else None

            # Parse JSON from form data if present
            if "json" in self._form_data and isinstance(self._form_data["json"], str):
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    self._json_data = json.loads(self._form_data["json"])

        # Now that body is parsed, initialize parent class event data
        self._ui_event = self._get_ui_event()
        self._fragment_id = self._get_fragment_id()

    def get_headers(self) -> dict[str, str]:
        return dict(self.request.headers)

    def get_path_params(self) -> Mapping[str, Any] | None:
        return self.request.path_params

    def get_referrer(self) -> str | None:
        return self.request.headers.get("referer")

    @property
    def method(self) -> str:
        return self.request.method

    def get_json(self) -> dict[str, Any] | None:
        """
        Get JSON data from request body.

        Note: build() must be called before this method.
        """
        return self._json_data

    def get_files(self) -> list[IOBase] | None:
        """
        Get files from request body.

        Note: build() must be called before this method.
        """
        return self._files

    def is_json(self) -> bool:
        content_type = self.request.headers.get("content-type", "")
        return "application/json" in content_type

    def is_multipart(self) -> bool:
        content_type = self.request.headers.get("content-type", "")
        return content_type.startswith("multipart/form-data")

    def get_query_param(self, key: str) -> str | None:
        return self.request.query_params.get(key)

    def get_query_param_list(self, key: str) -> list[str]:
        return list(self.request.query_params.getlist(key))

    def get_session_id(self) -> str:
        return self.request.cookies.get(COOKIE_SESSION_KEY, self.__default_session_id)

    def get_pathname(self) -> str:
        return self.request.url.path

    def get_host(self) -> str:
        return self.request.url.netloc

    @property
    def ui_event(self) -> Any | None:
        """
        Get the UI event from the request.

        Note: build() must be called before accessing this property.
        """
        return self._ui_event

    @property
    def fragment_id(self) -> str | None:
        """
        Get the fragment ID from the request.

        Note: build() must be called before accessing this property.
        """
        return self._fragment_id
