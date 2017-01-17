__author__ = 'kennyjoseph'

__author__ = 'kjoseph'

import codecs
import glob
import random
import sys

from twitter_dm import TwitterApplicationHandler

#sys.argv = ['',
#            '/Users/kennyjoseph/git/thesis/thesis_python/twitter_login_creds/',
#            'sns_to_get.txt',
#            'out_user_sns.tsv']

print sys.argv

if len(sys.argv) != 4:
    print 'usage:  [known_user_dir] [screen_name_file] [out_fil_name] '
    sys.exit(-1)

handles = []
for fil in glob.glob(sys.argv[1]+"/*.txt"):
    print 'FIL: ' , fil
    app_handler = TwitterApplicationHandler(pathToConfigFile=fil)
    handles += app_handler.api_hooks

print 'n authed users: ', len(handles)

user_sns = set([line.strip().lower() for line in open(sys.argv[2]).readlines()])

print 'len user sns: ', len(user_sns)
#if os.path.exists(sys.argv[3]):
#    with open(sys.argv[3]) as infil:
#        already_gotten = set([line.split(",")[0].lower() for line in infil])
#        print len(already_gotten)
#    user_ids = user_ids - already_gotten

print "N TO FIND: ", len(user_sns)

#user_ids = [u for u in user_ids]
user_ids = [u.lower() for u in user_sns]
out_fil = codecs.open(sys.argv[3], "w")

i = 0
j = 0
print len(user_sns)
while i < len(user_sns):
    j +=1
    print j
    api_hook = handles[random.randint(0,len(handles)-1)]

    curr_ids = set(user_ids[i:(i+100)])
    user_data = api_hook.get_from_url("users/lookup.json",{"user_id":",".join(curr_ids),"include_entities":"false"})

    for u in user_data:
        out_fil.write(",".join([str(u['id']),'1'])+"\n")
        curr_ids.remove(str(u['id']).lower())
    print 'Num deleted: ', len(curr_ids)
    for c in curr_ids:
        out_fil.write(",".join([str(c),'0'])+"\n")

    i += 100

out_fil.close()
