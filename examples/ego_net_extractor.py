import glob,sys, os
from twitter_dm.utility import general_utils
from twitter_dm.multiprocess.WorkerTwitterEgoNetwork import TwitterEgoNetworkWorker
from twitter_dm.multiprocess import multiprocess_setup

if len(sys.argv) != 4:
    print 'usage:  [login_credentials_directory] [output_dir] [user_sn_file]'
    sys.exit(-1)

OUTPUT_DIRECTORY = sys.argv[2]

##get all the handles we have to the api
handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))

print 'n authed users: ', len(handles)

#user screen names we are interested in
user_screenname_id_pairs = [line.strip().split("\t") for line in open(sys.argv[3]).readlines()]

print user_screenname_id_pairs[0]

pickle_dir = OUTPUT_DIRECTORY +"/obj/"
network_dir = OUTPUT_DIRECTORY+"/net/"

general_utils.mkdir_no_err(OUTPUT_DIRECTORY)
general_utils.mkdir_no_err(pickle_dir)
general_utils.mkdir_no_err(network_dir)

multiprocess_setup.init_good_sync_manager()

##put data on the queue
request_queue = general_utils.load_request_queue(user_screenname_id_pairs, len(handles))

processes = []
for i in range(len(handles)):
    p = TwitterEgoNetworkWorker(request_queue, handles[i], network_dir, pickle_dir)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'




