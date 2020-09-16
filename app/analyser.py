import json
import time
import re
import os
from datetime import datetime
from dataclasses import dataclass
import sys, traceback

from src.common.config_loader import ConfigLoader
from src.common.data_base_wrapper import GetDataBaseWrapper
from src.common.ochoba_api_wrapper import OchobaApiWrapper

class GetPosts:
    def __init__(self):
        config = ConfigLoader.load()
        self.categories = config["parse_targets"]["categories"]
        self.users = config["parse_targets"]["users"]
        self.api = OchobaApiWrapper(config["api"])
        self.db = GetDataBaseWrapper(config["db"])
        self.middle_rating = {}
        
        self.__init_database()
        
        
    def scan(self):
        print("Started at " + datetime.now().strftime("%H:%M:%S"))
        
        print("update categories")
        self.__update_categories()
        
        print("check subsites")
        for category in self.categories:
            time.sleep(self.api.min_delay)
            
            if category["is_user"] > 0:
                timeline = self.api.execute("user/%s/entries" % category["userid"])
            else:
                timeline = self.api.execute("subsite/%s/timeline/new" % category["userid"])
            
            if self.__is_error(timeline):
                continue
            
            timeline = timeline.json()
            #print("found %d posts in %s category" % (len(timeline["result"]), category["name"]))
            if len(timeline["result"]) == 0: continue
            
            for post in timeline["result"]:
                if post["date"] < category["last_post_time"]:
                    break
                if post["isEditorial"] > 0: continue
                
                self.add_post_to_database(post)
                
            first_post_time = timeline["result"][0]["date"]
            
            if first_post_time > category["last_post_time"]:
                category["last_post_time"] = first_post_time
                self.db.execute(f"""update categories set last_post_time={first_post_time} where id='{category["id"]}'""")
            self.db.commit()
        
        posts = self.db.execute_select("select * from posts where statsCalculated < 5 and published=0 order by publication_time asc", [])
        if posts is None: return
        
        print("update posts")
        for post in posts:
            timeFromPublication = time.time() - post[3]
            if post[6] == 0 and timeFromPublication <  3600: continue
            if post[6] == 1 and timeFromPublication <  7200: continue
            if post[6] == 2 and timeFromPublication < 10800: continue
            
            time.sleep(self.api.min_delay)
            post_stats = self.api.execute("entry/%d" % post[0])
            if self.__is_error(post_stats):
                self.db.execute("delete from posts where post_id=%d" % post[0])
                continue

            post_stats = post_stats.json()["result"]
            views = post_stats["hitsCount"]
            bookmarks = post_stats["favoritesCount"]
            comments = post_stats["commentsCount"]
            rating = post_stats["likes"]["summ"]
            
            if post[6] == 0:
                if self.db.execute_select_one(f"select * from posts_views where post_id={post[0]}", '1') is None:
                    self.db.execute(f"insert into posts_views (post_id, count1hr, count2hr, count3hr) values ({post[0]}, 0, 0, 0)")
                if self.db.execute_select_one(f"select * from posts_bookmarks where post_id={post[0]}", '1') is None:
                    self.db.execute(f"insert into posts_bookmarks (post_id, count1hr, count2hr, count3hr) values ({post[0]}, 0, 0, 0)")
                if self.db.execute_select_one(f"select * from posts_comments where post_id={post[0]}", '1') is None:
                    self.db.execute(f"insert into posts_comments (post_id, count1hr, count2hr, count3hr) values ({post[0]}, 0, 0, 0)")
                if self.db.execute_select_one(f"select * from posts_rating where post_id={post[0]}", '1') is None:
                    self.db.execute(f"insert into posts_rating (post_id, count1hr, count2hr, count3hr) values ({post[0]}, 0, 0, 0)")
            
            if timeFromPublication > 43000:
                nextState = 5
                column = "now"
            elif timeFromPublication > 12000:
                nextState = 4
                column = "now"
            elif timeFromPublication > 10800:
                nextState = 3
                column = "count3hr"
            elif timeFromPublication > 7200:
                nextState = 2
                column = "count2hr"
            elif timeFromPublication > 3600:
                nextState = 1
                column = "count1hr"
            
            for i, x in (('views', views), ('bookmarks', bookmarks), ('comments', comments), ('rating', rating)):
                self.db.execute(f"update posts_{i} set {column}={x}{', now=' + str(x) if column != 'now' else ''} where post_id={post[0]}")
            self.db.execute(f"update posts set statsCalculated={nextState} where post_id='{post[0]}'")

            #print ("updated state for post %d" % post[0])
            
            self.publish(post, post_stats)
            if nextState >= 4:
                self.db.execute(f"update posts set published=1 where post_id='{post[0]}'")
                
            self.db.commit()
        
            
    def __init_database(self):
        self.db.execute("""
                    create table if not exists categories (
                        id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY not null,
                        userid integer not null,
                        name varchar,
                        is_user integer not null,
                        subscribers integer,
                        last_post_time integer not null,
                        watch integer not null
                    );
            """)
        self.db.execute("""
                    create table if not exists posts (
                        post_id integer primary key not null,
                        cat_id integer not null,
                        name varchar not null,
                        publication_time integer not null,
                        words integer not null,
                        media integer not null,
                        statsCalculated integer not null,
                        published integer not null,
                        score integer
                    );
            """)
        self.db.execute("""
                    create table if not exists posts_views (
                        post_id integer not null,
                        count1hr integer,
                        count2hr integer,
                        count3hr integer,
                        now integer
                    );
           """)
        self.db.execute("""
                    create table if not exists posts_rating (
                        post_id integer not null,
                        count1hr integer,
                        count2hr integer,
                        count3hr integer,
                        now integer
                    );
           """)
        self.db.execute("""
                    create table if not exists posts_comments (
                        post_id integer not null,
                        count1hr integer,
                        count2hr integer,
                        count3hr integer,
                        now integer
                    );
           """)
        self.db.execute("""
                    create table if not exists posts_bookmarks (
                        post_id integer not null,
                        count1hr integer,
                        count2hr integer,
                        count3hr integer,
                        now integer
                    );
            """)
        
        last_post_time = time.time() - 2 * 60 * 60 * 24

        for cat in self.categories:
            print(cat)
            if self.db.execute_select_one(f"select userid from categories where userid='{cat}'", ('1')) is None:
                self.db.execute(
                    f"insert into categories (userid, is_user, last_post_time, watch) values ({int(cat)}, 0, {last_post_time}, 1);"
                )
                
        for user in self.users:
            if self.db.execute_select_one(f"select userid from categories where userid='{user}'", ('1')) is None:
                self.db.execute(
                    f"""
                        insert into categories (userid, is_user, last_post_time, watch)
                            values ({user}, 1, {last_post_time}, 1);
                    """
                )
        
        self.db.commit()
        
    def __update_categories(self):
        self.categories = self.db.execute_select("select id, userid, is_user from categories;", [])
        for line in self.categories:
            time.sleep(self.api.min_delay)
            
            json = self.__get_category(line[1], line[2])
            if json is None:
                continue
            
            self.db.execute(f"update categories set subscribers='{json['subscribers_count']}', name='{json['name']}' where id='{line[0]}'")

        self.categories = [{ "id": i[0], "userid": i[1], "name": i[2], "is_user": i[3], "subscribers": i[4], "last_post_time": i[5]}
                           for i in self.db.execute_select("select * from categories where watch=1;", [])]
        self.db.commit()
              
    
    def __get_category(self, userid, isuser):
        if isuser > 0:
            response = self.api.execute('user/' + str(userid))
        else:
            response = self.api.execute('subsite/' + str(userid))
                
        if self.__is_error(response):
            return None
            
        # print(response.json())
        return response.json()["result"]
    
                
    def __is_error(self, response):
        if response.status_code == 429:
            # Too Many Requests
            traceback.print_stack()
            print(datetime.now().strftime("%H:%M:%S") + ": 429 Too Many Requests ")
            return True
        if response.status_code == 404:
            # Too Many Requests
            traceback.print_stack()
            print(datetime.now().strftime("%H:%M:%S") + ": 404 Not Found ")
            return True
        return False


    def add_post_to_database(self, post):
        # print(post)
        if self.db.execute_select_one(f"select * from posts where post_id={post['id']}", '1') is not None:
            return
        
        data = {}
        data["post_id"] = post["id"]
        data["cat_id"] = post["subsite"]["id"]
        data["name"] = re.sub(r"[\"\']", "", post["title"])
        if not data["name"]:
            data["name"] = 'NoName'
        data["media"] = 0
        data["words"] = 0
        data["publication_time"] = post["date"]
        
        post["blocks"].append({ "type": "text", "data": { "text": data["name"] }})

        for block in post["blocks"]:
            blocktype = block["type"]
            text = ""
            
            if blocktype == "text" or blocktype == "header" or blocktype == "quote" or blocktype == "incut":
                text = block['data']['text']
            elif blocktype == "media":
                text = ""
                for item in block['data']['items']:
                    text += item['title'] + " "
                    data["media"] += 1
            elif blocktype == "list":
                text = ""
                for item in block['data']['items']:
                    text += item + " "
            elif blocktype == "tweet":
                text = block['data']['tweet']['data']['tweet_data']['full_text']
                data["media"] += 1
            elif blocktype == "video" or blocktype == "audio" or blocktype == "link":
                data["media"] += 1
                
            text = re.sub(r']\([^\(\)]+\)', '', text)
            text = re.sub(r'—', '', text)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\#\w+', '', text)
            data["words"] += len(text.split())
        
        self.db.execute(
            f"""
                insert into posts (post_id, cat_id, name, publication_time, words, media, statsCalculated, published)
                values ({data["post_id"]}, {data["cat_id"]}, '{str(data["name"])}', {data["publication_time"]}, {data["words"]}, {data["media"]}, 0, 0);
            """
        )
        
        return data
        #print("added new post: [%d] %s" % (data["post_id"], data["name"]))
        

    def publish(self, post, post_stats):

        post_data = self.db.execute_select_one(
            f"""
                select posts.post_id, categories.name, posts.name, posts.publication_time, posts.words, posts.media,
                    posts_views.now, posts_bookmarks.now, posts_rating.now, posts_comments.now, categories.subscribers
                from posts
                left join categories on posts.cat_id=categories.userid
                left join posts_views on posts.post_id=posts_views.post_id
                left join posts_bookmarks on posts.post_id=posts_bookmarks.post_id
                left join posts_rating on posts.post_id=posts_rating.post_id
                left join posts_comments on posts.post_id=posts_comments.post_id
                where posts.post_id={post[0]}
            """, '1')
        
        if post_data is None: return
        
        post_id = post_data[0]
        category = post_data[1]
        title = post_data[2]
        publication_time = post_data[3]
        words = post_data[4]
        media = post_data[5]
        views = post_data[6]
        bookmarks = post_data[7]
        rating = post_data[8]
        comments = post_data[9]
        category_subs = post_data[10]
        
        if views is None or bookmarks is None or rating is None or comments is None: return
        
        if category_subs is None:
            json = self.__get_category(post_stats["subsite"]["id"], post_stats["subsite"]["type"] == 1)
            time.sleep(self.api.min_delay)
            category = json['name']
            category_subs = json["subscribers_count"]
            self.db.execute(
                f"""
                    insert into categories (userid, name, is_user, subscribers, last_post_time, watch)
                        values ({json["id"]}, '{json['name']}', {int(post_stats["subsite"]["type"] == 1)}, {json["subscribers_count"]}, 0, 0);
                """
            )

        category_subs = min(category_subs, 50000)

        expected_views = pow(category_subs * 2.3, 0.71)
        expected_likes = pow(category_subs * 3.5, 0.38)
        expected_bookmarks = pow(category_subs * 3.5, 0.38)
        expected_comments = pow(category_subs * 3.5, 0.38)
        
        score = words / 500.0 + media / 10.0 + views / expected_views + bookmarks / expected_bookmarks + rating / expected_likes + comments / expected_comments
        score = int(score * 10)
        self.db.execute(f"update posts set score={score} where post_id='{post[0]}'")
        
        if score > 50:
            print("Recommended: [https://dtf.ru/%d][%s][Score: %s] \"%s\" From %s / %d Words / %d Mediafiles / %d Views / %d Bookmarks / %d Rating / %d Comments" %
                  (post_id, time.strftime('%H:%M %m-%d-%YMSK', time.localtime(publication_time + 10800)), str(score).zfill(4), title, category,
                   words, media, views, bookmarks, rating, comments))
            self.db.execute(f"update posts set published=1 where post_id='{post[0]}'")
            data = f"""<a href="https://dtf.ru/{post_id}">[https://dtf.ru/{post_id}]</a> [{time.strftime('%H:%M %m-%d-%YMSK', time.localtime(publication_time + 10800))}][Score: {str(score).zfill(4)}] "{title}" From {category} / {words} Words / {media} Mediafiles / {views} Views / {bookmarks} Bookmarks / {rating} Rating / {comments} Comments"""
            self.db.execute(f"insert into published (data) values ('{data}');")

        
    def __get_post(self, post_id):
        response = self.api.execute("entry/" + str(post_id))
        
        response_json = response.json()
        print(str(response.status_code) + ": " + str(response_json))

        if "error" in response_json:
            self.db.execute(
                f"""
                    insert into post_errors (post_id, status_code, response)
                        values ({post_id}, {response.status_code}, {json.dumps(response_json)});
                """
            )
            self.stats.error_count += 1

        else:
            self.db.execute(
                f"""
                    insert into posts (id, json)
                        values ({post_id}, {json.dumps(response_json)})
                    on conflict (id)
                        do update set json = excluded.json;
                """
            )
            self.stats.post_count += 1

        self.stats.request_count += 1
        self.stats.requests_since_last_429 += 1

    def print_post_info(self, id):
        self.db.execute(f"delete from posts where post_id={id}")
        
        post = self.api.execute("entry/%d" % id)
        if self.__is_error(post):
            print("error")
        
        print(self.add_post_to_database(post.json()['result']))


if __name__ == "__main__":
    scanner = GetPosts()
    
    while True:
        scanner.scan()
        time.sleep(60)
