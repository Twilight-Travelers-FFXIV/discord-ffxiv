import discord
from discord.ext import commands
import bot


intents = discord.Intents.default()
discord_bot = commands.Bot(
    intents=intents, command_prefix=bot.config.prefix(), help_command=None
)


@discord_bot.event
async def on_ready():
    print("Connected to Discord!")
    # Now, register all cogs:
    for cog in bot.enabled_cogs:
        discord_bot.add_cog(cog(discord_bot))
    print(f"\nPrefix: '{bot.config.prefix()}'")
    available_cogs = [
        c.name
        for cog in discord_bot.cogs
        for c in discord_bot.get_cog(cog).get_commands()
    ]
    print(f"Available Commands: {available_cogs}")
    # Additional setup steps may be inserted here in the future. E.g. external OAUTH etc.


if __name__ == "__main__":
    discord_bot.run(bot.config.bot_token())
