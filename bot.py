import asyncio
import os

import discord
from discord import voice_client
from dotenv import load_dotenv
from discord.ext import commands
from pytube import YouTube
from pytube.exceptions import RegexMatchError
from db import Database

db = Database()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix='j!', intents=intents)

@bot.command(name='ping', help='Gives the latency of the bot.')
async def pong(ctx: commands.context.Context):
    await ctx.send(f'Pong! ({bot.latency} ms)')

@bot.command(name='set', help='Set your join sound to the given YouTube link.')
async def set_sound(ctx: commands.context.Context, link: str):
    msg = await ctx.send('🔃 Please wait...')
    try:
        yt = YouTube(link)
        sound = yt.streams.filter(type='audio').first()
        if sound.filesize < 100000:
            db.upload_sound(ctx.author.id, sound)
            await msg.edit(content="✅ Successful!")
        else:
            await msg.edit(content="❌ That video is too long! Videos should be less than 5 seconds in length.")
    except (RegexMatchError, KeyError):
        await msg.edit(content='❌ Not a valid YouTube link!')
    except Exception:
        await msg.edit(content='❌ Some unknown error occurred!')

@set_sound.error
async def missing_param(ctx: commands.context.Context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Missing YouTube link!')

@bot.command(name='remove', help='Removes your join sound from the records.')
async def remove_sound(ctx: commands.context.Context):
    if db.has_sound(ctx.author.id):
        msg = await ctx.send('🔃 Please wait...')
        try:
            db.remove_sound(ctx.author.id)
            await msg.edit(content='✅ Removed!')
        except Exception:
            await msg.edit(content='❌ Some unknown error occurred!')
    else:
        await ctx.send('❌ No join sound to remove!')

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
