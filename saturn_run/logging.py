import logging

from distributed.client import get_worker
from distributed.worker import logger as dask_logger


def logger():
    try:
        get_worker()
        return dask_logger
    except ValueError:
        # this means we're not in dask
        return logging
