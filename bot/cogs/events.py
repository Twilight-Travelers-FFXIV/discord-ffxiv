"""Event Management"""
from calendar import day_name
from collections import defaultdict
import logging
import re
from datetime import date, timedelta, datetime, time

import emoji
from discord import Embed, Emoji
from discord.ext import commands

from ..embeds import (
    event_types,
    day_map,
    emoji_activity_map,
    RAID_VOTE_RESULT,
    SIGNUP_RESULT,
    ROLES_REACTIONS,
    VOICE_REACTIONS,
)
from ..utils import flatten, delete_caller

logger = logging.getLogger(__name__)

BLOCK_LIST = "space|ffxivintrial|ffxivinraids|ffxivinhighendraids|ffxivstoryicon|hand"


def dc_emojize(emoji_text: str):
    """Turn :string: emojis into Unicode (or valid discord emoji)"""
    if "<" in emoji_text:
        return emoji_text
    return emoji.emojize(emoji_text, use_aliases=True)


def dc_timestamp(day: str, hours=18, minutes=00):
    days = {name: i for i, name in enumerate(day_name)}
    today = date.today()
    weekday = today.weekday()
    return datetime.combine(
        today + timedelta(days=days[day] - weekday), time(hours, minutes)
    ).timestamp()


def dc_demojize(emoji_rendered: str):
    """Turn Unicode emojis back into :string: format (or valid custom discord emoji string)"""
    if isinstance(
        emoji_rendered, Emoji
    ):  # TODO: what about foreign emotes from other servers??
        return str(emoji_rendered)
    return emoji.demojize(emoji_rendered, language="alias")


class Events(commands.Cog):
    """Events Scheduler"""

    def __init__(self, bot):
        self.bot = bot
        self.emoji_re = re.compile(f"<:(?!{BLOCK_LIST})\w+:\d+\>|:(?!{BLOCK_LIST})\w+:")

    @staticmethod
    async def _emoji_reactions(msg, emojis: list):
        """React to msg with all emojis specified.

        Args:
            msg: Message to react to
            emojis (List of srt): list of emojis to add.
        """
        for emoji_reaction in flatten(emojis):
            logging.debug("Adding Reaction: %s", emoji_reaction)
            await msg.add_reaction(dc_emojize(emoji_reaction))

    @commands.command()
    @delete_caller
    async def events(self, ctx, event_type="raids"):
        """Push out event planning message of according type.

        Args:
            ctx (Context): Context from discord.py
            event_type (String): Optional event type. Must be specified in event_types dict.
        """
        event = event_types.get(event_type)

        if not event:
            await ctx.send(f":warning: {event_type} is not a valid event.")
            return

        # Add initial announcement
        await ctx.send(event.get("before_embed", ""))

        # Add Potential embeds:
        for emb in event.get("embeds", []):
            msg = await ctx.send(embed=Embed().from_dict(emb))
            emojis = [
                self.emoji_re.findall(field)
                for fields in emb["fields"]
                for field in fields.values()
            ]
            await self._emoji_reactions(msg, emojis)

        # Finally:
        final_text = event.get("after_embed", "")
        msg = await ctx.send(final_text)
        await self._emoji_reactions(msg, [self.emoji_re.findall(final_text)])

    @commands.command()
    @delete_caller
    async def event_results(self, ctx):
        """Fetch results of most recent event

        Args:
            ctx (Context): Passed automatically by discord.py
        """
        messages_to_check = []

        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user and message.reactions:
                messages_to_check.append(message)
                if len(messages_to_check) >= 3:
                    break

        # get max emoji helper to
        def _max_emoji(messages):
            return max(
                [
                    (dc_demojize(r.emoji), r.count)
                    for m in messages
                    for r in m.reactions
                ],
                key=lambda tup: tup[1],
            )

        # 0th message from the bottom should be the date vote:
        winning_day = _max_emoji(messages_to_check[0:1])
        if not winning_day or winning_day[0] not in day_map.keys():
            await ctx.send(":warning: No valid previous event vote found.")
            return

        # from then, the erst are vote votes
        winning_event = _max_emoji(messages_to_check[1:])
        winning_event_name = emoji_activity_map.get(winning_event[0])
        timestamp = int(dc_timestamp(day_map.get(winning_day[0])))
        msg = await ctx.send(
            RAID_VOTE_RESULT.format(
                winning_event_name,
                f"{winning_event_name} {winning_event[0]}",
                day_map.get(winning_day[0]),
                f"<t:{timestamp}:F> - That's <t:{timestamp}:R>",
                ctx.message.author.id,
            )
        )
        await self._emoji_reactions(
            msg,
            [ROLES_REACTIONS, VOICE_REACTIONS],
        )

    @commands.command()
    @delete_caller
    async def signup_results(self, ctx):
        """Fetch sign up of most recent event result announcement."""
        async for message in ctx.channel.history(limit=50):
            if (
                message.author == self.bot.user
                and message.reactions
                and "ACTIVITY" in message.content
            ):
                signup_message = message
                break

        logger.debug(
            "Signup Message: %s - Content: %s", signup_message, signup_message.content
        )
        if not signup_message:
            await ctx.send(":warning: No valid previous event result found.")
            return

        print(signup_message.reactions)

        # Parse the day back out :D
        day_re = re.compile(r"The farm will commence on (?P<name>.*) at")
        winning_day = day_re.search(signup_message.content)
        if not winning_day:
            await ctx.send(":warning: No valid previous event result day found.")
            return
        winning_day = winning_day.group("name")

        # Convert to lookups for reporting
        role_to_user_reacts = defaultdict(list)
        user_to_voice_reacts = {}
        for r in signup_message.reactions:
            flat_user_list = await r.users().flatten()
            for user in flat_user_list:
                if user == self.bot.user:
                    continue
                emote = dc_demojize(r.emoji)
                if emote in ROLES_REACTIONS:
                    role_to_user_reacts[dc_demojize(r.emoji)].append(user)
                if emote in VOICE_REACTIONS:
                    if user not in user_to_voice_reacts.keys():
                        user_to_voice_reacts[user] = emote
                    else:
                        # User has more than 1 voice reaction - パン肉
                        user_to_voice_reacts[user] = ":question:"

        logger.debug(dict(role_to_user_reacts))
        logger.debug(user_to_voice_reacts)

        def _userformat(role):
            users = [
                user_to_voice_reacts.get(u, ":question:") + u.mention
                for u in role_to_user_reacts[role]
            ]
            return "\n - ".join(users)

        msg = await ctx.send(
            SIGNUP_RESULT.format(
                "\n\n".join(
                    [f"{role}: \n - {_userformat(role)}" for role in ROLES_REACTIONS]
                )
            )
        )
