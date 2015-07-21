__author__ = 'kjoseph'
import sys
from twitter_dm.TwitterUser import TwitterUser
import os
import glob
from datetime import datetime
import random
from vaderSentiment.vaderSentiment import sentiment
from langid import langid
import cPickle as pickle

sys.argv = ['','/Users/kjoseph/Desktop/desktop/tmp_ferg/json',
                '1-2013',
                '8-2014',
                'ferguson=150',
                'random=250',
                'police=200',
                'garner=150']


# repeatable
#random.seed(0)

# where the json files are, one per user
json_data_dir = sys.argv[1]


# only get accounts around since 2013
min_acct_age = sys.argv[2].split("-")
MIN_ACCOUNT_AGE = datetime(int(min_acct_age[1]),int(min_acct_age[0]),1)

# only tweets from last August onwards
min_tweet_date = sys.argv[3].split("-")
MIN_TWEET_DATE = datetime(int(min_tweet_date[1]),int(min_tweet_date[0]),1)


# datasets to collect
datasets_to_collect = []
for dataset_descrip in sys.argv[4:]:
    spl = dataset_descrip.split("=")

    if spl[0] == 'random':
        datasets_to_collect.append(['',int(spl[1]),[]])
    else:
        datasets_to_collect.append([spl[0],int(spl[1]),[]])

# get all user files
files = glob.glob(os.path.join(json_data_dir,"*"))


curr_dataset = datasets_to_collect[0]

print datasets_to_collect

for f in files:
    user = TwitterUser(filename_for_tweets=f)

    if user.n_total_tweets < 10000 and user.n_total_tweets > 50 and\
        user.followers_count < 25000 and user.creation_date <= MIN_ACCOUNT_AGE:

        tweet_set = [t for t in user.tweets if t.retweeted is None and\
                                                len(t.urls) == 0 and\
                                                len(t.tokens) > 5 and\
                                                t.created_at <= MIN_TWEET_DATE and\
                                                curr_dataset[0] in t.tokens and\
                                                langid.classify(t.text)[0] == 'en'and\
                                                sentiment(t.text)['compound'] != 0]
        if len(tweet_set) == 0:
            continue

        tweet = random.sample(tweet_set, 1)[0]
        print user.screen_name, curr_dataset[0:2], "::::  ", tweet.text
        curr_dataset[2].append(tweet)
        curr_dataset[1] -= 1
        if curr_dataset[1] == 0:
            pickle.dump(curr_dataset[2],open(curr_dataset[0]+".p",'wb'))
            if len(datasets_to_collect) == 1:
                print 'DONE!!!'
                break
            datasets_to_collect = datasets_to_collect[1:]
            curr_dataset = datasets_to_collect[0]


