import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"

logging.basicConfig(format=FORMAT, level=logging.NOTSET, handlers=[RichHandler(locals_max_string=None)])


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger instance.

    """
    return logging.getLogger(name)
