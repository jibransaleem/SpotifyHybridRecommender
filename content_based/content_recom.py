from db import load_database ,load_chroma
from supabase import Client
from postgrest.exceptions import APIError
from httpx import ConnectError, ConnectTimeout, ReadTimeout
import os
import pandas as pd
from tabulate import tabulate
import sys

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from preprocessors.clean import load_cleaner , make_frame

col_to_remove = ["track_id" ,"name" ,"spotify_preview_url" , "spotify_id" , "genre"]


def client():
    try :
        db_client= load_database()
        return db_client
    except Exception as e:
        return e
class QUERY_ERROR(Exception):
    "raise when error occurs in query"
    pass
def fetch_by_id(idx:list ):
    try :
        db_client = load_database()
        if not isinstance(db_client , Client):
            return db_client
        db_client = load_database()
        response = (
        db_client.table("my_songs")
        .select("name, artist, spotify_preview_url")
        .in_("index", idx)
        .execute())


        data = response.data
        return data
    except APIError as e:
        raise QUERY_ERROR(f"Query error {e.message}") from e
    except (ConnectError , ReadTimeout ,ConnectTimeout) as e:
        raise QUERY_ERROR(f"Query error {e.message}") from e
    except Exception as e:
        raise QUERY_ERROR(f"Unexpected error: {e}") from e

def fetch_result(song_name:str , artist_name:str):
    try :
        db_client = client()
        if not isinstance(db_client , Client):
            return db_client
        song_name = song_name.strip().lower()
        artist_name =  artist_name.strip.lower()
        response = (
            db_client.table("my_songs")
            .select("*")
            .eq("name", song_name)
            .eq("artist", artist_name)   # narrows down duplicates with the same song name
            .execute()
        )

        data = response.data
        return data
    except APIError as e:
        raise QUERY_ERROR(f"Query error {e.message}") from e
    except (ConnectError , ReadTimeout ,ConnectTimeout) as e:
        raise QUERY_ERROR(f"Query error {e.message}") from e
    except Exception as e:
        raise QUERY_ERROR(f"Unexpected error: {e}") from e
    

def recommend_by_content(name:str , artist:str):
    try :
        name =  name.strip().lower()
        res = fetch_result(name)
        df = make_frame(res)
        trans = load_cleaner()
        embeddings = trans.transform(df).toarray()
        client = load_chroma()
        collection =  client.get_collection(name = "song")
        results = collection.query(
            query_embeddings=embeddings,   # must be a list of embeddings, even for one query
            n_results=5
        )
        

        resp = fetch_by_id(results["ids"][0])

        return resp
        
    except Exception as e:
        print(e)