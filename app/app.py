import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sys
sys.path.append(Path(__file__).resolve().parent.parent)


from Hybrid.hybrid_ import Recommend_content

# -----------------------------------------------------------------
# Path to Music Info.csv, used to populate the browse/search grid.
# -----------------------------------------------------------------
DATA_PATH = r"C:\Users\ADIL TRADERS\Desktop\spotify\SpotifyHybridRecommender\Data\Music Info.csv"

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Groove Hybrid Recommender")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# -----------------------------------------------------------------
# Thread pool: pandas/sklearn calls are blocking (CPU + sync I/O).
# Running them here keeps the asyncio event loop free to keep
# accepting/serving other requests while a recommendation computes.
# Tune max_workers to your CPU core count in production.
# -----------------------------------------------------------------
executor = ThreadPoolExecutor(max_workers=8)

# -----------------------------------------------------------------
# In-memory state — loaded once at startup, never touched per request.
# -----------------------------------------------------------------
_songs_df: Optional[pd.DataFrame] = None

# Simple in-memory recommendation cache: (song, artist) -> list[dict]
# In production, swap this dict for Redis so it survives restarts
# and is shared across multiple app instances.
_rec_cache: dict[tuple[str, str], list[dict]] = {}


@app.on_event("startup")
async def load_data():
    global _songs_df
    df = pd.read_csv(DATA_PATH)
    _songs_df = df.dropna(subset=["name", "artist"]).reset_index(drop=True)
    print(f"[startup] Loaded {len(_songs_df)} songs into memory.")


def row_to_card(row) -> dict:
    preview = row.get("spotify_preview_url")
    return {
        "name": row["name"],
        "artist": row["artist"],
        "preview_url": preview if pd.notna(preview) else None,
    }


# -----------------------------------------------------------------
# Blocking work, run inside the thread pool via run_in_executor.
# -----------------------------------------------------------------
def _search_songs_sync(query: str) -> list[dict]:
    df = _songs_df
    if query:
        mask = (
            df["name"].str.lower().str.contains(query, na=False)
            | df["artist"].str.lower().str.contains(query, na=False)
        )
        df = df[mask]
    df = df.head(40)
    return [row_to_card(r) for _, r in df.iterrows()]


def _recommend_sync(song_name: str, artist_name: str) -> list[dict]:
    """This is your existing blocking recommender — untouched, just
    called off the event loop instead of on it."""
    result = Recommend_content(song_name=song_name, artist_name=artist_name)
    return [
        {
            "name": r["name"],
            "artist": r["artist"],
            "preview_url": r["spotify_preview_url"] if pd.notna(r["spotify_preview_url"]) else None,
        }
        for _, r in result.iterrows()
    ]


# -----------------------------------------------------------------
# Routes
# -----------------------------------------------------------------
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/songs")
async def api_songs(q: str = Query(default="")):
    query = q.strip().lower()
    loop = asyncio.get_running_loop()
    cards = await loop.run_in_executor(executor, _search_songs_sync, query)
    return cards


@app.get("/api/recommend")
async def api_recommend(
    song_name: str = Query(default=""),
    artist_name: str = Query(default=""),
):
    song_name = song_name.strip()
    artist_name = artist_name.strip()

    if not song_name or not artist_name:
        return JSONResponse(
            {"error": "song_name and artist_name are required"}, status_code=400
        )

    cache_key = (song_name.lower(), artist_name.lower())
    if cache_key in _rec_cache:
        return _rec_cache[cache_key]

    loop = asyncio.get_running_loop()
    try:
        cards = await loop.run_in_executor(executor, _recommend_sync, song_name, artist_name)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=404)

    _rec_cache[cache_key] = cards
    return cards


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)