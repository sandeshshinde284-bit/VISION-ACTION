# /backend/app/core/logging_config.py

import logging
import os
import json

class GCPJsonFormatter(logging.Formatter):
    """
    Surgical, human-written JSON formatter for Google Cloud Logging.
    Maps Python's logging record fields to GCP-structured JSON logs
    for instant filtering and searching inside GCP Log Explorer.
    """
    def format(self, record):
        severity = record.levelname
        # Standardize warning and critical labels for GCP
        if severity == "WARNING":
            severity = "WARNING"
        elif severity == "ERROR" or severity == "CRITICAL":
            severity = "ERROR"
            
        payload = {
            "severity": severity,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ")
        }
        
        # Capture and format stack trace automatically if an exception is present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(payload)


def setup_logging():
    """
    Sets up our unified logging system.
    - On Cloud Run: Uses structured JSON logging directly to stdout/stderr. No disk writes.
    - Locally: Uses human-friendly readable text logs, and saves them to backend/logs/app.log.
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clean pre-existing handlers to avoid duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Detect if we are running inside Google Cloud Run
    is_cloud = os.environ.get("DATABASE_TARGET") == "CLOUD" or os.environ.get("K_SERVICE") is not None

    if is_cloud:
        # 1. Cloud-Native JSON Logging (Writes to stream for GCP ingestion)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(GCPJsonFormatter())
        root_logger.addHandler(console_handler)
        
        # Print initial handshake log in clean structured format
        logging.info("V.I.S.I.O.N. Telemetry: Cloud-native structured JSON logging initialized.")
    else:
        # 2. Local-Friendly Readable Text Logging
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "..", "logs"))
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Standard console output
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Backup file log
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        logging.info(f"Local development logging active. Saved to: {log_file}")
