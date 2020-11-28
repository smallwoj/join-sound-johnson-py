import os

import discord
from dotenv import load_dotenv
from discord.ext import commands
from pytube import YouTube
from db import Database

db = Database()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='j!')

@bot.command(name='ping')
async def pong(ctx):
    print(ctx.author.id)
    await ctx.send(f'Pong! ({bot.latency})')

@bot.command(name='set')
async def set_sound(ctx, link):
    yt = YouTube(link)
    sound = yt.streams.filter(type='audio').first()
    if sound.filesize < 100000:
        db.upload_sound(ctx.author.id, sound)
        await ctx.send("Successful!")
    else:
        await ctx.send("too big")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

bot.run(TOKEN)
