# Script to grab all player names from the VLR API and save them into a dictionary.

import aiohttp
import time
import json
import os

CACHE_FILE = "player_cache.json"
CACHE_EXPIRY = 86400  # 24 hours in seconds

async def fetchPlayersByChunks(session):
    """Fetch players in chunks to handle API limitations"""
    url = f"http://localhost:5000/api/v1/players?limit=all"
    
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data.get("data", []), data.get("metadata", {}).get("total", 0)
    return [], 0

async def fetchPlayersFromTeams(session, teams_ids):
    """Fetch players directly from team rosters to ensure completeness"""
    players = []
    
    for team_id in teams_ids:
        url = f"http://localhost:5000/api/v1/teams/{team_id}"
        
        async with session.get(url) as response:
            if response.status == 200:
                team_data = await response.json()
                team_players = team_data.get("data", {}).get("players", [])
                players.extend(team_players)
                
    return players

async def fetchAllPlayerNames():
    playerNameMappings = {}
    playersNameList = []
    fetched_player_ids = set()
    
    async with aiohttp.ClientSession() as session:
        
        chunk, total = await fetchPlayersByChunks(session)
        
        for player in chunk:
            player_id = player.get("id")
            player_name = player.get("user") or player.get("name")
            
            if player_id and player_name and player_id not in fetched_player_ids:
                playerNameMappings[player_name.lower()] = player_id
                playersNameList.append({"name": player_name, "id": player_id})
                fetched_player_ids.add(player_id)
        
        print(f"Fetched {len(fetched_player_ids)} players")
            
        teams_endpoint = "http://localhost:5000/api/v1/teams?limit=all"
        async with session.get(teams_endpoint) as teams_response:
            if teams_response.status == 200:
                teams_data = await teams_response.json()
                team_ids = [team.get("id") for team in teams_data.get("data", []) if team.get("id")]
                
                roster_players = await fetchPlayersFromTeams(session, team_ids)
                
                for player in roster_players:
                    player_id = player.get("id")
                    player_name = player.get("user") or player.get("name")
                    
                    if player_id and player_name and player_id not in fetched_player_ids:
                        playerNameMappings[player_name.lower()] = player_id
                        playersNameList.append({"name": player_name, "id": player_id})
                        fetched_player_ids.add(player_id)
    
    cache = {
        "timestamp": time.time(),
        "playerNameMappings": playerNameMappings,
        "playersNameList": playersNameList
    }

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)
    
    print(f"Fetched and cached {len(playersNameList)} player names.")
    return playerNameMappings, playersNameList

async def getPlayerMapping():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
                
            # Check if cache is still valid
            if time.time() - cache.get("timestamp", 0) < CACHE_EXPIRY:
                return cache.get("playerNameMappings", {}), cache.get("playersNameList", [])
            else:
                print("🔄 Player cache expired, refreshing...")
        except Exception as e:
            print(f"⚠️ Error reading player cache: {str(e)}")
    
    # Cache doesn't exist or is expired
    return await fetchAllPlayerNames()

def getCachedPlayerMappingSync():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
            return cache.get("playerNameMappings", {}), cache.get("playersNameList", [])
        except Exception:
            return {}, []
    return {}, []

# Add this to your bot's startup routine
async def initializePlayerCache():
    print("🔄 Initializing player cache...")
    await getPlayerMapping()
    print("✅ Player cache initialized")