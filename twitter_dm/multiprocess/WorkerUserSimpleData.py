"""
This file contains a class that subclasses multiprocess worker.

The goal of this worker is to do get simple information (e.g. n followers)
for a particular user id
"""
__author__ = 'kjoseph'


import multiprocessing
import codecs
import sys, os
import traceback
from time import sleep
from twitter_dm.utility.general_utils import tab_stringify_newline

class UserSimpleDataWorker(multiprocessing.Process):
    def __init__(self, queue, api_hook, conn_number, out_dir,
                 gets_user_id=True):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.api_hook = api_hook
        self.out_file = codecs.open(os.path.join(out_dir,str(conn_number)+".txt"),"w","utf8")
        self.conn_number = conn_number
        self.gets_user_id = gets_user_id

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
                print 'collecting data'
                user_data = self.api_hook.get_from_url("users/lookup.json", {"user_id": ",".join(data), "include_entities": "false"})
                user_ret_ids = [str(u['id']) for u in user_data]
                print len(data),len(user_ret_ids)
                not_there = set.difference(set(data),set(user_ret_ids))
                print len(not_there)
                for u in not_there:
                    self.out_file.write(tab_stringify_newline([u]))
                print 'sleeping'
                sleep(20)
            except Exception:
                print('FAILED:: ', data)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print("*** print_tb:")
                traceback.print_tb(exc_traceback, limit=30, file=sys.stdout)
                print("*** print_exception:")

            print('finished collecting data for: ', data)
