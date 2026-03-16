import json
from typing import Any


class JSONSerializationError(TypeError):
    """Exception raised when an object cannot be serialized to JSON."""

    pass


def custom_json_dumps(obj: Any, **kwargs: Any) -> str:
    """
    Custom JSON dumps function that handles special objects.

    Args:
        obj: The object to serialize.
        **kwargs: Additional keyword arguments to pass to json.dumps.

    Returns:
        JSON string representation of the object.
    """
    kwargs.setdefault("skipkeys", True)
    kwargs.setdefault("default", _default_handler)
    return json.dumps(obj, **kwargs)


def _default_handler(obj: Any) -> Any:
    """
    Default handler for JSON serialization.

    Args:
        obj: The object to serialize.

    Returns:
        Serializable representation of the object.
    """
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if v is not None}
    raise JSONSerializationError(f"Object of type {type(obj).__name__} is not JSON serializable")  # noqa: TRY003
