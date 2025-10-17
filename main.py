from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nba_api.stats.endpoints import playercareerstats
from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import players
from nba_api.stats.endpoints import boxscoretraditionalv2, franchiseplayers, commonallplayers, commonplayerinfo
from datetime import date, datetime
from nba_api.stats.endpoints import scheduleleaguev2
from nba_api.stats.library.http import NBAStatsHTTP
from nba_api.stats.static import players, teams
import time, json


# Aumentar timeout
NBAStatsHTTP.timeout = 60

# Adicionar headers que a NBA espera
NBAStatsHTTP.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
}

app = FastAPI(title="Minha API NBA")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # ou ["*"] para liberar geral
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API da NBA funcionando 🚀 2.0"}

@app.get("/common_all_players")
def get_all_players():
    all_players = commonallplayers.CommonAllPlayers(is_only_current_season=1).get_json()
    
    # Converte o texto JSON em dicionário Python
    data = json.loads(all_players)
    
    # Agora você pode acessar as partes
    players = data['resultSets'][0]['rowSet']
    headers = data['resultSets'][0]['headers']

    # Se quiser transformar em lista de dicionários (mais legível):
    players_list = [dict(zip(headers, row)) for row in players]

    return players_list

@app.get("/players")
def get_players():
    active_players = players.get_active_players()
    return active_players;


@app.get("/franchise_players/{team_id}")
def get_team_players(team_id: int):
    team_players = franchiseplayers.FranchisePlayers(team_id=team_id)
    return team_players.get_dict()

@app.get("/teams")
def get_teams():
    all_teams = teams.get_teams()
    return all_teams


@app.get("/players/{player_id}")
def get_player_stats(player_id: str):
    player_info  = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
    
    # Extrair os resultSets
    result_sets = {item["name"]: item for item in player_info["resultSets"]}

    # Extrair dados do jogador (CommonPlayerInfo)
    player_data = dict(zip(
        result_sets["CommonPlayerInfo"]["headers"],
        result_sets["CommonPlayerInfo"]["rowSet"][0]
    ))

    # Extrair estatísticas (PlayerHeadlineStats)
    stats_data = dict(zip(
        result_sets["PlayerHeadlineStats"]["headers"],
        result_sets["PlayerHeadlineStats"]["rowSet"][0]
    )) if result_sets["PlayerHeadlineStats"]["rowSet"] else None

    # Extrair temporadas disponíveis
    available_seasons = [
        season[0] for season in result_sets["AvailableSeasons"]["rowSet"]
    ]

    # Montar o JSON final
    return {
        "id": player_data["PERSON_ID"],
        "name": player_data["DISPLAY_FIRST_LAST"],
        "team": {
            "id": player_data["TEAM_ID"],
            "name": player_data["TEAM_NAME"],
            "abbreviation": player_data["TEAM_ABBREVIATION"],
            "city": player_data["TEAM_CITY"],
        },
        "bio": {
            "first_name": player_data["FIRST_NAME"],
            "last_name": player_data["LAST_NAME"],
            "birthdate": player_data["BIRTHDATE"],
            "school": player_data["SCHOOL"],
            "country": player_data["COUNTRY"],
            "height": player_data["HEIGHT"],
            "weight": player_data["WEIGHT"],
            "position": player_data["POSITION"],
            "jersey": player_data["JERSEY"],
            "experience": player_data["SEASON_EXP"],
        },
        "stats": {
            "season": stats_data["TimeFrame"] if stats_data else None,
            "points": stats_data["PTS"] if stats_data else None,
            "assists": stats_data["AST"] if stats_data else None,
            "rebounds": stats_data["REB"] if stats_data else None,
            "pie": stats_data["PIE"] if stats_data else None,
        },
        "available_seasons": available_seasons,
    }

@app.get("/scoreboard")
def get_scoreboard():
    sb = scoreboard.ScoreBoard()
    return sb.get_dict()
 

@app.get("/boxscore/{game_id}")
def get_boxscore(game_id: str):
    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    return boxscore.get_dict();

