import discord
import os
from dotenv import load_dotenv

from teamInfo import teamInfoById, teamInfoByName, teamNameAutocomplete
from scripts.teamNameFetcher import initializeCache

from discord.ext import commands
from discord import app_commands

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot setup with slash commands
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Grab the team ID and call the teamInfoById function
@bot.tree.command(name="teamid", description="Get team info by ID")
async def team(interaction: discord.Interaction, team_id: int):
    await teamInfoById(interaction, team_id)

# Grab the team name from the autocomplete, find the corresponding ID, and call the teamInfoById function
@bot.tree.command(name="teamname", description="Get team info by Name")
@app_commands.autocomplete(team_name=teamNameAutocomplete)
async def team(interaction: discord.Interaction, team_name: int):
    await teamInfoById(interaction, team_name)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()  # Force sync commands
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    print(f"Logged in as {bot.user}")

    await initializeCache()  # Initialize the cache when the bot is ready

bot.run(DISCORD_BOT_TOKEN)
