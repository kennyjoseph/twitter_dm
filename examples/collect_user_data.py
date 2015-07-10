"""This file shows an example of how to use
the UserDataWorker to get information about a bunch of
Twitter users fairly quickly.

Note that the input is expected to be a list of user names, one per line.

If you have user_ids, you can do that too, just change the user_id=False line
when you're creating the workers
"""

__author__ = 'kjoseph'

import os, sys, glob
from twitter_dm.multiprocess.WorkerUserTweetData import UserDataWorker
from twitter_dm.utility import general_utils
from twitter_dm.multiprocess import multiprocess_setup


if len(sys.argv) != 4:
    print 'usage:  [known_user_dir] [output_dir] [tweet_id_file]'
    sys.exit(-1)

handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))
print 'n authed users: ', len(handles)

out_dir = sys.argv[2]

user_ids = [line.strip().split(",")[0] for line in open(sys.argv[3]).readlines()]

print 'num users: ', len(user_ids)

general_utils.mkdir_no_err(out_dir)
general_utils.mkdir_no_err(os.path.join(out_dir,"obj"))
general_utils.mkdir_no_err(os.path.join(out_dir,"json"))
multiprocess_setup.init_good_sync_manager()

#already_done = set([os.path.basename(f) for f in glob.glob(out_dir+"/*")])
print 'len already done:', 0
#user_screennames = [u for u in user_screennames if u not in already_done]

##put data on the queue
request_queue = general_utils.load_request_queue(user_ids, len(handles))

processes = []
for i in range(1):
    p = UserDataWorker( request_queue,handles[i],i,out_dir,
                        to_pickle=True,gets_user_id=False,
                        populate_lists=False,populate_friends_and_followers=True)
    p.start()
    processes.append(p)

try:
    for p in processes:
        print p.join(100000000)
except KeyboardInterrupt:
    print 'keyboard interrupt'



