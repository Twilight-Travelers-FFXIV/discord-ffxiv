import asyncio
import logging
import aiohttp
from aiohttp.helpers import CHAR
from aiolimiter import AsyncLimiter
import pyxivapi
from pyxivapi.models import Filter, Sort
import discord
from yarl import URL
from configKeys import FFXIV_API_KEY, DISCORD_TOKEN
from emoteIdList import EMOTE_ID, ROLES_EMOTE_ID
import json

MAX_REQ = 20 - 3 # buffer (request per second)
DATA_WORLDS = ["Adamantoise","Aegis","Alexander","Anima","Asura","Atomos","Bahamut","Balmung","Behemoth","Belias","Brynhildr","Cactuar",
                "Carbuncle","Cerberus","Chocobo","Coeurl","Diabolos","Durandal","Excalibur","Exodus","Faerie","Famfrit","Fenrir","Garuda",
                "Gilgamesh","Goblin","Gungnir","Hades","Hyperion","Ifrit","Ixion","Jenova","Kujata","Lamia","Leviathan","Lich","Louisoix",
                "Malboro","Mandragora","Masamune","Mateus","Midgardsormr","Moogle","Odin","Omega","Pandaemonium","Phoenix","Ragnarok","Ramuh",
                "Ridill","Sargatanas","Shinryu","Shiva","Siren","Tiamat","Titan","Tonberry","Typhon","Ultima","Ultros","Unicorn","Valefor",
                "Yojimbo","Zalera","Zeromus","Zodiark","Spriggan","Twintania","HongYuHai","ShenYiZhiDi","LaNuoXiYa","HuanYingQunDao","MengYaChi",
                "YuZhouHeYin","WoXianXiRan","ChenXiWangZuo","BaiYinXiang","BaiJinHuanXiang","ShenQuanHen","ChaoFengTing","LvRenZhanQiao",
                "FuXiaoZhiJian","Longchaoshendian","MengYuBaoJing","ZiShuiZhanQiao","YanXia","JingYuZhuangYuan","MoDuNa","HaiMaoChaWu","RouFengHaiWan",
                "HuPoYuan"]


CHAR_CLASS_NAMES = {1: ['gladiator', 'paladin'], 2: ['pugilist', 'monk'], 3: ['marauder', 'warrior'], 4: ['lancer', 'dragoon'], 5: ['archer', 'bard'], 
                6: ['conjurer', 'white mage'], 7: ['thaumaturge', 'black mage'], 8: ['carpenter'], 9: ['blacksmith'], 10: ['armorer'], 
                11: ['goldsmith'], 12: ['leatherworker'], 13: ['weaver'], 14: ['alchemist'], 15: ['culinarian'], 
                16: ['miner'], 17: ['botanist'], 18: ['fisher'], 26: ['arcanist', 'summoner'], 28: ['arcanist', 'scholar'], 29: ['rogue', 'ninja'], 
                31: ['machinist'], 32: ['dark knight'], 33: ['astrologian'], 34: ['samurai'], 35: ['red mage'], 
                36: ['blue mage'], 37: ['gunbreaker'], 38: ['dancer'], 39: ['reaper'], 40: ['sage']}


TEMP_CHAR_CLASS_NAMES = { 1: 'gladiator', 2: 'pugilist', 3: 'marauder', 4: 'lancer', 5: 'archer', 6: 'conjurer',
                          7: 'thaumaturge', 8: 'carpenter', 9: 'blacksmith', 10: 'armorer', 11: 'goldsmith', 12: 'leatherworker',
                         13: 'weaver', 14: 'alchemist', 15: 'culinarian', 16: 'miner', 17: 'botanist', 18: 'fisher',
                         19: 'paladin', 20: 'monk', 21: 'warrior', 22: 'dragoon', 23: 'bard', 24: 'white mage',
                         25: 'black mage', 26: 'arcanist', 27: 'summoner', 28: 'scholar', 29: 'rogue', 30: 'ninja',
                         31: 'machinist',32: 'dark knight', 33: 'astrologian', 34: 'samurai', 35: 'red mage', 36: 'blue mage',
                         37: 'gunbreaker', 38: 'dancer', 39: 'reaper', 40: 'sage'}

CHAR_LODESTONE_URL = "https://eu.finalfantasyxiv.com/lodestone/character/"

CHAR_CLASS_TYPE_MELEE_DPS = (2,4,29,30,34,39)
CHAR_CLASS_TYPE_RANGE_PHY_DPS = (5,23,31,38)
CHAR_CLASS_TYPE_RANGE_MAG_DPS = (7,25,26,27,35,36)
CHAR_CLASS_TYPE_TANK = (1,3,19,21,32,37)
CHAR_CLASS_TYPE_HEALER = (6,24,28,33,40)

