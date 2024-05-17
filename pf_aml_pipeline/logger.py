"""Reusable logger for pf_aml for promptflow."""
import logging
import sys


def pf_aml_logger(name: str = "pf_aml",
                  level: int = logging.INFO) -> logging.Logger:
    """Get PF_AML logger.

    Args:
        name (str, optional): Logger name. Defaults to "pf_aml".
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
