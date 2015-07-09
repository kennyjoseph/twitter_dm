"""
This file contains a class that subclasses multiprocess worker.

The goal of this worker is to take in user ids and to collect
full information about that user's ego network.  This was used for
my ICWSM'15 paper.

"""
__author__ = 'kjoseph'

from ..TwitterUser import TwitterUser
import os, sys,  multiprocessing, glob, traceback, codecs
from ..utility.general_utils import mkdir_no_err
import cPickle as pickle


class TwitterEgoNetworkWorker(multiprocessing.Process):
    def __init__(self, queue, api_hook, network_dir, pickle_dir):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.api_hook = api_hook
        self.network_dir = network_dir
        self.pickle_dir = pickle_dir

    def write_user_network(self, dir, user,uid, restricted_to):
        network_fil = codecs.open(os.path.join(dir,str(uid)),"w", "utf-8")
        net = user.get_ego_network(restricted_to)
        for link in net:
            network_fil.write('Agent,' + ",".join([str(x) for x in link])+"\n")
        network_fil.close()

    def get_user_network(self, this_user_network_dir_name, user_ids,restrict_output_to_ids, stored_user_list):
        counter_val = 0
        for uid in user_ids:
            counter_val +=1
            if counter_val % 10 == 0:
                print(counter_val, " / ", len(user_ids), this_user_network_dir_name.replace(self.network_dir, ""))

            # try to find user in stored_users
            if str(uid) in stored_user_list:
                user = pickle.load(open(self.pickle_dir+"/"+str(uid), "rb"))
            else:
                user = TwitterUser(self.api_hook, user_id=uid)
                user.populate_tweets_from_api()
                out_fil = open(self.pickle_dir+"/"+str(uid), "wb")
                pickle.dump(user, out_fil)
                out_fil.close()

            self.write_user_network(this_user_network_dir_name,user,uid,restrict_output_to_ids)


    def run(self):
        print('Worker started')

        while True:

            try:
                data = self.queue.get(True)
                if data is None:
                    print 'ALL DONE, EXITING!'
                    return

                user_id,screen_name = data[0], data[1]
                print('Starting: ', screen_name, user_id)

                this_user_network_dir_name = os.path.join(self.network_dir,user_id)
                mkdir_no_err(this_user_network_dir_name)

                stored_user_list = set([os.path.basename(user_pickle) for user_pickle in glob.glob(self.pickle_dir+"*")])

                # Get the ego
                if user_id in stored_user_list:
                    print('\tgot pickled: ', user_id)
                    user = pickle.load(open(self.pickle_dir+"/"+str(user_id), "rb"))
                else:
                    user = TwitterUser(self.api_hook,user_id=user_id)
                    print('\tgetting tweets for: ', user_id)
                    user.populate_tweets_from_api()
                    print('\t num tweets received for: ', user_id, ' (',  screen_name, '): ', len(user.tweets))
                    if len(user.tweets) > 0:
                        print('\tgetting lists, friends, followers for: ', user_id)
                        user.populate_lists()
                        #user.populate_followers()
                        #user.populate_friends()

                    print('pickling: ', screen_name)
                    pickle.dump(user, open(self.pickle_dir+"/"+user_id, "wb"))

                self.write_user_network(this_user_network_dir_name, user, user_id, None)

                if len(user.tweets) == 0:
                    print('finished collecting data for: ', user_id, ', no tweets')
                    continue

                # Find the ego network based on retweets, mentions and replies
                user_network_to_pull = user.get_ego_network_actors()

                print('Starting to get ', user.user_id, "'s network of ", len(user_network_to_pull), ' actors')
                restrict_to_users = [u for u in user_network_to_pull]
                restrict_to_users.append(user_id)

                self.get_user_network(this_user_network_dir_name,
                                      user_network_to_pull,
                                      restrict_to_users,
                                      stored_user_list)
            except Exception:
                print('FAILED:: ', data)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print("*** print_tb:")
                traceback.print_tb(exc_traceback, limit=50, file=sys.stdout)

            print('finished collecting data for: ', screen_name)
