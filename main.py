# Imports #
from typing import Optional
import requests
import json
import discord
from discord.ext import commands
from discord import app_commands
from discord import Intents
from PIL import Image
import shutil
import datetime
from datetime import *
import os
from discord.ui import Button, button, View
from bsor.Bsor import *
import re
import io
from pp import blPpFromAcc
from scoresort import sort_scores
from profilecard import makecard

# Setup Stuff #
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents = intents)
token = "" #hidden token lol!!!!!
user_agent = "StatSaberBot/v3.4 (Contact me: dizzyjuneee@gmail.com, Discord: @dizzyjune)"

# Syncing Bot Commands #
@bot.event
async def on_ready():
  print("Bot is alive")
  try:
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Scores Get Set!"))
    await bot.tree.sync()
    print(f"Servers: {len(bot.guilds)}")
    for guild in bot.guilds:
        print(guild.name)
  except Exception as e:
    print(e)

# Get Profile Data #
class ProfileData:
    pass

def get_profile_data(id):
    headers = {
    "User-Agent": user_agent,
    }
    response = requests.get(url=f"https://api.beatleader.xyz/player/{id}", headers=headers)

    if response.status_code == 404:
        return None

    response_json = response.json()

    profile = ProfileData()
    profile.country = response_json.get("country", 'not set')
    profile.player_name = response_json.get("name", '')
    profile.pp = response_json.get("pp", 0)
    profile.rank = response_json.get("rank", 0)
    profile.top_pp = response_json.get("scoreStats", {}).get("topPp", 0)
    profile.accuracy = response_json.get("scoreStats", {}).get("averageAccuracy", 0)
    profile.country_rank = response_json.get('countryRank', 0)
    profile.score = response_json.get("scoreStats", {}).get("totalScore", 0)
    profile.avatar = response_json.get("avatar", '')
    profile.hmd = response_json.get("scoreStats", {}).get("topHMD", 0)
    profile.cover = response_json.get("profileSettings", {}).get("profileCover", "")
    profile.mapperId = response_json.get("mapperId", 0)

    return profile

# Get Scores #
class ScoreData:
    pass

def getscoredata(id, metric, order, search, num_scores):
    headers = {
    "User-Agent": user_agent,
    }
    response = requests.get(url=f"https://api.beatleader.xyz/player/{id}/scores?page=1&sortBy={metric}&order={order}&search={search}&count={num_scores}", headers=headers).json()
    scores = response["data"]

    if not scores:
        return []

    score_data_list = []
    for score in scores:
        leaderboard = score.get('leaderboard', {})
        song = leaderboard.get('song', {})
        difficulties = leaderboard.get('difficulty', [{}])

        score_data = ScoreData()
        score_data.song_name = song.get('name', '')
        score_data.song_cover = song.get('coverImage', '')
        score_data.pp = score.get('pp', 0)
        score_data.map_id = leaderboard.get('id', '')
        score_data.starrating = difficulties.get('stars', 0)
        score_data.status = difficulties.get('status', '')
        score_data.rank = score.get('rank', 0)
        score_data.timeset = score.get('timepost', '')
        score_data.accuracy = score.get('accuracy', 0)
        score_data.misses = score.get('missedNotes', 0)
        score_data.badcuts = score.get('badCuts', 0)
        score_data.bombcuts = score.get('bombCuts', 0)
        score_data.wallhits = score.get('wallsHit', 0)
        score_data.topcombo = score.get('maxCombo', 0)
        score_data.mods = score.get('modifiers', '')
        score_data.replayid = score.get('id', '')
        minutes, seconds = divmod(difficulties.get('duration', 0), 60)
        score_data.length = "%02d:%02d" % (minutes, seconds)
        score_data.score = '{:,}'.format(score.get('modifiedScore', 0))
        score_data.pauses = score.get('pauses', 0)
        score_data.notecount = difficulties.get('notes', 0)
        score_data.bombcount = difficulties.get('bombs', 0)
        score_data.wallcount = difficulties.get('walls', 0)
        score_data.nps = difficulties.get('nps', 0)
        diffname = difficulties.get('difficultyName', '')
        score_data.difficultyname = diffname.replace("Plus", "+")
        score_data.accfull = round(float(score.get('accuracy', 0)) * 100, 2)

        accfull = score_data.accfull
        rank_names = ["SSS", "SS", "S", "A", "B", "C", "D", "E"]
        rank_thresholds = [100.0, 90.0, 80.0, 65.0, 50.0, 35.0, 20.0, 0.0]
        score_data.accl = next((rank_names[i] for i, threshold in enumerate(rank_thresholds) if accfull >= threshold), 'E')
        if num_scores == 1:
            replay = score.get('replay', '')
            pausetime = ""
            if score_data.pauses > 0:
                pausetimeint = 0
                offset = score.get('offsets', {}).get('pauses', 0) - 1
                headers = {
                'Range': f'bytes={offset}-',
                "User-Agent": user_agent
                }
                b = requests.get(replay, headers=headers)
                bytestream = io.BytesIO(b.content)
                p = make_pauses(bytestream)
                try:
                    for p in p:
                        pausetimeint += p.duration
                    minutes, seconds = divmod(pausetimeint, 60)
                    pausetime = f" adding up to {minutes:02d}:{seconds:02d}"
                except BSException as e:
                    raise

            score_data.pausetime = pausetime
        score_data_list.append(score_data)

    return score_data_list

