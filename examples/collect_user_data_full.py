"""This file shows an example of how to use
the UserDataWorker to get information about a bunch of
Twitter users fairly quickly.

Note that the input is expected to be a list of user names, one per line.

If you have user_ids, you can do that too, just change the user_id=False line
when you're creating the workers
"""

__author__ = 'kjoseph'

import glob
import os
import sys

from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.multiprocess.WorkerUserData import UserDataWorker
from datetime import datetime
from twitter_dm.utility.general_utils import mkdir_no_err, collect_system_arguments

(handles, out_dir, user_ids, is_ids,
collect_friends, collect_followers,
gen_tweet_counts_file) = collect_system_arguments(sys.argv,
                                                 ['collect_friends (y/n)',
                                                  'collect_followers (y/n)',
                                                  "gen_tweet_counts_file (y/n)"])


print 'num users: ', len(user_ids)

mkdir_no_err(out_dir)
mkdir_no_err(os.path.join(out_dir, "obj"))
mkdir_no_err(os.path.join(out_dir, "json"))

multiprocess_setup.init_good_sync_manager()

##put data on the queue
request_queue = multiprocess_setup.load_request_queue(user_ids, len(handles))

tweet_count_file_dir = None
if gen_tweet_counts_file == 'y':
    tweet_count_file_dir = "tweet_count" + str(datetime.now()).split(" ")[0]
    mkdir_no_err(os.path.join(out_dir, tweet_count_file_dir))

processes = []
for i in range(len(handles)):
    p = UserDataWorker(request_queue, handles[i], out_dir,
                       always_pickle=True, gets_user_id=is_ids,
                       populate_lists=False, populate_friends=collect_friends == 'y',
                       add_to_file=True,
                       populate_followers=collect_followers == 'y',
                       tweet_count_file_dir=tweet_count_file_dir)
    p.start()
    processes.append(p)

try:
    for p in processes:
        print p.join(100000000)
except KeyboardInterrupt:
    print 'keyboard interrupt'

if gen_tweet_counts_file:
    for p in processes:
        p.tweet_count_file.close()