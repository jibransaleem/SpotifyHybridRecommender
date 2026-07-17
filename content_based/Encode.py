from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from category_encoders.count import CountEncoder
import pickle
import chromadb
import numpy as np

import os
from pathlib import Path
import pandas as pd
BASE_PATH = Path(__file__).resolve().parent.parent  / "Data"

PROCESS_PATH = str(BASE_PATH / "content_base_data" / "filter_content.csv")
TRANSFORMER_PATH =str( BASE_PATH / "processor_pickels" / "pre.pkl")
CHROMA_DB_PATH = str(BASE_PATH /"chroma_db")
SAVE_ENCODINGS  = str(BASE_PATH/ "content_base_data" / "encoding.npy")
def load_transform_data(path: str = PROCESS_PATH):
    try :
        if not os.path.exists(str(path)):
            raise FileNotFoundError(f"file does not exists at path {path}")
        df = pd.read_csv(str(path))
        return df
    except Exception as e:
        raise e
import pickle
from sklearn.compose import ColumnTransformer

def save_transformer(transformer_object, path=TRANSFORMER_PATH):
    if not isinstance(transformer_object, ColumnTransformer):
        raise TypeError("transformer_object must be a ColumnTransformer.")

    with open(path, "wb") as file:
        pickle.dump(transformer_object, file)
def load_transformer(path : str = TRANSFORMER_PATH):
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"file not found at place {path}")
        with open(path , "rb") as file:
            transformer = pickle.load(file)
        return transformer
    except Exception as e:
        raise e
def init_transformer():
    try :
        freq_encode_cols = ["year"]
        tfidf_col = "tags"

        one_hot_cols = [
            "artist",
            "key",
            "mode",
            "time_signature",
        ]

        standard_scale_cols = [
            "duration_ms",
            "loudness",
            "tempo",
        ]

        min_max_cols = [
            "danceability",
            "energy",
            "speechiness",
            "acousticness",
            "instrumentalness",
            "liveness",
            "valence",
        ]

        preprocessor = ColumnTransformer(
            transformers=[
                ("freq", CountEncoder(), freq_encode_cols),
                ("tfidf", TfidfVectorizer(max_features=85), tfidf_col),
                ("onehot", OneHotEncoder(handle_unknown="ignore"), one_hot_cols),
                ("standard", StandardScaler(), standard_scale_cols),
                ("minmax", MinMaxScaler(), min_max_cols),
            ],
            remainder="drop",
        )
        return preprocessor
    except Exception as e:
        raise e
def load_from_numpy(path):
    array = np.load(path)
    return array
def encoding(df:pd.DataFrame , encdoding_safe_path:str = SAVE_ENCODINGS ):
    try :
        if not isinstance(df , pd.DataFrame):
            raise ValueError("given object is not pandas dataframe")
        filtered  = load_transform_data(PROCESS_PATH)
        filtered =  filtered.drop(columns=["track_id"])
        filtered["year"] = filtered["year"].astype("category")
        transformer = init_transformer()
        transformer= transformer.fit(filtered)
        processed = transformer.transform(filtered).toarray()
        save_transformer(transformer)
        print("saved")
        np.save(str(encdoding_safe_path), processed, allow_pickle=True)
    except Exception as e:
        raise e
def load_vector_db(vec_db_path : str = CHROMA_DB_PATH):
    client = chromadb.PersistentClient(path=vec_db_path)
    return client

def save_to_vector_db():
    try:
        batch_size = 5000
        client = load_vector_db(CHROMA_DB_PATH)
        collection = client.get_or_create_collection(
            name="song",
            metadata={"hnsw:space": "cosine"}
        )
        processed  = load_from_numpy(SAVE_ENCODINGS)
        ids = [str(i) for i in range(processed.shape[0])]
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i:i + batch_size],
                embeddings=processed[i:i + batch_size]
            )
    except Exception as e:
        raise e
# df = load_transform_data()
# encoding(df)
