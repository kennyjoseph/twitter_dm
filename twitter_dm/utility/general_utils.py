"""
General utilities that I tend to use
"""
__author__ = 'kjoseph'


import os
from twitter_dm.TwitterApplicationHandler import TwitterApplicationHandler
def mkdir_no_err(dir_name):
    try:
        os.mkdir(dir_name)
    except:
        pass

def stringify(data):
    return [unicode(x) for x in data]

def tab_stringify_newline(data,newline=True):
    to_return = "\t".join(stringify(data))
    if newline:
         return to_return + "\n"
    return to_return


def get_handles(file_list,silent=False):
    handles = []
    for fil in file_list:
        if not silent:
            print fil
        app_handler = TwitterApplicationHandler(pathToConfigFile=fil,silent=silent)
        handles += app_handler.api_hooks
    return handles

def powerset(iterable,combs=None):
    from itertools import combinations
    from itertools import chain
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    if not combs:
        combs = range(1,len(s)+1)
    return chain.from_iterable(combinations(s, r) for r in combs)
