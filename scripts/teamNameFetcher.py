# Script to grab all team names from the VLR API and save them into a dictionary.

import asyncio
import aiohttp
import time
import json
import os

CACHE_DIR = os.getenv("CACHE_DIR", ".")
CACHE_FILE = os.path.join(CACHE_DIR, "team_cache.json")
CACHE_EXPIRY = 86400  # 24 hours in seconds

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")

REGIONS = ['na', 'eu', 'ap', 'jp', 'br', 'oce', 'gc', 'la-s', 'la-n', 'oceania', 'mena']

async def fetchTeamsByRegion(session, region):
    url = f"{API_BASE_URL}/api/v1/teams?limit=all&region={region}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("data", [])
            else:
                print(f"⚠️ Error fetching teams for region {region}: Status {response.status}")
                return []
    except Exception as e:
        print(f"⚠️ Exception fetching teams for region {region}: {str(e)}")
        return []

async def fetchAllTeamNames():

    teamNameMappings = {}
    teamsNameList = []
    seen_team_ids = set()

    async with aiohttp.ClientSession() as session:
        region_tasks = [fetchTeamsByRegion(session, region) for region in REGIONS]
        all_region_results = await asyncio.gather(*region_tasks)

        for i, teams in enumerate(all_region_results):
            region = REGIONS[i]
            print(f"Found {len(teams)} teams in region {region}")
            
            for team in teams:
                team_id = team.get("id")
                team_name = team.get("name")
                
                # Only add if we haven't seen this team ID before
                if team_id and team_name and team_id not in seen_team_ids:
                    teamNameMappings[team_name.lower()] = team_id
                    teamsNameList.append({"name": team_name, "id": team_id})
                    seen_team_ids.add(team_id)
        
        try:
            url = f"{API_BASE_URL}/api/v1/teams?limit=all"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    main_teams = data.get("data", [])
                    
                    for team in main_teams:
                        team_id = team.get("id")
                        team_name = team.get("name")
                        
                        if team_id and team_name and team_id not in seen_team_ids:
                            teamNameMappings[team_name.lower()] = team_id
                            teamsNameList.append({"name": team_name, "id": team_id})
                            seen_team_ids.add(team_id)
        except Exception as e:
            print(f"⚠️ Error fetching teams from main endpoint: {str(e)}")
        
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
