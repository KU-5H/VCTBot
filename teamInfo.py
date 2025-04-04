import discord
import aiohttp
from dotenv import load_dotenv

from discord.ui import Button, View

class TeamInfoView(View):
    def __init__(self, team_data, team_id):
        super().__init__()
        self.team_data = team_data
        self.team_name = team_data["data"]["info"]["name"]
        self.team_id = team_id
        self.players_data = team_data["data"].get("players", [])
        self.staff_data = team_data["data"].get("staff", [])
    
    def create_player_embed(self):
        if self.players_data:
            players = "\n".join(
                f"**{player['user']}** ({player['name']})"
                for player in self.players_data if "name" in player and "user" in player
            )
        else:
            players = "No players listed"
        
        embed = discord.Embed(title=f"🏆 {self.team_name}", color=discord.Color.blue())
        embed.add_field(name="👥 Players", value=players, inline=False)
        embed.set_footer(text=f"Team ID: {self.team_id}")
        return embed
    
    def create_staff_embed(self):
        if self.staff_data:
            staff = "\n".join(
                f"**{staff['user']}** ({staff['name']}, Role: {staff.get('tag', 'Unknown')})"
                for staff in self.staff_data if "name" in staff and "user" in staff
            )
        else:
            staff = "No staff listed"
            
        embed = discord.Embed(title=f"{self.team_name}", color=discord.Color.green())
        embed.add_field(name="👥 Staff", value=staff, inline=False)
        embed.set_footer(text=f"Team ID: {self.team_id}")
        return embed
    
    @discord.ui.button(label="View Staff 👔", style=discord.ButtonStyle.primary, custom_id="view_staff")
    async def view_staff_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Create staff view and embed
        staff_view = StaffView(self.team_data, self.team_id)
        staff_embed = self.create_staff_embed()
        
        # Edit the message with staff info
        await interaction.response.edit_message(embed=staff_embed, view=staff_view)

class StaffView(discord.ui.View):
    def __init__(self, team_data, team_id):
        super().__init__(timeout=None)  # No timeout for the view
        self.team_data = team_data
        self.team_name = team_data["data"]["info"]["name"]
        self.team_id = team_id
        self.players_data = team_data["data"].get("players", [])
        self.staff_data = team_data["data"].get("staff", [])
    
    def create_player_embed(self):
        if self.players_data:
            players = "\n".join(
                f"**{player['user']}** ({player['name']})"
                for player in self.players_data if "name" in player and "user" in player
            )
        else:
            players = "No players listed"
            
        embed = discord.Embed(title=f"{self.team_name}", color=discord.Color.blue())
        embed.add_field(name="👥 Players", value=players, inline=False)
        embed.set_footer(text=f"Team ID: {self.team_id}")
        return embed
    
    @discord.ui.button(label="View Players 👥", style=discord.ButtonStyle.secondary, custom_id="view_players")
    async def view_players_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Create player view and embed
        player_view = TeamInfoView(self.team_data, self.team_id)
        player_embed = self.create_player_embed()
        
        # Edit the message with player info
        await interaction.response.edit_message(embed=player_embed, view=player_view)

async def teamInfo(interaction: discord.Interaction, team_id: int):
    url = f"http://localhost:5000/api/v1/teams/{team_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                team_data = await response.json()
                
                # Create the view and embed
                view = TeamInfoView(team_data, team_id)
                embed = view.create_player_embed()
                
                # Send the initial message
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(f"❌ Error: Unable to fetch data (status code {response.status})")