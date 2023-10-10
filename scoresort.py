import requests
import aiohttp
import asyncio
from datetime import timedelta

async def get_scores(api_url):
    all_scores = []
    page = 1
    total_scores = 0

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url + f"&page={page}") as first_response:
            if first_response.status == 200:
                first_data = await first_response.json()
                total_scores = first_data["metadata"]["total"]
                all_scores.extend(first_data["data"])
            else:
                print(f"Error fetching data from page {page}. Status code: {first_response.status}")
                return []

        while len(all_scores) < total_scores:
            page += 1
            async with session.get(api_url + f"?page={page}") as response:
                if response.status == 200:
                    data = await response.json()
                    scores = data["data"]
                    all_scores.extend(scores)
                else:
                    print(f"Error fetching data from page {page}. Status code: {response.status}")
                    print(await response.text())
                    break

    return all_scores

def sort_by_max_combo(scores, order):
    sorted_by_max_combo = sorted(scores, key=lambda x: x["maxCombo"], reverse=order)
    return sorted_by_max_combo

def get_map_length(score):
    duration_seconds = score["leaderboard"]["song"]["duration"]
    duration_formatted = convert_seconds_to_hh_mm_ss(duration_seconds)
    return duration_seconds, duration_formatted

def convert_seconds_to_hh_mm_ss(seconds):
    duration = timedelta(seconds=seconds)
    return str(duration)

async def sort_scores(metric, player_id, sort, search):
    if search != "":
        search = search
    else:
        search = ""
        
    api_base_url = "https://api.beatleader.xyz/player"
    api_url = f"{api_base_url}/{player_id}/scores?search={search}"

    async with aiohttp.ClientSession() as session:
        all_scores = await get_scores(api_url)

        if all_scores:
            if sort == "asc":
                order = False
            elif sort == "desc":
                order = True
            if metric == "maxCombo":
                score_data_list = sort_by_max_combo(all_scores, order)
                return score_data_list
            elif metric == "length":
                sorted_data_list = sorted(all_scores, key=get_map_length, reverse=order)
                return sorted_data_list
        else:
            print("No scores found for the specified player.")