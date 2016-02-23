"""
An example of how to use the TwitterFollowingNetworkWorker to perform a snowball sampling
"""
import glob
import os
import sys

from twitter_dm.multiprocess.WorkerUserData import UserDataWorker

from twitter_dm.TwitterUser import get_user_ids_and_sn_data_from_list
from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.utility import general_utils

#sys.argv = ['', '/Users/kennyjoseph/git/thesis/thesis_python/twitter_login_creds',
#            'out_here', '1']
if len(sys.argv) != 4:
    print 'usage:  [known_user_dir] [output_dir][step_count]'
    sys.exit(-1)

OUTPUT_DIRECTORY = sys.argv[2]

# get all the handles we have to the api
handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))

print len(handles)
print 'n authed users: ', len(handles)

step_count = int(sys.argv[3])

# user screen names we are interested in
user_sns = ['ManchesterMJC','Aviationeuro','superD99bc','DLplanespotter','SanteriSanttus','OneworldLover',
            'ENORsquawker','plane_spotters','MANSpotter99','Planespotting12','PercyPlanespot1','BennyPlanespot']

pickle_dir = OUTPUT_DIRECTORY +"/obj/"
network_dir = OUTPUT_DIRECTORY+"/json/" # what does the network directory do for me?

general_utils.mkdir_no_err(OUTPUT_DIRECTORY)
general_utils.mkdir_no_err(pickle_dir)
general_utils.mkdir_no_err(network_dir)

multiprocess_setup.init_good_sync_manager()

# put data on the queue
request_queue = multiprocess_setup.load_request_queue(
        [(x,0) for x in user_sns], len(handles), add_nones=False)

processes = []

def get_mentions_2012(user):
    sns_mentioned = set()
    for t in user.tweets:
        if t.created_at.year > 2012:
            for m in t.mentions_sns:
                sns_mentioned.add(m)
    return sns_mentioned


for h in handles:

    p = UserDataWorker(queue=request_queue,
                       api_hook=h,
                       out_dir=OUTPUT_DIRECTORY,
                       gets_user_id=False,
                       step_count=1,
                       add_users_to_queue_function=get_mentions_2012)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'

