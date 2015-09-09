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
import re
import gzip

DIRECTORY_I_EXIST_IN = os.path.dirname(os.path.realpath(__file__))

def replace_tweet_newlines(text):
    return text.replace(r"\r\n","\n").replace("\n", "     ").replace("\r","    ")

def dependency_parse_tweets(location_of_tweebo_parser,tweets,output_filename,gzip_final_output=True):
    """
    :param location_of_tweebo_parser: Path to the TweeboParser directory on your machine
    :param tweets: A list of Tweet objects that you would like to run dependency parsing on
    :param output_filename: The name of the file that you would like to export the data to
    :return: the data read in to python that facilitates further analysis
    """

    final_output_filename = output_filename
    if gzip_final_output and not output_filename.endswith(".gz"):
        final_output_filename += ".gz"
    if gzip_final_output and output_filename.endswith(".gz"):
        output_filename.replace(".gz","")

    if os.path.exists(final_output_filename):
        print 'found existing parse, returning'
        return read_tweebo_parse(final_output_filename)
    else:
        # create the input file
        tweebo_output_fil = codecs.open(output_filename+".inp","w","utf8")
        for tweet in tweets:
            to_output = replace_tweet_newlines(tweet.text)
            tweebo_output_fil.write(to_output + "\n")
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

        if gzip_final_output:
            with open(output_filename, 'rb') as f_in:
                with gzip.open(final_output_filename, 'wb') as f_out:
                    f_out.writelines(f_in)
            os.remove(output_filename)

        print 'FINISHED dependency parse'
    return read_tweebo_parse(final_output_filename)

def read_tweebo_parse(filename):
    if filename.endswith(".gz"):
        zf = gzip.open(filename, 'rb')
        reader = codecs.getreader("utf-8")
        contents = reader(zf)
        return "".join(contents).split("\n\n")
    return "".join(codecs.open(filename,"r","utf8").readlines()).split("\n\n")

