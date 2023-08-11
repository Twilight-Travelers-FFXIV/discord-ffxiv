"""Bot that is callable from wherever in the code"""
import logging
from discord import Intents, AllowedMentions
from discord.ext import commands
from .config import prefix

logger = logging.getLogger(__name__)
intents: Intents = Intents.default()
intents.message_content = True  # pylint: disable=assigning-non-slot


class TataruBot(commands.Bot):
    """Bot / Commands Class"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("First time bot class is called... creating!")
            cls._instance = super(TataruBot, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__(
            intents=intents,
            command_prefix=prefix(),
            help_command=None,
            allowed_mentions=AllowedMentions(everyone=True),
        )
