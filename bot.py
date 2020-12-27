import asyncio
import os
import logging
import discord
from dotenv import load_dotenv
from discord.ext import commands
from pytube import YouTube
from pytube.exceptions import RegexMatchError
from db import Database

logging.basicConfig(filename='bot.log', format='[%(levelname)s] (%(asctime)s): %(message)s', level=logging.DEBUG)
db = Database()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix='j!', intents=intents)

@bot.command(name='ping', help='Gives the latency of the bot.')
async def pong(ctx: commands.context.Context):
    await ctx.send(f'Pong! (Took {bot.latency})')

@bot.command(name='set', help='Set your join sound to the given YouTube link.')
async def set_sound(ctx: commands.context.Context, link: str):
    msg = await ctx.send('🔃 Please wait...')
    try:
        yt = YouTube(link)
        if yt.length <= 10:
            sound = yt.streams.filter(type='audio').first()
            db.upload_sound(ctx.author.id, sound)
            await msg.edit(content="✅ Successful!")
        else:
            await msg.edit(content="❌ That video is too long! Videos should be less than 10 seconds in length.")
    except (RegexMatchError, KeyError):
        await msg.edit(content='❌ Not a valid YouTube link!')
    except Exception as e:
        logging.error('Error while setting sound: ' + e)
        await msg.edit(content='❌ Some unknown error occurred!')

@set_sound.error
async def missing_param(ctx: commands.context.Context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Missing YouTube link!')
    else:
        logging.error('Error while setting sound: ' + error)

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

@remove_sound.error
async def remove_error(ctx: commands.context.Context, error):
    logging.error('Error while removing: ' + error)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    logging.info(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='j!help'))

@bot.event
async def on_voice_state_update(user: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """
    The meat of the bot, whenever a user connects to a voice channel, connect and play their sound.

    :param user: The user that joined the channel
    :param before: The user's voice state before the change.
    :param after: The user's voice state after the change
    """
    try:
        # Since this event fires multiple times, ensure that there is not a channel before, and a channel after
        if not before.channel and after.channel:
            # Check if this user has a sound in the database
            if db.has_sound(user.id):
                path = db.get_sound(user.id)
                # Create an audio source for the sound
                source = discord.FFmpegPCMAudio(path)
                # Check if the bot is already connected to a voice channel in the server
                if user.guild in map(lambda x: x.guild, bot.voice_clients):
                    # If the bot is connected to a different channel than the one the user just connected to, disconnect
                    voice_connection = list(filter(lambda x: x.guild == user.guild, bot.voice_clients))[0]
                    if after.channel != voice_connection.channel:
                        await voice_connection.disconnect()
                        voice_connection = await after.channel.connect(reconnect=False)
                else:
                    voice_connection = await after.channel.connect(reconnect=False)
                # Interrupt the current sound if there is one playing
                if voice_connection.is_playing():
                    voice_connection.stop()
                # Reduce the volume
                source = discord.PCMVolumeTransformer(source, volume=0.01)
                # Play it
                voice_connection.play(source)

                # Auto disconnect after a little bit
                while voice_connection.is_playing():
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(10)
                    while voice_connection.is_playing():
                        break
                    else:
                        await voice_connection.disconnect()
    except Exception as e:
        logging.error('Error while playing sound: ' + e)

bot.run(TOKEN)
