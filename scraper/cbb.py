import csv
import datetime
import re
import requests
import sys
import time
import typer
from bs4 import BeautifulSoup
from typing import Dict, List

app = typer.Typer()


def get_team_urls(year: str) -> List[str]:
    years_to_id = {
        "2023": "16060",
    }
    team_urls = []
    teams = []
    with open("teams.csv") as f:
        reader = csv.DictReader(f)
        for team in reader:
            teams.append(team)
    for team in teams:
        team_urls.append((team["name"], f"https://stats.ncaa.org/player/game_by_game?game_sport_year_ctl_id={years_to_id[year]}&org_id={team['id']}&stats_player_seq=-100"))
    return team_urls


def get_team_page(url: str) -> str:
    header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0'}
    response = requests.get(url, headers=header)
    return response.text


def format_stat(stat: str) -> str:
    stat = stat.strip()
    if len(stat) == 0:
        return "0"
    if stat.endswith("/"):
        stat = stat[:-1]
    if stat.endswith("*"):
        stat = stat[:-1]
    return stat


def parse_team_page(page: str) -> List[Dict]:
    page = BeautifulSoup(page, "html.parser")
    team = page.find("div", id="contentarea").table.tr.td.table.find_all("tr")[2].find_all("td")[1].a.get_text().strip()
    games = []
    for game in page.find("div", id="contentarea").find("div", id="game_breakdown_div").table.tr.td.table.find_all("tr"):
        stats = [format_stat(x.get_text()) for x in game.find_all("td")]
        if len(stats) > 3 and stats[2] != "-":
            if stats[1] == "Defensive Totals":
                games[-1].update({
                    "opp_field_goals_made": stats[5],
                    "opp_field_goals_attempted": stats[6],
                    "opp_3_point_field_goals_made": stats[7],
                    "opp_3_point_field_goals_attempted": stats[8],
                    "opp_free_throws_made": stats[9],
                    "opp_free_throws_attempted": stats[10],
                    "opp_offensive_rebounds": stats[12],
                    "opp_defensive_rebounds": stats[13],
                    "opp_rebounds": stats[14],
                    "opp_assists": stats[15],
                    "opp_turnovers": stats[16],
                    "opp_steals": stats[17],
                    "opp_blocks": stats[18],
                    "opp_fouls": stats[19],
                    "opp_disqualifications": stats[20],
                    "opp_technical_fouls": stats[21],
                })
            else:
                opponent = stats[1]
                location = "home"
                if opponent.startswith("@"):
                    opponent = opponent[2:]
                    location = "away"
                elif "@" in opponent:
                    opponent = opponent.split(" @ ")[0]
                    location = "neutral"
                points = int(stats[2].split("-")[0])
                opp_points = int(stats[2].split("-")[1].split(" ")[0])
                overtimes = stats[2].split(" ")[1][1:-1] if len(stats[2].split(" ")) > 1 else "0"
                games.append({
                    "date": stats[0],
                    "team": team,
                    "opponent": opponent,
                    "location": location,
                    "result": "W" if points > opp_points else "L",
                    "overtimes": overtimes,
                    "points": str(points),
                    "opp_points": str(opp_points),
                    "field_goals_made": stats[5],
                    "field_goals_attempted": stats[6],
                    "3_point_field_goals_made": stats[7],
                    "3_point_field_goals_attempted": stats[8],
                    "free_throws_made": stats[9],
                    "free_throws_attempted": stats[10],
                    "offensive_rebounds": stats[12],
                    "defensive_rebounds": stats[13],
                    "rebounds": stats[14],
                    "assists": stats[15],
                    "turnovers": stats[16],
                    "steals": stats[17],
                    "blocks": stats[18],
                    "fouls": stats[19],
                    "disqualifications": stats[20],
                    "technical_fouls": stats[21],
                })
    return games


def output_csv(games: List[Dict]):
    games_headers = list(games[0].keys())
    games_values = [list(game.values()) for game in games]
    writer = csv.writer(sys.stdout)
    writer.writerow(games_headers)
    writer.writerows(games_values)


@app.command()
def fetch(year: str = None, debug: bool = False):
    if not year:
        year = str(datetime.date.today().year)

    starttime = time.time()
    games = []
    for team, team_url in get_team_urls(year):
        if debug:
            print(f"Fetching {team} from {team_url}", file=sys.stderr)
        team_page = get_team_page(team_url)
        games.extend(parse_team_page(team_page))

    if debug:
        print(f"Total elapsed time: {time.time() - starttime}", file=sys.stderr)

    output_csv(games)

if __name__ == "__main__":
    app()