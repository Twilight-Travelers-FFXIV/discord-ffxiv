"""Generic Commands"""
from discord import Emoji, Embed
from discord.ext import commands

from ..utils import delete_caller


class Generic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! Latency: {round(self.bot.latency * 1000)}ms")

    @commands.command()
    async def emoji_debug(self, ctx, emoji: Emoji):
        embed = Embed(description=f"emoji: {emoji}", title=f"emoji: {emoji}")
        embed.add_field(name="id", value=repr(emoji.id))
        embed.add_field(name="name", value=repr(emoji.name))
        await ctx.send(embed=embed)
