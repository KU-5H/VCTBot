# Script to grab all player names from the VLR API and save them into a dictionary.

import aiohttp
import time
import json
import os
import asyncio

CACHE_FILE = "player_cache.json"
CACHE_EXPIRY = 86400  # 24 hours in seconds

REGIONS = ['na', 'eu', 'ap', 'jp', 'br', 'oce', 'gc', 'la-s', 'la-n', 'oceania', 'mena']

async def fetchPlayersByRegion(session, region):
    url = f"http://localhost:5000/api/v1/players?timespan=all&limit=all&region={region}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("data", [])
            else:
                print(f"⚠️ Error fetching players for region {region}: Status {response.status}")
                return []
    except Exception as e:
        print(f"⚠️ Exception fetching players for region {region}: {str(e)}")
        return []


async def fetchPlayersByChunks(session):
    """Fetch players in chunks to handle API limitations"""
    url = f"http://localhost:5000/api/v1/players?limit=all"
    
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data.get("data", []), data.get("metadata", {}).get("total", 0)
    return [], 0

async def fetchAllPlayerNames():
    playerNameMappings = {}
    playersNameList = []
    fetched_player_ids = set()
    
    async with aiohttp.ClientSession() as session:
        region_tasks = [fetchPlayersByRegion(session, region) for region in REGIONS]
        all_region_results = await asyncio.gather(*region_tasks)
        
        for i, players in enumerate(all_region_results):
            region = REGIONS[i]
            print(f"Found {len(players)} players in region {region}")
            
            for player in players:
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