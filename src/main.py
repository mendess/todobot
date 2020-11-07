import discord
from discord.ext import commands
from todo import Todos



BOT = commands.Bot(command_prefix='!', case_insensitive=True)

@BOT.event
async def on_ready():
    print('We have a lot to do :p')

BOT.add_cog(Todos())

with open('files/auth') as f:
    TOKEN = f.read()

BOT.run(TOKEN.strip())
