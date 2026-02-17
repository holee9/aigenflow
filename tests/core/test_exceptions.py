"""
Tests for core exceptions.
"""


from core.exceptions import (
    AigenFlowException,
    ErrorCode,
)


class TestAigenFlowException:
    def test_create_basic_exception(self):
        exc = AigenFlowException("Test error message")
        assert str(exc) == "Test error message"

    def test_create_exception_with_details(self):
        exc = AigenFlowException(message="Test error", details={"code": "T001"})
        assert exc.message == "Test error"
        assert exc.details["code"] == "T001"


class TestErrorCode:
    def test_pipeline_error_codes(self):
        assert ErrorCode.PIPELINE_INVALID_STATE == "P1001"

    def test_gateway_error_codes(self):
        assert ErrorCode.GATEWAY_CONNECTION_FAILED == "G2001"
