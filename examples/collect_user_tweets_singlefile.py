"""This file shows an example of how to use
the UserDataWorker to get information about a bunch of
Twitter users fairly quickly.

Note that the input is expected to be a list of user names, one per line.

If you have user_ids, you can do that too, just change the user_id=False line
when you're creating the workers
"""

__author__ = 'kjoseph'

import os
import sys

from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.multiprocess.WorkerUserBigFiles import BigFileUserDataWorker
from datetime import datetime
from twitter_dm.utility.general_utils import mkdir_no_err, collect_system_arguments

(handles, out_dir, user_ids, is_ids,
gen_tweet_counts_file) = collect_system_arguments(sys.argv, ["gen_tweet_counts_file (y/n)"])

# messes up the user id processing thing so we have to redo
is_ids = True
to_pass = []
for x in user_ids:
    spl = x.split("\t")
    try:
        if len(spl) == 1:
            to_pass.append((int(spl[0]), ''))
        else:
            to_pass.append((int(spl[0]), spl[1]))
    except:
        pass

handles = handles[:3]
print 'num users: ', len(user_ids)


mkdir_no_err(out_dir)
mkdir_no_err(os.path.join(out_dir, "json"))
mkdir_no_err(os.path.join(out_dir, "sinceid"))

multiprocess_setup.init_good_sync_manager()

##put data on the queue
request_queue = multiprocess_setup.load_request_queue(to_pass, len(handles))

tweet_count_file_dir = None
if gen_tweet_counts_file == 'y':
    tweet_count_file_dir = "tweet_count" + str(datetime.now()).split(" ")[0]
    mkdir_no_err(os.path.join(out_dir, tweet_count_file_dir))

processes = []
for i in range(len(handles)):
    p = BigFileUserDataWorker(request_queue,
                              handles[i],
                              out_dir,
                              gets_user_id=is_ids,
                              tweet_count_file_dir=tweet_count_file_dir)

    p.start()
    processes.append(p)

try:
    for p in processes:
        print p.join(100000000)
except KeyboardInterrupt:
    print 'keyboard interrupt'