# Quick profile command #
@bot.tree.command(name="profile", description="Gets the Beatleader account linked to your Discord.")
@app_commands.describe(member = "Profile to send.")
async def discprofile(interaction: discord.Interaction, member: discord.Member):
    headers = {
    "User-Agent": user_agent,
    }
    statresponse = requests.get(url=f"https://api.beatleader.xyz/player/discord/{member.id}", headers=headers)
    if statresponse.status_code == 404:
        await interaction.response.send_message(f"No Beatleader account linked to this Discord! Try again after you have linked them at <https://www.beatleader.xyz/signin/socials>.")
    elif statresponse.status_code == 200:
        await interaction.response.defer()
        response = statresponse.json()
        id = response["id"]
        profile = get_profile_data(id)
        img_byte_array = await makecard(profile)
        class Buttons(discord.ui.View):
            def __init__(self, accid: int):
                super().__init__()
                self.add_item(discord.ui.Button(label="Profile", url = f"https://www.beatleader.xyz/u/{accid}"))
        try:
            await interaction.followup.send(f"Profile for **{profile.player_name}**", ephemeral = False, file=discord.File(img_byte_array, 'Card.png') , view=Buttons(accid = id))
        except Exception as e:
            print(e)
            await interaction.followup.send(f"An error has occured! Please try again.", ephemeral = False)
    else: 
        await interaction.response.send_message(f"Error code `{statresponse.status_code}`! Please try again.")

