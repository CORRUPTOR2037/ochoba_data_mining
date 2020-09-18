from flask import Flask, request, render_template
from src.common.config_loader import ConfigLoader
from src.common.data_base_wrapper import GetDataBaseWrapper

import time

app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
config = ConfigLoader.load()
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route("/") 
def home_view():

    html = []
    
    count = int(request.args.get('count', default=50))
    minScore = int(request.args.get('minScore', default=50))
    
    db = GetDataBaseWrapper(config["db"])
    data = db.execute_select("""
                select posts.post_id, authors.id, authors.name, categories.id, categories.name, posts.name, posts.publication_time, posts.words, posts.media,
                    posts_views.now as views,
                    posts_bookmarks.now as bookmarks,
                    posts_rating.now as rating,
                    posts_comments.now as comments,
                    posts_reposts.now as reposts,
                    posts.score
                from posts
                left join categories on posts.cat_id=categories.userid
                left join categories as authors on posts.author_id=authors.userid
                left join posts_views on posts.post_id=posts_views.post_id
                left join posts_bookmarks on posts.post_id=posts_bookmarks.post_id
                left join posts_rating on posts.post_id=posts_rating.post_id
                left join posts_comments on posts.post_id=posts_comments.post_id
                left join posts_reposts on posts.post_id=posts_reposts.post_id
                order by published desc;
            """, [])
    
    data = [ post for post in data if post[14] is not None and post[14] >= minScore ]
    if len(data) > count:
        data = data[0:count]

    for post in data:
        
        post_id = post[0]
        author_id = post[1]
        author_name = post[2]
        cat_id = post[3]
        cat_name = post[4]
        post_name = post[5]
        publication_time = post[6]
        words = post[7]
        media = post[8]
        views = post[9]
        bookmarks = post[10]
        rating = post[11]
        comments = post[12]
        reposts = post[13]
        score = post[14]
        
        html.append("<tr>")
        html.append("  <td content='%s'><a target='_blank' title='%s' href='https://dtf.ru/%d'>%s</a></td>" % (post_name, post_name, post_id, post_name))
        html.append("  <td content='%s'><a target='_blank' href='https://dtf.ru/u/%d'>%s</a></td>" % (author_name, author_id, author_name))
        html.append("  <td content='%s'><a target='_blank' href='https://dtf.ru/u/%d'>%s</a></td>" % (cat_name, cat_id, cat_name))
        html.append("  <td content='%d'>%s</td>" % (publication_time, time.strftime('%H:%M %m-%d-%YMSK', time.localtime(publication_time + 10800))))
        html.append("  <td content='%d'>%d</td>" % (score, score))
        html.append("  <td content='%d'>%d</td>" % (words, words))
        html.append("  <td content='%d'>%d</td>" % (media, media))
        html.append("  <td content='%d'>%d</td>" % (rating, rating))
        html.append("  <td content='%d'>%d</td>" % (views, views))
        html.append("  <td content='%d'>%d</td>" % (bookmarks, bookmarks))
        html.append("  <td content='%d'>%d</td>" % (comments, comments))
        html.append("  <td content='%d'>%d</td>" % (reposts, reposts))
        html.append("</tr>")
    
    return render_template("ratingTable.html",
        ratingRows = "\n".join(html),
        count = count,
        minScore = minScore)

if __name__ == "__main__": 
    app.run() 
