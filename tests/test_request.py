"""Tests for the FastAPIRLRequest class."""

import json
import uuid
from io import BytesIO

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from routelit_fastapi.request import FastAPIRLRequest


class TestFastAPIRLRequest:
    """Test the FastAPIRLRequest class."""

    @pytest.fixture
    def fastapi_app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app

    @pytest.mark.asyncio
    async def test_get_headers(self, fastapi_app):
        """Test get_headers returns request headers."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            headers = rl_request.get_headers()
            # httpx lowercases headers, so check for lowercase version
            return {"has_custom_header": "x-custom-header" in headers}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test", headers={"X-Custom-Header": "custom-value"})
            assert response.status_code == 200
            assert response.json()["has_custom_header"]

    @pytest.mark.asyncio
    async def test_get_path_params(self, fastapi_app):
        """Test get_path_params returns path params."""

        @fastapi_app.get("/test/{item_id}")
        async def test_endpoint(item_id: str, request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            params = rl_request.get_path_params()
            return {"item_id": params.get("item_id") if params else None}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test/123")
            assert response.status_code == 200
            assert response.json()["item_id"] == "123"

    @pytest.mark.asyncio
    async def test_get_referrer(self, fastapi_app):
        """Test get_referrer returns referer header."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"referrer": rl_request.get_referrer()}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test", headers={"referer": "http://example.com/page"})
            assert response.status_code == 200
            assert response.json()["referrer"] == "http://example.com/page"

    @pytest.mark.asyncio
    async def test_method_property_get(self, fastapi_app):
        """Test method property returns HTTP method for GET."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"method": rl_request.method}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test")
            assert response.status_code == 200
            assert response.json()["method"] == "GET"

    @pytest.mark.asyncio
    async def test_method_property_post(self, fastapi_app):
        """Test method property returns POST for POST requests."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"method": rl_request.method}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.post("/test")
            assert response.status_code == 200
            assert response.json()["method"] == "POST"

    @pytest.mark.asyncio
    async def test_get_json_with_json_content_type(self, fastapi_app):
        """Test get_json returns parsed JSON for application/json."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            json_data = rl_request.get_json()
            return {"key": json_data.get("key") if json_data else None}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.post("/test", json={"key": "value"})
            assert response.status_code == 200
            assert response.json()["key"] == "value"

    @pytest.mark.asyncio
    async def test_get_json_returns_none_for_non_json(self, fastapi_app):
        """Test get_json returns None for non-JSON requests."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            json_data = rl_request.get_json()
            return {"json_data": json_data}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test")
            assert response.status_code == 200
            assert response.json()["json_data"] is None

    @pytest.mark.asyncio
    async def test_get_files_returns_list_for_multipart_with_files(self, fastapi_app):
        """Test get_files returns list of files for multipart requests with files."""

        @fastapi_app.post("/upload")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            files = rl_request.get_files()
            # Return count of files
            return {"file_count": len(files) if files else 0}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            files = {
                "files": ("file1.txt", BytesIO(b"file1 content"), "text/plain"),
            }
            response = await ac.post("/upload", files=files)
            assert response.status_code == 200
            result = response.json()
            assert result["file_count"] == 1, f"Expected 1 file, got {result}"

    @pytest.mark.asyncio
    async def test_get_files_returns_none_for_non_multipart(self, fastapi_app):
        """Test get_files returns None for non-multipart requests."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            files = rl_request.get_files()
            return {"files": files}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.post("/test", json={"key": "value"})
            assert response.status_code == 200
            assert response.json()["files"] is None

    @pytest.mark.asyncio
    async def test_is_json_true_for_application_json(self, fastapi_app):
        """Test is_json returns True for application/json content type."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"is_json": rl_request.is_json()}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.post("/test", json={})
            assert response.status_code == 200
            assert response.json()["is_json"]

    @pytest.mark.asyncio
    async def test_is_json_false_for_multipart(self, fastapi_app):
        """Test is_json returns False for multipart content type."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"is_json": rl_request.is_json()}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
            response = await ac.post("/test", files=files)
            assert response.status_code == 200
            assert not response.json()["is_json"]

    @pytest.mark.asyncio
    async def test_is_multipart_true_for_multipart(self, fastapi_app):
        """Test is_multipart returns True for multipart/form-data."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"is_multipart": rl_request.is_multipart()}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
            response = await ac.post("/test", files=files)
            assert response.status_code == 200
            assert response.json()["is_multipart"]

    @pytest.mark.asyncio
    async def test_is_multipart_false_for_json(self, fastapi_app):
        """Test is_multipart returns False for application/json."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"is_multipart": rl_request.is_multipart()}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.post("/test", json={})
            assert response.status_code == 200
            assert not response.json()["is_multipart"]

    @pytest.mark.asyncio
    async def test_get_query_param(self, fastapi_app):
        """Test get_query_param returns single value."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            value = rl_request.get_query_param("key")
            return {"value": value}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test?key=value")
            assert response.status_code == 200
            assert response.json()["value"] == "value"

    @pytest.mark.asyncio
    async def test_get_query_param_returns_none_for_missing(self, fastapi_app):
        """Test get_query_param returns None for missing param."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            value = rl_request.get_query_param("nonexistent")
            return {"value": value}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test")
            assert response.status_code == 200
            assert response.json()["value"] is None

    @pytest.mark.asyncio
    async def test_get_query_param_list(self, fastapi_app):
        """Test get_query_param_list returns list of values."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            values = rl_request.get_query_param_list("foo")
            return {"values": values}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test?foo=bar&foo=baz")
            assert response.status_code == 200
            assert response.json()["values"] == ["bar", "baz"]

    @pytest.mark.asyncio
    async def test_get_query_param_list_returns_empty_for_missing(self, fastapi_app):
        """Test get_query_param_list returns empty list for missing param."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            values = rl_request.get_query_param_list("nonexistent")
            return {"values": values}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test")
            assert response.status_code == 200
            assert response.json()["values"] == []

    @pytest.mark.asyncio
    async def test_get_session_id_generates_new_id_when_missing(self, fastapi_app):
        """Test get_session_id generates new UUID when cookie is missing."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            session_id = rl_request.get_session_id()
            # Validate it's a valid UUID
            is_valid = False
            try:
                uuid.UUID(session_id)
                is_valid = True
            except ValueError:
                pass
            return {"valid": is_valid}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test")
            assert response.status_code == 200
            assert response.json()["valid"]

    @pytest.mark.asyncio
    async def test_get_session_id_from_cookie(self, fastapi_app):
        """Test get_session_id returns session id from cookie."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            session_id = rl_request.get_session_id()
            return {"session_id": session_id}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test", cookies={"ROUTELIT_SESSION_ID": "test-session-123"})
            assert response.status_code == 200
            assert response.json()["session_id"] == "test-session-123"

    @pytest.mark.asyncio
    async def test_get_pathname(self, fastapi_app):
        """Test get_pathname returns request path."""

        @fastapi_app.get("/test/path")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"pathname": rl_request.get_pathname()}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test/path")
            assert response.status_code == 200
            assert response.json()["pathname"] == "/test/path"

    @pytest.mark.asyncio
    async def test_get_host(self, fastapi_app):
        """Test get_host returns request host."""

        @fastapi_app.get("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            return {"host": rl_request.get_host()}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.get("/test")
            assert response.status_code == 200
            assert "test" in response.json()["host"]

    @pytest.mark.asyncio
    async def test_get_json_with_multipart_form_json(self, fastapi_app):
        """Test get_json extracts JSON from multipart form data."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            json_data = rl_request.get_json()
            return {"json_data": json_data}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            files = {"json": (None, json.dumps({"key": "value"}), "application/json")}
            response = await ac.post("/test", files=files)
            assert response.status_code == 200
            result = response.json()
            # The JSON data should be parsed
            assert result["json_data"] is not None

    @pytest.mark.asyncio
    async def test_build_idempotent(self, fastapi_app):
        """Test that build() can be called multiple times safely."""

        @fastapi_app.post("/test")
        async def test_endpoint(request: Request):
            rl_request = FastAPIRLRequest(request)
            await rl_request.build()
            await rl_request.build()  # Second call should be safe
            json_data = rl_request.get_json()
            return {"key": json_data.get("key") if json_data else None}

        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
            response = await ac.post("/test", json={"key": "value"})
            assert response.status_code == 200
            assert response.json()["key"] == "value"
