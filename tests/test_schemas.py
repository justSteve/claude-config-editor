"""
Tests for Pydantic schemas.

Validates schema creation, validation, and conversion.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.core.schemas import (
    SnapshotCreateRequest,
    SnapshotQueryRequest,
    PathQueryRequest,
    PaginatedResponse,
    SnapshotSummary,
    ErrorResponse,
)


class TestBaseSchemas:
    """Test base schema functionality."""

    def test_error_response(self):
        """Test error response schema."""
        error = ErrorResponse(
            error="Something went wrong",
            error_type="ValueError",
            details={"field": "value"},
        )
        assert error.error == "Something went wrong"
        assert error.error_type == "ValueError"
        assert error.details == {"field": "value"}
        assert isinstance(error.timestamp, datetime)

    def test_paginated_response_creation(self):
        """Test paginated response creation."""
        items = [
            SnapshotSummary(
                id=i,
                snapshot_time=datetime.utcnow(),
                snapshot_hash=f"hash{i}",
                trigger_type="manual",
                triggered_by=None,
                notes=None,
                os_type="windows",
                os_version="10",
                hostname="test",
                username="user",
                total_locations=10,
                files_found=5,
                directories_found=5,
                total_size_bytes=1000,
                changed_from_previous=None,
                is_baseline=False,
                tags=[],
            )
            for i in range(1, 6)
        ]

        paginated = PaginatedResponse[SnapshotSummary].create(
            items=items,
            total=100,
            page=1,
            page_size=5,
        )

        assert len(paginated.items) == 5
        assert paginated.total == 100
        assert paginated.page == 1
        assert paginated.page_size == 5
        assert paginated.total_pages == 20
        assert paginated.has_next is True
        assert paginated.has_previous is False


class TestSnapshotSchemas:
    """Test snapshot-related schemas."""

    def test_snapshot_create_request_valid(self):
        """Test valid snapshot creation request."""
        request = SnapshotCreateRequest(
            trigger_type="api",
            triggered_by="admin@example.com",
            notes="Test snapshot",
            tags=["test", "development"],
            include_content=True,
            detect_changes=True,
        )

        assert request.trigger_type == "api"
        assert request.triggered_by == "admin@example.com"
        assert request.notes == "Test snapshot"
        assert request.tags == ["test", "development"]

    def test_snapshot_create_request_invalid_trigger(self):
        """Test snapshot creation with invalid trigger type."""
        with pytest.raises(ValidationError):
            SnapshotCreateRequest(trigger_type="invalid")

    def test_snapshot_create_request_defaults(self):
        """Test snapshot creation with defaults."""
        request = SnapshotCreateRequest()

        assert request.trigger_type == "api"
        assert request.triggered_by is None
        assert request.notes is None
        assert request.tags is None
        assert request.include_content is True
        assert request.detect_changes is True

    def test_snapshot_query_request_valid(self):
        """Test valid snapshot query request."""
        query = SnapshotQueryRequest(
            page=2,
            page_size=25,
            trigger_type="manual",
            os_type="windows",
            is_baseline=False,
            sort_by="snapshot_time",
            sort_order="desc",
        )

        assert query.page == 2
        assert query.page_size == 25
        assert query.offset == 25  # (page - 1) * page_size
        assert query.limit == 25
        assert query.trigger_type == "manual"
        assert query.sort_by == "snapshot_time"

    def test_snapshot_query_request_invalid_sort_by(self):
        """Test snapshot query with invalid sort field."""
        with pytest.raises(ValidationError):
            SnapshotQueryRequest(sort_by="invalid_field")

    def test_snapshot_query_request_invalid_page(self):
        """Test snapshot query with invalid page number."""
        with pytest.raises(ValidationError):
            SnapshotQueryRequest(page=0)

    def test_snapshot_query_request_invalid_page_size(self):
        """Test snapshot query with invalid page size."""
        with pytest.raises(ValidationError):
            SnapshotQueryRequest(page_size=0)

        with pytest.raises(ValidationError):
            SnapshotQueryRequest(page_size=2000)  # > 1000


class TestPathSchemas:
    """Test path-related schemas."""

    def test_path_query_request_valid(self):
        """Test valid path query request."""
        query = PathQueryRequest(
            snapshot_id=123,
            category="mcp_config",
            exists=True,
            type="file",
            min_size_bytes=1024,
            max_size_bytes=1024 * 1024,
            search="claude",
            page=1,
            page_size=50,
        )

        assert query.snapshot_id == 123
        assert query.category == "mcp_config"
        assert query.exists is True
        assert query.type == "file"
        assert query.min_size_bytes == 1024
        assert query.max_size_bytes == 1024 * 1024

    def test_path_query_request_invalid_snapshot_id(self):
        """Test path query with invalid snapshot ID."""
        with pytest.raises(ValidationError):
            PathQueryRequest(snapshot_id=0)

        with pytest.raises(ValidationError):
            PathQueryRequest(snapshot_id=-1)

    def test_path_query_request_invalid_sort_by(self):
        """Test path query with invalid sort field."""
        with pytest.raises(ValidationError):
            PathQueryRequest(snapshot_id=1, sort_by="invalid_field")


class TestSchemaSerializationDeserialization:
    """Test schema serialization and deserialization."""

    def test_snapshot_create_to_dict(self):
        """Test converting snapshot create request to dict."""
        request = SnapshotCreateRequest(
            trigger_type="manual",
            triggered_by="user@example.com",
            notes="Test",
        )

        data = request.model_dump()

        assert isinstance(data, dict)
        assert data["trigger_type"] == "manual"
        assert data["triggered_by"] == "user@example.com"
        assert data["notes"] == "Test"

    def test_snapshot_create_to_json(self):
        """Test converting snapshot create request to JSON."""
        request = SnapshotCreateRequest(
            trigger_type="manual",
            triggered_by="user@example.com",
        )

        json_str = request.model_dump_json()

        assert isinstance(json_str, str)
        assert "manual" in json_str
        assert "user@example.com" in json_str

    def test_snapshot_create_from_dict(self):
        """Test creating snapshot request from dict."""
        data = {
            "trigger_type": "api",
            "triggered_by": "system",
            "notes": "Automated backup",
            "tags": ["production", "backup"],
        }

        request = SnapshotCreateRequest(**data)

        assert request.trigger_type == "api"
        assert request.triggered_by == "system"
        assert request.notes == "Automated backup"
        assert request.tags == ["production", "backup"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
