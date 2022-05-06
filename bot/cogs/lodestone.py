"""Lodestone Interaction Module"""
import asyncio
import logging
import aiohttp
from aiohttp.helpers import CHAR
from aiolimiter import AsyncLimiter
import pyxivapi
from pyxivapi.models import Filter, Sort
import discord
from yarl import URL
import json
from discord.ext import commands

from ..config import xivapi_token
from ..constants import *
from ..emotes import *

MAX_REQ = 20 - 3  # buffer (request per second)
RATE_LIMIT = AsyncLimiter(MAX_REQ, 1)


class Lodestone(commands.Cog):
    """Lodestone commands and helper functions."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def lookup(self, ctx, world: str, first: str, last: str):
        # Check world if valid
        if not "%s%s" % (world[0].upper(), world[1:].lower()) in DATA_WORLDS:
            await ctx.send("Invalid world")
            return
        lodestoneCmd = {
            "cmd": "lookup",
            "world": world.lower(),
            "forename": first,
            "surname": last,
        }
        async with ctx.typing():
            resp, resp2 = await self._lodestone_process(ctx, lodestoneCmd)

        # Process response
        await self._send_response(ctx, lodestoneCmd, (resp, resp2))

    @commands.command()
    async def lookupId(self, ctx, id):
        lodestoneCmd = {"cmd": "lookupId", "id": id}
        await self._lodestone_process(ctx, lodestoneCmd)

    async def _lodestone_process(self, ctx, queryCmd):
        toClose = True
        resp = ""

        async with RATE_LIMIT:
            client = pyxivapi.XIVAPIClient(api_key=xivapi_token())

            if queryCmd["cmd"] == "lookup":
                print("Looking up character... ")
                resp = await client.character_search(
                    world=queryCmd["world"],
                    forename=queryCmd["forename"],
                    surname=queryCmd["surname"],
                )
                # print("Received Lodestone resp:\n %s" %(resp))
                print()

                # Check if a valid character exists.
                if resp["Pagination"]["Results"] == 0:
                    await ctx.send("User not found.")
                    await client.session.close()
                    return

                results = resp["Results"]
                firstResult = results[0]
                charId = firstResult["ID"]

                await client.session.close()

                lodestoneCmd = {"cmd": "lookupId", "id": charId}
                resp2 = await self._lodestone_process(ctx, lodestoneCmd)
                toClose = False
                if resp is None:
                    return ""

                return resp, resp2

            elif queryCmd["cmd"] == "lookupId":
                print("Looking up character by id... ")
                resp = await client.character_by_id(
                    lodestone_id=queryCmd["id"], extended=True, include_freecompany=True
                )
                # print("Received Lodestone resp:\n %s" %(resp))

            if toClose:
                await client.session.close()

            return resp

    async def _send_response(self, ctx, respCmd, resp):
        classStates = {}
        if respCmd["cmd"] == "lookup":
            charInfo = resp[1]["Character"]
            charGrandCompInfo = charInfo["GrandCompany"]
            activeClass = charInfo["ActiveClassJob"]

            charStats = {
                "name": charInfo["Name"],
                "activeClassName": activeClass["UnlockedState"]["Name"],
                "activeClassLv": activeClass["Level"],
                "id": charInfo["ID"],
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
            print("")

            tankClasses = []
            healerClasses = []
            meleeDpsClasses = []
            rangePhyDpsClasses = []
            rangeMagDpsClasses = []
            crafterClasses = []
            gathererClasses = []

            for classInfo in charInfo["ClassJobs"]:
                # print(classInfo)
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
                    raise TypeError("Class %d not found" % (classId))

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
                    raise TypeError("Unknown class. ID = %d" % (classId))

            tankRoleStr = ""
            healerRoleStr = ""
            meleeDpsRoleStr = ""
            rangePhyDpsRoleStr = ""
            rangeMagDpsRoleStr = ""
            crafterRoleStr = ""
            gathererRoleStr = ""

            for tankClass in tankClasses:
                tankRoleStr += "%s  %s\n" % (tankClass[0], tankClass[1])

            for healerClass in healerClasses:
                healerRoleStr += "%s  %s\n" % (healerClass[0], healerClass[1])

            for meleeDpsClass in meleeDpsClasses:
                meleeDpsRoleStr += "%s  %s\n" % (meleeDpsClass[0], meleeDpsClass[1])

            for rangePhyDpsClass in rangePhyDpsClasses:
                rangePhyDpsRoleStr += "%s  %s\n" % (
                    rangePhyDpsClass[0],
                    rangePhyDpsClass[1],
                )

            for rangeMagDpsClass in rangePhyDpsClasses:
                rangeMagDpsRoleStr += "%s  %s\n" % (
                    rangeMagDpsClass[0],
                    rangeMagDpsClass[1],
                )

            for crafterClass in crafterClasses:
                crafterRoleStr += "%s  %s\n" % (crafterClass[0], crafterClass[1])

            for gathererClass in gathererClasses:
                gathererRoleStr += "%s  %s\n" % (gathererClass[0], gathererClass[1])

            # Generate Embed message
            embedVar = discord.Embed(
                title=charStats["name"], description=charStats["title"]
            )
            embedVar.url = "%s%s" % (CHAR_LODESTONE_URL, charStats["id"])
            if "grandCompId" in charStats:
                embedVar.colour = GRAND_COMP_HEX_COLORS[charStats["grandCompID"] - 1]

            embedVar.set_thumbnail(url=charStats["avatar"])
            embedVar.add_field(
                name="Current Class",
                value="%s Lv. %3d\n\n"
                % (charStats["activeClassName"], charStats["activeClassLv"]),
            )
            embedVar.add_field(
                name="Grand Company",
                value="%s" % (charStats["grandCompName"]),
                inline=False,
            )
            embedVar.add_field(
                name="%s Tank" % (ROLES_EMOTE_ID[0]),
                value="%s" % (tankRoleStr.replace(" ", " ")),
                inline=True,
            )
            embedVar.add_field(
                name="%s Healer" % (ROLES_EMOTE_ID[1]),
                value="%s" % (healerRoleStr.replace(" ", " ")),
                inline=True,
            )
            embedVar.add_field(
                name="%s Melee DPS" % (ROLES_EMOTE_ID[2]),
                value="%s" % (meleeDpsRoleStr.replace(" ", " ")),
                inline=True,
            )
            embedVar.add_field(
                name="%s Ranged Phys DPS" % (ROLES_EMOTE_ID[3]),
                value="%s" % (rangePhyDpsRoleStr.replace(" ", " ")),
                inline=True,
            )
            embedVar.add_field(
                name="%s Ranged Magic DPS" % (ROLES_EMOTE_ID[4]),
                value="%s" % (rangeMagDpsRoleStr.replace(" ", " ")),
                inline=False,
            )
            embedVar.add_field(
                name="Crafter",
                value="%s" % (crafterRoleStr.replace(" ", " ")),
                inline=True,
            )
            embedVar.add_field(
                name="Gatherer",
                value="%s" % (gathererRoleStr.replace(" ", " ")),
                inline=False,
            )

            await ctx.send(embed=embedVar)
