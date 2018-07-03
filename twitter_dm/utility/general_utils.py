"""
General utilities that I tend to use
"""
__author__ = 'kjoseph'


import os
import io
import codecs
import gzip
import sys
import glob
from itertools import groupby
from twitter_dm.TwitterApplicationHandler import TwitterApplicationHandler


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def get_unbuffered_output(filename, open_fun=io.open):
    return Unbuffered(open_fun(filename))

def collect_system_arguments(system_args, additional_args = list()):
    if len(system_args) != (4+len(additional_args)):
        print 'usage:  [partial_path_to_twitter_credentials]  ',
        print '[file with users (ids or sns) or tweet ids to collect]',
        print '[output_filename or directory]',
        for addtl_arg in additional_args:
            print '[' + addtl_arg + ']',
        print
        sys.exit(-1)

    creds_path, in_file, output_location = system_args[1:4]

    print("Input File: ", in_file)

    handles = get_handles_from_filepath(creds_path)

    print("Output Location: ", output_location)

    input_data = set([f.strip() for f in open(in_file).readlines()])
    input_data = [x for x in input_data if x != '']
    print 'N Input Tokens ', len(input_data)

    is_given_ids = False
    try:
        m = [int(x) for x in input_data]
        is_given_ids = True
    except:
        pass

    retv = [handles, output_location, input_data, is_given_ids]
    if len(additional_args):
        retv += system_args[4:]
    return retv

def get_handles_from_filepath(creds_path):
    if os.path.isdir(creds_path):
            creds_path = os.path.join(creds_path, "*.txt")
    elif not creds_path.endswith(".txt"):
        creds_path += "*.txt"

    print( " ".join(['Getting creds from: ',creds_path ]))
    handles = get_handles(glob.glob(creds_path))
    print 'N Auth Tokens: ', len(handles)
    return handles

def mkdir_no_err(dir_name):
    try:
        os.mkdir(dir_name)
    except:
        pass

def strip_newlines(x):
    return (unicode(x).replace(u"\r\n",u"   ")
                      .replace(u"\r",u"   ")
                      .replace(u"\n",u"   ")
                      .replace(u"\t", u"   ")
                      .replace(u"\"", u"'"))

def stringify(data):
    return [strip_newlines(x) for x in data]

def tab_stringify_newline(data,newline=True):
    to_return = "\t".join(stringify(data))
    if newline:
         return to_return + "\n"
    return to_return


def chunk_data(data,chunk_size=100):
    i = 0
    chunked = []
    while i+chunk_size < (len(data)):
        chunked.append(data[i:(i+chunk_size)])
        i += chunk_size
    chunked.append(data[i:len(data)])
    return chunked


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

