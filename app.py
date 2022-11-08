from flask import Flask
from nba_api.stats.endpoints import boxscoretraditionalv2
from nba_api.live.nba.endpoints import scoreboard

import json

app = Flask(__name__)

@app.route("/")
def hello_world():
    # Today's Score Board
    games = scoreboard.ScoreBoard();

    # json
    json_object = json.loads(games.get_json())
    games = json_object["scoreboard"]["games"]
    data = json_object["scoreboard"]["gameDate"]

    playersstats = []
    headers = []
    for game in games:
        stats = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id = game["gameId"], start_period = 1, end_period = 4)
        json_object = json.loads(stats.get_json())
        for rowset in  json_object["resultSets"]:
            if rowset["name"] == "PlayerStats":
                # print(json.dumps(rowset, indent=4))
                headers = rowset["headers"];
                players = rowset["rowSet"];
                for player in players:
                    if player[10] is not None:
                        playersstats.append(player)

    response = {
        'gameDate' : data,
        'headers' : headers,
        'rowSet' : playersstats

    }
    return response

