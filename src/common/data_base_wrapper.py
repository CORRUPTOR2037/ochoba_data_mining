from os import environ

def GetDataBaseWrapper(config):
    if config["type"] == "remote":
        from src.common.psycopg_database_wrapper import RemoteDataBaseWrapper
        return RemoteDataBaseWrapper(config)
    
    elif config["type"] == "url":
        from src.common.psycopg_database_wrapper import UrlDataBaseWrapper
        return UrlDataBaseWrapper(url=config['environ'])
    
    elif config["type"] == "sqlite_file":
        from src.common.sqlite_database_wrapper import SQLiteDataBaseWrapper 
        return SQLiteDataBaseWrapper(config)