# Top Play command #
@bot.tree.command(name="top", description="Gets the top play using your Discord.")
@app_commands.describe(amount = "Amount of scores to show.")
async def top(interaction: discord.Interaction, amount: str=''):
 headers = {
    "User-Agent": user_agent,
 }
 statresponse = requests.get(url=f"https://api.beatleader.xyz/player/discord/{interaction.user.id}", headers=headers)
 if statresponse.status_code == 404:
     await interaction.response.send_message(f"No Beatleader account linked to this Discord! Try again after you have linked them at <https://www.beatleader.xyz/signin/socials>.")
 elif statresponse.status_code == 200:
    await interaction.response.defer()
    response = statresponse.json()
    id = response["id"]
    metric = "pp"
    order = "desc"
    scores = ""
    if amount == '':
        amount = "1"
    else:
        amount = amount
    if amount.isnumeric() == False:
        await interaction.followup.send("That is not a valid number! Please try again.", ephemeral = False)
    else:
        scoreamount = min(max(int(amount), 1), 10)
        score_data_list = getscoredata(id, metric, order, search = "", num_scores=scoreamount)
        if not score_data_list:
            await interaction.followup.send(f"No scores found! Please try again.", ephemeral=False)
        else:
            profile = get_profile_data(id)
            if int(amount) > 1:
                class Buttons(discord.ui.View):
                        def __init__(self, accid: int):
                            super().__init__()
                            self.add_item(discord.ui.Button(label="Profile", url = f"https://www.beatleader.xyz/u/{accid}"))
                file = discord.File(f'assets/flags/{str(profile.country).lower()}.png', filename=f"{profile.country}.png")
                for score in score_data_list:
                    pp = f" - **{round(score.pp, 2)}PP**" if score.status == 3 else ""
                    scores += f"**{score.song_name}** - **{score.difficultyname}** - **{score.accfull}%**{pp}\n"
                embed=discord.Embed(title=f'Top {amount} scores for **{profile.player_name}**', description=f'{scores}', color=0x8A4BBE)
                embed.set_author(name=f"{profile.player_name} - #{profile.rank} - {profile.pp}pp", url=f"https://www.beatleader.xyz/u/{id}", icon_url=f"attachment://{profile.country}.png")
                embed.set_thumbnail(url=profile.avatar)
                try:
                    await interaction.followup.send(f"Top plays for **{profile.player_name}**", ephemeral = False, embed=embed, file=file, view=Buttons(accid = id))
                except Exception as e:
                    print(e)
                    await interaction.followup.send(f"An error has occured! Please try again.", ephemeral = False)
            else:
                for score in score_data_list:
                    totalmistakes = int(score.misses) + int(score.bombcuts) + int(score.badcuts) + int(score.wallhits)
                    if score.status == 3:
                        roundedsr = round(score.starrating, 2)
                        soundedsr = float(roundedsr)
                        sr_display = f"{soundedsr}★"
                        ppdisplay = f"**{round(score.pp, 2)}PP** - "
                    elif score.status == 1:
                        sr_display = "Nominated"
                        ppdisplay = "\u200b"
                    elif score.status == 4:
                        sr_display = "Unrankable"
                        ppdisplay = "\u200b"
                    elif score.status == 0:
                        sr_display = "Unranked"
                        ppdisplay = "\u200b"
                    elif score.status == 2:
                        sr_display = "Qualified"
                        ppdisplay = "\u200b"
                    else:
                        sr_display = "Map Status Unknown"
                        ppdisplay = "\u200b"
                    if totalmistakes == 0:
                        mistakesdisplay = "Full Combo!"
                    else:
                        mistakesdisplay = f"{totalmistakes} Mistakes"
                    if score.mods == "":
                        newmods = ""
                    else:
                        newmods = f' +{score.mods.replace(",", "")}'
                    class Buttons(discord.ui.View):
                        def __init__(self, replayid: int, accid: int, lb: int):
                            super().__init__()
                            self.add_item(discord.ui.Button(label="Replay", url = f"https://replay.beatleader.xyz/?scoreId={replayid}"))
                            self.add_item(discord.ui.Button(label="Profile", url = f"https://www.beatleader.xyz/u/{accid}"))
                            self.add_item(discord.ui.Button(label="Leaderboard", url = f"https://www.beatleader.xyz/leaderboard/global/{lb}/"))
                    pausetext = "Pause" if score.pauses == 1 else "Pauses"
                    if score.pauses > 0:
                        pausetime = f"{score.pausetime}"
                    else:
                        pausetime = ""
                    embed=discord.Embed(title=f'{score.song_name} - {score.difficultyname} - {sr_display}{newmods}', description=f"**{score.score}** - {ppdisplay}**{score.accfull}%** - **#{score.rank}**\n**{mistakesdisplay}** - **Top Combo | {score.topcombo}**\n**{score.length}** - **{score.pauses} {pausetext}{pausetime}** - **{round(score.nps, 2)}NPS**\n**{score.notecount} Notes** - **{score.bombcount} Bombs** - **{score.wallcount} Walls**", color=0x8A4BBE)
                    embed.set_author(name=f"{profile.player_name} - #{profile.rank} - {profile.pp}pp", url=f"https://www.beatleader.xyz/u/{id}", icon_url=f"attachment://{profile.country}.png")
                    embed.set_thumbnail(url=score.song_cover)
                    embed.set_footer(text=f"Set on")
                    embed.timestamp = datetime.fromtimestamp(int(score.timeset))
                    file = discord.File(f'assets/flags/{str(profile.country).lower()}.png', filename=f"{profile.country}.png")
                    try:
                        await interaction.followup.send(f"Top play for **{profile.player_name}**", ephemeral = False, embed=embed, file=file, view=Buttons(score.replayid, accid = id, lb = score.map_id))
                    except Exception as e:
                        print(e)
                        await interaction.followup.send(f"An error has occured! Please try again.", ephemeral = False)
 else:
     await interaction.response.send_message(f"Error code `{statresponse.status_code}`! Please try again.")

