from fastapi import FastAPI
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv2
from datetime import datetime, timedelta

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API da NBA rodando!"}

@app.get("/boxscore/today")
def get_today_boxscores():

    today = datetime.today().strftime('%Y-%m-%d')

    try:
        # Testa a API da NBA
        scoreboard = scoreboardv2.ScoreboardV2(game_date="2025-03-18")
        games = scoreboard.get_dict()["resultSets"][0]["rowSet"]

        all_boxscores = []  # Lista para armazenar os boxscores

        for game in games:
            game_id = game[2]  # O ID do jogo está na terceira posição do array
            
            # Obtém o boxscore para esse jogo
            boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            player_stats = boxscore.get_dict()["resultSets"][0]["rowSet"]

            # return boxscore.get_dict()["resultSets"][0]['headers']
            formatted_players = []
            for player in player_stats:
                formatted_players.append({                    
                    "player": player[5],  # Nome do jogador
                    "team": player[2],  # Sigla do time
                    "player_id": player[4],  # ID do jogador
                    "min": player[9],  # Minutos (MIN)
                    "pts": player[27],  # Pontos (PTS)
                    "reb": player[21],  # Rebotes (REB)
                    "ast": player[22],  # Assistências (AST)
                    "blk": player[24],  # Blocks (BLK)
                    "stl": player[23],  # Steals (STL)
                    "tov": player[25],  # Turnovers (TO)
                    "3fgm": player[13]  # 3FGM (FG3M)
                })

            all_boxscores.append({
                "game_id": game_id,
                "players": formatted_players
            })

        return {"boxscores": all_boxscores}
      
    except Exception as e:
        print("Erro ao acessar a API da NBA:", e)