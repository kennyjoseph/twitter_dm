__author__ = 'kennyjoseph'

__author__ = 'kjoseph'

import codecs
import glob
import random
import sys
import io

from twitter_dm import TwitterApplicationHandler
from twitter_dm.utility.general_utils import tab_stringify_newline
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
out_fil = io.open(sys.argv[3], "w")

i = 0
j = 0
print len(user_sns)


out_fil.write(tab_stringify_newline([
"id",
'name',
"screen_name",
'url',
'protected',
'location',
'description',
"followers_count",
"friends_count",
"favourites_count",
"created_at",
"utc_offset",
'time_zone',
"statuses_count",
"lang",
"status_created_at",
"status_coordinates",
"status_lang",
"profile_image_url_https",
"verified"]))

while i < len(user_sns):
    j +=1
    print j
    api_hook = handles[random.randint(0,len(handles)-1)]

    curr_ids = set(user_ids[i:(i+100)])
    user_data = api_hook.get_from_url("users/lookup.json",{"user_id":",".join(curr_ids),"include_entities":"false"})

    for user in user_data:
        output_data = [user["id"],
                       user.get('name'),
                       user["screen_name"],
                       user.get('url',''),
                       user['protected'],
                       user.get('location',''),
                       user.get('description', ''),
                       user["followers_count"],
                       user["friends_count"],
                       user["favourites_count"],
                       user["created_at"],
                       user.get("utc_offset",''),
                       user.get('time_zone',''),
                       user["statuses_count"],
                       user["lang"]]
        if 'status' in user:
            output_data += [user["status"]["created_at"],
                            user["status"]["coordinates"] if user['status']['coordinates'] else '',
                            user["status"]["lang"]]
        else:
            output_data += ['','','']

        output_data += [user.get("profile_image_url_https",""),user.get("verified","")]

        output_data = [(x.replace("\r\n","  ")
                        .replace("\n","  ")
                        .replace("\r","  ")
                        .replace("\t","  ")) if type(x) is str else x for x in output_data ]
        output_data = [(x.replace(u"\r\n",u"  ")
                        .replace(u"\n",u"  ")
                        .replace(u"\r","  ")
                        .replace(u"\t",u"  ")) if type(x) is unicode else x for x in output_data ]
        to_write = tab_stringify_newline(output_data)

        out_fil.write(to_write)
        curr_ids.remove(str(user['id']).lower())
    print 'Num deleted: ', len(curr_ids)
    #for c in curr_ids:
        #out_fil.write(",".join([str(c),'0'])+"\n")

    i += 100

out_fil.close()
