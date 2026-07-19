import logging
from app.logger import logger, PIIRedactionFilter

def test_pii_redaction_filter():
    # Create a custom log record to test the filter
    record_email = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="User email is test.user@example.com, and phone is +1-555-123-4567. Please contact them.",
        args=(),
        exc_info=None
    )
    
    filtr = PIIRedactionFilter()
    filtr.filter(record_email)
    
    # Assert that email and phone number are redacted
    assert "test.user@example.com" not in record_email.msg
    assert "[REDACTED_EMAIL]" in record_email.msg
    assert "555-123-4567" not in record_email.msg
    assert "[REDACTED_PHONE]" in record_email.msg


def test_pii_redaction_extra_attributes():
    record_extra = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=20,
        msg="Logging user activity",
        args=(),
        exc_info=None
    )
    # Add structured attributes (extra)
    record_extra.email = "jane.doe@gmail.com"
    record_extra.phone = "1234567890"
    record_extra.nested_data = {
        "user": {
            "ssn": "999-99-9999",
            "cc": "1111-2222-3333-4444"
        }
    }
    
    filtr = PIIRedactionFilter()
    filtr.filter(record_extra)
    
    # Assert that all standard and extra fields are redacted
    assert record_extra.email == "[REDACTED_EMAIL]"
    assert record_extra.phone == "[REDACTED_PHONE]"
    assert record_extra.nested_data["user"]["ssn"] == "[REDACTED_SSN]"
    assert record_extra.nested_data["user"]["cc"] == "[REDACTED_CARD]"
