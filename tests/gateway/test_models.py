"""
Tests for gateway models.
"""


from gateway.models import GatewayRequest, GatewayResponse


class TestGatewayRequest:
    """Tests for GatewayRequest model."""

    def test_create_request(self):
        """Test creating a gateway request."""
        request = GatewayRequest(
            task_name="test_task",
            prompt="Test prompt",
        max_tokens=100,
            timeout=120,
        )
        assert request.task_name == "test_task"
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 100
        assert request.timeout == 120

    def test_request_with_optional_fields(self):
        """Test request with optional fields."""
        request = GatewayRequest(
            task_name="test_task",
            prompt="Test prompt",
            max_tokens=100,
        timeout=120,
        )
        assert request.max_tokens is not None


class TestGatewayResponse:
    """Tests for GatewayResponse model."""

    def test_create_success_response(self):
        """Test creating a success response."""
        response = GatewayResponse(
            content="Test content",
            success=True,
            tokens_used=50,
            response_time=1.5,
        )
        assert response.success is True
        assert response.content == "Test content"

    def test_create_error_response(self):
        """Test creating an error response."""
        response = GatewayResponse(
            content="",
            success=False,
            error="Test error",
        )
        assert response.success is False
        assert response.error == "Test error"

    def test_response_with_metadata(self):
        """Test response with metadata."""
        response = GatewayResponse(
            content="Test content",
            success=True,
            metadata={"key": "value"},
        )
        assert response.metadata == {"key": "value"}
