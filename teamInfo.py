import discord
import aiohttp

from discord.ui import Button, View
from discord import ButtonStyle, Embed, Interaction, app_commands
from datetime import datetime

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
        self.results = team_data["data"].get("results", [])

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
            list_of_matches = []

            for match in self.upcoming_matches:
                match_url = match["match"]["url"]
                event_name = match["event"]["name"]
                team1_name = match["teams"][0]["tag"]
                team2_name = match["teams"][1]["tag"]

                try:
                    match_time = datetime.strptime(match["utc"], "%a, %d %b %Y %H:%M:%S %Z")
                    date_str = match_time.strftime("%b %d")
                    time_str = match_time.strftime("%H:%M UTC")
                except ValueError:
                    date_str = "TBD"
                    time_str = "TBD"

                match_line = f"**{date_str}** · {time_str} · [{team1_name} vs {team2_name}]({match_url}) | {event_name}"
                list_of_matches.append(match_line)
            
            matches_text = "\n".join(list_of_matches)
            embed.description = matches_text

            if self.team_logo:
                embed.set_thumbnail(url=self.team_logo)
            embed.set_footer(text=f"Team ID: {self.team_id}")

        else:
            embed.description = "No upcoming matches"
            if self.team_logo:
                embed.set_thumbnail(url=self.team_logo)
        return embed
    
    def create_results_embed(self):
        embed = Embed(title=f"{self.team_name} - Recent Results", color=discord.Color.brand_green())

        if self.results and len(self.results) > 0:
            list_of_matches = []

            for i, match in enumerate(self.results[:15]):

                event_name = (match["event"]["name"] or "N/A")[:22].ljust(22)

                team1 = match["teams"][0]
                team2 = match["teams"][1]

                tag1 = (team1.get("tag") or "N/A")[:5].ljust(5)
                tag2 = (team2.get("tag") or "N/A")[:5].ljust(5)
                score = f"{team1.get('points') or 0}-{team2.get('points') or 0}".center(5)

                match_text = f"{score} · {tag1.strip()} vs {tag2.strip()}"
                match_line = f"{match_text.ljust(20)}| {event_name}"

                list_of_matches.append(match_line)

            matches_text = "\n".join(list_of_matches)
            matches_text = f"```{matches_text}```\nView full results on the team's VLR page"

            embed.description = matches_text

            if self.team_logo:
                embed.set_thumbnail(url=self.team_logo)

            embed.set_footer(text=f"Team ID: {self.team_id}")
        else:
            embed.description = "No recent results"
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
    
    @discord.ui.button(label="View Results 📊", style=ButtonStyle.green, custom_id="view_results_from_matches")
    async def view_results_button(self, interaction: Interaction, button: Button):
        results_view = ResultsView(self.team_data, self.team_id)
        results_embed = self.create_results_embed()
        await interaction.response.edit_message(embed=results_embed, view=results_view)

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
    
    @discord.ui.button(label="View Results 📊", style=ButtonStyle.green, custom_id="view_results_from_matches")
    async def view_results_button(self, interaction: Interaction, button: Button):
        results_view = ResultsView(self.team_data, self.team_id)
        results_embed = self.create_results_embed()
        await interaction.response.edit_message(embed=results_embed, view=results_view)

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
    
    @discord.ui.button(label="View Results 📊", style=ButtonStyle.green, custom_id="view_results_from_matches")
    async def view_results_button(self, interaction: Interaction, button: Button):
        results_view = ResultsView(self.team_data, self.team_id)
        results_embed = self.create_results_embed()
        await interaction.response.edit_message(embed=results_embed, view=results_view)

class ResultsView(BaseTeamView):
    @discord.ui.button(label="View Players 👥", style=ButtonStyle.primary, custom_id="view_players_from_results")
    async def view_players_button(self, interaction: Interaction, button: Button):
        player_view = TeamInfoView(self.team_data, self.team_id)
        player_embed = self.create_player_embed()
        await interaction.response.edit_message(embed=player_embed, view=player_view)
    
    # Add button to view staff
    @discord.ui.button(label="View Staff 👔", style=ButtonStyle.primary, custom_id="view_staff_from_results")
    async def view_staff_button(self, interaction: Interaction, button: Button):
        staff_view = StaffView(self.team_data, self.team_id)
        staff_embed = self.create_staff_embed()
        await interaction.response.edit_message(embed=staff_embed, view=staff_view)

    @discord.ui.button(label="View Matches 📅", style=ButtonStyle.success, custom_id="view_matches_from_staff")
    async def view_matches_button(self, interaction: Interaction, button: Button):
        matches_view = UpcomingMatchesView(self.team_data, self.team_id)
        matches_embed = self.create_upcoming_embed()
        await interaction.response.edit_message(embed=matches_embed, view=matches_view)

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

