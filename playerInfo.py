import discord
import aiohttp

from discord.ui import Button, View
from discord import ButtonStyle, Embed, Interaction

from scripts.teamNameFetcher import getCachedMappingSync


class PlayerView(View):
    def __init__(self, player_data, player_id):
        super().__init__(timeout=None)
        self.player_data = player_data
        self.player_id = player_id
        self.player_user_name = player_data["data"]["info"]["user"]
        self.player_name = player_data["data"]["info"]["name"]
        self.player_image = player_data["data"]["info"]["img"]
        self.player_url = player_data["data"]["info"]["url"]
        self.player_team_name = player_data["data"]["team"]["name"]
        self.player_team_id = player_data["data"]["team"]["id"]
        self.player_team_joined = player_data["data"]["team"]["joined"]
        self.player_country = player_data["data"]["info"]["flag"]
        self.player_socials = player_data["data"]["socials"]
    
    def create_player_embed(self):
        embed = Embed(
            title=f"{self.player_user_name}",
            url=self.player_url,
            color=discord.Color.blue()
        )

        if self.player_image:
            embed.set_thumbnail(url=self.player_image)
        
        country_text = f":flag_{self.player_country.lower()}:" if self.player_country else "Unknown"
        
        description = f"**Name:** {self.player_name}\n"
        description += f"**Team:** {self.player_team_name}\n"
        description += f"**Team Joined:** {self.player_team_joined}\n"
        description += f"**Country:** {country_text}\n"
        
        embed.description = description

        if self.player_socials and "twitter_url" in self.player_socials and self.player_socials["twitter_url"]:
            self.add_item(Button(
                style=ButtonStyle.url,
                label="🐦 X",
                url=self.player_socials["twitter_url"],
            )
        )
        
        if self.player_socials and "twitch_url" in self.player_socials and self.player_socials["twitch_url"]:
            self.add_item(Button(
                style=ButtonStyle.url,
                label="📺 Twitch",
                url=self.player_socials["twitch_url"],
            )
        )
        
        self.add_item(Button(
            style=ButtonStyle.url,
            label="VLR",
            url=self.player_url
        ))

        embed.set_footer(text=f"Player ID: {self.player_id}")
        
        return embed
    
    @discord.ui.button(label="View Team 📅", style=ButtonStyle.green, custom_id="view_team_from_player")
    async def view_team_button(self, interaction: Interaction, button: Button):
        from teamInfo import teamInfoById
        await teamInfoById(interaction, self.player_team_id)
        
async def playerInfoById(interaction: Interaction, player_id: int):
    url = f"http://localhost:5000/api/v1/players/{player_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                # Get team data
                player_data = await response.json()
                
                # Create the view and embed
                view = PlayerView(player_data, player_id)
                embed = view.create_player_embed()
                
                # Send the initial message
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(f"❌ Error: Unable to fetch data for team ID {player_id} (status code {response.status})")


