from flask import Flask
from src.common.config_loader import ConfigLoader
from src.common.data_base_wrapper import GetDataBaseWrapper
from src.common.ochoba_api_wrapper import OchobaApiWrapper

app = Flask(__name__)
config = ConfigLoader.load()
db = GetDataBaseWrapper(config["db"])

@app.route("/") 
def home_view():
    html = ["<h1>Welcome to Geeks for Geeks</h1>"]
    data = db.execute_select('select data from published order by pub_time desc;', '1')
    for i in data:
        html.append(f"<h2>{i[0]}</h2>")
    return '<br>'.join(html)
