import discord
import aiohttp

from discord.ui import Button, View
from discord import ButtonStyle, Embed, Interaction, app_commands

from scripts.teamNameFetcher import getCachedMappingSync

class BaseTeamView(View):
    def __init__(self, team_data, team_id):
        super().__init__(timeout=None) 
        self.team_data = team_data
        self.team_id = team_id
        self.team_logo = team_data["data"]["info"].get("logo", None)
        self.team_name = team_data["data"]["info"]["name"]
        self.players_data = team_data["data"].get("players", [])
        self.staff_data = team_data["data"].get("staff", [])
        self.upcoming_matches = team_data["data"].get("upcoming", [])

        vlr_url = f"https://www.vlr.gg/team/{team_id}"
        self.add_item(Button(
            style=ButtonStyle.primary,
            label="VLR Team Page",
            url=vlr_url
        ))
    
    def create_player_embed(self):
        if self.players_data:
            players = "\n".join(
                f"**[{player['user']}]({player.get('url', '#')})** ({player['name']})"
                for player in self.players_data if "name" in player and "user" in player
            )
        else:
            players = "No players listed"
        
        embed = Embed(title=f"{self.team_name}", color=discord.Color.blue())
        embed.add_field(name="👥 Players", value=players, inline=False)
        embed.set_footer(text=f"Team ID: {self.team_id}")

        if self.team_logo:
            embed.set_thumbnail(url=self.team_logo)
        return embed
    
    def create_staff_embed(self):
        if self.staff_data:
            staff = "\n".join(
                f"**[{staff['user']}]({staff.get('url', '#')})** ({staff['name']}, Role: {staff.get('tag', 'Unknown')})"
                for staff in self.staff_data if "name" in staff and "user" in staff
            )
        else:
            staff = "No staff listed"
            
        embed = Embed(title=f"{self.team_name}", color=discord.Color.blurple())
        embed.add_field(name="👥 Staff", value=staff, inline=False)
        embed.set_footer(text=f"Team ID: {self.team_id}")

        if self.team_logo:
            embed.set_thumbnail(url=self.team_logo)
        return embed
    
    def create_upcoming_embed(self):
        embed = Embed(title=f"{self.team_name} - Upcoming Matches", color=discord.Color.green())

        if self.upcoming_matches and len(self.upcoming_matches) > 0:
            listOfMatches = []

            for match in self.upcoming_matches:
                matchUrl = match["match"]["url"]
                eventName = match["event"]["name"]
                team1 = match["teams"][0]
                team2 = match["teams"][1]

                from datetime import datetime
                try:
                    matchTime = datetime.strptime(match["utc"], "%a, %d %b %Y %H:%M:%S %Z")
                    dateStr = matchTime.strftime("%b %d")
                    timeStr = matchTime.strftime("%H:%M UTC")
                except:
                    dateStr = "TBD"
                    timeStr = "TBD"

                matchLine = f"**{dateStr}** · {timeStr} · [{team1['tag']} vs {team2['tag']}]({matchUrl}) | {eventName}"
                listOfMatches.append(matchLine)
            
            matchesText = "\n".join(listOfMatches)
            embed.description = matchesText

            if self.team_logo:
                embed.set_thumbnail(url=self.team_logo)

        else:
            embed.description = "No upcoming matches"
            if self.team_logo:
                embed.set_thumbnail(url=self.team_logo)
        return embed

class TeamInfoView(BaseTeamView):
    @discord.ui.button(label="View Staff 👔", style=ButtonStyle.primary, custom_id="view_staff")
    async def view_staff_button(self, interaction: Interaction, button: Button):
        staff_view = StaffView(self.team_data, self.team_id)
        staff_embed = self.create_staff_embed()
        await interaction.response.edit_message(embed=staff_embed, view=staff_view)

    @discord.ui.button(label="View Matches 📅", style=ButtonStyle.success, custom_id="view_matches_from_players")
    async def view_matches_button(self, interaction: Interaction, button: Button):
        matches_view = UpcomingMatchesView(self.team_data, self.team_id)
        matches_embed = self.create_upcoming_embed()
        await interaction.response.edit_message(embed=matches_embed, view=matches_view)

class StaffView(BaseTeamView):
    @discord.ui.button(label="View Players 👥", style=ButtonStyle.primary, custom_id="view_players")
    async def view_players_button(self, interaction: Interaction, button: Button):
        player_view = TeamInfoView(self.team_data, self.team_id)
        player_embed = self.create_player_embed()
        await interaction.response.edit_message(embed=player_embed, view=player_view)
    
    @discord.ui.button(label="View Matches 📅", style=ButtonStyle.success, custom_id="view_matches_from_staff")
    async def view_matches_button(self, interaction: Interaction, button: Button):
        matches_view = UpcomingMatchesView(self.team_data, self.team_id)
        matches_embed = self.create_upcoming_embed()
        await interaction.response.edit_message(embed=matches_embed, view=matches_view)

class UpcomingMatchesView(BaseTeamView):
    @discord.ui.button(label="View Players 👥", style=ButtonStyle.primary, custom_id="view_players_from_matches")
    async def view_players_button(self, interaction: Interaction, button: Button):
        player_view = TeamInfoView(self.team_data, self.team_id)
        player_embed = self.create_player_embed()
        await interaction.response.edit_message(embed=player_embed, view=player_view)
    
    # Add button to view staff
    @discord.ui.button(label="View Staff 👔", style=ButtonStyle.primary, custom_id="view_staff_from_matches")
    async def view_staff_button(self, interaction: Interaction, button: Button):
        staff_view = StaffView(self.team_data, self.team_id)
        staff_embed = self.create_staff_embed()
        await interaction.response.edit_message(embed=staff_embed, view=staff_view)

async def teamInfoById(interaction: Interaction, team_id: int):
    url = f"http://localhost:5000/api/v1/teams/{team_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                # Get team data
                team_data = await response.json()
                
                # Create the view and embed
                view = TeamInfoView(team_data, team_id)
                embed = view.create_player_embed()
                
                # Send the initial message
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(f"❌ Error: Unable to fetch data for team ID {team_id} (status code {response.status})")

async def teamNameAutocomplete(interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:

    _, teamList = getCachedMappingSync()

    if not current:
        matches = teamList[:25]
    else:
        currentLower = current.lower()
        matches = [
            team for team in teamList if currentLower in team["name"].lower()
        ][:25]
    
    return [
        app_commands.Choice(name=team["name"], value=team["id"])
        for team in matches
    ]