def convert_date_format(d: str) -> str:
    """
    Converte YYYY-MM-DD -> MM/DD/YYYY para stats.ScoreboardV2
    """
    dt = datetime.strptime(d, "%Y-%m-%d")
    return dt.strftime("%m/%d/%Y")


@app.get("/games/")
@app.get("/games/{game_date}")
def get_games(game_date: str | None = None):
    """
    Retorna:
    - gameId
    - status
    - todos os jogadores (home + away) em um único array
      com o campo teamTricode
    """
    lista = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nba.com/'
    }

    try:
        if game_date is None:
            # Jogos de hoje - live API
            sb = scoreboard.ScoreBoard(headers=headers)
            games = sb.games.get_dict()

            for g in games:
                game_id = g["gameId"]
                status = g["gameStatusText"]

                try:
                    bs = boxscore.BoxScore(game_id=game_id, headers=headers).game.get_dict()

                    home_team = bs["homeTeam"]
                    away_team = bs["awayTeam"]

                    home_players = [
                        {**p, "teamTricode": home_team["teamTricode"]}
                        for p in home_team.get("players", [])
                    ]
                    away_players = [
                        {**p, "teamTricode": away_team["teamTricode"]}
                        for p in away_team.get("players", [])
                    ]

                    players = home_players + away_players
                except Exception as e:
                    print(f"Erro ao buscar boxscore do jogo {game_id}: {e}")
                    players = []

                lista.append({
                    "gameId": game_id,
                    "status": status,
                    "players": players,
                })

                time.sleep(0.5)

        else:
            # Jogos de uma data específica - stats API
            formatted_date = convert_date_format(game_date)
            sb = scoreboardv2.ScoreboardV2(game_date=formatted_date, headers=headers)
            df = sb.get_data_frames()[0]

            for _, row in df.iterrows():
                game_id = row["GAME_ID"]
                status = row.get("GAME_STATUS_TEXT", row.get("LIVE_PERIOD", ""))

                try:
                    bs = boxscoretraditionalv2.BoxScoreTraditionalV2(
                        game_id=game_id, 
                        headers=headers
                    ).get_dict()

                    player_data = next(
                        (r for r in bs["resultSets"] if r["name"] == "PlayerStats"),
                        None
                    )
                    players = []
                    if player_data:
                        headers_list = player_data["headers"]
                        for row_set in player_data["rowSet"]:
                            player = dict(zip(headers_list, row_set))
                            # adiciona o teamTricode (TIME_ABBREVIATION na resposta da API)
                            player["teamTricode"] = player.get("TEAM_ABBREVIATION")
                            players.append(normalize_player(player))
                except Exception as e:
                    print(f"Erro ao buscar boxscore do jogo {game_id}: {e}")
                    players = []

                lista.append({
                    "gameId": game_id,
                    "status": status,
                    "players": players,
                })

                time.sleep(0.5)

        return lista

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogos: {str(e)}")


@app.get("/schedule/")
def get_schedule():
    """
    Retorna o calendário completo da temporada atual.
    """
    # Chama o endpoint ScheduleLeagueV2
    schedule = scheduleleaguev2.ScheduleLeagueV2()

    # Extrai os dados dos jogos
    games = schedule.get_dict()["leagueSchedule"]

    return {"games": games}

def normalize_player(player: dict) -> dict:
    """
    Converte o formato da API stats (caixa alta) para o formato usado pela live API.
    """
    return {
        "personId": player.get("PLAYER_ID"),
        "firstName": player.get("PLAYER_NAME", "").split(" ")[0],
        "familyName": " ".join(player.get("PLAYER_NAME", "").split(" ")[1:]),
        "jerseyNum": player.get("START_POSITION", ""),
        "position": player.get("START_POSITION", ""),
        "points": player.get("PTS", 0),
        "assists": player.get("AST", 0),
        "rebounds": player.get("REB", 0),
        "steals": player.get("STL", 0),
        "blocks": player.get("BLK", 0),
        "turnovers": player.get("TO", 0),
        "teamTricode": player.get("TEAM_ABBREVIATION"),
    }