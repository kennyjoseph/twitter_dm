import glob
import os
import sys
from time import sleep
import io

from twitter_dm.utility.general_utils import mkdir_no_err,collect_system_arguments

handles, output_dir, data_to_collect, is_ids, friends_or_followers = collect_system_arguments(sys.argv,
                                                                                           ['friends or followers'])

# in case its weird format
accounts = [x.strip().split()[-1] for x in data_to_collect]

mkdir_no_err(output_dir)

handle_iter = 0

param_arg = 'user_id' if is_ids else 'screen_name'

for i, handle in enumerate(accounts):
    print('user: ', i,  handle)

    if os.path.exists(os.path.join(output_dir,handle)):
        continue

    of = open(os.path.join(output_dir,handle),"w")

    params = {param_arg: handle, 'cursor': -1, 'count': 5000}

    n_collected = 0

    while True:
        print("\t\t", n_collected, n_collected, handle_iter)

        if handle_iter == len(handles):
            print(' sleeping now')
            sleep(120)
            handle_iter = 0


        handle = handles[handle_iter]
        print(handle.CONSUMER_KEY, handle.access_token)
        try:
            json_data = handle.get_from_url(friends_or_followers + "/ids.json",params)
        except ValueError as e:
            print(e)
            handle_iter += 1
            continue

        handle_iter += 1

        if json_data is None or not len(json_data):
            print(json_data is None)
            break

        n_collected += len(json_data.get("ids",[]))
        [of.write(str(x)+"\n") for x in json_data.get("ids",[])]

        if json_data['next_cursor'] == 0:
            break
        params['cursor'] = json_data['next_cursor']

    of.close()
