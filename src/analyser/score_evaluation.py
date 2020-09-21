def smooth_progression(x, x_exp, max_exp):
    d = x / x_exp
    return (-1 / pow(5, d*0.14 - 1) + 5) * 0.65 + (x_exp / max_exp) * 0.35

def score_evaluation_full(words, media, views, bookmarks, rating, comments, reposts, category_subs):
    
    category_subs = min(category_subs, 50000)
    category_subs = max(category_subs, 100)

    expected_views = pow(category_subs * 50, 0.5)
    expected_bookmarks = pow(category_subs * 0.01, 0.57)
    expected_likes = pow(category_subs * 3, 0.35)
    expected_comments = pow(category_subs * 3, 0.31)
    expected_reposts = 2
        
    score_parts = [words / 500.0,
                   media / 10.0,
                   smooth_progression(rating, expected_likes, 47),
                   smooth_progression(views, expected_views, 2476),
                   smooth_progression(bookmarks, expected_bookmarks, 34),
                   smooth_progression(comments, expected_comments, 33),
                   smooth_progression(reposts, expected_reposts, 2)]
    score = sum(score_parts)
            
    score = int(score * 10)
    
    return score, score_parts


def score_evaluation(words, media, views, bookmarks, rating, comments, reposts, category_subs):
    
    return score_evaluation_full(words, media, views, bookmarks, rating, comments, reposts, category_subs)[0]


if __name__== "__main__":
    import sys
    print(score_evaluation_full(*[int(i) for i in sys.argv[1:9]]))
    
    # words media rating views bookmarks comments reposts
    #test = {"Богуславкий": [1169, 10, 878, 38323, 540, 593, 2, 115],
    #        "Бэтмен": [4715, 56, 171, 5992, 315, 31, 1, 269966],
    #        "Хасаги": [77, 2, 1, 23, 339, 3, 84, 0, 269],
    #        "ЕлистратовМем": [8, 1, 10, 284, 2, 51, 1, 4],
    #        "Анализатор": [463, 1, 131, 2016, 110, 61, 1, 270000]}
    #for k, v in test.items():
    #    print(k, score_evaluation_full(v[0], v[1], v[3], v[4], v[2], v[5], v[6], v[7]))