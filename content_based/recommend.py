import chromadb
from pathlib import Path
from Encode import load_transform_data  ,load_transformer

import pandas as pd
BASE_PATH = Path(__file__).resolve().parent.parent  / "Data"
from ingest import load_songs
PROCESS_PATH = str(BASE_PATH / "content_base_data" / "filter_content.csv")
TRANSFORMER_PATH =str( BASE_PATH / "processor_pickels" / "pre.pkl")
CHROMA_DB_PATH = str(BASE_PATH /"chroma_db")
SAVE_ENCODINGS  = str(BASE_PATH/ "content_base_data" / "encoding.npy")
def load_vector_db(vec_db_path : str = CHROMA_DB_PATH):
    client = chromadb.PersistentClient(path=vec_db_path)
    return client
def load_collection():
    client = load_vector_db()
    collection = client.get_collection(name = "song")
    return collection
def content_recommend(artist_name :str , song_name:str , top_k=5):
    try :
        df =load_transform_data()
        # print(type(df))
        query = df[(df["artist"]==artist_name) & (df["name"]==song_name)]
        
        
        preprocessor = load_transformer()
        collection = load_collection()
        cols = [
        "name", "artist", "tags", "year", "duration_ms", "danceability",
        "energy", "key", "loudness", "mode", "speechiness",
        "acousticness", "instrumentalness", "liveness",
        "valence", "tempo", "time_signature"
    ]

        query_df = pd.DataFrame(query, columns=cols)
        query_vector = preprocessor.transform(query_df).toarray()
        result = collection.query(
            query_embeddings=query_vector,
            n_results=top_k
        )
        ids = result["ids"][0]
        ids=[int(i) for i in ids]
        
        # recome_data = df.iloc[ids ,:]
        df = load_songs()
        dt = df.iloc[ids,:]
        return dt
    except Exception as e:
        raise e
            
#     try :
try:
    content_recommend(artist_name="radiohead" ,song_name="creep")
except Exception as e:
    print(e)