from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
import pandas as pd
from content_based.recommend import content_recommend
from collabrative.collab import (
    load_filter_data,
    load_track_ids,
    load_interaction_matrix,
    recommend,
)

def recommend_by_content(song_name , artist_name):
    df = content_recommend(
        artist_name=artist_name,
        song_name=song_name
    )
    return df.rename(columns={"score": "content_score"})


def recom_by_collab(song_name , artist_name):
    fil_data = load_filter_data()
    track_ids = load_track_ids()
    interaction_matrix = load_interaction_matrix()

    df = recommend(
        song_name=song_name ,
        artist_name= artist_name,
        track_ids=track_ids,
        song_data=fil_data,
        interaction_matrix=interaction_matrix,
        top_k=5,
    )

    return df.rename(columns={"score": "collab_score"})



# Merge both recommenders
def Recommend_content(song_name , artist_name):
    
    content_df = recommend_by_content(song_name , artist_name)
    collab_df = recom_by_collab(song_name , artist_name)

    hybrid = content_df.merge(
        collab_df,
        on="track_id",
        how="outer"
    ).fillna(0)

    # Case 1: both empty
    if content_df.empty and collab_df.empty:
        raise ValueError("Song not found in either content-based or collaborative recommender.")

    # Case 2: only content available
    elif collab_df.empty:
        hybrid = content_df.rename(columns={"score": "content_score"}).copy()
        hybrid["collab_score"] = 0

    # Case 3: only collaborative available
    elif content_df.empty:
        hybrid = collab_df.rename(columns={"score": "collab_score"}).copy()
        hybrid["content_score"] = 0

    # Case 4: both available
    else:
        content_df = content_df.rename(columns={"score": "content_score"})
        collab_df = collab_df.rename(columns={"score": "collab_score"})

        hybrid = content_df.merge(
            collab_df,
            on="track_id",
            how="outer"
        ).fillna(0)

    # Compute hybrid score
    alpha = 0.4

    hybrid["final_score"] = (
        alpha * hybrid["content_score"] +
        (1 - alpha) * hybrid["collab_score"]
    )

    hybrid = hybrid.sort_values(
        "final_score",
        ascending=False
    ).reset_index(drop=True)
    to_get =  hybrid["track_id"]
    songs_= pd.read_csv(r"C:\Users\ADIL TRADERS\Desktop\spotify\SpotifyHybridRecommender\Data\Music Info.csv")
    
    result = songs_[songs_["track_id"].isin(hybrid["track_id"])]
    return result[["name" , "artist" ,"spotify_preview_url"]]
# import time

# start = time.perf_counter()

# try:
#     result = Recommend_content(
#         song_name="Numb",
#         artist_name="Linkin Park"
#     )
#     print(result)
# except Exception as e:
#     print(e)

# end = time.perf_counter()

# print(f"Latency: {(end - start):.4f} seconds")
# print(f"Latency: {(end - start) * 1000:.2f} ms")