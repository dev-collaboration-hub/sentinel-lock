"""Bounded operational logging without input content."""

from __future__ import annotations

from logging import Formatter, Logger, StreamHandler, getLogger
from logging.handlers import RotatingFileHandler

from sentinel_lock.config import LoggingConfig

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(config: LoggingConfig) -> Logger:
    """Configure and return the package logger."""

    logger = getLogger("sentinel_lock")
    logger.setLevel(config.level)
    logger.propagate = False

    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    formatter = Formatter(_FORMAT)
    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if config.file is not None:
        config.file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            config.file,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
