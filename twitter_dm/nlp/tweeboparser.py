"""
The functions and classes in the file are for when you want to dependency parse your tweets using
the TweeboParser library from the ArkNLP lab.  You can find the parser at http://www.ark.cs.cmu.edu/TweetNLP/
"""
__author__ = 'kjoseph'

import os
import codecs
import subprocess
from twitter_dm.utility.general_utils import mkdir_no_err
import shutil

DIRECTORY_I_EXIST_IN = os.path.dirname(os.path.realpath(__file__))

def dependency_parse_tweets(location_of_tweebo_parser,tweets,output_filename):
    """
    :param location_of_tweebo_parser: Path to the TweeboParser directory on your machine
    :param tweets: A list of Tweet objects that you would like to run dependency parsing on
    :param output_filename: The name of the file that you would like to export the data to
    :return: the data read in to python that facilitates further analysis
    """

    if os.path.exists(output_filename):
        print 'found existing parse, returning'
        return read_tweebo_parse(output_filename)
    else:
        # create the input file
        tweebo_output_fil = codecs.open(output_filename+".inp","w","utf8")
        for tweet in tweets:
            tweebo_output_fil.write(tweet.text.replace("\n","   ")+"\n")
        tweebo_output_fil.close()

        # create the working directory
        mkdir_no_err(output_filename+"_wd")

        subprocess.Popen(DIRECTORY_I_EXIST_IN+'/tweeboparser_runner.sh ' +
                         '{tweeboparser_location} {input_fil} {working_dir} {output_fil}'.format(
                                tweeboparser_location=location_of_tweebo_parser,
                                input_fil=output_filename+".inp",
                                working_dir=output_filename+"_wd",
                                output_fil=output_filename),
                shell=True).wait()

        shutil.rmtree(output_filename+"_wd")
        os.remove(output_filename+".inp")

        print 'FINISHED dependency parse'
    return read_tweebo_parse(output_filename)

def read_tweebo_parse(filename):
    return "".join(codecs.open(filename,"r","utf8").readlines()).split("\n\n")

