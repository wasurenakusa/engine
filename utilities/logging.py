import logging

import colorlog

FORMAT = "%(asctime)s %(levelname)-7s %(name)-16s %(message)s"

formatter = colorlog.ColoredFormatter(
    "%(light_white)s%(asctime)s%(reset)s %(log_color)s %(levelname)-8s%(reset)s %(name)-16s %(message)s",
)

handler = colorlog.StreamHandler()
handler.setFormatter(formatter)

logging.basicConfig(
    format=FORMAT,
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
