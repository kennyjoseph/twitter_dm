from twitter_dm.TwitterUser import TwitterUser
import datetime
from time import mktime
u = TwitterUser()
u.populate_tweets_from_file("/Users/kennyjoseph/git/thesis/twitter_dm/examples/2431225676.json.gz")

for t in u.tweets:
    print mktime(t.created_at.timetuple())