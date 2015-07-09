"""An example of how to load in a set of user ids, get their tweets and
create a mention network between them and a network of the hashtags they used
"""

__author__ = 'kjoseph'

import os, sys, glob, codecs
from twitter_dm import TwitterUser
from twitter_dm.utility.general_utils import get_handles

sys.argv = ['',
            '/Users/kjoseph/git/thesis/thesis_python/twitter_login_creds',
            '/Users/kjoseph/Desktop/for_jon/data',
           '/Users/kjoseph/Desktop/for_jon/real_user.csv']

print sys.argv

if len(sys.argv) != 4:
    print 'usage:  [known_user_dir] [output_dir] [user_id_file]'
    sys.exit(-1)

handles = get_handles(glob.glob(os.path.join(sys.argv[1],"*.txt")))
print 'n authed users: ', len(handles)

out_dir = sys.argv[2]

user_ids = [line.strip().split(",")[0] for line in open(sys.argv[3]).readlines()]

print 'num users: ', len(user_ids)

net_out = codecs.open("mention_net.csv","w","utf8")
net_out.write("sender,mentioned,date\n")
ht_out = codecs.open("ht_net.csv","w","utf8")
ht_out.write("user,hashtag,date\n")
att_out = codecs.open("att_net.csv","w","utf8")
att_out.write("user,user_name,times_listed,n_followers,n_following\n")
for i in range(len(user_ids)):
    user = TwitterUser(handles[i], screen_name=user_ids[i])
    user.populate_tweets_from_api(sleep_var=False)
    print user.screen_name
    for t in user.tweets:
        datetime = t.created_at.strftime("%Y-%m-%d")
        for m in t.mentions_sns:
            net_out.write(",".join([user.screen_name, m, datetime])+"\n")
        for h in t.hashtags:
            ht_out.write(",".join([user.screen_name,h,datetime])+"\n")
    try:
        att_out.write(",".join([user.screen_name,user.name,str(user.times_listed),str(user.followers_count),str(user.following_count)])+"\n")
    except:
        pass
net_out.close()
ht_out.close()
att_out.close()



