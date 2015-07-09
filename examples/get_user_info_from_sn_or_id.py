"""
Another simple, alternative way to get basic information about a file of user_ids/sns
"""

import os, sys, glob
from twitter_dm.utility import general_utils
from twitter_dm.TwitterUser import get_user_ids_and_sn_data_from_list


if len(sys.argv) != 5:
    print 'usage:  [known_user_dir]  [user_id_filename] [output_filename] [do_user_id (y if sns, n if user_ids]'
    sys.exit(-1)


handles = general_utils.get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))
print 'n authed users: ', len(handles)

data = [f.strip() for f in open(sys.argv[2]).readlines()]

print 'N USERS: ', len(data)
print data[0:10]

user_data = get_user_ids_and_sn_data_from_list(data,handles,sys.argv[4] == 'y', sys.argv[3])
print user_data