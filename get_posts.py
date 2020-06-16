import json
import pathlib
import re
import time
import urllib.parse
from datetime import datetime

import psycopg2
import requests

from ochoba_api_wrapper import OchobaApiWrapper


class GetPosts:
    class Stats:
        def __init__(self):
            self.request_count = 0
            self.post_count = 0
            self.error_count = 0
            self.requests_since_last_429 = 0

    def __init__(self):
        script_path = pathlib.Path(__file__).parent.absolute()
        with open(str(script_path) + "/config.json") as json_file:
            config = json.load(json_file)

        self.api = OchobaApiWrapper(config["api"])
        self.conn = psycopg2.connect(host=config["db"]["host"],
                                     port=config["db"]["port"],
                                     database=config["db"]["database"],
                                     user=config["db"]["user"],
                                     password=config["db"]["password"])
        self.cursor = self.conn.cursor()

        self.tag_regex = re.compile(config["api"]["tag_regex"])

        self.stats = self.Stats()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def get_posts(self):
        print("Started at " + datetime.now().strftime("%H:%M:%S"))
        for post_id in range(1, 154000):
            if self.stats.request_count % 100 == 0:
                self.conn.commit()
                print("{0}: {1} requests processed ({2} posts, {3} errors)"
                      .format(datetime.now().strftime("%H:%M:%S"),
                              self.stats.request_count,
                              self.stats.post_count,
                              self.stats.error_count))

            self.__get_post(post_id)

        self.conn.commit()

    def __get_post(self, post_id):
        response = self.api.execute("entry/" + str(post_id))
        if response.status_code == 429:
            # Too Many Requests
            print(datetime.now().strftime("%H:%M:%S")
                  + ": 429 Too Many Requests. Requests processed since last 429 error: "
                  + str(self.stats.requests_since_last_429)
                  + ". Wait for 60 seconds and repeat")
            self.stats.requests_since_last_429 = 0
            time.sleep(60)
            self.__get_post(post_id)
            return

        response_json = response.json()
        print(str(response.status_code) + ": " + str(response_json))

        if "error" in response_json:
            self.cursor.execute(
                """
                    insert into post_errors (post_id, status_code, response)
                        values (%s, %s, %s);
                """,
                (post_id, response.status_code, json.dumps(response_json))
            )
            self.stats.error_count += 1

        else:
            result = response_json["result"]
            if "entryContent" in result:
                search_index = 0
                parsed_tags = []
                while True:
                    match = self.tag_regex.search(result["entryContent"]["html"], search_index)
                    if match is None:
                        break

                    parsed_tags.append(urllib.parse.unquote(match.group(1)))
                    search_index = match.end(1)

                result["parsed_tags"] = parsed_tags
                del result["entryContent"]

            text_length = 0
            media_count = 0
            if "blocks" in result:
                for block in result["blocks"]:
                    if block["type"] in ["media", "video"]:
                        media_count += 1
                    elif block["type"] in ["text", "header", "incut", "quote"]:
                        text_length += len(block["data"]["text"])
                del result["blocks"]

            self.cursor.execute(
                """
                    insert into posts (id, json, text_length, media_count)
                        values (%s, %s, %s, %s)
                    on conflict (id)
                        do update set json = excluded.json;
                """,
                (post_id, json.dumps(response_json), text_length, media_count)
            )
            self.stats.post_count += 1

        self.stats.request_count += 1
        self.stats.requests_since_last_429 += 1


if __name__ == "__main__":
    GetPosts().get_posts()