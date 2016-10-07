"""
An example of how to use the TwitterFollowingNetworkWorker to perform a snowball sampling
"""
import glob
import os
import sys

from twitter_dm.multiprocess.old.WorkerTwitterFollowerEgoNetwork import TwitterFollowingNetworkWorker

from twitter_dm.TwitterUser import get_user_ids_and_sn_data_from_list
from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.utility import general_utils

if len(sys.argv) != 4:
    print 'usage:  [known_user_dir] [output_dir] [user_sn_file]'
    sys.exit(-1)

OUTPUT_DIRECTORY = sys.argv[2]

# get all the handles we have to the api
handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))
handles = handles[:5]
print 'n authed users: ', len(handles)

# user screen names we are interested in
user_sns = ['Khalid_Maqdisi','SaqrAnsaar','AbuSiqr','JabhtAnNusrah_s','ShamiWitness']

# Get a bit more data on users
user_screenname_id_pairs = get_user_ids_and_sn_data_from_list(user_sns,handles,True)
print 'got screen names, ', len(user_screenname_id_pairs)

pickle_dir = OUTPUT_DIRECTORY +"/obj/"
network_dir = OUTPUT_DIRECTORY+"/net/" # what does the network directory do for me?

general_utils.mkdir_no_err(OUTPUT_DIRECTORY)
general_utils.mkdir_no_err(pickle_dir)
general_utils.mkdir_no_err(network_dir)

multiprocess_setup.init_good_sync_manager()

# put data on the queue
request_queue = multiprocess_setup.load_request_queue([(x[1],0) for x in user_screenname_id_pairs], len(handles), add_nones=False)

processes = []
for i in range(len(handles)):
    p = TwitterFollowingNetworkWorker(request_queue,handles[i],network_dir,pickle_dir)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'