# Recent Play command #
@bot.tree.command(name="recent", description="Gets the most recent play using your Discord.")
@app_commands.describe(amount = "Amount of scores to show.")
async def recent(interaction: discord.Interaction, amount: str=''):
 headers = {
    "User-Agent": user_agent,
 }
 statresponse = requests.get(url=f"https://api.beatleader.xyz/player/discord/{interaction.user.id}", headers=headers)
 if statresponse.status_code == 404:
     await interaction.response.send_message(f"No Beatleader account linked to this Discord! Try again after you have linked them at <https://www.beatleader.xyz/signin/socials>.")
 elif statresponse.status_code == 200:
    await interaction.response.defer()
    response = statresponse.json()
    id = response["id"]
    metric = "date"
    order = "desc"
    scores = ""
    if amount == '':
        amount = "1"
    else:
        amount = amount
    if amount.isnumeric() == False:
        await interaction.followup.send("That is not a valid number! Please try again.", ephemeral = False)
    else:
        scoreamount = min(max(int(amount), 1), 10)
        score_data_list = getscoredata(id, metric, order, search = "", num_scores=scoreamount)
        if not score_data_list:
            await interaction.followup.send(f"No scores found! Please try again.", ephemeral=False)
        else:
            profile = get_profile_data(id)
            if int(amount) > 1:
                class Buttons(discord.ui.View):
                        def __init__(self, accid: int):
                            super().__init__()
                            self.add_item(discord.ui.Button(label="Profile", url = f"https://www.beatleader.xyz/u/{accid}"))
                file = discord.File(f'assets/flags/{str(profile.country).lower()}.png', filename=f"{profile.country}.png")
                for score in score_data_list:
                    pp = f" - **{round(score.pp, 2)}PP**" if score.status == 3 else ""
                    scores += f"**{score.song_name}** - **{score.difficultyname}** - **{score.accfull}%**{pp}\n"
                embed=discord.Embed(title=f'{amount} most recent plays for **{profile.player_name}**', description=f'{scores}', color=0x8A4BBE)
                embed.set_author(name=f"{profile.player_name} - #{profile.rank} - {profile.pp}pp", url=f"https://www.beatleader.xyz/u/{id}", icon_url=f"attachment://{profile.country}.png")
                embed.set_thumbnail(url=profile.avatar)
                try:
                    await interaction.followup.send(f"Most recent plays for **{profile.player_name}**", ephemeral = False, embed=embed, file=file, view=Buttons(accid = id))
                except Exception as e:
                    print(e)
                    await interaction.followup.send(f"An error has occured! Please try again.", ephemeral = False)
            else:
                for score in score_data_list:
                    totalmistakes = int(score.misses) + int(score.bombcuts) + int(score.badcuts) + int(score.wallhits)
                    if score.status == 3:
                        roundedsr = round(score.starrating, 2)
                        soundedsr = float(roundedsr)
                        sr_display = f"{soundedsr}★"
                        ppdisplay = f"**{round(score.pp, 2)}PP** - "
                    elif score.status == 1:
                        sr_display = "Nominated"
                        ppdisplay = "\u200b"
                    elif score.status == 4:
                        sr_display = "Unrankable"
                        ppdisplay = "\u200b"
                    elif score.status == 0:
                        sr_display = "Unranked"
                        ppdisplay = "\u200b"
                    elif score.status == 2:
                        sr_display = "Qualified"
                        ppdisplay = "\u200b"
                    else:
                        sr_display = "Map Status Unknown"
                        ppdisplay = "\u200b"
                    if totalmistakes == 0:
                        mistakesdisplay = "Full Combo!"
                    else:
                        mistakesdisplay = f"{totalmistakes} Mistakes"
                    if score.mods == "":
                        newmods = ""
                    else:
                        newmods = f' +{score.mods.replace(",", "")}'
                    class Buttons(discord.ui.View):
                        def __init__(self, replayid: int, accid: int, lb: int):
                            super().__init__()
                            self.add_item(discord.ui.Button(label="Replay", url = f"https://replay.beatleader.xyz/?scoreId={replayid}"))
                            self.add_item(discord.ui.Button(label="Profile", url = f"https://www.beatleader.xyz/u/{accid}"))
                            self.add_item(discord.ui.Button(label="Leaderboard", url = f"https://www.beatleader.xyz/leaderboard/global/{lb}/"))
                    pausetext = "Pause" if score.pauses == 1 else "Pauses"
                    if score.pauses > 0:
                        pausetime = f"{score.pausetime}"
                    else:
                        pausetime = ""
                    embed=discord.Embed(title=f'{score.song_name} - {score.difficultyname} - {sr_display}{newmods}', description=f"**{score.score}** - {ppdisplay}**{score.accfull}%** - **#{score.rank}**\n**{mistakesdisplay}** - **Top Combo | {score.topcombo}**\n**{score.length}** - **{score.pauses} {pausetext}{pausetime}** - **{round(score.nps, 2)}NPS**\n**{score.notecount} Notes** - **{score.bombcount} Bombs** - **{score.wallcount} Walls**", color=0x8A4BBE)
                    embed.set_author(name=f"{profile.player_name} - #{profile.rank} - {profile.pp}pp", url=f"https://www.beatleader.xyz/u/{id}", icon_url=f"attachment://{profile.country}.png")
                    embed.set_thumbnail(url=score.song_cover)
                    embed.set_footer(text=f"Set on")
                    embed.timestamp = datetime.fromtimestamp(int(score.timeset))
                    file = discord.File(f'assets/flags/{str(profile.country).lower()}.png', filename=f"{profile.country}.png")
                    try:
                        await interaction.followup.send(f"Most recent play for **{profile.player_name}**", ephemeral = False, embed=embed, file=file, view=Buttons(score.replayid, accid = id, lb = score.map_id))
                    except Exception as e:
                        print(e)
                        await interaction.followup.send(f"An error has occured! Please try again.", ephemeral = False)
 else:
     await interaction.response.send_message(f"Error code `{statresponse.status_code}`! Please try again.")

