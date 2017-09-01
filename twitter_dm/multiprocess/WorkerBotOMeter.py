"""
This file contains a class that subclasses multiprocess worker.

The goal of this worker is to do get simple information (e.g. n followers)
for a particular user id
"""
__author__ = 'kjoseph'


import multiprocessing
import sys, os
import gzip
import ujson as json
import traceback
import botometer
from tweepy import TweepError
from time import sleep

class BotOMeterWorker(multiprocessing.Process):
    def __init__(self, queue, api_hook, conn_number, out_dir, mashape_key):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.api_hook = api_hook
        self.out_dir = out_dir
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
                    break

                print 'checking: ', data
                result = self.bom._get_twitter_data(data)
                json.dump(result, gzip.open(os.path.join(self.out_dir,str(data)+".gz"),"wb"))
                sleep(7)
            except botometer.NoTimelineError:
                print 'no timeline for: ', data, ' continuing'
            except TweepError as e:
                print e
            except KeyboardInterrupt as e:
                print e
                break
            except Exception:
                print('FAILED:: ', data)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print("*** print_tb:")
                traceback.print_tb(exc_traceback, limit=50, file=sys.stdout)
                print("*** print_exception:")

            print 'finished: ', data
