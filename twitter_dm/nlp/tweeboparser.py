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
from ..utility.general_utils import read_grouped_by_newline_file

DIRECTORY_I_EXIST_IN = os.path.dirname(os.path.realpath(__file__))

def replace_tweet_newlines(text):
    return text.replace(r"\r\n","\n").replace("\n", "     ").replace("\r","    ")

def dependency_parse_tweets(location_of_tweebo_parser,tweets,output_filename,gzip_final_output=True):
    """
    :param location_of_tweebo_parser: Path to the TweeboParser directory on your machine
    :param tweets: A list of Tweet objects that you would like to run dependency parsing on
    :param output_filename: The name of the file that you would like to export the data to
           NOTE THIS HAS TO BE AN ABSOLUTE PATH RIGHT NOW
    :return: the data read in to python that facilitates further analysis
    """

    final_output_filename = output_filename
    if gzip_final_output and not output_filename.endswith(".gz"):
        final_output_filename += ".gz"
    if gzip_final_output and output_filename.endswith(".gz"):
        output_filename.replace(".gz","")

    if os.path.exists(final_output_filename):
        print 'found existing parse, returning'
        return {f[0] : f[1:] for f in read_grouped_by_newline_file(final_output_filename)}
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

        # rewrite file with tweet_ids
        grouped = read_grouped_by_newline_file(output_filename)
        fn = output_filename+"tmp"
        with codecs.open(fn, 'w',"utf8") as f_in:
            for i, g in enumerate(grouped):
                f_in.write(str(tweets[i].id) + "\n")
                f_in.write("\n".join(g))
                f_in.write("\n\n")


        if gzip_final_output:
            with codecs.open(fn, 'r',"utf8") as f_in:
                with gzip.open(final_output_filename, 'wb') as f_out:
                    for line in f_in:
                        f_out.write(line.encode("utf8"))
            os.remove(output_filename)
            os.remove(fn)
        else:
            shutil.move(fn, output_filename)

        print 'FINISHED dependency parse'
    return {f[0] : f[1:] for f in read_grouped_by_newline_file(final_output_filename)}