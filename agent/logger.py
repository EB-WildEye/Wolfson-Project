"""Logger factory — dev=DEBUG, prod=WARNING. Logs to console + file."""

import logging
import sys
from pathlib import Path
from agent.config import settings

_LEVEL_MAP = {"dev": logging.DEBUG, "prod": logging.WARNING}
_DEFAULT = _LEVEL_MAP.get(settings.ENV, logging.INFO)

LOG_DIR = settings.BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "gali.log"

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """Return a named logger with console + file handlers."""
    lvl = level if level is not None else _DEFAULT
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(lvl)

        console = logging.StreamHandler(sys.stdout)
        console.setLevel(lvl)
        console.setFormatter(_FORMATTER)
        logger.addHandler(console)

        file_h = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_h.setLevel(logging.DEBUG)
        file_h.setFormatter(_FORMATTER)
        logger.addHandler(file_h)

        logger.propagate = False

    return logger
