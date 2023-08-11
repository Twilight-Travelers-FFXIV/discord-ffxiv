"""Misc Utility functions"""

import contextlib
import functools
from .config import schedule_channel


def delete_caller(f):
    """Decorator for automatically deleting the calling message after completion of the command."""

    @functools.wraps(f)
    async def wrapper(*args, **kwargs):
        """Function wrapped"""
        return_value = await f(*args, **kwargs)
        ctx = args[1]
        with contextlib.suppress(AttributeError, IndexError):
            if not ctx.interaction_type:
                await ctx.message.delete()
        return return_value

    return wrapper


def flatten(list_of_lists):
    """Flatten a list of lists"""
    return [item for sublist in list_of_lists for item in sublist]


def schedule_command(discord_bot, command):
    """Higher-order function wrapper that creates a callable function for a bot command

    Args:
        discord_bot (Bot): The discord.py bot the command exists in.
        command (str): name of the command
    """

    async def func():
        """The actual function that's called by the apscheduler"""
        channel = discord_bot.get_channel(schedule_channel())
        message = await channel.send(f"!{command}")
        ctx = await discord_bot.get_context(message)
        await ctx.invoke(discord_bot.get_command(command))

    return func
