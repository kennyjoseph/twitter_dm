# This script builds various network edge lists from twitter_dm output and can be done with 
# Parallel execution

__author__ = 'mbenigni'

import cPickle as pickle
import codecs
import itertools
import sys
import time
from collections import Counter
from multiprocessing import Pool
from multiprocessing import freeze_support
from os import listdir, mkdir

from twitter_dm.utility.general_utils import tab_stringify_newline

if len(sys.argv) != 3:
    print 'usage:  [edgelist output dir] [# cores for execution]'
    sys.exit(-1)


def get_user_info(filename):
    try:
        u = pickle.load(open('obj/' + filename, 'rb'))
    except:
        return
    fname = 'json/' + filename + '.json.gz'

    try:
        u.populate_tweets_from_file(fname, store_json=True, do_arabic_stemming=False, do_lemmatize=False,
                                    do_tokenize=False)
    except:
        return

    twText = []
    userMentions = 0
    urlCount = 0
    mlinks = []
    urlLinks=[]
    mUrlLinks=[]
    htlinks = []
    hthtlinks=[]
    geotags = []
    retweets= []

    language_counter = Counter()
    for tw in u.tweets:
        urlCount = urlCount + len(tw.urls)
        twText.append(tw.text)
        language_counter[tw.lang] += 1
        try:
            t = time.mktime(tw.created_at.timetuple())
        except:
            t = 0
        userMentions += len(tw.mentions)
        if tw.geo:
            geotags.append([tw.geo[0], tw.geo[1], t])
        for url in tw.urls:
            urlLinks.append([url,tw.id,t,len(tw.urls)])
        for mention in tw.mentions:
            mlinks.append([mention,tw.id,t])
            if tw.urls:
                for url in tw.urls:
                    mUrlLinks.append([mention,url,tw.id,t])
        if tw.retweeted:
            retweets.append([tw.retweeted_sn,tw.id,t])
        for hashtag in tw.hashtags:
            htlinks.append([hashtag,tw.id, t])

        for comb in itertools.combinations(tw.hashtags, 2):
            hthtlinks.append([comb[0], comb[1],tw.id, t])

    attr = None
    if u.screen_name:
        attr = [u.user_id,
                u.screen_name,
                len(u.friend_ids),
                u.followers_count,
                u.n_total_tweets,
                len(u.tweets),
                u.earliest_tweet_time,
                u.latest_tweet_time,
                u.creation_date,
                urlCount,
                userMentions]

    return {"uid": u.user_id,
            "description": u.description,
            "attributes": attr,
            "lang": language_counter,
            "hashtags": htlinks,
            "hashtagEdges":hthtlinks,
            "mentions": mlinks,
            "urlLinks":urlLinks,
            "urlmentions":mUrlLinks,
            "friends": u.friend_ids,
            "geotags": geotags,
            "followers": u.follower_ids,
            "retweets" : retweets
    }


