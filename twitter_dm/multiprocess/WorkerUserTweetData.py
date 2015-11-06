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


class UserDataWorker(multiprocessing.Process):
    def __init__(self, queue, api_hook, conn_number, out_dir,
                 to_pickle=False, gets_user_id=True,
                 populate_lists=False,
                 populate_friends=False,
                 populate_followers=False):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.api_hook = api_hook
        self.conn_number = conn_number
        self.out_dir = out_dir
        self.to_pickle = to_pickle
        self.gets_user_id = gets_user_id
        self.populate_lists = populate_lists
        self.populate_friends = populate_friends
        self.populate_followers = populate_followers
    def run(self):
        print('Worker started')
        # do some initialization here

        while True:
            data = self.queue.get(True)
            try:
                if data is None:
                    print('ALL FINISHED!!!!', self.conn_number)
                    break

                print('Starting: ', data)
                if self.gets_user_id:
                    user = TwitterUser(self.api_hook, user_id=data)
                else:
                    user = TwitterUser(self.api_hook, screen_name=data)

                user.populate_tweets_from_api(json_output_directory=os.path.join(self.out_dir,"json"))

                if len(user.tweets) == 0:
                    print(" ".join(['pickling and dumping: ', user.screen_name]))
                    pickle.dump(user, open(os.path.join(self.out_dir,"obj",data), "wb"))
                    continue
                if self.populate_lists:
                    user.populate_lists()

                if self.populate_friends:
                    print(" ".join(['populating friends, ', user.screen_name]))
                    user.populate_friends()

                if self.populate_followers:
                    print(" ".join(['populating followers, ', user.screen_name]))
                    user.populate_followers()

                if self.to_pickle or self.populate_lists or self.populate_friends or self.populate_followers:
                    # Pickle and dump user
                    print(" ".join(['pickling and dumping (no tweets): ', user.screen_name]))
                    user.tweets = []
                    pickle.dump(user, open(os.path.join(self.out_dir,"obj",data), "wb"))
            except Exception:
                print('FAILED:: ', data)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print("*** print_tb:")
                traceback.print_tb(exc_traceback, limit=30, file=sys.stdout)
                print("*** print_exception:")

            print('finished collecting data for: ', data)
