"""Main Configuration File"""
import os
import sys

sys.path.append("..")

try:
    import configKeys
except ImportError:
    configKeys = None  # We are running from env variables!


def prefix():
    """Prefix for the bot. Defaults to $"""
    return os.getenv("BOT_PREFIX", "!")


def bot_token():
    """Discord access token, reverts to old style config if not in environment."""
    return configKeys.DISCORD_TOKEN if configKeys else os.getenv("BOT_TOKEN", "")


def xivapi_token():
    """Lodestone API token, reverts to old style config if not in environment."""
    return configKeys.FFXIV_API_KEY if configKeys else os.getenv("XIVAPI_TOKEN", "")


def schedule_channel():
    """Channel ID for scheduled commands, reverts to bot testing channel by default."""
    return int(os.getenv("SCHEDULE_CHANNEL", "1132654623858098246#"))
