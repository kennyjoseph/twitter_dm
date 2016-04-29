__author__ = 'kjoseph'


from twitter_dm import TwitterApplicationHandler

users = [   'USER_1','USER_2']

app_info = [
                ['CONSUMER_KEY_1', 'CONSUMER_SECRET_1'],
                ['CONSUMER_KEY_2', 'CONSUMER_SECRET_2'],
            ]

for app in app_info:
    handler = TwitterApplicationHandler(consumer_key=app[0],consumer_secret=app[1],pathToConfigFile=app[0]+".txt")
    for user in users:
        handler.init_session(user)
