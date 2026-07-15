from pathlib import Path
import sys


from supabase import Client , create_client
import os
from dotenv import load_dotenv
from functools import lru_cache
load_dotenv()
import chromadb
class DB_CONNECTION_ERROR(Exception):
    "raise when error in connecting with db error"
    pass
@lru_cache
def load_database()->Client:
    
    key =  os.getenv("db_key")
    url = os.getenv("db_url")
    if not key or not url:
        raise DB_CONNECTION_ERROR(
            "Missing db credentials"
        )    
    try :    
        client = create_client(supabase_url=url , supabase_key=key)
        return client
    except Exception as e:
      raise  DB_CONNECTION_ERROR("failed to get client object")
  

def load_chroma():
    client = chromadb.PersistentClient(path="./chroma_db")
    return client
idx = ['4', '72', '357', '27', '26481']
