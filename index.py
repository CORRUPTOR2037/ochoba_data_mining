from flask import Flask, request, render_template
from src.common.config_loader import ConfigLoader
from src.common.data_base_wrapper import GetDataBaseWrapper

import time

app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
config = ConfigLoader.load()
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.db = GetDataBaseWrapper(config["db"])

@app.route("/") 
def home_view():

    html = []
    
    count = int(request.args.get('count', default=50))
    minScore = int(request.args.get('minScore', default=50))
    
    additionalWhere = ""
    showBlogs = request.args.get('showBlogs', default="true") == "true"
    showSubsites = request.args.get('showSubsites', default="true") == "true"
    showEditorial = request.args.get('showEditorial', default="true") == "true"
    if not showBlogs:
        additionalWhere += " and categories.is_user != 1"
    elif not showSubsites:
        additionalWhere += " and categories.is_user != 0"
    if not showEditorial:
        additionalWhere += " and posts.editorial != true"
    
    try:
        data = app.db.execute_select("""
                select posts.post_id, authors.userid, authors.name, categories.userid, categories.name, posts.name, posts.publication_time, posts.words, posts.media,
                    posts_views.now as views,
                    posts_bookmarks.now as bookmarks,
                    posts_rating.now as rating,
                    posts_comments.now as comments,
                    posts_reposts.now as reposts,
                    posts.score,
                    posts.editorial,
                    categories.is_user
                from posts
                left join categories on posts.cat_id=categories.userid
                left join categories as authors on posts.author_id=authors.userid
                left join posts_views on posts.post_id=posts_views.post_id
                left join posts_bookmarks on posts.post_id=posts_bookmarks.post_id
                left join posts_rating on posts.post_id=posts_rating.post_id
                left join posts_comments on posts.post_id=posts_comments.post_id
                left join posts_reposts on posts.post_id=posts_reposts.post_id
                where posts.score >= %d %s
                order by publication_time desc
                limit %d;
            """ % (minScore, additionalWhere, count), [])
    except:
        return "<h1>Слишком много запросов к базе данных, зайдите через пару минут<h1>"
    

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
        editorial = post[15]
        is_blog = post[16]
        post_class = ""
        
        if editorial:
            post_class = "editorial"
        elif is_blog:
            post_class = "blog"
        else: 
            post_class = "subsite"
            
        if len(post_name) == 0 or post_name == "-":
            post_name = "[Заголовок не указан]"
            
        html.append("<tr>")
        html.append("  <td content='%s' class='post-title %s'><a target='_blank' title='%s' href='https://dtf.ru/%d'>%s</a></td>" % (post_name, post_class, post_name, post_id, post_name))
        html.append("  <td content='%s' class='post-author'><a target='_blank' href='https://dtf.ru/u/%d'>%s</a></td>" % (author_name, author_id, author_name))
        html.append("  <td content='%s' class='post-author'><a target='_blank' href='https://dtf.ru/u/%d'>%s</a></td>" % (cat_name, cat_id, cat_name))
        html.append("  <td content='%d' class='post-time'><span>%s</span></td>" % (publication_time, time.strftime('%H:%M MSK<br>%d.%m.%Y', time.localtime(publication_time + 10800))))
        html.append("  <td content='%d' class='post-number'><span>%d</span></td>" % (score, score))
        html.append("  <td content='%d' class='post-number'><span>%d</span></td>" % (words, words))
        html.append("  <td content='%d' class='post-number'><span>%d</span></td>" % (media, media))
        html.append("  <td content='%d' class='post-number'><span>%d</span></td>" % (rating, rating))
        html.append("  <td content='%d' class='post-number'><span>%d</span></td>" % (views, views))
        html.append("  <td content='%d' class='post-number'><span>%d</span></td>" % (bookmarks, bookmarks))
        html.append("  <td content='%d' class='post-number'><span>%d</span></td>" % (comments, comments))
        html.append("  <td content='%d' class='post-number'><span>%d</span></td>" % (reposts, reposts))
        html.append("</tr>")
    
    return render_template("ratingTable.html",
        ratingRows = "\n".join(html),
        count = count,
        minScore = minScore,
        checkBlogs = "checked" if showBlogs else "",
        checkSubsites = "checked" if showSubsites else "",
        checkEditorial = "checked" if showEditorial else "")

if __name__ == "__main__": 
    app.run() 
