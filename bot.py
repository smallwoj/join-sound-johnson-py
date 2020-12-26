import asyncio
import os

import discord
from discord import voice_client
from dotenv import load_dotenv
from discord.ext import commands
from pytube import YouTube
from db import Database

db = Database()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix='j!', intents=intents)

@bot.command(name='ping')
async def pong(ctx: commands.context.Context):
    await ctx.send(f'Pong! ({bot.latency})')

@bot.command(name='set')
async def set_sound(ctx: commands.context.Context, link: str):
    yt = YouTube(link)
    sound = yt.streams.filter(type='audio').first()
    if sound.filesize < 100000:
        db.upload_sound(ctx.author.id, sound)
        await ctx.send("Successful!")
    else:
        await ctx.send("too big")

@bot.command(name='remove')
async def remove_sound(ctx: commands.context.Context):
    if db.has_sound(ctx.author.id):
        db.remove_sound(ctx.author.id)
        await ctx.send('Removed!')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_voice_state_update(user: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if not before.channel and after.channel:
        if db.has_sound(user.id):
            path = db.get_sound(user.id)
            source = await discord.FFmpegOpusAudio.from_probe(path)
            if user.guild in map(lambda x: x.guild, bot.voice_clients):
                voice_connection = list(filter(lambda x: x.guild == user.guild, bot.voice_clients))[0]
                if after.channel != voice_connection.channel:
                    await voice_connection.disconnect()
                    voice_connection = await after.channel.connect(reconnect=False)
            else:
                voice_connection = await after.channel.connect(reconnect=False)
            if voice_connection.is_playing():
                voice_connection.stop()
            voice_connection.play(source)
            while voice_connection.is_playing():
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(10)
                while voice_connection.is_playing():
                    break
                else:
                    await voice_connection.disconnect()

bot.run(TOKEN)
