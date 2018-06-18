"""
This file contains a class that subclasses multiprocess worker.

The goal of this worker is to collect information about a user, writing out the data
on a per-worker basis
"""
__author__ = 'kjoseph'

from twitter_dm.TwitterUser import TwitterUser

import multiprocessing
import sys, os
import traceback
import bz2
import ujson as json
from twitter_dm.utility.general_utils import Unbuffered, tab_stringify_newline as tsn

class BigFileUserDataWorker(multiprocessing.Process):
    def __init__(self,
                 queue,
                 api_hook,
                 output_dir,
                 gets_user_id,
                 tweet_count_file_dir=None
                 ):
        multiprocessing.Process.__init__(self)

        self.queue = queue
        self.api_hook = api_hook
        self.gets_user_id = gets_user_id
        self.tweet_count_file = None

        self.id = self.api_hook.consumer_key+"_"+self.api_hook.access_token
        if tweet_count_file_dir:
            self.tweet_count_file = Unbuffered(
                open(
                    os.path.join(self.out_dir, tweet_count_file_dir,self.id +".txt"),"w"))
        self.output_file = bz2.BZ2File(os.path.join(output_dir,"json", self.id+".json.bz2"), "w")

        self.sinceid_output_file = open(os.path.join(output_dir, "sinceid", self.id + ".txt"), "w")

    def run(self):
        print('Worker started')

        while True:
            data = self.queue.get(True)

            try:
                if data is None:
                    print 'ALL FINISHED!!!!'
                    self.output_file.close()
                    self.sinceid_output_file.close()

                    if self.tweet_count_file:
                        self.tweet_count_file.close()

                    break
                if len(data) != 2:
                    raise Exception("Must specify tuple of user_identifier, last tweet ID (None if there is none)")

                user_identifier, since_tweet_id = str(data[0]), data[1]

                # Get the tweets
                if self.gets_user_id:
                    user = TwitterUser(self.api_hook, user_id=user_identifier)
                else:
                    user = TwitterUser(self.api_hook, screen_name=user_identifier)

                print 'populating tweets: ', user_identifier
                if since_tweet_id != '':
                    tweets = user.populate_tweets_from_api(since_id=since_tweet_id,
                                                         populate_object_with_tweets=False,
                                                         return_tweets=True)
                else:
                    tweets = user.populate_tweets_from_api(populate_object_with_tweets=False,
                                                           return_tweets=True)

                # Write out the tweets
                for tweet in tweets:
                    self.output_file.write(json.dumps(tweet).strip().encode("utf8") + "\n")

                if len(tweets):
                    # write out the since tweet id file
                    self.sinceid_output_file.write(tsn([user_identifier, tweets[0]['id']]))
                else:
                    self.sinceid_output_file.write(tsn([user_identifier, since_tweet_id]))

                # if desired, write out the count file
                if self.tweet_count_file:
                    self.tweet_count_file.write(user_identifier+"\t"+str(len(tweets))+"\n")

            except KeyboardInterrupt as e:
                print e
                break
            except Exception:
                print('FAILED:: ', data)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print("*** print_tb:")
                traceback.print_tb(exc_traceback, limit=30, file=sys.stdout)
                print("*** print_exception:")

          #print('finished collecting data for: ', data)
