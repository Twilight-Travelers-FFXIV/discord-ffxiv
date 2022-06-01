"""Misc Utility functions"""
import functools


def delete_caller(f):
    """Decorator for automatically deleting the calling message after completion of the command."""

    @functools.wraps(f)
    async def wrapper(*args, **kwargs):
        """Function wrapped"""
        return_value = await f(*args, **kwargs)
        try:
            await args[1].message.delete()
        except AttributeError:  # Not a context
            pass
        except IndexError:  # Not a bot command. Fail open.
            pass
        return return_value

    return wrapper


def flatten(list_of_lists):
    """Flatten a list of lists"""
    return [item for sublist in list_of_lists for item in sublist]
