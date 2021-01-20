"""
An example of how to use a UserSimpleDataWorker to collect basic information about users,
and then to see if users have been suspended/deleted from that.

Basically, we don't get information back from the API if these users have been suspended/deleted, so
we can learn from that information
"""
__author__ = 'kjoseph'

import glob
import sys

from twitter_dm.utility.general_utils import collect_system_arguments, chunk_data
from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.multiprocess.WorkerSimpleUserLookup import SimpleUserLookupWorker
from twitter_dm.utility import general_utils

import multiprocessing as mp
if __name__ == '__main__':
	mp.set_start_method("spawn")
	handles, out_dir, data_to_collect, is_ids = collect_system_arguments(sys.argv)

	general_utils.mkdir_no_err(out_dir)

	user_data_chunked = chunk_data(data_to_collect)
	print('len chunked: ', len(user_data_chunked))

	# initialize a better sync manager
	#multiprocess_setup.init_good_sync_manager()

	# put data on the queue
	request_queue = multiprocess_setup.load_request_queue(
		[x for x in user_data_chunked], len(handles), add_nones=True)

	processes = []
	for i in range(len(handles)):
	    p = SimpleUserLookupWorker(request_queue,handles[i],i, out_dir,gets_user_id=is_ids)
	    p.start()
	    processes.append(p)

	try:
	    for p in processes:
	        p.join()
	except KeyboardInterrupt:
	    print('keyboard interrupt')

