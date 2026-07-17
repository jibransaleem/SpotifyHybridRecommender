import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import dask.dataframe as dd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix, save_npz , load_npz
sys.path.append(str(Path(__file__).resolve().parent.parent))

BASE_PATH = Path(__file__).resolve().parent.parent / "Data" # consistent with sys.path, not cwd-dependent
FILTERED_DATA_SAVE_PATH = BASE_PATH / "filtered_data.csv"
TRACK_ID_DATA_SAVE_PATH = BASE_PATH / "track_id.npy"
INTERACTION_MATRIX_PATH = BASE_PATH / "interaction_matrix.npz"

SONG_PATH = BASE_PATH / "Music Info.csv"
USER_DATA = BASE_PATH / "User Listening History.csv"


def save_to_csv(df: pd.DataFrame, save_path):
    df.to_csv(save_path, index=False)


def save_sparse_matrix(matrix, save_path):
    save_npz(save_path, matrix)


def filter_data(songs_data: pd.DataFrame, track_ids: list, save_df_path=FILTERED_DATA_SAVE_PATH):
    filter_data = songs_data[songs_data["track_id"].isin(track_ids)]
    filter_data["name"] = filter_data["name"].str.lower()
    filter_data["artist"] = filter_data["artist"].str.lower()
    filter_data = filter_data.reset_index(drop=True)
    save_to_csv(filter_data, save_df_path)
    return filter_data
def load_filter_data():
    path = FILTERED_DATA_SAVE_PATH
    df = pd.read_csv(path)
    return df

def load_interaction_matrix():
    pth =INTERACTION_MATRIX_PATH
    
    interaction_matrix = load_npz(pth)
    return interaction_matrix
    
def load_track_ids():
    pth = TRACK_ID_DATA_SAVE_PATH
    return np.load(pth ,allow_pickle=True)
    
    
def create_interaction_matrix(
    history_data: dd.DataFrame,
    track_id_save_path=TRACK_ID_DATA_SAVE_PATH,
    save_matrix_path=INTERACTION_MATRIX_PATH,
):
    df = history_data.copy()
    df["playcount"] = df["playcount"].astype(np.float64)
    df = df.categorize(columns=["track_id", "user_id"])

    track_ids = df["track_id"].cat.categories.values
    user_ids = df["user_id"].cat.categories.values
    np.save(track_id_save_path, track_ids, allow_pickle=True)

    df = df.assign(
        track_idx=df["track_id"].cat.codes,
        user_idx=df["user_id"].cat.codes,
    )

    interaction_matrix = (
        df.groupby(["track_idx", "user_idx"])["playcount"]
        .sum()
        .compute()
        .reset_index()  # gives back real columns: track_idx, user_idx, playcount
    )

    row_indices = interaction_matrix["track_idx"]
    col_indices = interaction_matrix["user_idx"]
    values = interaction_matrix["playcount"]

    n_tracks = len(track_ids)  # use full category count, not nunique of interactions
    n_users = len(user_ids)

    matrix = csr_matrix((values, (row_indices, col_indices)), shape=(n_tracks, n_users))
    save_sparse_matrix(matrix, save_matrix_path)
    return matrix


def recommend(song_name, artist_name, track_ids, song_data, interaction_matrix, top_k=5):
    
    song_name = song_name.strip().lower()
    artist_name = artist_name.strip().lower()

    song_row = song_data[
        (song_data["name"].str.lower() == song_name)
        & (song_data["artist"].str.lower() == artist_name)
    ]
    if song_row.empty:
        return pd.DataFrame(columns=["track_id", "score"])

    input_track_id = song_row["track_id"].iloc[0]
    idx = np.where(track_ids == input_track_id)[0].item()
    input_array = interaction_matrix[idx]

    scores = cosine_similarity(input_array, interaction_matrix).ravel()

    # exclude the input song itself before taking top_k
    scores[idx] = -np.inf

    top_indices = np.argsort(scores)[-top_k:][::-1]
    top_track_ids = track_ids[top_indices]
    top_scores = scores[top_indices]

    scores_df = pd.DataFrame({"track_id": top_track_ids.tolist(), "score": top_scores})

    # print(scores_df)
    # mask = song_data["track_id"].isin(scores_df["track_id"].values)
    # recom = song_data[mask]
    # recom["scores"] =  scores_df["scoore"]
    #  .drop(columns=["track_id", "score"])
    # top_k_songs = (
    #     song_data.loc[song_data["track_id"].isin(top_track_ids)]
    #     .merge(scores_df, on="track_id")
    #     .sort_values(by="score", ascending=False)  
    #     .reset_index(drop=True)
    # )
    return scores_df
def main():
    user_data = dd.read_csv(USER_DATA)
    
    unique_track_ids = user_data.loc[:,"track_id"].unique().compute()
    unique_track_ids = unique_track_ids.tolist()
    
    songs_data = pd.read_csv(SONG_PATH)
    filter_data(songs_data , unique_track_ids,FILTERED_DATA_SAVE_PATH)
    create_interaction_matrix(user_data , TRACK_ID_DATA_SAVE_PATH , INTERACTION_MATRIX_PATH)