if __name__ == "__main__":
    freeze_support()

    objfiles = listdir('obj/')
    jsonfiles = [f[:-8] for f in listdir('json/')]
    onlyfiles = list(set(objfiles).intersection(jsonfiles))
    # onlyfiles=[ join('obj/',f) for f in onlyfiles]

    if '.DS_Store' in onlyfiles: onlyfiles.remove('.DS_Store')
    dir1 = sys.argv[1]
    dir2 = dir1 + 'descriptions'
    try:
        stat(dir1)
    except:
        mkdir(dir1)

    try:
        stat(dir2)
    except:
        mkdir(dir2)

    friend_file = codecs.open(dir1+"friend_edgefile.tsv", "w", "utf8") # user by user network edgelist of following ties
    user_ht_file = codecs.open(dir1+"user_ht_edgefile.tsv", "w", "utf8") # bipartite network edgelist of users and hashtags
    ht_ht_file = codecs.open(dir1+"ht_ht_edgefile.tsv", 'w', 'utf8') # hashtag by hashtag network edgelist where co-occurrence in a tweet defines an edge
    mention_file = codecs.open(dir1+"mention_edgefile.tsv", "w", "utf8") # user by user network edgelist of mention ties
    user_url_file = codecs.open(dir1+"user_url_edgefile.tsv", "w", "utf8") # bipartite network edgelist of users and urls
    url_mention_file=codecs.open(dir1+"url_mention_edgefile.tsv","w","utf8") # 
    attribute_file = codecs.open(dir1+"attribute.tsv", "w", "utf8") # node attribute table
    geo_file = codecs.open(dir1+"geofile.tsv", "w", "utf8") # a list of all geo tagged tweets
    lang_file = codecs.open(dir1+"langfile.tsv", "w", "utf8") # language frequencies at the user level
    retweet_file=codecs.open(dir1+ "retweet.tsv", "w", "utf8") # user by user where an edge is a retweet


    friend_file.write(tab_stringify_newline(['Source', 'Target']))
    user_ht_file.write(tab_stringify_newline(['Source', 'Target','tweetID', 'date']))
    user_url_file.write(tab_stringify_newline(['Source', 'Target','tweetID', 'date','urls_tweet']))
    ht_ht_file.write(tab_stringify_newline(['userID','hashtag_A','hashtag_B','tweetID','date']))
    mention_file.write(tab_stringify_newline(['Source', 'Target','tweetID', 'date']))
    url_mention_file.write(tab_stringify_newline(['Source', 'Target','url','tweetID', 'date']))
    geo_file.write(tab_stringify_newline(['userID', 'lat', 'lon', 'date']))
    lang_file.write(tab_stringify_newline(['userID', 'lang', 'count']))
    retweet_file.write(tab_stringify_newline(['Source', 'retweet_sn','tweetID', 'date']))
    attribute_file.write(tab_stringify_newline(['userID', 'ScreenName', 'followingCount', 'followerCount',
                                                'tweetCount', 'tweetsCollected','firstTweet', 'lastTweet', 'creation_date',
                                                'urlCount', 'mentionCount']))

    pool = Pool(int(sys.argv[2]))

    results = pool.map(get_user_info, onlyfiles)

    for res in results:
        uid = res['uid']
        if res['description']:
            d_file = codecs.open(dir1 + "/descriptions/" + res['uid'] + ".txt", "w", "utf8")
            d_file.write(res['description'])
            d_file.close()
        if res['friends'] is not None:
            for f in res['friends']:
                friend_file.write(tab_stringify_newline([uid, f]))
        if res['followers'] is not None:
            for q in res['followers']:
                friend_file.write(tab_stringify_newline([q, uid]))
        for lang, count in res['lang'].items():
            lang_file.write(tab_stringify_newline([uid, lang, count]))
        for g in res['geotags']:
            geo_file.write(tab_stringify_newline([uid, g[0], g[1], g[2]]))
        for h in res['hashtags']:
            user_ht_file.write(tab_stringify_newline([uid, h[0], h[1],h[2]]))
        for hh in res['hashtagEdges']:
            ht_ht_file.write(tab_stringify_newline([uid,hh[0], hh[1],hh[2],hh[3]]))
        for m in res['mentions']:
            mention_file.write(tab_stringify_newline([uid, m[0], m[1],m[2]]))
        for url in res['urlLinks']:
            user_url_file.write(tab_stringify_newline([uid, url[0], url[1],url[2],url[3]]))
        for u in res['urlmentions']:
            url_mention_file.write(tab_stringify_newline([uid, u[0], u[1],u[2],u[3]]))
        if res['attributes'] is not None:
            attribute_file.write(tab_stringify_newline(res['attributes']))

    pool.close()

    friend_file.close()
    user_ht_file.close()
    user_url_file.close()
    ht_ht_file.close()
    mention_file.close()
    url_mention_file.close()
    geo_file.close()
    lang_file.close()
    retweet_file.close()
    attribute_file.close()


