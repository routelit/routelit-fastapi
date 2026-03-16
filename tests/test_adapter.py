"""Tests for the RouteLitFastAPIAdapter class."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from routelit import RouteLit

from routelit_fastapi.adapter import RouteLitFastAPIAdapter, RunModeEnum


class TestRunModeEnum:
    """Test the RunModeEnum class."""

    def test_enum_values(self):
        """Test that enum has correct values."""
        assert RunModeEnum.PROD.value == "prod"
        assert RunModeEnum.DEV_CLIENT.value == "dev_client"
        assert RunModeEnum.DEV_COMPONENTS.value == "dev_components"


class TestRouteLitFastAPIAdapter:
    """Test the RouteLitFastAPIAdapter class."""

    @pytest.fixture
    def mock_routelit(self):
        """Create a mock RouteLit instance for testing."""
        mock_rl = Mock(spec=RouteLit)
        mock_builder = Mock()
        mock_builder.get_client_resource_paths.return_value = []
        mock_rl.get_builder_class.return_value = mock_builder
        mock_rl.default_client_assets.return_value = "default_assets"
        mock_rl.client_assets.return_value = "client_assets"
        return mock_rl

    @pytest.fixture
    def fastapi_app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app

    def test_init_default_values(self, mock_routelit):
        """Test adapter initialization with default values."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)

        assert adapter.routelit == mock_routelit
        assert adapter.run_mode == "prod"
        assert adapter.local_frontend_server is None
        assert adapter.local_components_server is None
        assert adapter.cookie_config == {
            "secure": True,
            "samesite": "none",
            "httponly": True,
            "max_age": 60 * 60 * 24 * 1,  # 1 day
        }

    def test_init_default_values_dev_mode(self, mock_routelit):
        """Test adapter initialization with default values in dev mode."""
        adapter = RouteLitFastAPIAdapter(mock_routelit, run_mode="dev_client")

        assert adapter.routelit == mock_routelit
        assert adapter.run_mode == "dev_client"
        assert adapter.local_frontend_server is None
        assert adapter.local_components_server is None
        assert adapter.cookie_config == {}  # Empty dict in dev mode

    def test_init_custom_values(self, mock_routelit):
        """Test adapter initialization with custom values."""
        adapter = RouteLitFastAPIAdapter(
            mock_routelit,
            static_path="/custom/static",
            template_path="/custom/templates",
            local_frontend_server="http://localhost:3000",
            local_components_server="http://localhost:3001",
        )

        assert adapter.static_path == "/custom/static"
        assert adapter.template_path == "/custom/templates"
        assert adapter.local_frontend_server == "http://localhost:3000"
        assert adapter.local_components_server == "http://localhost:3001"

    def test_init_custom_cookie_config_complete_override(self, mock_routelit):
        """Test adapter initialization with custom cookie configuration that completely overrides defaults."""
        from routelit_fastapi import CookieConfig

        custom_cookie_config: CookieConfig = {
            "secure": False,
            "samesite": "lax",
            "httponly": False,
            "max_age": 3600,
        }

        adapter = RouteLitFastAPIAdapter(mock_routelit, cookie_config=custom_cookie_config)

        # In production mode, custom config should completely override defaults
        assert adapter.cookie_config == {
            "secure": False,
            "samesite": "lax",
            "httponly": False,
            "max_age": 3600,
        }

    def test_init_custom_cookie_config_partial_override(self, mock_routelit):
        """Test adapter initialization with partial custom cookie configuration that merges with defaults."""
        from routelit_fastapi import CookieConfig

        # Only override some of the default values
        custom_cookie_config: CookieConfig = {
            "secure": False,
            "max_age": 7200,  # 2 hours instead of 1 day
        }

        adapter = RouteLitFastAPIAdapter(mock_routelit, cookie_config=custom_cookie_config)

        # In production mode, custom config should merge with defaults
        assert adapter.cookie_config == {
            "secure": False,  # Overridden
            "samesite": "none",  # Default preserved
            "httponly": True,  # Default preserved
            "max_age": 7200,  # Overridden
        }

    def test_init_cookie_config_none_prod_mode(self, mock_routelit):
        """Test adapter initialization with None cookie_config in production mode."""
        adapter = RouteLitFastAPIAdapter(mock_routelit, cookie_config=None)
        # In production mode with None cookie_config, should use default production config
        assert adapter.cookie_config == {
            "secure": True,
            "samesite": "none",
            "httponly": True,
            "max_age": 60 * 60 * 24 * 1,  # 1 day
        }

    def test_init_dev_components_mode(self, mock_routelit):
        """Test adapter initialization in dev_components mode."""
        adapter = RouteLitFastAPIAdapter(
            mock_routelit, run_mode="dev_components", local_components_server="http://localhost:3001"
        )

        assert adapter.run_mode == "dev_components"
        assert adapter.local_components_server == "http://localhost:3001"
        assert adapter.cookie_config == {}

    def test_init_dev_mode_with_cookie_config(self, mock_routelit):
        """Test that cookie_config is ignored in dev mode."""
        from routelit_fastapi import CookieConfig

        custom_cookie_config: CookieConfig = {
            "secure": False,
            "samesite": "lax",
            "httponly": False,
            "max_age": 3600,
        }
        adapter = RouteLitFastAPIAdapter(mock_routelit, run_mode="dev_client", cookie_config=custom_cookie_config)
        # In dev mode, cookie_config should be empty regardless of provided config
        assert adapter.cookie_config == {}

    @patch("routelit_fastapi.adapter.StaticFiles")
    def test_configure_static_assets(self, mock_static_files, fastapi_app):
        """Test static asset configuration."""
        from routelit import AssetTarget

        asset_target: AssetTarget = {"package_name": "test_package", "path": "static/assets"}

        with patch("routelit_fastapi.adapter.resources.files") as mock_files:
            mock_files.return_value.joinpath.return_value = "/mock/path"

            RouteLitFastAPIAdapter.configure_static_assets(fastapi_app, asset_target)

            # Check that mount was called
            assert any(route.path.startswith("/routelit/test_package") for route in fastapi_app.routes)

    def test_configure_fastapi_app(self, mock_routelit, fastapi_app):
        """Test FastAPI app configuration."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)

        with (
            patch("routelit_fastapi.adapter.StaticFiles"),
        ):
            result = adapter.configure(fastapi_app)

            # Check that the adapter is returned
            assert result == adapter

            # Check that templates were configured
            assert adapter.templates is not None

            # Check that routes were added
            assert any(route.path.startswith("/routelit") for route in fastapi_app.routes)

    @pytest.mark.asyncio
    async def test_handle_get_request(self, mock_routelit, fastapi_app):
        """Test GET request handling."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)
        adapter.configure(fastapi_app)

        # Mock RouteLit response
        mock_response = Mock()
        mock_response.get_str_json_elements.return_value = "json_elements"
        mock_response.head.title = "Test Title"
        mock_response.head.description = "Test Description"
        mock_routelit.handle_get_request.return_value = mock_response

        # Set return values for methods used in _handle_get_request
        mock_routelit.get_importmap_json.return_value = "importmap_json"
        mock_routelit.get_extra_head_content.return_value = "extra_head_content"
        mock_routelit.get_extra_body_content.return_value = "extra_body_content"

        from fastapi import Request
        from starlette.datastructures import URL

        # Create a mock request
        mock_request = Mock(spec=Request)
        mock_request.url = URL("http://testserver/")
        mock_request.headers = {}
        mock_request.cookies = {}

        response = await adapter._handle_get_request(Mock(), mock_request)

        # Verify RouteLit was called correctly
        mock_routelit.handle_get_request.assert_called_once()

        # Verify response is HTML
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_post_request(self, mock_routelit, fastapi_app):
        """Test POST request handling."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)
        adapter.configure(fastapi_app)

        view_fn = Mock()
        mock_actions = ["action1", "action2"]
        mock_routelit.handle_post_request.return_value = mock_actions

        from fastapi import Request
        from starlette.datastructures import URL, Headers

        # Create a mock POST request with async json method
        mock_request = Mock(spec=Request)
        mock_request.url = URL("http://testserver/")
        mock_request.method = "POST"
        mock_request.headers = Headers({"content-type": "application/json"})
        mock_request.cookies = {}
        mock_request.json = AsyncMock(return_value={"uiEvent": {"type": "click", "componentId": "btn1", "data": {}}})
        mock_request.form = AsyncMock(return_value={})

        response = await adapter.response(view_fn, mock_request)

        # Verify RouteLit was called correctly
        mock_routelit.handle_post_request.assert_called_once()

        # Verify JSON response
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_get_request(self, mock_routelit, fastapi_app):
        """Test GET request handling through response method."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)
        adapter.configure(fastapi_app)

        view_fn = Mock()

        # Mock RouteLit response
        mock_response = Mock()
        mock_response.get_str_json_elements.return_value = "json_elements"
        mock_response.head.title = "Test Title"
        mock_response.head.description = "Test Description"
        mock_routelit.handle_get_request.return_value = mock_response
        mock_routelit.get_importmap_json.return_value = "importmap_json"
        mock_routelit.get_extra_head_content.return_value = "extra_head_content"
        mock_routelit.get_extra_body_content.return_value = "extra_body_content"

        from fastapi import Request
        from starlette.datastructures import URL

        # Create a mock GET request
        mock_request = Mock(spec=Request)
        mock_request.url = URL("http://testserver/")
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.cookies = {}

        response = await adapter.response(view_fn, mock_request)

        # Verify GET handler was called
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stream_response_post_request(self, mock_routelit, fastapi_app):
        """Test POST request handling in stream_response method."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)
        adapter.configure(fastapi_app)

        view_fn = Mock()

        async def mock_stream():
            yield '{"action": "test"}'

        mock_routelit.handle_post_request_stream_jsonl.return_value = mock_stream()

        from fastapi import Request
        from starlette.datastructures import URL, Headers

        # Create a mock POST request with async json method
        mock_request = Mock(spec=Request)
        mock_request.url = URL("http://testserver/")
        mock_request.method = "POST"
        mock_request.headers = Headers({"content-type": "application/json"})
        mock_request.cookies = {}
        mock_request.json = AsyncMock(return_value={"uiEvent": {"type": "click", "componentId": "btn1", "data": {}}})
        mock_request.form = AsyncMock(return_value={})

        response = await adapter.stream_response(view_fn, mock_request)

        # Verify RouteLit was called correctly
        mock_routelit.handle_post_request_stream_jsonl.assert_called_once()

        # Verify streaming response
        assert response.status_code == 200
        assert response.media_type == "application/jsonlines"

    @pytest.mark.asyncio
    async def test_stream_response_get_request(self, mock_routelit, fastapi_app):
        """Test GET request handling through stream_response method."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)
        adapter.configure(fastapi_app)

        view_fn = Mock()

        # Mock RouteLit response
        mock_response = Mock()
        mock_response.get_str_json_elements.return_value = "json_elements"
        mock_response.head.title = "Test Title"
        mock_response.head.description = "Test Description"
        mock_routelit.handle_get_request.return_value = mock_response
        mock_routelit.get_importmap_json.return_value = "importmap_json"
        mock_routelit.get_extra_head_content.return_value = "extra_head_content"
        mock_routelit.get_extra_body_content.return_value = "extra_body_content"

        from fastapi import Request
        from starlette.datastructures import URL

        # Create a mock GET request
        mock_request = Mock(spec=Request)
        mock_request.url = URL("http://testserver/")
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.cookies = {}

        response = await adapter.stream_response(view_fn, mock_request)

        # Verify GET handler was called
        assert response.status_code == 200

    def test_configure_with_multiple_static_paths(self, mock_routelit, fastapi_app):
        """Test configuration with multiple static asset paths."""
        # Mock multiple static paths
        mock_builder = Mock()
        mock_builder.get_client_resource_paths.return_value = [
            {"package_name": "package1", "path": "static/assets1"},
            {"package_name": "package2", "path": "static/assets2"},
        ]
        mock_routelit.get_builder_class.return_value = mock_builder

        adapter = RouteLitFastAPIAdapter(mock_routelit)

        with (
            patch("routelit_fastapi.adapter.StaticFiles"),
            patch("routelit_fastapi.adapter.resources.files") as mock_files,
        ):
            mock_files.return_value.joinpath.return_value = "/mock/path"

            adapter.configure(fastapi_app)

            # Check that routes were added
            routes = [route.path for route in fastapi_app.routes]
            assert any("/routelit/package1" in route for route in routes)
            assert any("/routelit/package2" in route for route in routes)
            assert any("/routelit" in route for route in routes)

    @pytest.mark.asyncio
    async def test_handle_get_request_dev_mode(self, mock_routelit, fastapi_app):
        """Test GET request handling in dev mode with local servers."""
        adapter = RouteLitFastAPIAdapter(
            mock_routelit,
            run_mode="dev_client",
            local_frontend_server="http://localhost:3000",
            local_components_server="http://localhost:3001",
        )
        adapter.configure(fastapi_app)

        # Mock RouteLit response
        mock_response = Mock()
        mock_response.get_str_json_elements.return_value = "json_elements"
        mock_response.head.title = "Test Title"
        mock_response.head.description = "Test Description"
        mock_routelit.handle_get_request.return_value = mock_response
        mock_routelit.get_importmap_json.return_value = "importmap_json"
        mock_routelit.get_extra_head_content.return_value = "extra_head_content"
        mock_routelit.get_extra_body_content.return_value = "extra_body_content"

        from fastapi import Request
        from starlette.datastructures import URL

        # Create a mock request
        mock_request = Mock(spec=Request)
        mock_request.url = URL("http://testserver/")
        mock_request.headers = {}
        mock_request.cookies = {}

        response = await adapter._handle_get_request(Mock(), mock_request)

        # Verify response is HTML
        assert response.status_code == 200

    def test_response_is_coroutine_function(self, mock_routelit, fastapi_app):
        """Test that response method is a coroutine function."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)
        adapter.configure(fastapi_app)

        import inspect

        # Verify response is a coroutine function
        assert inspect.iscoroutinefunction(adapter.response)

    def test_stream_response_is_coroutine_function(self, mock_routelit, fastapi_app):
        """Test that stream_response method is a coroutine function."""
        adapter = RouteLitFastAPIAdapter(mock_routelit)
        adapter.configure(fastapi_app)

        import inspect

        # Verify stream_response is a coroutine function
        assert inspect.iscoroutinefunction(adapter.stream_response)
