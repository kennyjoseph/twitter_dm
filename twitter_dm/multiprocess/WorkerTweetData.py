"""
This file contains a class that subclasses multiprocess worker.

The goal of this worker is to take in tweet ids and to "hydrate"
these ids with full json objects. It writes these out to the output file
provided. It also creates a file that tells you what tweets it was able to get
and what tweets it couldn't get back (because the user or the tweet was deleted,
most likely)
"""
__author__ = 'kjoseph'

import codecs
import ujson as json
import multiprocessing
from time import sleep

class TweetDataWorker(multiprocessing.Process):
    def __init__(self, queue, api_hook, conn_number, out_dir, to_pickle=False, gets_user_id=True):
        multiprocessing.Process.__init__(self)
        self.queue= queue
        self.api_hook = api_hook
        self.conn_number = conn_number
        self.out_dir = out_dir
        self.to_pickle = to_pickle
        self.gets_user_id = gets_user_id
        self.tweet_output_file = codecs.open(self.out_dir+"/"+str(conn_number)+".json", "a", "utf-8")
        self.tweet_id_output_file = open(self.out_dir+"/"+str(conn_number)+".txt", "a")

    def run(self):
        print('Worker started')
        # do some initialization here

        while True:
            data = self.queue.get(True)
            sleep(10)
            #try:
            if data is None:
                print 'ALL FINISHED!!!!', self.conn_number
                self.tweet_id_output_file.close()
                self.tweet_output_file.close()
                break

            tweet_data = self.api_hook.get_from_url("statuses/lookup.json", {"id": ",".join(data)})

            data = set([int(d) for d in data])
            good = 0
            for tw in tweet_data:
                try:
                    good += 1
                    self.tweet_output_file.write(json.dumps(tw)+"\n")
                    self.tweet_id_output_file.write(str(tw['id']) + "\tg\n")
                    data.remove(tw['id'])
                except KeyboardInterrupt as e:
                    print e
                    break
                except:
                    print 'writing tweet failed'
                    pass
                
            for failed_tweet in data:
                try:
                    self.tweet_id_output_file.write(str(failed_tweet) + "\tf\n")
                except KeyboardInterrupt as e:
                    print e
                    break
                except:
                    print 'writing tweet_id failed'
                    
            print('N GOOD: ', good)

