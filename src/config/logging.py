import logging
import sys

from . import LOGGER_LEVEL

def config_logger(level: logging._Level) -> logging.Logger:
    logger = logging.getLogger("app")
    if logger.handlers:
        return logger # already configured

    logger.setLevel(logging.DEBUG) # let handlers check log levels
    logger.propagate = False # prevent double logging

    pattern = "[%(levelname)s - %(asctime)s] %(message)s"
    formatter = logging.Formatter(pattern)
    
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    return logger

logger = config_logger(LOGGER_LEVEL)