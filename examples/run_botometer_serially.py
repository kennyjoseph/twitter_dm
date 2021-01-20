import botometer
from twitter_dm.utility.general_utils import Unbuffered, collect_system_arguments
import ujson as json
import sys


handles, out_file, user_ids, is_ids, mashape_key = collect_system_arguments(sys.argv, ['mashape_key'])

twitter_app_auth = {
    'consumer_key': handles[0].consumer_key,
    'consumer_secret': handles[0].consumer_secret,
    'access_token': handles[0].access_token,
    'access_token_secret':  handles[0].access_token_secret,
    "wait_on_ratelimit" : True
  }

bom = botometer.Botometer(mashape_key=mashape_key,**twitter_app_auth)

accounts = set([x.strip() for x in open(out_file)])

with open(out_file) as inf:
    for line in inf:
        uid = json.loads(line)['user']['id_str']
        accounts.remove(uid)

print('n accounts: ', len(accounts))

of = Unbuffered(open("bot_out.json", "a"))

for i, a in enumerate(accounts):
    if i % 250 == 0:
        print(i)

    # Check a single account
    try:
        result = bom.check_account(a)
        of.write(json.dumps(result) + "\n")
    except:
        print('fail', a)

