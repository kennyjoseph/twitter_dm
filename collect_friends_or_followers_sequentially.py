import glob
import os
import sys
from time import sleep
import io
import pandas as pd

from twitter_dm.utility.general_utils import mkdir_no_err,get_handles


if len(sys.argv) != 5:
    print 'Usage: collect_followers_sequentially.py [handles_path] [output_dir] "\
          " [infil] [screen_name or user_id] [friends or followers]'

accounts = [x.strip().split()[-1] for x in io.open(sys.argv[3])]
# get handles to the twitter api
handles = get_handles(glob.glob(sys.argv[1]+"*.txt"))
print 'n authed users: ', len(handles)

output_dir = sys.argv[2]
mkdir_no_err(output_dir)


handle_iter = 0

for i, handle in enumerate(accounts):
    print 'user: ', i,  handle

    if os.path.exists(os.path.join(output_dir,handle)):
        continue

    of = open(os.path.join(output_dir,handle),"w")

    params = {sys.argv[4]: handle,
              'cursor' : -1,
              'count' : 5000}

    n_collected = 0

    while True:
        print "\t\t", n_collected, n_collected, handle_iter

        if handle_iter == len(handles):
            print ' sleeping now'
            sleep(60)
            handle_iter = 0
            
        handle = handles[handle_iter]
        json_data = handle.get_from_url(sys.argv[5] + "/ids.json",params)
        handle_iter += 1

        if json_data is None or not len(json_data):
            break

        n_collected += len(json_data.get("ids",[]))
        [of.write(str(x)+"\n") for x in json_data.get("ids",[])]

        if json_data['next_cursor'] == 0:
            break
        params['cursor'] = json_data['next_cursor']

        if handle_iter == len(handles):
            print ' sleeping now'
            sleep(60)
            handle_iter = 0

    of.close()