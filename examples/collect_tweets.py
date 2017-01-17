"""
This file shows an example of how to use the TweetDataWorker to "hydrate"
a whole bunch of tweet IDs very quickly.


"""
__author__ = 'kjoseph'

import glob
import os
import sys
from multiprocessing import Queue

from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.multiprocess.WorkerTweetData import TweetDataWorker
from twitter_dm.utility import general_utils

# read in system arguments
if len(sys.argv) != 4:
    print 'usage:  [known_user_dir] [output_dir] [tweet_id_file]'
    sys.exit(-1)

# get handles to the twitter api
handles = general_utils.get_handles(glob.glob(sys.argv[1]+"*.txt"))
print 'n authed users: ', len(handles)


# get tweet ids to hydrate
f = open(sys.argv[3])
tweet_ids = []
for line in f:
    line_spl = line.strip().split("\t")
    tweet_ids.append(line_spl[1])
    print line_spl[1]
tweet_ids = [t for t in set(tweet_ids)]
f.close()
print 'num tweets: ', len(tweet_ids)

# Create the output directory
out_dir = sys.argv[2]
try:
    os.mkdir(out_dir)
except:
    pass

# chunk tweets into 100s (the API takes them by 100)
i = 0
tweets_chunked = []
while i < len(tweet_ids):
    tweets_chunked.append(tweet_ids[i:(i+100)])
    i += 100

tweets_chunked.append(tweet_ids[i-100:len(tweet_ids)])
# init a sync manager
multiprocess_setup.init_good_sync_manager()

# put data on the queue
request_queue = Queue()

for tweet_chunk in tweets_chunked:
    request_queue.put( tweet_chunk )

# Sentinel objects to allow clean shutdown: 1 per worker.
for i in range(len(handles)):
    request_queue.put(None)

# run!
processes = []
for i in range(len(handles)):
    p = TweetDataWorker(request_queue,handles[i],i,out_dir)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'



