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

from twitter_dm.utility.general_utils import mkdir_no_err,collect_system_arguments, chunk_data

handles, output_dir, tweet_ids, is_ids = collect_system_arguments(sys.argv)


# Create the output directory
mkdir_no_err(output_dir)

# chunk tweets into 100s (the API takes them by 100)
i = 0
tweets_chunked = chunk_data(tweet_ids)


print tweets_chunked[0]
# init a sync manager
multiprocess_setup.init_good_sync_manager()

# put data on the queue
request_queue = multiprocess_setup.load_request_queue(tweets_chunked, len(handles))
# run!
processes = []
for i in range(len(handles)):
    p = TweetDataWorker(request_queue,handles[i],i,output_dir)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'



