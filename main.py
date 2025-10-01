from fastapi import FastAPI
from nba_api.stats.endpoints import playercareerstats
from nba_api.live.nba.endpoints import scoreboard

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
