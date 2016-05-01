"""
This file holds utility functions to create a sync manager and one to load a request queue
"""
__author__ = 'kjoseph'



def init_good_sync_manager():
    from multiprocessing.managers import SyncManager
    #handle SIGINT from SyncManager object
    def mgr_sig_handler(signal, frame):
        print 'not closing the mgr'

    #initilizer for SyncManager
    def mgr_init():
        import signal
        signal.signal(signal.SIGINT, mgr_sig_handler)
        print 'initialized mananger'

    #using syncmanager directly instead of letting Manager() do it for me
    manager = SyncManager()
    manager.start(mgr_init)


def load_request_queue(data, n_terminals, add_nones=True):
    from multiprocessing import Manager
    m = Manager()
    request_queue = m.Queue()

    print 'loading ', len(data), ' objects onto queue'
    for d in data:
        request_queue.put( d)

    # Sentinel objects to allow clean shutdown: 1 per worker.
    if add_nones:
        for i in range(n_terminals):
            request_queue.put( None )
    return request_queue
