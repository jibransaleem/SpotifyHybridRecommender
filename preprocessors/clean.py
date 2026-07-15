from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from category_encoders.count import CountEncoder
from pathlib import Path
import os
import pickle
import numpy as np
import pandas as pd


import pandas as pd
import chromadb

def make_frame(list_ : dict):
    dict_obj=list_[0]
    col_to_remove = ["track_id" ,"name" ,"spotify_preview_url" , "spotify_id" , "genre" ,"index"]
    columns = ['artist', 'tags', 'year', 'duration_ms', 'danceability', 'energy',
               'key', 'loudness', 'mode', 'speechiness', 'acousticness',
               'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature']
    array = []
    for  key in dict_obj:
        if key not in col_to_remove:
          array.append(dict_obj[key])
    df = pd.DataFrame([array], columns=columns)
    df["year"] = df["year"].astype("category")
    return df

def load_cleaner():
    try:
        file_path = Path(__file__).resolve().parent.parent / "Data"/"processor_pickels"/ "pre.pkl" 
        if not os.path.exists(str(file_path)):
            raise FileNotFoundError(f"given preprocessing file {file_path.name} does not exist")
        with open(str(file_path) , "rb") as file:
            pre = pickle.load(file)
        return pre
    except Exception as e:
        raise e

    
