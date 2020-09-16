from os import environ
from src.common.psycopg_database_wrapper import RemoteDataBaseWrapper , UrlDataBaseWrapper
from src.common.sqlite_database_wrapper import SQLiteDataBaseWrapper 

def GetDataBaseWrapper(config):
    if config["type"] == "remote":
        return RemoteDataBaseWrapper(config)
    elif config["type"] == "url":
        return UrlDataBaseWrapper(url=environ[config['environ']])
    elif config["type"] == "file":
        return SQLiteDataBaseWrapper(config)