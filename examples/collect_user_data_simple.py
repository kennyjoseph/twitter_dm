"""
An example of how to use a UserSimpleDataWorker to collect basic information about users,
and then to see if users have been suspended/deleted from that.

Basically, we don't get information back from the API if these users have been suspended/deleted, so
we can learn from that information
"""
__author__ = 'kjoseph'

import glob
import sys

from twitter_dm import TwitterApplicationHandler
from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.multiprocess.WorkerSimpleUserLookup import SimpleUserLookupWorker
from twitter_dm.utility import general_utils

if len(sys.argv) != 4:
    print 'usage:  [known_user_dir] [user_ids] [out_dir]'
    sys.exit(-1)

handles =[]
for fil in glob.glob(sys.argv[1]+"/*.txt"):
    print 'FIL: ' , fil
    app_handler = TwitterApplicationHandler(pathToConfigFile=fil)
    handles += app_handler.api_hooks

print 'n authed users: ', len(handles)

user_ids = set([line.strip().lower() for line in open(sys.argv[2]).readlines()])
out_dir = sys.argv[3]
general_utils.mkdir_no_err(out_dir)

print "N TO FIND: ", len(user_ids)

user_ids = [u for u in user_ids]

user_data_chunked = []
i=0
while i < len(user_ids):
    user_data_chunked.append(user_ids[i:(i+100)])
    i += 100

user_data_chunked.append(user_ids[i-100:len(user_ids)])

print 'len chunked: ', len(user_data_chunked)

multiprocess_setup.init_good_sync_manager()

##put data on the queue
request_queue = multiprocess_setup.load_request_queue([x for x in user_data_chunked], len(handles), add_nones=True)

processes = []
for i in range(len(handles)):
    p = SimpleUserLookupWorker(request_queue,handles[i],i, out_dir)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'

