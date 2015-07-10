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


def get_handles(file_list):
    handles = []
    for fil in file_list:
        print fil
        app_handler = TwitterApplicationHandler(pathToConfigFile=fil)
        handles += app_handler.api_hooks
    return handles
