"""Reusable logger for llmops for promptflow."""
import logging
import sys


def llmops_logger(name: str = "llmops",
                  level: int = logging.INFO) -> logging.Logger:
    """Get LLMOps logger.

    Args:
        name (str, optional): Logger name. Defaults to "llmops".
        level (int, optional): Log level. Defaults to logging.INFO.

    Returns:
        logging.Logger: named logger.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
