"""Main Configuration File"""
import os
import sys

sys.path.append("..")

try:
    import configKeys
except ImportError:
    pass  # We are running from env variables!


def prefix():
    """Prefix for the bot. Defaults to $"""
    return os.getenv("BOT_PREFIX", "$")


def bot_token():
    """Discord access token, reverts to old style config if not in environment."""
    return os.getenv("BOT_TOKEN", configKeys.DISCORD_TOKEN)


def xivapi_token():
    """Lodestone API token, reverts to old style config if not in environment."""
    return os.getenv("XIVAPI_TOKEN", configKeys.FFXIV_API_KEY)
