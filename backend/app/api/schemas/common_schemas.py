"""Common API schemas and standardized error responses."""

from __future__ import annotations

from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured error detail representation."""

    code: str
    message: str
    details: dict[str, str | int | float | bool] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standardized top-level error response envelope."""

    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list envelope."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    total: int
    limit: int
    offset: int
