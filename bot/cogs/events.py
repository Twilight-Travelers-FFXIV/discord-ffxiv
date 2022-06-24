"""Event Management"""
import logging
import re

import emoji
from discord import Embed, Emoji
from discord.ext import commands

from ..embeds import (
    event_types,
    day_map,
    emoji_activity_map,
    RAID_VOTE_RESULT,
    ROLES_REACTIONS,
)
from ..utils import flatten, delete_caller

logger = logging.getLogger(__name__)

BLOCK_LIST = "space|ffxivintrial|ffxivinraids|ffxivinhighendraids|ffxivstoryicon|hand"


def dc_emojize(emoji_text: str):
    """Turn :string: emojis into Unicode (or valid discord emoji)"""
    if "<" in emoji_text:
        return emoji_text
    return emoji.emojize(emoji_text, use_aliases=True)


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
        """Fetch results of most recent event"""
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
        msg = await ctx.send(
            RAID_VOTE_RESULT.format(
                winning_event_name,
                f"{winning_event_name} {winning_event[0]}",
                day_map.get(winning_day[0]),
                ctx.message.author.id,
            )
        )
        await self._emoji_reactions(msg, [ROLES_REACTIONS])
