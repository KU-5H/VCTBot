import discord
import os
from dotenv import load_dotenv
from teamInfo import teamInfo

from discord.ext import commands

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot setup with slash commands
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.tree.command(name="team", description="Get team info by ID")
async def team(interaction: discord.Interaction, team_id: int):
    await teamInfo(interaction, team_id)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()  # Force sync commands
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    print(f"Logged in as {bot.user}")

bot.run(DISCORD_BOT_TOKEN)
