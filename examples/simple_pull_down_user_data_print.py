"""
This is the most basic script for using twitter_dm.

From here, you may want to go look at some of the more complex examples
that leverage the library's NLP/rapid collection tools, as this is basically
a replication of tweepy with less documentation :)
"""
from twitter_dm.TwitterAPIHook import TwitterAPIHook
from twitter_dm.TwitterUser import TwitterUser

username_to_collect_data_for = 'Jackie_Pooo'

consumer_key = "YOUR_CONSUMER_KEY_HERE"
consumer_secret = "YOUR_CONSUMER_SECRET_HERE"
access_token = "YOUR_ACCESS_TOKEN_HERE"
access_token_secret = "YOUR_ACCESS_TOKEN_SECRET_HERE"

## get a "hook", or connection, to the API using your consumer key/secret and access token/secret
api_hook = TwitterAPIHook(consumer_key,consumer_secret,
                          access_token=access_token,access_token_secret=access_token_secret)

#creates a Twitter User object to fill with information from the API
user = TwitterUser(api_hook,screen_name=username_to_collect_data_for)


# we call populate_tweets_from_api,which goes to the Twitter API
# and collects the user's data it is outputted to the file username_you_put.json
# the sleep_var param tells the function it shouldn't worry
# about rate limits (we're only collecting for one user, so it doesn't really matter
# If you remove the is_gzip argument, the output file will be gzipped
print('populating users tweets!')
user.populate_tweets_from_api(json_output_filename=username_to_collect_data_for+".json",
                              sleep_var=False, is_gzip=False, since_id=None)


for t in user.tweets:
    print(t.mentions)
print('user had {n_tweets} tweets'.format(n_tweets=len(user.tweets)))


