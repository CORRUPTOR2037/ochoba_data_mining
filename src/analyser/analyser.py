import json
import time
import re
from datetime import datetime
import sys, traceback

sys.path.append("../..")

from src.common.score_evaluation import score_evaluation
from src.common.config_loader import ConfigLoader
from src.common.data_base_wrapper import GetDataBaseWrapper
from src.common.ochoba_api_wrapper import OchobaApiWrapper

class GetPosts:
    def __init__(self):
        config = ConfigLoader.load()
        self.categories = []
        self.users = []
        self.timeline_length = 2000
        self.api = OchobaApiWrapper(config["api"])
        self.db = GetDataBaseWrapper(config["db"])
        self.commit_every_step = False
        
        self.__init_database()
        
        
    def scan(self):
        print("Started at " + datetime.now().strftime("%H:%M:%S"))

        print("check timeline")
        parsed_entries = 0
        timeline_request_appendix = ''
        last_post_time = self.db.execute_select_one("select value from parse_data where key='last_post_time';", [])[0]
        first_post = last_post_time
        
        while parsed_entries < self.timeline_length:

            url = "timeline?allSite=true" + timeline_request_appendix
            timeline = self.api.execute_with_delay(url)
            
            if self.__is_error(timeline):
                continue
            
            timeline = timeline.json()
            #print("found %d posts in %s category" % (len(timeline["result"]), category["name"]))
            if len(timeline["result"]) == 0: continue
            
            for post in timeline["result"]["items"]:
                if post["type"] != 'entry':
                    continue
                
                post = post["data"]
                
                if post["date"] < last_post_time:
                    parsed_entries = self.timeline_length
                    break
                if post["isEditorial"] > 0: continue
                
                first_post = max(last_post_time, post["date"])
                
                parsed_entries += 1
                self.add_post_to_database(post)
            
            if self.commit_every_step:
                self.db.commit()
            
            try:
                timeline_request_appendix = '&lastId=%d&lastSortingValue=%d' % (timeline["result"]["lastId"], timeline["result"]["lastSortingValue"])
            except:
                print("no pagination data found at", url, timeline["result"]["lastId"], timeline["result"]["lastSortingValue"])
                break
        
        self.db.execute_update("update parse_data set value=%d where key='last_post_time';", [first_post])
        
        self.db.commit()
        
        print("update categories")
        self.__update_categories()
        
        posts = self.db.execute_select("select * from posts where statsCalculated < 5 order by publication_time asc", [])
        if posts is None: return
        
        print("update posts")
        for post in posts:
            timeFromPublication = time.time() - post[4]

            if post[6] == 0 and timeFromPublication <  3600: continue
            if post[6] == 1 and timeFromPublication <  7200: continue
            if post[6] == 2 and timeFromPublication < 10800: continue
            
            post_stats = self.api.execute_with_delay("content?id=%d" % post[0])
            if self.__is_error(post_stats):
                self.db.execute("delete from posts where post_id=%d" % post[0])
                continue

            post_stats = post_stats.json()["result"]
            views = post_stats["hitsCount"]
            bookmarks = post_stats["counters"]["favorites"]
            comments = post_stats["counters"]["comments"]
            rating = post_stats["likes"]["summ"]
            reposts = post_stats["counters"]["reposts"]
            
            if post[7] == 0:
                for i in ['views', 'bookmarks', 'comments', 'rating', 'reposts']:
                    if self.db.execute_select_one(f"select * from posts_{i} where post_id=%d", [post[0]]) is None:
                        self.db.execute_insert(f"insert into posts_{i} (post_id, count1hr, count2hr, count3hr, now) values (%d, 0, 0, 0, 0)",
                                           [post[0]])

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
            
            for i, x in (('views', views), ('bookmarks', bookmarks), ('comments', comments), ('rating', rating), ('reposts', reposts)):
                self.db.execute(f"update posts_{i} set {column}={x}{', now=' + str(x) if column != 'now' else ''} where post_id={post[0]}")
            self.db.execute(f"update posts set statsCalculated={nextState} where post_id='{post[0]}'")

            #print ("updated state for post %d" % post[0])
            
            self.publish(post, post_stats)
            if nextState >= 4:
                self.db.execute(f"update posts set published=1 where post_id='{post[0]}'")
            
            if self.commit_every_step:
                self.db.commit()
        
        self.db.commit()
            
    def __init_database(self):
        self.db.execute("""
                    create table if not exists categories (
                        id SERIAL,
                        userid integer not null,
                        name text,
                        is_user integer not null,
                        subscribers integer
                    );
            """)

        self.db.execute("""
                    create table if not exists posts (
                        post_id integer primary key not null,
                        author_id integer not null,
                        cat_id integer not null,
                        name text not null,
                        publication_time integer not null,
                        words integer not null,
                        media integer not null,
                        statsCalculated integer not null,
                        published integer not null,
                        score integer,
                        last_update_time integer not null
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
        self.db.execute("""
                    create table if not exists posts_reposts (
                        post_id integer not null,
                        count1hr integer,
                        count2hr integer,
                        count3hr integer,
                        now integer
                    );
           """)

        self.db.execute("""
                    create table if not exists parse_data (
                        key text not null,
                        value integer
                    );
            """)
        if self.db.execute_select_one("select * from parse_data where key = 'last_post_time';", []) is None:
            self.db.execute_insert("""
                    insert into parse_data (key, value)
                    values ('last_post_time', 0);
            """, [])
            
        self.db.commit()
        
    def __update_categories(self):
        self.categories = self.db.execute_select("select id, userid from categories;", [])
        for line in self.categories:

            json = self.__get_category(line[1])
            if json is None:
                continue
            
            self.db.execute_update("update categories set subscribers='%s', name='%s' where id='%s'",
                                   (json["counters"]["subscribers"], json["name"], line[0]))

        self.categories = [{ "id": i[0], "userid": i[1], "name": i[2], "is_user": i[3], "subscribers": i[4]}
                           for i in self.db.execute_select("select * from categories;", [])]
        if self.commit_every_step:
            self.db.commit()
              
    
    def __get_category(self, userid):
        response = self.api.execute_with_delay('subsite?id=' + str(userid))
                
        if self.__is_error(response):
            return None
            
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
        if "result" not in response.json():
            # No result
            traceback.print_stack()
            print(datetime.now().strftime("%H:%M:%S") + ": No result on response, message: " + response.json()["message"])
            return True
        return False


    def add_post_to_database(self, post):

        if self.db.execute_select_one("select * from posts where post_id=%d", [post["id"]]) is not None:
            return
        
        data = {}
        data["post_id"] = post["id"]
        data["author_id"] = post["author"]["id"]
        data["cat_id"] = post["subsite"]["id"]
        data["name"] = re.sub(r"[\"\']", "", post["title"])
        if not data["name"]:
            data["name"] = '-'
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
        
        self.db.execute_insert(
            """
                insert into posts (post_id, cat_id, author_id, name, publication_time, words, media, statsCalculated, published, last_update_time)
                values (%d, %d, %d, "%s", %d, %d, %d, 0, 0, %d);
            """,
            [data["post_id"], data["cat_id"], data["author_id"], str(data["name"]), data["publication_time"], data["words"], data["media"], time.time()]
        )
        
        # add subsite category
        if self.db.execute_select_one("select * from categories where userid=%d", [data["cat_id"]]) is None:
            json = self.__get_category(data["cat_id"])
            self.db.execute_insert("""
                        insert into categories (userid, name, is_user, subscribers)
                            values (%s, '%s', %d, %d);
                    """,
                    [json["id"], json['name'], max(0, 2 - json['type']), json["counters"]["subscribers"]]
            )
            
        # add author category
        if self.db.execute_select_one("select * from categories where userid=%d", [data["author_id"]]) is None:
            json = self.__get_category(data["author_id"])
            self.db.execute_insert("""
                        insert into categories (userid, name, is_user, subscribers)
                            values (%s, '%s', %d, %d);
                    """,
                    [json["id"], json['name'], max(0, 2 - json['type']), json["counters"]["subscribers"]]
            )
        
        return data
        #print("added new post: [%d] %s" % (data["post_id"], data["name"]))
        

    def publish(self, post, post_stats):

        post_data = self.db.execute_select_one(
            """
                select posts.post_id, categories.name, posts.name, posts.publication_time, posts.words, posts.media,
                    posts_views.now, posts_bookmarks.now, posts_rating.now, posts_comments.now, posts_reposts.now, categories.subscribers
                from posts
                left join categories on posts.cat_id=categories.userid
                left join posts_views on posts.post_id=posts_views.post_id
                left join posts_bookmarks on posts.post_id=posts_bookmarks.post_id
                left join posts_rating on posts.post_id=posts_rating.post_id
                left join posts_comments on posts.post_id=posts_comments.post_id
                left join posts_reposts on posts.post_id=posts_reposts.post_id
                where posts.post_id=%d
            """, [post[0]])
        
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
        reposts = post_data[10]
        category_subs = post_data[11]
        
        if views is None or bookmarks is None or rating is None or comments is None: return

        score = score_evaluation(words, media, views, bookmarks, rating, comments, reposts, category_subs)
        
        self.db.execute_update("update posts set score=%d where post_id='%d'", [score, post[0]])
        
        #if score > 50:
            #print("Recommended: [https://dtf.ru/%d][%s][Score: %s] \"%s\" From %s / %d Words / %d Mediafiles / %d Views / %d Bookmarks / %d Rating / %d Comments" %
            #      (post_id, time.strftime('%H:%M %m-%d-%YMSK', time.localtime(publication_time + 10800)), str(score).zfill(4), title, category,
            #       words, media, views, bookmarks, rating, comments))
        #    self.db.execute_update("update posts set published=1 where post_id='%d'", (post[0]))


if __name__ == "__main__":
    scanner = GetPosts()
    
    while True:
        scanner.scan()
        time.sleep(60)
