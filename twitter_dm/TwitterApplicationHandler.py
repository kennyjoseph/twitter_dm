"""
This class handles users that have authed to a specific application.

It accepts a configuration file in the following format:
APP_KEY,APP_SECRET
FIRST_USER_AUTHED_TO_THIS_APP_SCREENNAME,FIRST_USER_AUTHED_TO_THIS_APP__KEY,FIRST_USER_AUTHED_TO_THIS_APP_SECRET
SECOND_USER_AUTHED_TO_THIS_APP_SCREENNAME,SECOND_USER_AUTHED_TO_THIS_APP__KEY,SECOND_USER_AUTHED_TO_THIS_APP_SECRET
THIRD_USER_AUTHED_TO_THIS_APP_SCREENNAME,THIRD_USER_AUTHED_TO_THIS_APP__KEY,THIRD_USER_AUTHED_TO_THIS_APP_SECRET
...

"""

__author__ = 'pmlandwehr|kjoseph'

import codecs
import os

from rauth import OAuth1Service

from TwitterAPIHook import TwitterAPIHook


class TwitterApplicationHandler:
    ###################################################
    ###########SESSION HANDLING METHODS###########
    ###################################################
    def __init__(self, pathToConfigFile=None,
                 consumer_key=None,
                 consumer_secret=None,
                 silent=False):

        if pathToConfigFile is None and consumer_key is None:
            raise Exception("Need a config file and/or consumer_key")

        if consumer_key is not None:
            print 'got key from constructor'
            self.consumer_key = consumer_key
        if consumer_secret is not None:
            print 'got secret from constructor'
            self.consumer_secret = consumer_secret

        self.knownUserDict = {}
        if pathToConfigFile is not None:
            self.configFileName = pathToConfigFile
        else:
            self.configFileName = str(consumer_key) + ".txt"
        if not os.path.exists(self.configFileName):
            outfile = codecs.open(self.configFileName, 'w', 'utf8')
            outfile.write(','.join([self.consumer_key,self.consumer_secret])+'\n')
            outfile.close()

        self.load_known_users(silent)

        self.twitter = OAuth1Service(
            name='twitter',
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            request_token_url='https://api.twitter.com/oauth/request_token',
            access_token_url='https://api.twitter.com/oauth/access_token',
            authorize_url='https://api.twitter.com/oauth/authorize',
            base_url='https://api.twitter.com/1.1/')

        self.api_hooks = []
        for name in self.knownUserDict.keys():
            self.api_hooks.append(TwitterAPIHook(self.consumer_key, self.consumer_secret, self.init_session(name)))

    def new_session(self, username):
        request_token, request_token_secret = self.twitter.get_request_token()
        authorize_url = self.twitter.get_authorize_url(request_token)
        print('{un} : Visit this URL in your browser: {url}'.format(un=username,url=authorize_url))

        try:
            pin = raw_input('Enter PIN from browser: ')
        except NameError:
            pin = input('Enter PIN from browser: ')

        session = self.twitter.get_auth_session(request_token, request_token_secret, method='POST',
                                                data={'oauth_verifier': pin})
        # Print token for reference / saving
        print(session.access_token, session.access_token_secret)


        # Write token to known user file.
        outfile = codecs.open(self.configFileName, 'a', 'utf8')
        outfile.write(','.join([username, session.access_token, session.access_token_secret])+'\n')
        outfile.close()

        return session

    def reuse_session(self, user):
        access_token, access_token_secret = self.knownUserDict[user]
        session = self.twitter.get_session((access_token, access_token_secret))
        return session


    def init_new_user(self,user):
        if user in self.knownUserDict:
            print 'already have user'
            return
        self.api_hooks.append(TwitterAPIHook(self.consumer_key, self.consumer_secret, self.init_session(user)))

    def init_session(self, user=''):
        if user == '':
            try:
                user = raw_input('Enter user to be tied to this session: ')
            except NameError:
                user = input('Enter user to be tied to this session: ')

        if user in self.knownUserDict:
            session = self.reuse_session(user)
        else:
            session = self.new_session(user)

        return session

    def load_known_users(self, silent=False):
        if not silent:
            print('Loading known users...')
        if not os.path.exists(self.configFileName):
            return
        try:
            lines = codecs.open(self.configFileName, 'r', 'utf8').readlines()

            # the first line now may be app token, app secret. Check
            first_line_split = lines[0].strip().split(',')
            if len(first_line_split) == 2:
                if not silent:
                    print('got consumer key and secret from config file')
                self.consumer_key = first_line_split[0]
                self.consumer_secret = first_line_split[1]
            elif len(first_line_split) == 4:
                self.knownUserDict[first_line_split[0]] = (first_line_split[1], first_line_split[2])
            else:
                raise Exception("First line is not a user or app info")

            for line in lines[1:]:
                user, user_access_token, user_access_token_secret = line.strip().split(',')
                self.knownUserDict[user] = (user_access_token, user_access_token_secret)
                if not silent:
                    print(' Got', user)
        except:
            raise Exception("Config file not specified correctly")