# Search Plays command #
@bot.tree.command(name="search", description="Search for a play from a player")
@app_commands.describe(sort = "Change sorting option.")
@app_commands.describe(direction = "Change sorting direction, Descending is the default")
@app_commands.describe(search = "Search by score name.")
@app_commands.describe(amount = "Amount of scores to show.")
@app_commands.choices(sort=[
    discord.app_commands.Choice(name='PP', value="pp"),
    discord.app_commands.Choice(name='Date', value="date"),
    discord.app_commands.Choice(name='Accuracy', value="acc"),
    discord.app_commands.Choice(name='Rank', value="rank"),
    discord.app_commands.Choice(name='Stars', value="stars"),
    discord.app_commands.Choice(name='Pauses', value="pauses"),
    discord.app_commands.Choice(name='115 Streak', value="maxStreak"),
    #discord.app_commands.Choice(name='Combo [DEPRECATED]', value="maxCombo"),
    #discord.app_commands.Choice(name='Length', value="length")
])
@app_commands.choices(direction=[
    discord.app_commands.Choice(name='Ascending', value="asc"),
    discord.app_commands.Choice(name='Descending', value="desc")
])
async def search(interaction: discord.Interaction, sort: discord.app_commands.Choice[str], direction: discord.app_commands.Choice[str], search: str='', amount: str=''):
 headers = {
    "User-Agent": user_agent,
 }
 statresponse = requests.get(url=f"https://api.beatleader.xyz/player/discord/{interaction.user.id}", headers=headers)
 if statresponse.status_code == 404:
     await interaction.response.send_message(f"No Beatleader account linked to this Discord! Try again after you have linked them at <https://www.beatleader.xyz/signin/socials>.")
 elif statresponse.status_code == 200:
    await interaction.response.defer()
    response = requests.get(url=f"https://api.beatleader.xyz/player/discord/{interaction.user.id}", headers=headers).json()
    id = response["id"]
    metric = sort.value
    order = direction.value
    scores = ""
    if amount == '':
        amount = "1"
    else:
        amount = amount
    if amount.isnumeric() == False:
        await interaction.followup.send("That is not a valid number! Please try again.", ephemeral = False)
    else:
        scoreamount = min(max(int(amount), 1), 10)
        score_data_list = getscoredata(id, metric, order, search = "", num_scores=scoreamount)
        if not score_data_list:
            await interaction.followup.send(f"No scores found! Please try again.", ephemeral=False)
        else:
            score_data_list = score_data_list[:int(scoreamount)]
            profile = get_profile_data(id)
            if int(amount) > 1:
                class Buttons(discord.ui.View):
                        def __init__(self, accid: int):
                            super().__init__()
                            self.add_item(discord.ui.Button(label="Profile", url = f"https://www.beatleader.xyz/u/{accid}"))
                file = discord.File(f'assets/flags/{str(profile.country).lower()}.png', filename=f"{profile.country}.png")
                for score in score_data_list:
                    pp = f" - **{round(score.pp, 2)}PP**" if score.status == 3 else ""
                    scores += f"**{score.song_name}** - **{score.difficultyname}** - **{score.accfull}%**{pp}\n"
                embed=discord.Embed(title=f'Top {amount} scores for **{profile.player_name}**', description=f'{scores}', color=0x8A4BBE)
                embed.set_author(name=f"{profile.player_name} - #{profile.rank} - {profile.pp}pp", url=f"https://www.beatleader.xyz/u/{id}", icon_url=f"attachment://{profile.country}.png")
                embed.set_thumbnail(url=profile.avatar)
                try:
                    await interaction.followup.send(f"Top plays for **{profile.player_name}**", ephemeral = False, embed=embed, file=file, view=Buttons(accid = id))
                except Exception as e:
                    print(e)
                    await interaction.followup.send(f"An error has occured! Please try again.", ephemeral = False)
            else:
                for score in score_data_list:
                    totalmistakes = int(score.misses) + int(score.bombcuts) + int(score.badcuts) + int(score.wallhits)
                    if score.status == 3:
                        roundedsr = round(score.starrating, 2)
                        soundedsr = float(roundedsr)
                        sr_display = f"{soundedsr}★"
                        ppdisplay = f"**{round(score.pp, 2)}PP** - "
                    elif score.status == 1:
                        sr_display = "Nominated"
                        ppdisplay = "\u200b"
                    elif score.status == 4:
                        sr_display = "Unrankable"
                        ppdisplay = "\u200b"
                    elif score.status == 0:
                        sr_display = "Unranked"
                        ppdisplay = "\u200b"
                    elif score.status == 2:
                        sr_display = "Qualified"
                        ppdisplay = "\u200b"
                    else:
                        sr_display = "Map Status Unknown"
                        ppdisplay = "\u200b"
                    if totalmistakes == 0:
                        mistakesdisplay = "Full Combo!"
                    else:
                        mistakesdisplay = f"{totalmistakes} Mistakes"
                    if score.mods == "":
                        newmods = ""
                    else:
                        newmods = f' +{score.mods.replace(",", "")}'
                    class Buttons(discord.ui.View):
                        def __init__(self, replayid: int, accid: int, lb: int):
                            super().__init__()
                            self.add_item(discord.ui.Button(label="Replay", url = f"https://replay.beatleader.xyz/?scoreId={replayid}"))
                            self.add_item(discord.ui.Button(label="Profile", url = f"https://www.beatleader.xyz/u/{accid}"))
                            self.add_item(discord.ui.Button(label="Leaderboard", url = f"https://www.beatleader.xyz/leaderboard/global/{lb}/"))
                    pausetext = "Pause" if score.pauses == 1 else "Pauses"
                    if score.pauses > 0:
                        pausetime = f"{score.pausetime}"
                    else:
                        pausetime = ""
                    embed=discord.Embed(title=f'{score.song_name} - {score.difficultyname} - {sr_display}{newmods}', description=f"**{score.score}** - {ppdisplay}**{score.accfull}%** - **#{score.rank}**\n**{mistakesdisplay}** - **Top Combo | {score.topcombo}**\n**{score.length}** - **{score.pauses} {pausetext}{pausetime}** - **{round(score.nps, 2)}NPS**\n**{score.notecount} Notes** - **{score.bombcount} Bombs** - **{score.wallcount} Walls**", color=0x8A4BBE)
                    embed.set_author(name=f"{profile.player_name} - #{profile.rank} - {profile.pp}pp", url=f"https://www.beatleader.xyz/u/{id}", icon_url=f"attachment://{profile.country}.png")
                    embed.set_thumbnail(url=score.song_cover)
                    embed.set_footer(text=f"Set on")
                    embed.timestamp = datetime.fromtimestamp(int(score.timeset))
                    file = discord.File(f'assets/flags/{str(profile.country).lower()}.png', filename=f"{profile.country}.png")
                    try:
                        await interaction.followup.send(f"", ephemeral = False, embed=embed, file=file, view=Buttons(score.replayid, accid = id, lb = score.map_id))
                    except Exception as e:
                        print(e)
                        await interaction.followup.send(f"An error has occured! Please try again.", ephemeral = False)
 else:
     await interaction.response.send_message(f"Error code `{statresponse.status_code}`! Please try again.")

