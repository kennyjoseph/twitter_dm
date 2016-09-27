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

from twitter_dm.multiprocess.WorkerUserData import UserDataWorker

from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.utility import general_utils

if len(sys.argv) != 4:
    print 'usage:  [twitter_login_credentials_dir] [output_dir] [tweet_id_file]'
    sys.exit(-1)

handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))
print 'n authed connections to the Twitter API: ', len(handles)

out_dir = sys.argv[2]

user_id_and_max_id = []
for line in open(sys.argv[3]).readlines():
    line_spl = line.strip().split(",")
    if line_spl[1] == 'None':
        continue
    user_id_and_max_id.append((line_spl[0],line_spl[1]))

print 'num users: ', len(user_id_and_max_id)

general_utils.mkdir_no_err(out_dir)
general_utils.mkdir_no_err(os.path.join(out_dir,"obj"))
general_utils.mkdir_no_err(os.path.join(out_dir,"json"))
multiprocess_setup.init_good_sync_manager()

##put data on the queue
request_queue = multiprocess_setup.load_request_queue(user_id_and_max_id, len(handles))

processes = []
for i in range(len(handles)):
    p = UserDataWorker(request_queue,handles[i],out_dir,
                        always_pickle=True,
                        gets_user_id=False,
                        populate_lists=False,
                        populate_friends=True,
                        populate_followers=True,
                        gets_max_tweet_id=True)
    p.start()
    processes.append(p)

try:
    for p in processes:
        print p.join(100000000)
except KeyboardInterrupt:
    print 'keyboard interrupt'



