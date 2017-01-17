from twitter_dm.TwitterUser import TwitterUser

u = TwitterUser()
u.populate_tweets_from_file("_kenny_joseph.json")

for t in u.tweets:
    print t.tokens