"""
General utilities that I tend to use
"""
__author__ = 'kjoseph'


import os
import codecs
import gzip
from itertools import groupby

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


def read_grouped_by_newline_file(filename):
    if not filename.endswith(".gz"):
        contents = codecs.open(filename,'r','utf8')
    else:
        zf = gzip.open(filename, 'rb')
        reader = codecs.getreader("utf-8")
        contents = reader(zf)
    lines = (line.strip() for line in contents)
    data = (grp for nonempty, grp in groupby(lines, bool) if nonempty)
    return [list(g) for g in data]