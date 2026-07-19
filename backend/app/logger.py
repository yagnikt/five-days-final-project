import os
import re
import logging
from typing import Any

# Regex patterns for common PII
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


class PIIRedactionFilter(logging.Filter):
    """
    A Logging Filter that recursively redacts sensitive information (emails, phone numbers, SSNs, credit cards)
    from log messages and structured attributes.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        # Redact the main log message if it's a string
        if isinstance(record.msg, str):
            record.msg = self.redact_text(record.msg)
        elif isinstance(record.msg, dict):
            record.msg = self.redact_obj(record.msg)

        # Redact args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = self.redact_obj(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(self.redact_obj(list(record.args)))

        # Redact custom properties in extra
        for attr in list(record.__dict__.keys()):
            # Skip standard log record attributes
            if attr in {
                "name", "levelno", "levelname", "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "msg", "args"
            }:
                continue
            val = getattr(record, attr)
            if isinstance(val, (str, dict, list)):
                setattr(record, attr, self.redact_obj(val))
                
        return True

    def redact_text(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        text = SSN_REGEX.sub("[REDACTED_SSN]", text)
        text = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", text)
        return text

    def redact_obj(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self.redact_text(obj)
        elif isinstance(obj, dict):
            return {k: self.redact_obj(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.redact_obj(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(self.redact_obj(v) for v in obj)
        return obj


# Set up logger
logger = logging.getLogger("aeroplan")
logger.setLevel(logging.INFO)
logger.addFilter(PIIRedactionFilter())

# Check environment for GCP Logging configuration
if os.getenv("GCP_PROJECT") or os.getenv("K_SERVICE"):
    try:
        import google.cloud.logging
        client = google.cloud.logging.Client()
        # Retrieves a Cloud Logging handler based on the environment
        gcp_handler = client.get_default_handler()
        logger.addHandler(gcp_handler)
    except Exception as e:
        print(f"⚠️ Failed to initialize Google Cloud Logging handler: {e}. Falling back to StreamHandler.")
        # Local console fallback
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '{"timestamp":"%(asctime)s", "name":"%(name)s", "level":"%(levelname)s", "message":"%(message)s"}'
        ))
        logger.addHandler(handler)
else:
    # Local developer/testing fallback with structured output
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '{"timestamp":"%(asctime)s", "name":"%(name)s", "level":"%(levelname)s", "message":"%(message)s"}'
    ))
    logger.addHandler(handler)
