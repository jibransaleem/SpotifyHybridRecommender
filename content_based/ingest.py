
import os
from pathlib import Path
import pandas as pd
BASE_PATH = Path(__file__).resolve().parent.parent  / "Data"

SONGS_PATH = BASE_PATH / "Music Info.csv"
PROCESS_PATH = BASE_PATH / "content_base_data" / "filter_content.csv"
def load_songs(songs_path : str =  SONGS_PATH):
    try :
        if not os.path.exists(str(songs_path)):
                raise FileNotFoundError(f"File is not found at location {songs_path}")
        df = pd.read_csv(songs_path)
        return df
    except Exception as e:
        raise e
def preprocess(df : pd.DataFrame , process_data_save_path:str =PROCESS_PATH ):
    try :
        if not isinstance(df , pd.DataFrame):
            raise ValueError("Given object is not pandas dataframe.")
        df.drop_duplicates(subset=["spotify_id" ,'year' , "duration_ms"] , inplace=True)
        df.reset_index(drop=True , inplace=True)
        df["name"] = df["name"].str.lower()
        df["artist"] =  df["artist"].str.lower()
        col_to_remove = ["track_id"  ,"spotify_preview_url" , "spotify_id" , "genre"]
        filtered = df.drop(columns=col_to_remove)
        filtered.fillna({"tags":"no-tag"},inplace=True)
        filtered["artist"] = filtered["artist"].str.lower()
        filtered.to_csv(process_data_save_path  , index=False)
    except Exception as e:
        raise e
# try:
#     df =  load_songs()
#     preprocess(df)
# except Exception as e:
#     print(e)
