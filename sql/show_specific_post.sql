select posts.post_id, categories.name, posts.name, posts.publication_time, posts.words, posts.media,
                posts_views.now as views, posts_bookmarks.now as bookmarks, posts_rating.now as rating, posts_comments.now as comments, posts_reposts.now as reposts, categories.subscribers, posts.score
                from posts
                left join categories on posts.cat_id=categories.userid
                left join posts_views on posts.post_id=posts_views.post_id
                left join posts_bookmarks on posts.post_id=posts_bookmarks.post_id
                left join posts_rating on posts.post_id=posts_rating.post_id
                left join posts_comments on posts.post_id=posts_comments.post_id
                left join posts_reposts on posts.post_id=posts_reposts.post_id
                where posts.post_id=212058;