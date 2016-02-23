"""
This file contains a class that subclasses multiprocess worker.

The goal of this worker is to do a snowball sample on the directed
Twitter network. More specifically, it assumes a snowball of size 1.
Starting from a set of seed users, for a particular user, this
worker gets all of that person's friends and then adds them to the queue
of people to get. When the code gets to the edge of the snowball sample, it
stops getting data
"""
from twitter_dm.TwitterUser import TwitterUser

import codecs
import glob
import multiprocessing
import os
import cPickle as pickle


class TwitterFollowingNetworkWorker(multiprocessing.Process):
    def __init__(self, queue, api_hook, network_dir, pickle_dir):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.api_hook = api_hook
        self.network_dir = network_dir
        self.pickle_dir = pickle_dir

    def run(self):
        print('Worker started')

        while True:

            user_id, snow_sample_number = self.queue.get(True)

            print('Starting: ', user_id, snow_sample_number)

            stored_user_list = set([os.path.basename(user_pickle) for user_pickle in glob.glob(self.pickle_dir+"*")])

            # Get the ego
            if user_id in stored_user_list:
                print('\tgot pickled: ', user_id)
                user = pickle.load(open(self.pickle_dir+"/"+str(user_id), "rb"))
            else:
                user = TwitterUser(self.api_hook, user_id=user_id)
                print('\tgetting tweets for: ', user_id)
                user.populate_tweets_from_api()
                print('\t num tweets received for: ',  user_id, ' ', len(user.tweets))
                # print '\tgetting followers for: ', screen_name
                #user.populate_followers()

                print('\tgetting friends for: ', user_id)
                user.populate_friends()

                print('pickling: ', user_id)
                pickle.dump(user, open(self.pickle_dir+"/"+user_id, "wb"))

            ##write out their following network and add each id to queue
            network_fil = codecs.open(os.path.join(self.network_dir,user_id),"w", "utf-8")
            added = 0
            for following_id in user.friend_ids:
                if snow_sample_number < 2:
                    added +=1
                    self.queue.put([str(following_id),snow_sample_number+1])
                network_fil.write(",".join([user_id,str(following_id)])+"\n")
            network_fil.close()


            print 'finished collecting data for: ', user_id
            print 'added: ', added

