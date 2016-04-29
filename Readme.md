# Introduction

This library has chiefly been developed for a few purposes (in order of importance to us):

1. Rapidly collect data from the Twitter *Search* API. The main goal here has been to leverage multiple 
connections, or "handles" to the API via multiprocessing. The ```examples``` directory contains a bunch of examples
of how this is done, and you can "extend" the classes in ```twitter_dm/multiprocess``` folder either by adding various function (e.g. to change how a snowball search is done) or by actually extending them in the OOP sense. These classes are all subclasses of Twitter's multiprocessing library that help to do what we want to do fast and with a bunch of handles.  

2. Provide a repeatable way to tokenize, part-of-speech-tag, and dependency parse a Tweet in python. We use the great work by Brendan O'Connor, Myle Ott, Lingpeng Kong and others who did all the hard work of creating great Twitter NLP tools and put a few wrappers around them to hopefully make it slightly more easy to integrate into your workflow. 

3. [new!] We added a way to extract social identities from text - see ```examples/run_identity_extractor.py``` to get started!  

4. Provide a convenient way to manipulate and access data from Twitter users and Tweets in an object-oriented, extendible
fashion.  The classes in ```Tweet.py``` and ```TwitterUser.py``` are convenient representations that make accessing data about users and tweets relatively painless.

The documentation and examples here are woefully incomplete, and testing is non-existent. However, I and several others at least have been using and developing the library for the last 2 years or so, and so it is fairly stable.

# Citations

If you use the tokenizer, please cite:
```
@inproceedings{oconnor_tweetmotif:_2010,
	title = {{TweetMotif}: {Exploratory} {Search} and {Topic} {Summarization} for {Twitter}.},
	url = {http://www.aaai.org/ocs/index.php/ICWSM/ICWSM10/paper/viewFile/1540/1907/},
	urldate = {2014-03-30},
	booktitle = {{ICWSM}},
	author = {O'Connor, Brendan and Krieger, Michel and Ahn, David},
	year = {2010}
}
```
If you use the POS tagger, please cite:
```
@inproceedings{owoputi_improved_2013,
	title = {Improved part-of-speech tagging for online conversational text with word clusters},
	booktitle = {Proceedings of {NAACL}},
	author = {Owoputi, Olutobi and O’Connor, Brendan and Dyer, Chris and Gimpel, Kevin and Schneider, Nathan and Smith, Noah A},
	year = {2013}
}
```

If you use the dependency parser, please cite:
```
@inproceedings{kong_dependency_2014,
	title = {A dependency parser for tweets},
	urldate = {2015-01-05},
	booktitle = {Proceedings of the {Conference} on {Empirical} {Methods} in {Natural} {Language} {Processing}, {Doha}, {Qatar}, to appear},
	author = {Kong, Lingpeng and Schneider, Nathan and Swayamdipta, Swabha and Bhatia, Archna and Dyer, Chris and Smith, Noah A.},
	year = {2014}
}
```

If you use the social identity extractor, please cite:
```
@inproceedings{joseph_exploring_2016,
	title = {Exploring patterns of identity usage in tweets: a new problem, solution and case study},
	booktitle = {{WWW}},
	author = {Joseph, Kenneth and Wei, Wei and Carley, Kathleen M},
	year = {2016}
}
```

# Getting Started

Once you've cloned the repo, install the package and its dependencies

```$ python setup.py install```

Then, open up the examples and check out how they work.  I recommend starting with ```collect_user_data_serially.py``` for single-process collection of tweets, ```snowball_sample_custom_function_example.py``` for multithreaded collection and 
and ```run_identity_extraction.py``` for NLP stuff.

Anything where you're collecting from the API will require you to have access to the API - that is, you'll need a consumer key & secret (an application) and an acces token & secret (a user who has subscribed to the API). ```twitter_dm``` can either help you set up new credentials (see ```examples/auth_example.py```) or can handle credentials stored in text files in the following way (one text file per application):

```
consumer_key,consumer_secret
user_sn_1 (or blank, this is not needed), user_1_access_token, user_1_access_token_secret
user_sn_2 (or blank, this is not needed), user_2_access_token, user_2_access_token_secret
...
```

You may also want to check out ```Tweet.py``` and ```TwitterUser.py``` if you're interested in the Object Oriented
approach to Twitter data.

# Notes
- Importantly, the multiprocess stuff won't work on a OSX because of some crazy bug in urllib2.  Give it a try, feel free to 
submit a fix/tell me what I'm doing wrong, but I have traced it all the way into urllib2 and where it interacts with
 the OS as a heads up.
 

# Todo:

1. More examples
2. More documentation
3. Integrate with tweepy
4. Integrate with pandas
5. Test
