"""
Another simple, alternative way to get basic information about a file of user_ids/sns
"""

import io
import sys
from twitter_dm.TwitterUser import get_user_ids_and_sn_data_from_list
from twitter_dm.utility.general_utils import collect_system_arguments

handles, output_file, data_to_collect, is_ids = collect_system_arguments(sys.argv)

out_fil = io.open(output_file,"w")

user_data = get_user_ids_and_sn_data_from_list(data_to_collect,handles,not is_ids, out_fil)
out_fil.close()