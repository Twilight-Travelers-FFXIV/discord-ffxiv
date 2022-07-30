"""Generic Commands"""
import re
import time

from discord import Emoji, Embed, Color
from discord.ext import commands
from ..config import prefix

from ..utils import delete_caller


class Generic(commands.Cog):
    """Generic Commands that don't fit into any other modules."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Simple back and forth message. Useful for confirming that the bot is alive, and what latency it has.

        Args:
            ctx (Context): Passed automatically by discord.py
        """
        await ctx.send(f"Pong! Latency: {round(self.bot.latency * 1000)}ms")

    @commands.command()
    @delete_caller
    async def timed_ping(self, ctx):
        """Ping that returns current timestamp. Useful for debugging.

        Args:
            ctx (Context): Passed automatically by discord.py
        """
        await ctx.send(f"Timed Ping! Sent at <t:{int(time.time())}:T>")

    @commands.command()
    async def emoji_debug(self, ctx, emoji: Emoji):
        """Given an emoji, output the proper name and id. The id is needed when configuring the bot.

        Args:
            ctx (Context): Passed automatically by discord.py
            emoji (Emoji): Discord emoji, must be given as message argument.
        """
        embed = Embed(description=f"emoji: {emoji}", title=f"emoji: {emoji}")
        embed.add_field(name="id", value=repr(emoji.id))
        embed.add_field(name="name", value=repr(emoji.name))
        await ctx.send(embed=embed)

    @commands.command()
    async def help(self, ctx, *module):
        """Display documentation, listing modules or commands within a given module

        Args:
            ctx (Context): Passed automatically by discord.py
            *module (str): The module
        """
        if not module:
            # no module given -> Display modules
            emb = Embed(
                title="Commands and Modules",
                color=Color.blue(),
                description=f"Use `{prefix()}help <module>` to view documentation "
                f"for the module and its commands.",
            )

            cogs_desc = ""
            for cog in self.bot.cogs:
                cogs_desc += f"`{cog}` {self.bot.cogs[cog].__doc__}\n"

            emb.add_field(name="Modules", value=cogs_desc, inline=False)

        elif len(module) == 1:
            # Module given -> Display commands
            for cog in self.bot.cogs:
                if cog.lower() == module[0].lower():

                    emb = Embed(
                        title=f"{cog} - Commands",
                        description=self.bot.cogs[cog].__doc__,
                        color=Color.green(),
                    )

                    # Regex to find ctx docstring
                    ctx_regex = re.compile(r"^\s*ctx \(.*$", re.IGNORECASE)

                    for command in self.bot.get_cog(cog).get_commands():
                        if not command.hidden:
                            help_text = (
                                command.help or "No further information provided."
                            )
                            emb.add_field(
                                name=f"`{prefix()}{command.name}`",
                                value=str(ctx_regex.sub(help_text, " ")),
                                inline=False,
                            )
                    break  # can break as we found the correct cog :)
            else:
                emb = Embed(
                    title="What's that?!",
                    description=f"A module called `{module[0]}` could not be found.",
                    color=Color.orange(),
                )

        else:
            # too many arguments!
            emb = Embed(
                title="That's too much.",
                description="Please request only one module at once :sweat_smile:",
                color=Color.orange(),
            )

        emb.set_footer(text="Please shout at Lem or Countii if things are broken.")
        await ctx.send(embed=emb)
