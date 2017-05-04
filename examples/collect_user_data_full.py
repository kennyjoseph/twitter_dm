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
from twitter_dm.utility import general_utils


from twitter_dm.utility.general_utils import mkdir_no_err,collect_system_arguments

handles, out_dir, user_ids, is_ids = collect_system_arguments(sys.argv)

print 'num users: ', len(user_ids)

mkdir_no_err(out_dir)
mkdir_no_err(os.path.join(out_dir,"obj"))
mkdir_no_err(os.path.join(out_dir,"json"))

multiprocess_setup.init_good_sync_manager()

##put data on the queue
request_queue = multiprocess_setup.load_request_queue(user_ids, len(handles))

processes = []
for i in range(len(handles)):
    p = UserDataWorker(request_queue,handles[i],out_dir,
                        always_pickle=True,gets_user_id=False,
                        populate_lists=False,populate_friends=True,
                        populate_followers=True)
    p.start()
    processes.append(p)

try:
    for p in processes:
        print p.join(100000000)
except KeyboardInterrupt:
    print 'keyboard interrupt'



