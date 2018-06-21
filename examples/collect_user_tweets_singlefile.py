"""This file shows how to collect tweets for users in a format suitable for both backing up and
to put onto spark (bz2)

"""

__author__ = 'kjoseph'

import os
import sys

from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.multiprocess.WorkerUserBigFiles import BigFileUserDataWorker
from datetime import datetime
from twitter_dm.utility.general_utils import mkdir_no_err, collect_system_arguments
from glob import glob

(handles, out_dir, user_ids, is_ids,
full_sinceid_output_filename,
 gen_tweet_counts_file) = collect_system_arguments(sys.argv, ["full_sinceid_output_filename",
                                                             "gen_tweet_counts_file (y/n)"])

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

print 'num users: ', len(user_ids)

try:
    os.mkdir(out_dir)
except:
    print 'output directory already exists, not going to overwrite, exiting'
    sys.exit(-1)
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


with open(full_sinceid_output_filename,"w") as of:
    for fil in glob(os.path.join(out_dir,"sinceid","*")):
        for line in open(fil):
            of.write(line)
