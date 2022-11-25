"""Misc Utility functions"""

import contextlib
import functools


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
