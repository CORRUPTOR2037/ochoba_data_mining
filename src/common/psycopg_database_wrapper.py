import psycopg2


class RemoteDataBaseWrapper:
    def __init__(self, config):
        self.config = config
        self._connect()
    
    def _connect(self):
        self.conn = psycopg2.connect(host=self.config["host"],
                                     port=self.config["port"],
                                     database=self.config["database"],
                                     user=self.config["user"],
                                     password=self.config["password"])
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.cursor.close()
        self.conn.close()
        
    def sanitize_query(self, query):
        return query.replace("%d", "%s").replace('"%s"', "%s").replace("'%s'", "%s")

    def commit(self):
        self.conn.commit()
        
    def execute(self, query, values = []):
        query = self.sanitize_query(query)
        self.error_counter = 5
        while self.error_counter > 0:
            try:
                self.cursor.execute(query, values)
                return
            except:
                self.__connect()
        self.cursor.execute(query, values)

    def execute_insert(self, query, values = []):
        self.execute(query, values)

    def execute_select(self, query, values = []):
        self.execute(query, values)
        return self.cursor.fetchall()

    def execute_select_one(self, query, values = []):
        self.execute(query, values)
        return self.cursor.fetchone()

    def execute_update(self, query, values = []):
        self.execute(query, values)
    
    def fetch_data(self, query, values = []):
        self.execute(query, values)
        data = self.cursor.fetchall()
        x = []
        y = []
        for row in data:
            x.append(row[0])
            y.append(row[1])
        return x, y

class UrlDataBaseWrapper(RemoteDataBaseWrapper):
    def __init__(self, config):
        self.config = config
        self._connect = self._connect_override
        self._connect()
        
    def _connect_override(self):
        self.conn = psycopg2.connect(self.config, sslmode='require')
        self.cursor = self.conn.cursor()
