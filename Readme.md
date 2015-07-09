# Introduction

This library has chiefly been developed for three purposes:

1. Rapidly collect data from the Twitter *Search* API. We hopefully will be able to integrate it with ```tweepy```
at some point soon so it can also handle the Streaming API.  The main goal here has been to leverage multiple 
connections, or "handles" to the API via multiprocessing. The ```examples``` directory contains a bunch of examples
of how this is done, and you can start with the ```twitter_dm/multiprocess``` folder to see how we extend the Worker
class of Twitter's multiprocessing library to do what we want to do.  

2. Provide a convenient way to manipulate and access data from Twitter users and Tweets in an object-oriented, extendible
fashion.  The classes in Tweet.py and TwitterUser.py are convenient representations that make accessing data about 
users and tweets relatively painless.

3. Provide a repeatable way to tokenize a Tweet in python. We leverage the great work by Brendan O'Connor, Myle Ott and others who
did all the hard work of creating a great Twitter tokenizer and put a few wrappers around it to hopefully make it slightly
more easy to integrate into your workflow.


The documentation and examples here are woefully incomplete, and testing is non-existent. However, I at least have
been using and developing the library for the last year or so with the help of Peter Landwehr, and so I do think it is useful.

I promise to continue adding documentation and examples ASAP, and feel free to do the same!

# GETTING STARTED

Once you've cloned the repo, install the package and its dependencies

```$ python setup.py install```

Then, open up the examples and check out how they work.  I recommend starting with ```collect_user_data_serially.py```
and ```gen_user_ht_networks.py```.

You should also probably check out ```Tweet.py``` and ```TwitterUser.py``` if you're interested in the Object Oriented
approach to Twitter data - I think they're pretty useful!

# NOTES:
- Importantly, the multiprocess stuff won't work on a OSX because of some crazy bug in urllib2.  Give it a try, feel free to 
submit a fix/tell me what I'm doing wrong, but I have traced it all the way into urllib2 and where it interacts with
 the OS as a heads up.
 

# TODO:

1. More examples
2. More documentation
3. Integrate with tweepy
4. Integrate with pandas
5. Test
