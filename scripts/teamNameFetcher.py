# Script to grab all team names from the VLR API and save them into a dictionary.

import aiohttp
import time
import json
import os

CACHE_FILE = "team_cache.json"
CACHE_EXPIRY = 86400  # 24 hours in seconds

async def fetchAllTeamNames():
    url = "http://localhost:5000/api/v1/teams?limit=all"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                teamNameMappings = {}
                teamsNameList = []

                for team in data.get("data"):
                    team_id = team.get("id")
                    team_name = team.get("name")
                    
                    
                    if team_id and team_name:
                        teamNameMappings[team_name.lower()] = team_id
                        teamsNameList.append({"name": team_name, "id": team_id})
                    
                cache = {
                    "timestamp": time.time(),
                    "teamNameMappings": teamNameMappings,
                    "teamsNameList": teamsNameList
                }

                with open(CACHE_FILE, "w") as f:
                    json.dump(cache, f, indent=2)
                
                print(f"Fetched and cached {len(teamsNameList)} team names.")
                return teamNameMappings, teamsNameList

async def getTeamMapping():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
                
            # Check if cache is still valid
            if time.time() - cache.get("timestamp", 0) < CACHE_EXPIRY:
                return cache.get("teamNameMappings", {}), cache.get("teamsNameList", [])
            else:
                print("🔄 Cache expired, refreshing...")
        except Exception as e:
            print(f"⚠️ Error reading cache: {str(e)}")
    
    # Cache doesn't exist or is expired
    return await fetchAllTeamNames()

def getCachedMappingSync():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
            return cache.get("teamNameMappings", {}), cache.get("teamsNameList", [])
        except Exception:
            return {}, []
    return {}, []

# Add this to your bot's startup routine
async def initializeCache():
    print("🔄 Initializing team cache...")
    await getTeamMapping()
    print("✅ Team cache initialized")
