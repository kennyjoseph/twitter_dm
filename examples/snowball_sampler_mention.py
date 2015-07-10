"""
An example of how to use the TwitterFollowingNetworkWorker to perform a snowball sampling
"""
import glob,sys, os
from twitter_dm.multiprocess.WorkerTwitterMentionEgoNetwork import TwitterMentionEgoNetwork
from twitter_dm.utility import general_utils
from twitter_dm.TwitterUser import get_user_ids_and_sn_data_from_list
from twitter_dm.multiprocess import multiprocess_setup


sys.argv = ['', '/Users/kjoseph/git/thesis/thesis_python/twitter_login_creds',
            'blah','2','f.txt']

if len(sys.argv) != 5:
    print 'usage:  [known_user_dir] [output_dir][step_count] [seed_agent_file]'
    sys.exit(-1)

OUTPUT_DIRECTORY = sys.argv[2]

# get all the handles we have to the api
handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))

handles = handles[0:3]
print 'n authed users: ', len(handles)

step_count = int(sys.argv[3])

# user screen names we are interested in
user_sns = ['coalitionfd','InfoResist_EN','InfoResist','MusuLatvija','SpecGhost','NATOlizer','Stormtroepen']

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
    p = TwitterMentionEgoNetwork(request_queue,handles[i],network_dir,pickle_dir,step_count)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'

