"""
An example of how to use BotOMeter in parallel
"""
__author__ = 'kjoseph'

import glob
import sys

from twitter_dm.utility.general_utils import collect_system_arguments
from twitter_dm.multiprocess import multiprocess_setup
from twitter_dm.multiprocess.WorkerBotOMeter import BotOMeterWorker
from twitter_dm.utility import general_utils

handles, out_dir, data_to_collect, is_ids, mashape_key = collect_system_arguments(sys.argv, ['mashape_key'])

general_utils.mkdir_no_err(out_dir)

# initialize a better sync manager
multiprocess_setup.init_good_sync_manager()

# put data on the queue
request_queue = multiprocess_setup.load_request_queue([x.strip() for x in data_to_collect], len(handles), add_nones=True)

processes = []
for i in range(len(handles)):
    p = BotOMeterWorker(request_queue,handles[i],i, out_dir,mashape_key)
    p.start()
    processes.append(p)

try:
    for p in processes:
        p.join()
except KeyboardInterrupt:
    print 'keyboard interrupt'

