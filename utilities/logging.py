import logging

import colorlog

formatter = colorlog.ColoredFormatter(
    "%(light_white)s%(asctime)s%(reset)s  "
    "%(log_color)s%(levelname)-8s%(reset)s "
    "%(light_white)s%(name)-20s%(reset)s  "
    "%(message)s",
)

handler = colorlog.StreamHandler()
handler.setFormatter(formatter)

logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.NOTSET,
    handlers=[handler],
)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger instance.

    """
    return logging.getLogger(name)
