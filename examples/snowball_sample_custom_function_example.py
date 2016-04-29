"""
An example of how to use the TwitterFollowingNetworkWorker to perform a snowball sampling
"""
import glob
import os
import sys

from twitter_dm.multiprocess.WorkerUserData import UserDataWorker
from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.utility import general_utils
from twitter_dm.TwitterUser import get_user_ids_and_sn_data_from_list


#sys.argv = ['', '/Users/kennyjoseph/git/thesis/thesis_python/twitter_login_creds',
#            'out_here', '1']
if len(sys.argv) != 5:
    print 'usage:  [known_user_dir] [output_dir][step_count][friends or mentions]'
    sys.exit(-1)

OUTPUT_DIRECTORY = sys.argv[2]
step_count = int(sys.argv[3])

# get all the handles we have to the api
handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))

print len(handles)
print 'n authed users: ', len(handles)


# user screen names we are interested in
user_sns = ['ManchesterMJC','Aviationeuro','SanteriSanttus','OneworldLover',
            'ENORsquawker','plane_spotters','MANSpotter99','BennyPlanespot','PlanespotterGuy','planespotterWal']

user_screenname_id_pairs = get_user_ids_and_sn_data_from_list(user_sns,handles,True)
print 'got screen names, ', len(user_screenname_id_pairs)

# put data on the queue
request_queue = multiprocess_setup.load_request_queue(
         [(x[1],0) for x in user_screenname_id_pairs], len(handles), add_nones=False)

pickle_dir = OUTPUT_DIRECTORY +"/obj/"
network_dir = OUTPUT_DIRECTORY+"/json/"

general_utils.mkdir_no_err(OUTPUT_DIRECTORY)
general_utils.mkdir_no_err(pickle_dir)
general_utils.mkdir_no_err(network_dir)

multiprocess_setup.init_good_sync_manager()

# put data on the queue
user_screenname_id_pairs = get_user_ids_and_sn_data_from_list(user_sns,handles,True)
print 'got screen names, ', len(user_screenname_id_pairs)

# put data on the queue
request_queue = multiprocess_setup.load_request_queue(
[(x[1],0) for x in user_screenname_id_pairs], len(handles), add_nones=False)

processes = []

def get_mentions_2012(user):
    sns_mentioned = set()
    for t in user.tweets:
        if t.created_at.year > 2012:
            for m in t.mentions:
                sns_mentioned.add(m)
    return sns_mentioned

def get_friends(user):
    sns_list = set()
    for f in user.friend_ids:
        sns_list.add(f)
    return sns_list

if sys.argv[4] == 'mentions':
    snowball_func = get_mentions_2012
else:
    snowball_func = get_friends


processes = []
for h in handles:

    p = UserDataWorker(queue=request_queue,
                       api_hook=h,
                       out_dir=OUTPUT_DIRECTORY,
                       step_count=step_count,
                       populate_friends=True,
                       gets_user_id=True,
                       populate_followers=False,
                       add_users_to_queue_function= snowball_func)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'

