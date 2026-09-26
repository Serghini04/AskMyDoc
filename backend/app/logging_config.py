import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

# Libraries that log every HTTP request at INFO.
NOISY_LOGGERS = ("httpx", "httpx2", "httpcore", "httpcore2")


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level.upper(), format=LOG_FORMAT, force=True)
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
