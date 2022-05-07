"""Lodestone Interaction Module"""
import logging
import discord
import pyxivapi
from aiolimiter import AsyncLimiter
from discord.ext import commands

from ..config import xivapi_token
from ..constants import *
from ..emotes import *

logger = logging.getLogger(__name__)

MAX_REQ = 20 - 3  # buffer (request per second)
RATE_LIMIT = AsyncLimiter(MAX_REQ, 1)


class Lodestone(commands.Cog):
    """Lodestone commands and helper functions."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def lookup(self, ctx, world: str, first: str, last: str):
        """Lookup Character on the Lodestone

        Args:
            ctx (Context): Passed automatically by discord.py
            world (str): World the character is in
            first (str): Char first name
            last (str): Char last name

        Returns:
            Nothing
        """
        # Check world if valid
        if not f"{world[0].upper()}{world[1:].lower()}" in DATA_WORLDS:
            await ctx.send("Invalid world")
            return
        lodestone_cmd = {
            "cmd": "lookup",
            "world": world.lower(),
            "forename": first,
            "surname": last,
        }
        async with ctx.typing():
            resp, resp2 = await self._lodestone_process(ctx, lodestone_cmd)

        # Process response
        await self._send_response(ctx, lodestone_cmd, (resp, resp2))

    @commands.command()
    async def lookupId(self, ctx, char_id):
        """Lookup char by known ID. Mostly used for debugging.

        Args:
            ctx (Context): Passed automatically by discord.py
            char_id (str): Lodestone ID of character.
        """
        lodestone_cmd = {"cmd": "lookupId", "char_id": char_id}
        await self._lodestone_process(ctx, lodestone_cmd)

    async def _lodestone_process(self, ctx, query_cmd):
        to_close = True
        resp = ""

        async with RATE_LIMIT:
            client = pyxivapi.XIVAPIClient(api_key=xivapi_token())

            if query_cmd["cmd"] == "lookup":
                logger.info("Looking up character... ")
                resp = await client.character_search(
                    world=query_cmd["world"],
                    forename=query_cmd["forename"],
                    surname=query_cmd["surname"],
                )
                logger.debug("Received Lodestone resp:\n %s" % resp)

                # Check if a valid character exists.
                if resp["Pagination"]["Results"] == 0:
                    await ctx.send("User not found.")
                    await client.session.close()
                    return

                results = resp["Results"]
                firstResult = results[0]
                charId = firstResult["ID"]

                await client.session.close()

                lodestone_cmd = {"cmd": "lookupId", "char_id": charId}
                resp2 = await self._lodestone_process(ctx, lodestone_cmd)
                to_close = False
                if resp is None:
                    return ""

                return resp, resp2

            if query_cmd["cmd"] == "lookupId":
                logger.info("Looking up character by char_id... ")
                resp = await client.character_by_id(
                    lodestone_id=query_cmd["char_id"],
                    extended=True,
                    include_freecompany=True,
                )
                logger.debug("Received Lodestone resp:\n %s" % resp)

            if to_close:
                await client.session.close()

            return resp

    @staticmethod
    async def _send_response(ctx, respCmd, resp):
        classStates = {}
        if respCmd["cmd"] == "lookup":
            charInfo = resp[1]["Character"]
            charGrandCompInfo = charInfo["GrandCompany"]
            activeClass = charInfo["ActiveClassJob"]

            charStats = {
                "name": charInfo["Name"],
                "activeClassName": activeClass["UnlockedState"]["Name"],
                "activeClassLv": activeClass["Level"],
                "char_id": charInfo["ID"],
                "nameday": charInfo["Nameday"],
                "avatar": charInfo["Avatar"].replace("\\", ""),
                "title": charInfo["Title"]["Name"],
            }

            # Check if character is part of a Grand Company
            if charGrandCompInfo["Company"] is not None:
                charStats["grandCompName"] = charGrandCompInfo["Company"]["Name"]
                charStats["grandCompID"] = charGrandCompInfo["Company"]["ID"]
            else:
                charStats["grandCompName"] = "None"

            if "Blue Mage" in charStats["activeClassName"]:
                charStats["activeClassName"] = "Blue Mage"

            charStats["activeClassName"] = charStats["activeClassName"]

            # Class Info
            tankClasses = []
            healerClasses = []
            meleeDpsClasses = []
            rangePhyDpsClasses = []
            rangeMagDpsClasses = []
            crafterClasses = []
            gathererClasses = []

            for classInfo in charInfo["ClassJobs"]:
                logger.debug(classInfo)
                if classInfo["UnlockedState"]["ID"] is not None:
                    classId = classInfo["UnlockedState"]["ID"]
                else:
                    classId = classInfo["Class"]["ID"]
                classLv = classInfo["Level"]
                className = classInfo["UnlockedState"]["Name"]

                if "Blue Mage" in className:
                    className = "Blue Mage"

                classEmote = ""

                if classId in EMOTE_ID:
                    classEmote = EMOTE_ID[classId]

                else:
                    raise TypeError("Class %d not found" % classId)

                if classId in CHAR_CLASS_TYPE_TANK:
                    tankClasses.append((classEmote, classLv))

                elif classId in CHAR_CLASS_TYPE_HEALER:
                    healerClasses.append((classEmote, classLv))

                elif classId in CHAR_CLASS_TYPE_MELEE_DPS:
                    meleeDpsClasses.append((classEmote, classLv))

                elif classId in CHAR_CLASS_TYPE_RANGE_PHY_DPS:
                    rangePhyDpsClasses.append((classEmote, classLv))

                elif classId in CHAR_CLASS_TYPE_RANGE_MAG_DPS:
                    rangeMagDpsClasses.append((classEmote, classLv))

                elif classId in CHAR_CLASS_CRAFTER:
                    crafterClasses.append((classEmote, classLv))

                elif classId in CHAR_CLASS_GATHERER:
                    gathererClasses.append((classEmote, classLv))

                else:
                    raise TypeError("Unknown class. ID = %d" % classId)

            tankRoleStr = ""
            healerRoleStr = ""
            meleeDpsRoleStr = ""
            rangePhyDpsRoleStr = ""
            rangeMagDpsRoleStr = ""
            crafterRoleStr = ""
            gathererRoleStr = ""

            for tankClass in tankClasses:
                tankRoleStr += f"{tankClass[0]}  {tankClass[1]}\n"

            for healerClass in healerClasses:
                healerRoleStr += f"{healerClass[0]}  {healerClass[1]}\n"

            for meleeDpsClass in meleeDpsClasses:
                meleeDpsRoleStr += f"{meleeDpsClass[0]}  {meleeDpsClass[1]}\n"

            for rangePhyDpsClass in rangePhyDpsClasses:
                rangePhyDpsRoleStr += f"{rangePhyDpsClass[0]}  {rangePhyDpsClass[1]}\n"

            for rangeMagDpsClass in rangeMagDpsClasses:
                rangeMagDpsRoleStr += f"{rangeMagDpsClass[0]}  {rangeMagDpsClass[1]}\n"

            for crafterClass in crafterClasses:
                crafterRoleStr += f"{crafterClass[0]}  {crafterClass[1]}\n"

            for gathererClass in gathererClasses:
                gathererRoleStr += f"{gathererClass[0]}  {gathererClass[1]}\n"

            # Generate Embed message
            embed_var = discord.Embed(
                title=charStats["name"], description=charStats["title"]
            )
            embed_var.url = f"{CHAR_LODESTONE_URL}{charStats['char_id']}"
            if "grandCompId" in charStats:
                embed_var.colour = GRAND_COMP_HEX_COLORS[charStats["grandCompID"] - 1]

            embed_var.set_thumbnail(url=charStats["avatar"])
            embed_var.add_field(
                name="Current Class",
                value=f"{charStats['activeClassName']} Lv. {charStats['activeClassLv']:3d}\n\n",
            )
            embed_var.add_field(
                name="Grand Company",
                value=f"{charStats['grandCompName']}",
                inline=False,
            )
            embed_var.add_field(
                name=f"{ROLES_EMOTE_ID[0]} Tank",
                value=f"{tankRoleStr.replace(' ', ' ')}",
                inline=True,
            )
            embed_var.add_field(
                name=f"{ROLES_EMOTE_ID[1]} Healer",
                value=f"{healerRoleStr.replace(' ', ' ')}",
                inline=True,
            )
            embed_var.add_field(
                name="\u200B",
                value="\u200B",
                inline=False,
            )
            embed_var.add_field(
                name=f"{ROLES_EMOTE_ID[2]} Melee DPS",
                value=f"{meleeDpsRoleStr.replace(' ', ' ')}",
                inline=True,
            )
            embed_var.add_field(
                name=f"{ROLES_EMOTE_ID[3]} Ranged Phys DPS",
                value=f"{rangePhyDpsRoleStr.replace(' ', ' ')}",
                inline=True,
            )
            embed_var.add_field(
                name=f"{ROLES_EMOTE_ID[4]} Ranged Magic DPS",
                value=f"{rangeMagDpsRoleStr.replace(' ', ' ')}",
                inline=True,
            )
            embed_var.add_field(
                name="\u200B",
                value="\u200B",
                inline=False,
            )
            embed_var.add_field(
                name="Crafter",
                value=f"{crafterRoleStr.replace(' ', ' ')}",
                inline=True,
            )
            embed_var.add_field(
                name="Gatherer",
                value=f"{gathererRoleStr.replace(' ', ' ')}",
                inline=True,
            )

            await ctx.send(embed=embed_var)
