__author__ = 'kjoseph'


from twitter_dm import TwitterApplicationHandler

users = [
    'BenigniMatthew',
    'BotResearcher',
    'ungaBunga5000',
    'ungaBunga5001',
]

app_info = [ ['q6ynzUTI2hVuYSCtkCCgWJBnw','jNIN9CFF0gysebKJGjKsnle9tIDd7TDBkquXz0uFWVAaseFPw3']]

for user in users:
    for app in app_info:
        handler = TwitterApplicationHandler(consumer_key=app[0],consumer_secret=app[1],pathToConfigFile=app[0]+".txt")
        handler.init_session(user)
