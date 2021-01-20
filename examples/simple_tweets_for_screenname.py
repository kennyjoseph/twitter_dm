"""
A simple example of how to use a single api hook to get tweets for a particular user
"""

import codecs
import sys

from twitter_dm import TwitterApplicationHandler
from twitter_dm import TwitterUser

if len(sys.argv) != 4:
    print('usage:  [login_credentials_file] [user_screen_name] [output_file]')
    sys.exit(-1)

##get all the handles we have to the api
app_handler = TwitterApplicationHandler(pathToConfigFile=sys.argv[1])
print('n authed users: ', len(app_handler.api_hooks))

user = TwitterUser(app_handler.api_hooks[0], screen_name=sys.argv[2])

print(('\tgetting tweets for: ',  sys.argv[2]))
user.populate_tweets_from_api(sleep_var=False)

if len(user.tweets) > 0:
    out_fil = codecs.open(sys.argv[3], "w","utf8")
    for tweet in user.tweets:
        out_fil.write(tweet.text.replace("\n","   ")+"\n")

out_fil.close()