# Map Command #
@bot.tree.command(name="map", description="Shows various information about a map.")
@app_commands.describe(key = "Enter map key.")
async def map(interaction: discord.Interaction, key: str):
    headers = {
    "User-Agent": user_agent,
    }
    await interaction.response.defer()
    mapresponse = requests.get(url=f"https://api.beatleader.xyz/leaderboard/{key}", headers=headers)
    if mapresponse.status_code == 404:
        await interaction.followup.send("No map found, the map key is likely incorrect.")
    elif mapresponse.status_code == 200:
        mapjson = mapresponse.json()
        song = mapjson.get("song", {})
        difficulties = song.get("difficulties", [{}])[0]
        bsid = song.get("id", "")[:-len(mapjson.get("leaderboardGroup", "")) + 1]
        name = song.get("name", "")
        subName = song.get("subName", "")
        author = song.get("author", "")
        coverImage = song.get("coverImage", "")
        downloadUrl = song.get("downloadUrl", "")
        stars = difficulties.get("stars", 0)
        status = difficulties.get("status", "")
        difficulty = difficulties.get("difficultyName", "")
        notes = difficulties.get("notes", 0)
        bombs = difficulties.get("bombs", 0)
        walls = difficulties.get("walls", 0)
        ratings = {
            'passRating': difficulties.get("passRating", 0),
            'accRating': difficulties.get("accRating", 0),
            'techRating': difficulties.get("techRating", 0)
        }
        minutes, seconds = divmod(difficulties.get("duration", 0), 60)
        duration = "%02d:%02d" % (minutes, seconds)
        njs = difficulties.get("njs", 0)
        nps = difficulties.get("nps", 0)
        bpm = song.get("bpm", 0)
        beatsaver = requests.get(url=f"https://beatsaver.com/api/maps/id/{bsid}", headers=headers).json()
        createdAt = beatsaver.get("createdAt", "")
        mapper = beatsaver.get("uploader", {}).get("name", "")
        mapperid = beatsaver.get("uploader", {}).get("id", "")
        mapperavatar = beatsaver.get("uploader", {}).get("avatar", "")
        if status == 3:
            sr = f"{float(round(stars, 2))}★"
            ppcalc = f"```\n97% | {round(blPpFromAcc(0.97, ratings), 2)}PP\n95% | {round(blPpFromAcc(0.95, ratings), 2)}PP\n92% | {round(blPpFromAcc(0.92, ratings), 2)}PP\n90% | {round(blPpFromAcc(0.90, ratings), 2)}PP\n```"
        elif status == 1:
            sr = "Nominated"
            ppcalc = ""
        elif status == 2:
            sr = "Qualified"
            ppcalc = ""
        elif status == 4:
            sr = "Unrankable"
            ppcalc = ""
        elif status == 0:
            sr = "Unranked"
            ppcalc = ""
        else:
            sr = "Map Status Unknown"
            ppcalc = ""
        
        embed=discord.Embed(title=f"{name} {subName} - {difficulty.replace('Plus', '+')} - {sr}", description=f"**{duration}** - **{round(nps, 2)}NPS** - **{bpm}BPM**\n**{notes} Notes** - **{bombs} Bombs** - **{walls} Walls**\n{ppcalc}", color=0x8A4BBE)
        embed.set_author(name=f"Mapped by {mapper}", url=f"https://beatsaver.com/profile/{mapperid}", icon_url=mapperavatar)
        embed.set_thumbnail(url=coverImage)
        if createdAt == "":
            embed.set_footer(text=f"Uploaded time unknown or failed!")
        else:
            embed.set_footer(text=f"Uploaded")
            datetime_obj = datetime.fromisoformat(createdAt.replace("Z", "+00:00"))
            unix_timestamp = datetime_obj.timestamp()
            embed.timestamp = datetime.fromtimestamp(int(unix_timestamp))
        class Buttons(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(discord.ui.Button(label="BeatSaver", url = f"https://beatsaver.com/maps/{bsid}"))
                self.add_item(discord.ui.Button(label="Download", url = downloadUrl))
                self.add_item(discord.ui.Button(label="Leaderboard", url = f"https://www.beatleader.xyz/leaderboard/global/{key}"))
        try:
            await interaction.followup.send(f"", ephemeral = False, embed=embed, view=Buttons())
        except Exception as e:
            await interaction.followup.send(f"Error occured! {e}")
    else:
        await interaction.response.send_message(f"Error code `{mapresponse.status_code}`! Please try again.")

# Running the bot #
bot.run(token)