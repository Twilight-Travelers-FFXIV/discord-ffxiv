import asyncio
import logging
import aiohttp
from aiolimiter import AsyncLimiter
import pyxivapi
from pyxivapi.models import Filter, Sort
import discord
from configKeys import FFXIV_API_KEY, DISCORD_TOKEN
import json

MAX_REQ = 20 - 5 # buffer (request per second)
DATA_CENTERS = ["Adamantoise","Aegis","Alexander","Anima","Asura","Atomos","Bahamut","Balmung","Behemoth","Belias","Brynhildr","Cactuar","Carbuncle","Cerberus","Chocobo","Coeurl","Diabolos","Durandal","Excalibur","Exodus","Faerie","Famfrit","Fenrir","Garuda","Gilgamesh","Goblin","Gungnir","Hades","Hyperion","Ifrit","Ixion","Jenova","Kujata","Lamia","Leviathan","Lich","Louisoix","Malboro","Mandragora","Masamune","Mateus","Midgardsormr","Moogle","Odin","Omega","Pandaemonium","Phoenix","Ragnarok","Ramuh","Ridill","Sargatanas","Shinryu","Shiva","Siren","Tiamat","Titan","Tonberry","Typhon","Ultima","Ultros","Unicorn","Valefor","Yojimbo","Zalera","Zeromus","Zodiark","Spriggan","Twintania","HongYuHai","ShenYiZhiDi","LaNuoXiYa","HuanYingQunDao","MengYaChi","YuZhouHeYin","WoXianXiRan","ChenXiWangZuo","BaiYinXiang","BaiJinHuanXiang","ShenQuanHen","ChaoFengTing","LvRenZhanQiao","FuXiaoZhiJian","Longchaoshendian","MengYuBaoJing","ZiShuiZhanQiao","YanXia","JingYuZhuangYuan","MoDuNa","HaiMaoChaWu","RouFengHaiWan","HuPoYuan"]

client = discord.Client()
rate_limit = AsyncLimiter(MAX_REQ,1)

BOT_CMDS = ['lookup', 'lookupId']

prefix = "$"
bot_commands = []
worldList = []

@client.event
async def on_ready():
    global worldList
    print("Logged in as %s" %(client))
    await populate_commands()
    async with rate_limit:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://xivapi.com/servers') as resp:
                worldList = await resp.json()


    print("Available commands: %s" % (bot_commands))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    # async with rate_limit:
    if msg.content.startswith('$ping'):
        await msg.channel.send('pong')

    if msg.content.startswith(prefix):
        msgParsed = msg.content.split()
        print("Received query: %s" % (msgParsed))
        if msgParsed[0] in bot_commands:
            
            if msgParsed[0] == "%slookup" % (prefix):

                if len(msgParsed) == 4:
                    #Check world if valid
                    if not "%s%s" % (msgParsed[1][0].upper(),msgParsed[1][1:].lower()) in worldList:
                        await msg.channel.send("Invalid world")
                        return
                    lodestoneCmd = {'cmd':'lookup', 'world':msgParsed[1].lower(), 'forename':msgParsed[2], 'surname':msgParsed[3]}
                    resp = await lodestone_process(msg, lodestoneCmd)

                    #Process response


            elif msgParsed[0] == "%slookupId" % (prefix):
                if len(msgParsed) == 2:
                    lodestoneCmd = {'cmd':'lookupId', 'id': msgParsed[1]}
                    await lodestone_process(msg, lodestoneCmd)
                

    
async def populate_commands():
    global bot_commands
    bot_commands = ["%s%s" % (prefix, cmd) for cmd in BOT_CMDS]

async def lodestone_process(msg, queryCmd):
    toClose = True
    resp = ''

    async with rate_limit:
        client = pyxivapi.XIVAPIClient(api_key=FFXIV_API_KEY)

        if queryCmd['cmd'] == 'lookup':
            print("Looking up character... ")
            resp = await client.character_search(
                world = queryCmd['world'],
                forename = queryCmd['forename'],
                surname = queryCmd['surname']
            )
            print("Received Lodestone resp:\n %s" %(resp))

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
            print("Received Lodestone resp:\n %s" %(resp))
        
        if toClose:
            await client.session.close()

        return resp

client.run(DISCORD_TOKEN) 