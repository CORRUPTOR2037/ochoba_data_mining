def score_evaluation(words, media, views, bookmarks, rating, comments, reposts, category_subs):
    
    category_subs = min(category_subs, 50000)
    category_subs = max(category_subs, 25)

    expected_views = pow(category_subs * 2.3, 0.71)
    expected_likes = pow(category_subs * 3.5, 0.38)
    expected_bookmarks = pow(category_subs * 3.5, 0.38)
    expected_comments = pow(category_subs * 3.5, 0.38)
    expected_reposts = 2
        
    score = (words / 500.0 +
            media / 10.0 +
            views / expected_views +
            bookmarks / expected_bookmarks +
            rating / expected_likes +
            comments / expected_comments +
            reposts / expected_reposts)
    score = int(score * 10)
    
    return score

if __name__== "__main__":
    import sys
    
    print(score_evaluation(*[int(i) for i in sys.argv[1:9]]))