"""
This file shows an example of how to use twitter_dm to  "hydrate" tweet IDs very quickly.
"""
__author__ = 'kjoseph'

import gzip
import os

from twitter_dm.TwitterAPIHook import TwitterAPIHook
# replace ujson with some other json tool if you dont have/like ujson
import ujson as json
import io

consumer_key = "YOUR_CONSUMER_KEY_HERE"
consumer_secret = "YOUR_CONSUMER_SECRET_HERE"
access_token = "YOUR_ACCESS_TOKEN_HERE"
access_token_secret = "YOUR_ACCESS_TOKEN_SECRET_HERE"
path_to_gzipped_tweet_id_file = "PATH_TO_TWEET_ID_FILE (Still Gzipped)"
output_directory = "PATH_TO_OUTPUT_DIRECTORY"

## get a "hook", or connection, to the API using your consumer key/secret and access token/secret
api_hook = TwitterAPIHook(consumer_key,consumer_secret,
                          access_token=access_token,
                          access_token_secret=access_token_secret)

try:
    os.mkdir(output_directory)
except:
    print 'output directory already exists'

# get tweet ids to hydrate
if path_to_gzipped_tweet_id_file.endswith(".gz"):
    tweet_id_file = gzip.open(path_to_gzipped_tweet_id_file)
else:
    tweet_id_file = open(path_to_gzipped_tweet_id_file)

ids_to_get = []
outfile_counter = 0
# This code will write out tweets in batches of 100K. If your script gets interrupted,
# you can just restart from the beginning, skipping 10K*number of output files in the output directory
for line in tweet_id_file:
    ids_to_get.append(line.strip())
    if len(ids_to_get)  == 100:
        tweet_data = api_hook.get_from_url("statuses/lookup.json", {"id": ",".join(ids_to_get)})
        outfile = io.open(os.path.join(output_directory,str(outfile_counter)+".json"),"w")
        for tw in tweet_data:
            outfile.write(json.dumps(tw)+"\n")
        outfile.close()
