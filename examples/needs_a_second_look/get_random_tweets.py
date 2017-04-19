__author__ = 'kjoseph'
import cPickle as pickle
import glob
import os
import random
import sys
from datetime import datetime
from functools import partial

from langid import langid
from vaderSentiment.vaderSentiment import sentiment

from twitter_dm.TwitterUser import TwitterUser

"""
Input format:
arg1 : directory of gzipped json files, each containing tweets of a particular user
arg2 : min account age (i.e. acct must be created before this date). Format is month-year (6-2013)
arg3 : tweets must be sent after this period (same format as above)
arg4->inf : of format keyword=n_replies_to_get,n_non_replies_to_get
"""

sys.argv = ['','/Users/kjoseph/Desktop/desktop/tmp_ferg/json',
                '3',
                '1-2013',
                '1-2014',
                'random=2,4',
                'police=2,3',
                'baby sitter=2,3',
                'brat=2,3',
                'child=2,3',
                'bully=2,3',
                'businessman=2,3',
                'father=2,3',
                'guest=2,3',
                'redhead=2,3',
                'girlfriend=2,3',
                'lesbian=2,3',
                'moron=2,3',
                'friend=2,3',
                'roommate=2,3',
                'sports fan=2,3',
                'neighbor=2,3',
                'neurotic=2,3',
                'psychopath=2,3',
                'liar=2,3',
                'slut=2,3',
                'jew=2,3']

# repeatable
random.seed(0)

# where the json files are, one per user
json_data_dir = sys.argv[1]


cpu_count = int(sys.argv[2])


# only get accounts around since 2013
min_acct_age = sys.argv[3].split("-")
MIN_ACCOUNT_AGE = datetime(int(min_acct_age[1]),int(min_acct_age[0]),1)

# only tweets from last August onwards
min_tweet_date = sys.argv[4].split("-")
MIN_TWEET_DATE = datetime(int(min_tweet_date[1]),int(min_tweet_date[0]),1)

def gen_output(data, json_data_dir):

    term,is_reply,tweets_needed = data

    dataset = []

    # get all user files
    files = glob.glob(os.path.join(json_data_dir,"*"))
    random.shuffle(files)

    for f in files:
        user = TwitterUser()
        user.populate_tweets_from_file(f,store_json=True,do_arabic_stemming=False,lemmatize=False)

        if 50 <= user.n_total_tweets <= 10000 and\
           user.followers_count <= 25000 and user.creation_date <= MIN_ACCOUNT_AGE:

            tweet_set = [t for t in user.tweets if t.retweeted is None and\
                           len(t.urls) == 0 and 'http:' not in t.text and\
                           len(t.tokens) > 5 and\
                           t.created_at >= MIN_TWEET_DATE and\
                           (term == '' or term in t.tokens) and\
                           langid.classify(t.text)[0] == 'en'and\
                           sentiment(t.text)['compound'] != 0]

            if is_reply:
                tweet_set = [t for t in tweet_set if t.reply_to]
            else:
                tweet_set = [t for t in tweet_set if not t.reply_to]

            if len(tweet_set) == 0:
                print 'size 0', term, tweets_needed, is_reply
                continue

            tweet = random.sample(tweet_set, 1)[0]
            print user.screen_name, term, tweets_needed, is_reply, "::::  ", tweet.text
            dataset.append(tweet)
            tweets_needed -= 1
            if tweets_needed == 0:
                name = term if term != '' else 'random'
                name += '_reply' if is_reply else '_non_reply'
                pickle.dump(dataset,open(name+".p",'wb'))
                print 'done with: ',name, is_reply
                return

        else:
            print 'failed user'


# datasets to collect
datasets_to_collect = []
for dataset_descrip in sys.argv[5:]:
    spl = dataset_descrip.split("=")

    text = '' if spl[0] == 'random' else spl[0]
    replies,non_replies = spl[1].split(",")

    datasets_to_collect.append([text,True, int(replies)])
    datasets_to_collect.append([text,False, int(non_replies)])

print datasets_to_collect

partial_run = partial(gen_output, json_data_dir=json_data_dir)
#pool = multiprocessing.Pool(processes=cpu_count)
#output = pool.map(partial_run, datasets_to_collect)
partial_run(datasets_to_collect[0])
