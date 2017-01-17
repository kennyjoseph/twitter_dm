import glob
import os
import sys
from time import sleep

import pandas as pd

from twitter_dm.utility.general_utils import mkdir_no_err,get_handles

# get handles to the twitter api
handles = get_handles(glob.glob("/Users/kennyjoseph/git/lazerlab/twitter_login_creds/*.txt"))
print 'n authed users: ', len(handles)

d = pd.read_csv("all_users_of_interest_data.tsv",
                header=None,sep="\t")
d.columns = ['sn','id_str','statuses','followers','following','listed']

output_dir = sys.argv[2]
mkdir_no_err(output_dir)


handle_iter = 0

for i, irow in enumerate(d.iterrows()):
    u_count, user_row = irow
    user_id = user_row['id_str']
    n_followers = float(user_row['followers'])

    print 'user: ', i,  user_id, user_row['sn']
    print '\tn_followers: ', n_followers

    if os.path.exists(os.path.join(output_dir,user_id)):
        continue

    of = open(os.path.join(output_dir,user_id),"w")

    params = {'user_id': user_id,
              'cursor' : -1,
              'count' : 5000}

    n_collected = 0

    while True:
        print "\t\t", n_collected, n_collected/n_followers, handle_iter

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