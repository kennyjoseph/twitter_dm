"""
This file holds utility functions to create a sync manager and one to load a request queue
"""
__author__ = 'kjoseph'

import multiprocessing as mp

def load_request_queue(data, n_terminals, add_nones=True):
    request_queue = mp.Queue()

    print("DATA: ", data)
    print('loading ', len(data), ' objects onto queue')
    for d in data:
        request_queue.put( d)

    # Sentinel objects to allow clean shutdown: 1 per worker.
    if add_nones:
        for i in range(n_terminals):
            request_queue.put( None )
    return request_queue
