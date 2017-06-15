__author__ = 'kjoseph'


from twitter_dm import TwitterApplicationHandler

users = [
    'mondaytuesday88',
    'returnhatangle',
    'blademistake',
    'caresouthwake',
    'milkroddanger',
    'drumsecret',
    'faceclubcause',
    'norconvenient',
    'claimchairman',
    'mondaytuesday01',
    'PoisonJacquespl',
    'mcduffmonsterma',
    'robertalotias',
    'doctorablotata',
]

app_info = [ ['rrJL7zuoaekldDElRnE059nc5','N7uZYZj98J1LIlEEACp8k5f6ZaUVtsv05qaoB8KnJixYjqH40h']]

for user in users:
    for app in app_info:
        handler = TwitterApplicationHandler(consumer_key=app[0],consumer_secret=app[1],pathToConfigFile=app[0]+".txt")
        handler.init_session(user)
