from twitter_dm.utility.DictionaryLookUp import DictionaryLookUp
from twitter_dm.TwitterUser import TwitterUser
from twitter_dm.utility.general_utils import get_handles
import glob, os

PATH_TO_TWITTER_APP_HANDLES = "/Users/kennyjoseph/git/thesis/thesis_python/twitter_login_creds"

DICTIONARY_FILE = "/Users/kennyjoseph/git/thesis/thesis_work/lcss_study/data/identities_for_study"

sn = "_kenny_joseph"
json_filename = "kj.json"
handles = get_handles(glob(os.path.join(PATH_TO_TWITTER_APP_HANDLES,"*.txt")),silent=True)
u = TwitterUser(api_hook=handles[0],screen_name=sn)
u.populate_tweets_from_api(json_output_filename=json_filename,sleep_var=False)


dictionary = DictionaryLookUp()

for t in u.tweets:

