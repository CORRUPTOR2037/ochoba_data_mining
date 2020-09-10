from src.common.psycopg_database_wrapper import RemoteDataBaseWrapper 
from src.common.sqlite_database_wrapper import SQLiteDataBaseWrapper 

def GetDataBaseWrapper(config):
    if config["type"] == "remote":
        return RemoteDataBaseWrapper(config)
    elif config["type"] == "file":
        return SQLiteDataBaseWrapper(config)