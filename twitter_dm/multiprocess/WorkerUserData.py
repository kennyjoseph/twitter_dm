"""
This file contains a class that subclasses multiprocess worker.

The goal of this worker is to collect information about a user.
The class takes in a bunch of booleans that determines, e.g., whether or not
to collect the lists and/or followers and friends of the user
"""
__author__ = 'kjoseph'

from twitter_dm.TwitterUser import TwitterUser

import multiprocessing
import cPickle as pickle
import sys, os
import traceback
import glob
from twitter_dm.utility.general_utils import Unbuffered

class UserDataWorker(multiprocessing.Process):
    def __init__(self, queue, api_hook, out_dir,
                 gets_user_id,
                 always_pickle=False,
                 populate_lists=False,
                 populate_friends=False,
                 populate_followers=False,
                 step_count = None,
                 add_users_to_queue_function=None,
                 post_process_function=None,
                 save_user_tweets = True,
                 save_user_data=True,
                 gets_since_tweet_id=False,
                 add_to_file=False,
                 populate_tweets=True,
                 tweet_count_file_dir=None
                 ):
        multiprocessing.Process.__init__(self)

        self.queue = queue
        self.api_hook = api_hook
        self.out_dir = out_dir
        self.always_pickle = always_pickle
        self.gets_user_id = gets_user_id
        self.populate_lists = populate_lists
        self.populate_friends = populate_friends
        self.populate_followers = populate_followers
        self.step_count = step_count
        self.add_users_to_queue_function = add_users_to_queue_function
        self.post_process_function = post_process_function
        self.save_user_tweets= save_user_tweets
        self.save_user_data = save_user_data
        self.gets_since_tweet_id = gets_since_tweet_id
        self.add_to_file = add_to_file
        self.populate_tweets = populate_tweets
        self.tweet_count_file = None
        if tweet_count_file_dir:
            self.tweet_count_file = Unbuffered(
                open(
                    os.path.join(self.out_dir, tweet_count_file_dir,
                                 self.api_hook.consumer_key+"_"+self.api_hook.access_token+".txt"),"w"))

        if ((step_count and not add_users_to_queue_function) or
            (not step_count and add_users_to_queue_function)):
            print 'WARNING: you supplied a step count but no function, or vice versa, ',
            print 'for your snowball sample. This isnt going to work! Fix yo code'

    def run(self):
        print('Worker started')
        # do some initialization here
        snow_sample_number = None
        since_tweet_id = None
        while True:
            data = self.queue.get(True)

            try:
                if data is None:
                    print 'ALL FINISHED!!!!'
                    break

                if len(data) == 1 or type(data) is str or type(data) is unicode or type(data) is int:
                    user_identifier = data
                elif len(data) == 3:
                    user_identifier, snow_sample_number, since_tweet_id = data
                elif len(data) == 2:
                    if self.step_count:
                        user_identifier, snow_sample_number = data
                    elif self.gets_since_tweet_id:
                        user_identifier, since_tweet_id = data

                user_identifier = str(user_identifier)

                print 'Starting: ', data

                pickle_filename = os.path.join(self.out_dir,"obj",user_identifier)
                json_filename = os.path.join(self.out_dir,"json",user_identifier+".json.gz")

                # Get the user's data
                if os.path.exists(pickle_filename) and os.path.exists(json_filename) and not self.add_to_file:
                    print '\tgot existing data for: ', data
                    user = pickle.load(open(pickle_filename,"rb"))
                    user.populate_tweets_from_file(json_filename)
                else:
                    if self.gets_user_id:
                        user = TwitterUser(self.api_hook, user_id=user_identifier)
                    else:
                        user = TwitterUser(self.api_hook, screen_name=user_identifier)

                    print 'populating tweets', user_identifier

                    if self.populate_tweets:
                        if self.save_user_tweets:
                            print 'saving tweets to: ', json_filename
                            of_name, tweet_count = user.populate_tweets_from_api(
                                                            json_output_filename=json_filename,
                                                            since_id=since_tweet_id,
                                                            populate_object_with_tweets=False)
                        else:
                            of_name, tweet_count = user.populate_tweets_from_api(since_id=since_tweet_id,
                                                                                 populate_object_with_tweets=False)

                        if self.tweet_count_file:
                            self.tweet_count_file.write(str(user_identifier)+"\t"+str(tweet_count)+"\n")

                    if self.populate_lists:
                        print 'populating lists', user.screen_name
                        user.populate_lists_member_of()

                    if self.populate_friends:
                        print 'populating friends, ', user.screen_name
                        user.populate_friends()

                    if self.populate_followers:
                        print 'populating followers, ', user.screen_name
                        user.populate_followers()

                    if self.save_user_data and \
                        (self.always_pickle or self.populate_lists
                         or self.populate_friends or self.populate_followers):
                        # Pickle and dump user
                        #print 'pickling and dumping (no tweets): ', user.screen_name
                        user.tweets = []
                        pickle.dump(user, open(pickle_filename, "wb"))

                # now add to queue if necessary
                if snow_sample_number is not None and snow_sample_number < self.step_count:
                    for user_identifier in self.add_users_to_queue_function(user):
                        self.queue.put([str(user_identifier),snow_sample_number+1])

                if self.post_process_function:
                    self.post_process_function(user)

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
