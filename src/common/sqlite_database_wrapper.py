import sqlite3


class SQLiteDataBaseWrapper:
    def __init__(self, config):
        self.conn = sqlite3.connect(config["path"])
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()
        
    def execute(self, query):
        self.cursor.execute(query)

    def execute_insert(self, query, values):
        self.cursor.execute(query % values)

    def execute_select(self, query, values):
        self.cursor.execute(query % values)
        return self.cursor.fetchall()

    def execute_select_one(self, query, values):
        self.cursor.execute(query % values)
        return self.cursor.fetchone()

    def execute_update(self, query, values):
        self.cursor.execute(query % values)

    def fetch_data(self, query, values):
        self.cursor.execute(query % values)
        data = self.cursor.fetchall()
        x = []
        y = []
        for row in data:
            x.append(row[0])
            y.append(row[1])
        return x, y

