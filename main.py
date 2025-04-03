import discord
import aiohttp
import os
from dotenv import load_dotenv

from discord.ext import commands
from discord.ui import Button, View

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot setup with slash commands
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.tree.command(name="team", description="Get team info by ID")
async def team(interaction: discord.Interaction, team_id: int):
    url = f"http://localhost:5000/api/v1/teams/{team_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                team_name = data["data"]["info"]["name"]
                players_data = data["data"].get("players")
                staff_data = data["data"].get("staff")
                
                # Player Embed
                team_name = data["data"]["info"]["name"]
                players_data = data["data"].get("players")
                if players_data:
                    players = "\n".join(
                        f"**{player['user']}** ({player['name']})"
                        for player in players_data if "name" in player and "user" in player
                    )
                else:
                    players = "No players listed"
                
                # Create an embed
                embed = discord.Embed(title=f"🏆 {team_name}", color=discord.Color.blue())
                embed.add_field(name="👥 Players", value=players, inline=False)
                embed.set_footer(text=f"Team ID: {team_id}")
                

                #Staff Embed
                button = Button(label="View Staff", style=discord.ButtonStyle.primary)

                async def button_callback(interaction: discord.Interaction):
                    staff_data = data["data"].get("staff")
                    if staff_data:
                        staff = "\n".join(
                            f"**{staff['user']}** ({staff['name']}, Role: {staff.get('tag', 'Unknown')})"
                            for staff in staff_data if "name" in staff and "user" in staff
                        )
                    else:
                        staff = "No staff listed"
                    
                    # Create an embed for staff
                    staff_embed = discord.Embed(title=f"👔 Staff of {team_name}", color=discord.Color.green())
                    staff_embed.add_field(name="👥 Staff", value=staff, inline=False)
                    staff_embed.set_footer(text=f"Team ID: {team_id}")

                    # Add a "View Players" button to go back
                    players_button = Button(label="View Players", style=discord.ButtonStyle.secondary)

                    async def players_button_callback(interaction: discord.Interaction):
                        await interaction.response.edit_message(embed=embed, view=view)

                    players_button.callback = players_button_callback

                    # Create a new view with the "View Players" button
                    staff_view = View()
                    staff_view.add_item(players_button)

                    await interaction.response.edit_message(embed=staff_embed, view=staff_view)

                button.callback = button_callback

                view = View()
                view.add_item(button)

                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(f"❌ Error: Unable to fetch data (status code {response.status})")

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()  # Force sync commands
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    print(f"Logged in as {bot.user}")

bot.run(DISCORD_BOT_TOKEN)