CHAR_CLASS_CRAFTER = (8,9,10,11,12,13,14,15)
CHAR_CLASS_GATHERER = (16,17,18)


GRAND_COMP_HEX_COLORS = (0xb41b1e, 0xdaab16, 0x213443) # ("Maelstrom", "Twin Adder" ,"Immortal Flames")


client = discord.Client()
RATE_LIMIT = AsyncLimiter(MAX_REQ,1)

BOT_CMDS = ['lookup', 'lookupId']

prefix = "$"

bot_commands = []
worldList = []


@client.event
async def on_ready():
    global worldList
    global bot_commands
    bot_commands = ["%s%s" % (prefix, cmd) for cmd in BOT_CMDS]

    print("Available commands: %s" % (bot_commands))
    print("Bot is ready to serve")

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if msg.content.startswith('$ping'):
        await msg.channel.send('pong')

    if msg.content.startswith(prefix):
        msgParsed = msg.content.split()
        # print("Received query: %s" % (msgParsed))
        if msgParsed[0] in bot_commands:
            
            if msgParsed[0] == "%slookup" % (prefix):

                if len(msgParsed) == 4:
                    #Check world if valid
                    if not "%s%s" % (msgParsed[1][0].upper(),msgParsed[1][1:].lower()) in DATA_WORLDS:
                        await msg.channel.send("Invalid world")
                        return
                    lodestoneCmd = {'cmd':'lookup', 'world':msgParsed[1].lower(), 'forename':msgParsed[2], 'surname':msgParsed[3]}
                    resp,resp2 = await lodestone_process(msg, lodestoneCmd)

                    #Process response
                    await send_response(msg,lodestoneCmd,(resp,resp2))

            elif msgParsed[0] == "%slookupId" % (prefix):
                if len(msgParsed) == 2:
                    lodestoneCmd = {'cmd':'lookupId', 'id': msgParsed[1]}
                    await lodestone_process(msg, lodestoneCmd)

async def lodestone_process(msg, queryCmd):
    toClose = True
    resp = ''

    async with RATE_LIMIT:
        client = pyxivapi.XIVAPIClient(api_key=FFXIV_API_KEY)

        if queryCmd['cmd'] == 'lookup':
            print("Looking up character... ")
            resp = await client.character_search(
                world = queryCmd['world'],
                forename = queryCmd['forename'],
                surname = queryCmd['surname']
            )
            # print("Received Lodestone resp:\n %s" %(resp))
            print()

            # Check if a valid character exists. 
            if resp['Pagination']['Results'] == 0:
                await msg.channel.send("User not found.")
                await client.session.close()
                return

            results = resp['Results']
            firstResult = results[0]
            charId = firstResult['ID']

            await client.session.close()

            lodestoneCmd = {'cmd':'lookupId', 'id': charId}
            resp2 = await lodestone_process(msg, lodestoneCmd)
            toClose = False
            if resp is None:
                return ''

            return resp,resp2

        elif queryCmd['cmd'] == 'lookupId':
            print("Looking up character by id... ")
            resp = await client.character_by_id(
                lodestone_id = queryCmd['id'], 
                extended = True,
                include_freecompany = True
            )
            # print("Received Lodestone resp:\n %s" %(resp))

        if toClose:
            await client.session.close()

        return resp

