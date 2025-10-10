from fastapi import FastAPI, HTTPException
from nba_api.stats.endpoints import playercareerstats
from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import players
from nba_api.stats.endpoints import boxscoretraditionalv2
from datetime import date, datetime
from nba_api.stats.endpoints import scheduleleaguev2
from nba_api.stats.library.http import NBAStatsHTTP
from nba_api.stats.static import players
import time


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

@app.get("/")
def root():
    return {"message": "API da NBA funcionando 🚀 2.0"}

@app.get("/players")
def get_players():
    active_players = players.get_active_players()
    return active_players


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
    
    # Headers para evitar bloqueio da API
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nba.com/'
    }

    try:
        if game_date is None:
            # Jogos de hoje - live
            sb = scoreboard.ScoreBoard(headers=headers)
            games = sb.games.get_dict()

            for g in games:
                game_id = g["gameId"]
                status = g["gameStatusText"]

                # Tenta pegar boxscore, mas trata erro se não existir
                try:
                    bs = boxscore.BoxScore(game_id=game_id, headers=headers).game.get_dict()
                    boxscore_data = bs
                except Exception as e:
                    print(f"Erro ao buscar boxscore do jogo {game_id}: {e}")
                    boxscore_data = {"error": "Boxscore não disponível"}
                
                lista.append({
                    "game": g,
                    "boxscore": boxscore_data,
                })
                
                # Pequeno delay para não sobrecarregar a API
                time.sleep(0.5)

        else:
            # Jogos de uma data específica - stats
            formatted_date = convert_date_format(game_date)
            sb = scoreboardv2.ScoreboardV2(game_date=formatted_date, headers=headers)
            df = sb.get_data_frames()[0]

            for _, row in df.iterrows():
                game_id = row["GAME_ID"]
                status = row["LIVE_PERIOD"]

                # Tenta pegar boxscore, mas trata erro se não existir
                try:
                    bs = boxscoretraditionalv2.BoxScoreTraditionalV2(
                        game_id=game_id, 
                        headers=headers
                    ).get_dict()["resultSets"]
                    boxscore_data = bs
                except Exception as e:
                    print(f"Erro ao buscar boxscore do jogo {game_id}: {e}")
                    boxscore_data = [{"error": "Boxscore não disponível"}]

                lista.append({
                    "game": row.to_dict(),
                    "boxscore": boxscore_data,
                })
                
                # Pequeno delay para não sobrecarregar a API
                time.sleep(0.5)

        return {"date": game_date or date.today().strftime("%Y-%m-%d"), "games": lista}
    
    except Exception as e:
        print(f"ERRO GERAL: {str(e)}")
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