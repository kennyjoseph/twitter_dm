"""
This file contains a class that subclasses multiprocess worker.

The goal of this worker is to do get simple information (e.g. n followers)
for a particular user id
"""
__author__ = 'kjoseph'


import multiprocessing
import io
import sys, os
import traceback
import ujson as json
import botometer
from tweepy import TweepError

class BotOMeterWorker(multiprocessing.Process):
    def __init__(self, queue, api_hook, conn_number, out_dir, mashape_key):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.api_hook = api_hook
        self.out_file = io.open(os.path.join(out_dir,str(conn_number)+"_botometer.json"),"w")
        self.conn_number = conn_number

        twitter_app_auth = {
            'consumer_key':api_hook.CONSUMER_KEY,
            'consumer_secret': api_hook.CONSUMER_SECRET,
            'access_token':  api_hook.access_token ,
            'access_token_secret':  api_hook.access_token_secret,
            "wait_on_ratelimit": True
        }

        self.bom = botometer.Botometer(mashape_key=mashape_key,**twitter_app_auth)

        self.mashape_key = mashape_key


    def run(self):
        print('Worker started')
        # do some initialization here

        while True:
            data = self.queue.get(True)
            try:
                if data is None:
                    print('ALL FINISHED!!!!', self.conn_number)
                    self.out_file.close()
                    break

                print 'checking: ', data
                result = self.bom.check_account(data)
                self.out_file.write(json.dumps(result)+u"\n")

            except botometer.NoTimelineError:
                print 'no timeline for: ', data, ' continuing'
            except TweepError as e:
                print e
            # except Exception:
            #     print('FAILED:: ', data)
            #     exc_type, exc_value, exc_traceback = sys.exc_info()
            #     print("*** print_tb:")
            #     traceback.print_tb(exc_traceback, limit=50, file=sys.stdout)
            #     print("*** print_exception:")

            print 'finished: ', data
