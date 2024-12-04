
import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import schedule
import time
import asyncio
import openai  
from youtube_dl import YoutubeDL

TOKEN = os.getenv("SECRET_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  
openai.api_key = OPENAI_API_KEY

# Intents and bot initialization
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Feature 1: Text interaction (using OpenAI for responses)
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    check_events.start()

@bot.command(name="ask")
async def respond_to_text(ctx, *, query):
    """Send the user's query to OpenAI and get a response."""
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  
            prompt=query,
            max_tokens=100,
            temperature=0.7  
        )
        answer = response.choices[0].text.strip() 
        await ctx.send(answer)  
    except Exception as e:
        await ctx.send(f"Sorry, I couldn't process your request: {e}")

# Feature 2: Event Scheduling
events = []

@bot.command(name="schedule_event")
async def schedule_event(ctx, time: str, *, event: str):
    """Schedule an event at a specific time in HH:MM format."""
    events.append({"time": time, "event": event})
    await ctx.send(f"Scheduled event '{event}' at {time}.")

@tasks.loop(minutes=1)
async def check_events():
    """Check for scheduled events."""
    current_time = time.strftime("%H:%M")
    for event in events[:]:  # Copy list to avoid modifying while iterating
        if event["time"] == current_time:
            events.remove(event)  # Remove executed event
            for channel in bot.get_all_channels():
                if channel.name == "general":
                    await channel.send(f"Reminder: {event['event']} is happening now!")
                    break

# Feature 3: Real-time Alerts
@bot.command(name="set_alert")
async def set_alert(ctx, time: str, *, message: str):
    """Set a real-time alert."""
    async def alert():
        await ctx.send(f"🔔 Alert: {message}")
    schedule.every().day.at(time).do(asyncio.run, alert())
    await ctx.send(f"Alert set for {time}: {message}")

# Feature 4: Music Playback
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}
FFMPEG_OPTIONS = {'options': '-vn'}

@bot.command(name="play")
async def play(ctx, *, url: str):
    """Play a song from a YouTube URL."""
    if not ctx.author.voice:
        await ctx.send("You need to join a voice channel first!")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()

    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        voice_client.play(discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS))

@bot.command(name="stop")
async def stop(ctx):
    """Stop the music and disconnect."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel!")

bot.run(TOKEN)