async def send_response(msg, respCmd, resp):
    classStates = {}
    if respCmd['cmd'] == 'lookup':
        charInfo = resp[1]['Character']
        charGrandCompInfo = charInfo['GrandCompany']
        activeClass = charInfo['ActiveClassJob']

        charStats = {'name': charInfo['Name'], 'activeClassName': activeClass['UnlockedState']['Name'],
                     'activeClassLv': activeClass['Level'], 'id': charInfo['ID'],
                     'nameday': charInfo['Nameday'], 'avatar': charInfo['Avatar'].replace('\\',''),
                     'title': charInfo['Title']['Name']}

        # Check if character is part of a Grand Company
        if charGrandCompInfo['Company'] is not None:
            charStats['grandCompName'] = charGrandCompInfo['Company']['Name']
            charStats['grandCompID'] = charGrandCompInfo['Company']['ID']
        else:
            charStats['grandCompName'] = "None"

        if "Blue Mage" in charStats['activeClassName']:
            charStats['activeClassName'] = "Blue Mage"
        
        charStats['activeClassName'] = charStats['activeClassName']

        # Class Info
        print("")

        tankClasses = []
        healerClasses = []
        meleeDpsClasses = []
        rangePhyDpsClasses = []
        rangeMagDpsClasses = []
        crafterClasses = []
        gathererClasses = []


        for classInfo in charInfo['ClassJobs']:
            # print(classInfo)
            if classInfo['UnlockedState']['ID'] is not None:
                classId = classInfo['UnlockedState']['ID']
            else:
                classId = classInfo['Class']['ID']
            classLv = classInfo['Level']
            className = classInfo['UnlockedState']['Name']

            if "Blue Mage" in className:
                className = "Blue Mage"

            classEmote = ""

            if classId in EMOTE_ID:
                classEmote = EMOTE_ID[classId]

            else:
                raise TypeError('Class %d not found' % (classId))
            
            if classId in CHAR_CLASS_TYPE_TANK:
                tankClasses.append((classEmote,classLv))

            elif classId in CHAR_CLASS_TYPE_HEALER:
                healerClasses.append((classEmote,classLv))
            
            elif classId in CHAR_CLASS_TYPE_MELEE_DPS:
                meleeDpsClasses.append((classEmote,classLv))

            elif classId in CHAR_CLASS_TYPE_RANGE_PHY_DPS:
                rangePhyDpsClasses.append((classEmote,classLv))
            
            elif classId in CHAR_CLASS_TYPE_RANGE_MAG_DPS:
                rangeMagDpsClasses.append((classEmote,classLv))

            elif classId in CHAR_CLASS_CRAFTER:
                crafterClasses.append((classEmote,classLv))

            elif classId in CHAR_CLASS_GATHERER:
                gathererClasses.append((classEmote,classLv))

            else:
                raise TypeError('Unknown class. ID = %d' % (classId))        

        tankRoleStr = ""
        healerRoleStr = ""
        meleeDpsRoleStr = ""
        rangePhyDpsRoleStr = ""
        rangeMagDpsRoleStr = ""
        crafterRoleStr = ""
        gathererRoleStr = ""

        for tankClass in tankClasses:
            tankRoleStr += "%s  %s\n" %(tankClass[0],tankClass[1])
        
        for healerClass in healerClasses:
            healerRoleStr += "%s  %s\n" %(healerClass[0],healerClass[1])

        for meleeDpsClass in meleeDpsClasses:
            meleeDpsRoleStr += "%s  %s\n" %(meleeDpsClass[0],meleeDpsClass[1])

        for rangePhyDpsClass in rangePhyDpsClasses:
            rangePhyDpsRoleStr += "%s  %s\n" %(rangePhyDpsClass[0],rangePhyDpsClass[1])

        for rangeMagDpsClass in rangePhyDpsClasses:
            rangeMagDpsRoleStr += "%s  %s\n" %(rangeMagDpsClass[0],rangeMagDpsClass[1])
        
        for crafterClass in crafterClasses:
            crafterRoleStr += "%s  %s\n" %(crafterClass[0],crafterClass[1])

        for gathererClass in gathererClasses:
            gathererRoleStr += "%s  %s\n" %(gathererClass[0],gathererClass[1])

        # Generate Embed message
        embedVar = discord.Embed(title=charStats['name'], description=charStats['title'])
        embedVar.url='%s%s' %(CHAR_LODESTONE_URL, charStats['id'])
        if 'grandCompId' in charStats:
            embedVar.colour = GRAND_COMP_HEX_COLORS[charStats['grandCompID'] - 1]

        embedVar.set_thumbnail(url=charStats['avatar'])
        embedVar.add_field(name="Current Class", value="%s Lv. %3d\n\n" %(charStats["activeClassName"], charStats["activeClassLv"]))
        embedVar.add_field(name="Grand Company", value="%s" %(charStats['grandCompName']),inline=False)
        embedVar.add_field(name="%s Tank" % (ROLES_EMOTE_ID[0]), value="%s"%(tankRoleStr.replace(" ", " ")), inline=True)
        embedVar.add_field(name="%s Healer" % (ROLES_EMOTE_ID[1]), value="%s"%(healerRoleStr.replace(" ", " ")), inline=True)
        embedVar.add_field(name="%s Melee DPS" % (ROLES_EMOTE_ID[2]), value="%s"%(meleeDpsRoleStr.replace(" ", " ")), inline=True)
        embedVar.add_field(name="%s Ranged Phys DPS" % (ROLES_EMOTE_ID[3]), value="%s"%(rangePhyDpsRoleStr.replace(" ", " ")), inline=True)
        embedVar.add_field(name="%s Ranged Magic DPS" % (ROLES_EMOTE_ID[4]), value="%s"%(rangeMagDpsRoleStr.replace(" ", " ")), inline=False)
        embedVar.add_field(name="Crafter", value="%s"%(crafterRoleStr.replace(" ", " ")), inline=True)
        embedVar.add_field(name="Gatherer", value="%s"%(gathererRoleStr.replace(" ", " ")), inline=False)

        await msg.channel.send(embed=embedVar)
    

client.run(DISCORD_TOKEN) 