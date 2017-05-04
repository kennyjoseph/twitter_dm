import glob
import os
import sys
from time import sleep

import pandas as pd

from twitter_dm.utility.general_utils import mkdir_no_err,get_handles

accounts = ['potus','potus44','flotus','flotus44']

# get handles to the twitter api
handles = get_handles(glob.glob(sys.argv[1]+"*"))
print 'n authed users: ', len(handles)

output_dir = sys.argv[2]
mkdir_no_err(output_dir)


handle_iter = 0

for i, handle in enumerate(accounts):
    print 'user: ', i,  handle

    if os.path.exists(os.path.join(output_dir,handle)):
        continue

    of = open(os.path.join(output_dir,handle),"w")

    params = {'screen_name': handle,
              'cursor' : -1,
              'count' : 5000}

    n_collected = 0

    while True:
        print "\t\t", n_collected, n_collected, handle_iter

        handle = handles[handle_iter]
        api_data = handle.get_from_url("followers/ids.json",params)
        handle_iter += 1

        if api_data is None:
            break

        json_data = api_data.json()
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