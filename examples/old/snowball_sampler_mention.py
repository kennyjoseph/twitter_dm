"""
An example of how to use the TwitterFollowingNetworkWorker to perform a snowball sampling
"""
__author__ = 'mbenigni'

import glob
import os
import sys

from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.utility import general_utils

if len(sys.argv) != 5:
    print 'usage:  [known_user_dir] [output_dir] [seed_agent_file] [step_count] '
    sys.exit(-1)


handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))
print 'n authed users: ', len(handles)

out_dir = sys.argv[2]
step_count=int(sys.argv[4])

user_ids = [line.strip().split(",")[0] for line in open(sys.argv[3]).readlines()]

print 'num users: ', len(user_ids)

general_utils.mkdir_no_err(out_dir)
general_utils.mkdir_no_err(os.path.join(out_dir,"obj"))
general_utils.mkdir_no_err(os.path.join(out_dir,"json"))
multiprocess_setup.init_good_sync_manager()

# put data on the queue
request_queue = multiprocess_setup.load_request_queue([(x[1],0) for x in user_screenname_id_pairs], len(handles), add_nones=False)

processes = []
for i in range(len(handles)):
    p = TwitterMentionEgoNetwork(request_queue,handles[i],network_dir,pickle_dir,step_count)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'

