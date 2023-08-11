"""Scheduler that is callable from wherever in the code"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class TataruScheduler(AsyncIOScheduler):
    """Scheduler Class"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("First time scheduler is called... creating!")
            cls._instance = super(TataruScheduler, cls).__new__(cls)
        return cls._instance
