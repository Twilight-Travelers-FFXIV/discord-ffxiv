"""Main script that should be executed to start bot execution"""
import asyncio
import logging
import sys

import discord
from apscheduler.triggers.cron import CronTrigger

import bot

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("Main")
discord_bot = bot.TataruBot()

# Scheduling Stuff
SCHEDULER = None

# Scheduled commands with their respective triggers can be set here:
scheduled_commands = {
    "events": CronTrigger(
        week="1-53/2",
        day_of_week="sun",
        hour="21",
        minute="20",
        second="0",
        timezone="Europe/London",
    ),
    "event_results": CronTrigger(
        week="2-53/2",
        day_of_week="wed",
        hour="18",
        minute="00",
        second="0",
        timezone="Europe/London",
    ),
}


@discord_bot.event
async def on_ready():
    """Called when the client is done preparing the data received from Discord"""
    logger.info("Discord Init complete!")

    # Now, register all cogs:
    for cog in bot.enabled_cogs:
        await discord_bot.add_cog(cog(discord_bot))
    logger.info("\nPrefix: '%s'", bot.config.prefix())
    available_cogs = [
        c.name
        for cog in discord_bot.cogs
        for c in discord_bot.get_cog(cog).get_commands()
    ]
    logger.info("Available Commands: %s", available_cogs)

    logger.info("Now starting scheduler...")
    channel = discord_bot.get_channel(bot.config.schedule_channel())
    SCHEDULER.start()

    formatted_schedule = "\n\n".join(
        [
            f"{job.name} :arrow_right:  {job.trigger}\nNext: {job.next_run_time}\n"
            for job in SCHEDULER.get_jobs()
        ]
    )

    await channel.send(
        f"The following scheduled messages are set up for this channel: \n{formatted_schedule}\n"
        f"_This message will self-destruct in 10 seconds._",
        delete_after=10.0,
    )
    logger.info("Scheduler initiated!")


@discord_bot.event
async def on_connect():
    """Called when the client has successfully connected to Discord."""
    if not SCHEDULER.get_jobs():
        logger.debug("Adding Scheduled Functions...")
        for message, schedule in scheduled_commands.items():
            SCHEDULER.add_job(
                bot.utils.schedule_command(discord_bot, message), schedule, name=message
            )


async def __unused_on_disconnect():
    """Called when the client has disconnected from Discord."""
    logger.debug("Disconnected from Discord! Flushing jobs...")
    for job in SCHEDULER.get_jobs():
        job.remove()


async def main():
    """Entry function, wrap in extra asyn and ensure cmd tree is always synced!"""
    async with discord_bot:
        discord_bot.tree.copy_global_to(guild=discord.Object(id=926637968381329459))
        await discord_bot.start(bot.config.bot_token())
    # discord_bot.run(bot.config.bot_token())


if __name__ == "__main__":
    logger.info("Initializing scheduler...")
    SCHEDULER = bot.scheduler.TataruScheduler()

    logger.info("Running Bot...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
