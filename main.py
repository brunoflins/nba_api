from fastapi import FastAPI
from nba_api.stats.endpoints import playercareerstats
from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import players
from nba_api.stats.endpoints import boxscoretraditionalv2
from datetime import date, datetime
from nba_api.stats.endpoints import scheduleleaguev2

app = FastAPI(title="Minha API NBA")

@app.get("/")
def root():
    return {"message": "API da NBA funcionando 🚀"}

@app.get("/player/{player_id}")
def get_player_stats(player_id: str):
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    return career.get_dict()

@app.get("/scoreboard")
def get_scoreboard():
    sb = scoreboard.ScoreBoard()
    return sb.get_dict()

@app.get("/players")
def get_players():
    pl = players.get_players();
    return pl; 

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
    Retorna jogos de uma data:
    - Se não passar data -> live.ScoreBoard (jogos de hoje)
    - Se passar data -> stats.ScoreboardV2 (jogos dessa data)
    Para cada jogo: status e boxscore completo.
    """
    lista = []

    if game_date is None:
        # Jogos de hoje - live
        sb = scoreboard.ScoreBoard()
        games = sb.games.get_dict()

        for g in games:
            game_id = g["gameId"]
            status = g["gameStatusText"]

            # Boxscore completo do jogo
            bs = boxscore.BoxScore(game_id=game_id).game.get_dict()

            lista.append({
                "gameId": game_id,
                "status": status,
                "boxscore": bs,
            })

    else:
        # Jogos de uma data específica - stats
        formatted_date = convert_date_format(game_date)
        sb = scoreboardv2.ScoreboardV2(game_date=formatted_date)
        df = sb.get_data_frames()[0]

        for _, row in df.iterrows():
            game_id = row["GAME_ID"]
            status = row["LIVE_PERIOD"]  # simplificado

            # Boxscore tradicional do jogo
            bs = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id).get_dict()["resultSets"]

            lista.append({
                "game": row,
                "boxscore": bs,
            })

    return {"date": game_date or date.today().strftime("%Y-%m-%d"), "games": lista}

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